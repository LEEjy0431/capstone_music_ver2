"""
module4.py — LLM 기반 피드백 생성

우선순위:
  1. OLLAMA_MODEL 설정 → 로컬 Qwen 2.5-1.5B (무료, API 키 불필요)
  2. OPENAI_API_KEY 설정 → OpenAI GPT-4o-mini

사용:
    from module4 import generate_feedback
    feedback = generate_feedback(score_dict, lang="ko")
"""

import json
import os
import re
import sys
from urllib import request as urlrequest
from urllib.error import URLError

SUPPORTED_LANGS = {
    "ko": "한국어",
    "en": "English",
    "ja": "日本語",
    "zh": "中文",
}


def _normalize_lang(lang: str) -> str:
    return lang if lang in SUPPORTED_LANGS else "ko"


def _build_prompt(score: dict, lang: str) -> tuple[str, str]:
    lang = _normalize_lang(lang)
    lang_name = SUPPORTED_LANGS[lang]

    total = max(score.get("total", 1), 1)
    missed_pct = score.get("missed_count", 0) / total * 100
    extra_pct  = score.get("extra_count", 0)  / total * 100

    # 언어별 강제 지시어 (소형 모델용)
    lang_instruction = {
        "ko": "반드시 한국어로만 답하세요. All values must be written in Korean (한국어).",
        "en": "Respond in English only.",
        "ja": "必ず日本語のみで回答してください。All values must be in Japanese.",
        "zh": "必须只用中文回答。All values must be in Chinese.",
    }.get(lang, "Respond in Korean.")

    system = (
        f"You are an expert piano teacher. {lang_instruction}\n"
        f"Output ONLY a raw JSON object. No markdown, no explanation, no extra text.\n"
        f'Required JSON keys: "overall" (string), "pitch" (string), "rhythm" (string), '
        f'"timing" (string), "tips" (array of 2-3 strings), "encouragement" (string).\n'
        f"All string values must be written in {lang_name}."
    )

    user = (
        f"피아노 연주 분석 결과 (Piano performance data):\n"
        f"- Score: {score.get('score', 0):.1f}/100\n"
        f"- Correct notes: {score.get('correct', 0)} / {score.get('total', 0)}\n"
        f"- Missed notes: {score.get('missed_count', 0)} ({missed_pct:.1f}%)\n"
        f"- Timing errors: {score.get('wrong_timing_count', 0)}\n"
        f"- Extra notes: {score.get('extra_count', 0)} ({extra_pct:.1f}%)\n"
        f"- Avg timing deviation: {score.get('avg_timing_deviation', 0):.3f}s\n\n"
        f"Write feedback JSON in {lang_name}. Output JSON only."
    )

    return system, user


def _extract_json(raw: str) -> str:
    """LLM 응답에서 JSON 블록을 안전하게 추출."""
    # ```json ... ``` 블록 우선
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw, re.DOTALL)
    if m:
        return m.group(1)
    # { ... } 블록
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if m:
        return m.group(0)
    return raw


def _call_ollama(system: str, user: str) -> str:
    """Ollama OpenAI-compatible API 호출."""
    model = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")
    base  = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    url   = f"{base}/v1/chat/completions"

    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        "temperature": 0.4,
        "max_tokens": 1024,
        "stream": False,
    }).encode("utf-8")

    req = urlrequest.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer ollama",
        },
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())["choices"][0]["message"]["content"]
    except URLError as e:
        raise ConnectionError(
            f"Ollama 연결 실패: {e}\n"
            "Ollama가 실행 중인지 확인하세요: brew services start ollama"
        ) from e


def _call_openai(system: str, user: str) -> str:
    """OpenAI API 호출."""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("pip install openai")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=0.4,
        max_tokens=700,
    )
    return response.choices[0].message.content


def generate_feedback(score: dict, lang: str = "ko") -> dict:
    """
    채점 결과 → LLM 피드백 생성.

    OLLAMA_MODEL 설정 시 로컬 Qwen 사용, 없으면 OpenAI 사용.

    Returns:
        { overall, pitch, rhythm, timing, tips, encouragement }
    """
    system, user = _build_prompt(score, lang)

    use_ollama = bool(os.environ.get("OLLAMA_MODEL"))

    if use_ollama:
        print(f"[module4] Ollama({os.environ['OLLAMA_MODEL']}) 피드백 생성 중...", file=sys.stderr)
        raw = _call_ollama(system, user)
    else:
        print("[module4] OpenAI GPT 피드백 생성 중...", file=sys.stderr)
        raw = _call_openai(system, user)

    json_str = _extract_json(raw)
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"피드백 JSON 파싱 실패: {e}\nraw: {raw}") from e


# ── 단독 실행 테스트 ──────────────────────────────────────────────────
if __name__ == "__main__":
    sample = {
        "score": 83.5, "correct": 67, "total": 80,
        "missed_count": 8, "wrong_timing_count": 5,
        "extra_count": 2, "avg_timing_deviation": 0.087,
    }
    lang = sys.argv[1] if len(sys.argv) > 1 else "ko"
    try:
        result = generate_feedback(sample, lang)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"[오류] {e}", file=sys.stderr)
        sys.exit(1)
