"""
module4.py — LLM 기반 한국어 피드백 생성

우선순위:
  1. OLLAMA_MODEL 설정 → 로컬 Qwen 2.5-1.5B (무료, API 키 불필요)
  2. OPENAI_API_KEY 설정 → OpenAI GPT-4o-mini

사용:
    from module4 import generate_feedback
    feedback = generate_feedback(score_dict)
"""

import json
import os
import re
import sys
from urllib import request as urlrequest
from urllib.error import URLError

def _build_prompt(score: dict, lang: str = "ko") -> tuple[str, str]:
    """한국어 피드백 프롬프트 생성 (lang 파라미터는 호환성 유지용, 항상 ko 사용)."""
    total = max(score.get("total", 1), 1)
    missed_pct = score.get("missed_count", 0) / total * 100
    extra_pct  = score.get("extra_count", 0)  / total * 100

    # 점수 구간별 톤 지시 및 few-shot 예시
    s = score.get('score', 0)
    if s >= 85:
        tone = "점수가 높습니다. 긍정적이고 격려하는 톤으로 작성하되, 더 발전할 부분도 언급하세요."
        example = ('{"overall":"연주가 전반적으로 매우 훌륭합니다. 정확한 음정과 안정된 박자가 인상적입니다.",'
                   '"pitch":"음정 정확도가 매우 높습니다. 표현력을 더 높이면 완벽해질 것입니다.",'
                   '"rhythm":"박자가 안정적이고 리듬감이 좋습니다.",'
                   '"timing":"타이밍이 정확합니다. 빠른 구간에서도 흔들림이 없습니다.",'
                   '"tips":["다양한 다이나믹 표현을 연습해보세요.","감정 표현을 더 풍부하게 해보세요."],'
                   '"encouragement":"훌륭한 연주입니다. 이 수준을 유지하면서 더욱 발전하세요!"}')
    elif s >= 65:
        tone = "점수가 평균 수준입니다. 잘된 부분은 칭찬하고, 부족한 부분은 구체적으로 지적하세요."
        example = ('{"overall":"전반적으로 보통 수준의 연주입니다. 일부 음표는 정확했지만 누락된 음표가 많아 개선이 필요합니다.",'
                   '"pitch":"음정 정확도가 부분적으로 좋지만, 일부 구간에서 음을 놓쳤습니다.",'
                   '"rhythm":"리듬이 불안정한 구간이 있습니다. 박자 연습이 필요합니다.",'
                   '"timing":"타이밍 오차가 다소 있습니다. 느린 템포부터 연습하세요.",'
                   '"tips":["메트로놈과 함께 느린 속도로 연습하세요.","어려운 구간을 반복 연습하세요."],'
                   '"encouragement":"꾸준히 연습하면 반드시 실력이 향상될 것입니다."}')
    elif s >= 40:
        tone = "점수가 낮습니다. 부족한 점을 명확하고 직접적으로 지적하세요. 거짓 칭찬은 하지 마세요."
        example = ('{"overall":"연주에 많은 부분이 부족합니다. 정확한 음표 수가 적고 누락된 음표가 많습니다. 기초부터 다시 연습이 필요합니다.",'
                   '"pitch":"음정 정확도가 낮습니다. 악보를 정확히 읽고 각 음을 익히는 연습이 필요합니다.",'
                   '"rhythm":"리듬이 전반적으로 불안정합니다. 박자 감각을 기르는 것이 우선입니다.",'
                   '"timing":"타이밍 오차가 큽니다. 메트로놈을 사용하여 정확한 박자 감각을 키우세요.",'
                   '"tips":["악보를 먼저 충분히 읽고 음을 익힌 후 연주하세요.","매우 느린 속도로 정확하게 연습하세요.","메트로놈을 항상 사용하세요."],'
                   '"encouragement":"지금은 힘들더라도 꾸준히 연습하면 반드시 나아질 것입니다."}')
    else:
        tone = "점수가 매우 낮습니다. 대부분의 음표를 놓쳤습니다. 솔직하게 많이 틀렸다고 말하고, 기초부터 다시 시작해야 한다고 명확히 알려주세요. 거짓 칭찬은 절대 하지 마세요."
        example = ('{"overall":"연주 점수가 매우 낮습니다. 대부분의 음표를 놓쳤으며, 기초 연습이 많이 부족한 상태입니다. 기초부터 다시 시작해야 합니다.",'
                   '"pitch":"정확히 연주된 음표가 매우 적습니다. 악보의 음표를 하나씩 정확히 익히는 것부터 시작하세요.",'
                   '"rhythm":"리듬과 박자가 전혀 맞지 않습니다. 박자 연습을 최우선으로 해야 합니다.",'
                   '"timing":"악보와 연주 음원이 일치하는지 먼저 확인하세요.",'
                   '"tips":["올바른 악보와 음원을 사용하고 있는지 확인하세요.","한 마디씩 아주 천천히 연습하세요.","기초 음계 연습부터 다시 시작하세요."],'
                   '"encouragement":"지금은 많이 부족하지만, 기초부터 차근차근 연습하면 반드시 나아질 것입니다."}')

    missed_detail = _format_missed_notes(
        score.get('missed_notes_detail', score.get('missed_notes', [])),
        score.get('bpm', 120.0)
    )

    system = (
        "당신은 전문 피아노 선생님입니다. 학생의 연주 분석 결과를 보고 솔직하고 정확한 피드백을 작성합니다.\n"
        "반드시 순수 한국어(한글)로만 답하세요. 영어, 한자, 중국어를 절대 사용하지 마세요.\n\n"
        f"[톤 지침] {tone}\n\n"
        "아래 JSON 형식으로만 답하세요. 다른 텍스트는 절대 쓰지 마세요.\n"
        f"출력 예시:\n{example}"
    )

    user = (
        f"피아노 연주 분석 결과:\n"
        f"- 점수: {s:.1f}점 / 100점\n"
        f"- 정확한 음표: {score.get('correct', 0)}개 / {score.get('total', 0)}개\n"
        f"- 누락된 음표: {score.get('missed_count', 0)}개 ({missed_pct:.1f}%)\n"
        f"- 박자 오류: {score.get('wrong_timing_count', 0)}개\n"
        f"- 여분의 음표: {score.get('extra_count', 0)}개 ({extra_pct:.1f}%)\n"
        f"- 평균 타이밍 오차: {score.get('avg_timing_deviation', 0):.3f}초\n"
        f"- BPM: {score.get('bpm', 120):.0f}\n\n"
        f"[마디별 누락 음표 — 이 목록에 있는 음표만 언급하세요]\n{missed_detail}\n\n"
        "주의: 위 누락 음표 목록에 없는 음이름을 절대 만들어내지 마세요.\n"
        "'overall'과 'pitch' 항목에 위 목록을 참고해 '마디 X에서 Y음을 놓쳤습니다' 형식으로 구체적으로 언급하세요.\n"
        "위 결과를 바탕으로 실제 점수에 맞는 솔직한 한국어 피드백 JSON을 작성하세요."
    )

    return system, user


def _format_missed_notes(notes: list, bpm: float = 120.0) -> str:
    """누락 음표를 마디별로 그룹화해 '마디 1: C4, E4 / 마디 3: G4' 형식으로 반환."""
    if not notes:
        return "없음"
    spb = 60.0 / max(bpm, 1)
    spm = spb * 4  # 4/4 박자 기준

    by_measure: dict[int, list[str]] = {}
    for n in notes:
        start = n.get('start', 0)
        measure = n.get('measure') or (int(start / spm) + 1 if spm > 0 else 1)
        note_name = n.get('note', '?')
        by_measure.setdefault(measure, []).append(note_name)

    parts = [f"마디 {m}: {', '.join(ns)}" for m, ns in sorted(by_measure.items())]
    result = " / ".join(parts)
    return result[:400] + "..." if len(result) > 400 else result


def _contains_cjk(text: str) -> bool:
    """한자/중국어/일본어 문자 포함 여부 확인."""
    for ch in text:
        cp = ord(ch)
        if 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF:
            return True
    return False


def _contains_hangul(text: str) -> bool:
    """한글 포함 여부 확인."""
    for ch in text:
        cp = ord(ch)
        if 0xAC00 <= cp <= 0xD7A3 or 0x1100 <= cp <= 0x11FF or 0x3130 <= cp <= 0x318F:
            return True
    return False


def _feedback_contains_cjk(feedback: dict) -> bool:
    """피드백 dict의 모든 문자열 필드에 한자가 있는지 확인."""
    fields = [feedback.get(k, "") for k in ("overall", "pitch", "rhythm", "timing", "encouragement")]
    fields += feedback.get("tips", [])
    return any(_contains_cjk(f) for f in fields)


def _feedback_is_korean(feedback: dict) -> bool:
    """피드백이 실제로 한국어로 작성됐는지 확인 (한글 문자 존재 여부)."""
    fields = [feedback.get(k, "") for k in ("overall", "pitch", "rhythm", "timing", "encouragement")]
    fields += feedback.get("tips", [])
    full_text = " ".join(fields)
    return _contains_hangul(full_text)


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
        "temperature": 0.1,
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


def generate_feedback(score: dict, lang: str = "ko", max_retry: int = 2) -> dict:
    """
    채점 결과 → LLM 피드백 생성.

    OLLAMA_MODEL 설정 시 로컬 Qwen 사용, 없으면 OpenAI 사용.
    한자 혼입 감지 시 max_retry회 재시도.

    Returns:
        { overall, pitch, rhythm, timing, tips, encouragement }
    """
    system, user = _build_prompt(score, lang)
    use_ollama = bool(os.environ.get("OLLAMA_MODEL"))
    caller = _call_ollama if use_ollama else _call_openai
    model_name = os.environ.get("OLLAMA_MODEL", "OpenAI GPT")

    last_err = None
    for attempt in range(1, max_retry + 1):
        print(f"[module4] {model_name} 피드백 생성 중... (시도 {attempt}/{max_retry})", file=sys.stderr)
        try:
            raw = caller(system, user)
            json_str = _extract_json(raw)
            feedback = json.loads(json_str)

            # 한국어 요청 시 한자 혼입 또는 한글 미포함 → 재시도
            if lang == "ko":
                if _feedback_contains_cjk(feedback):
                    print("[module4] 한자 혼입 감지, 재시도...", file=sys.stderr)
                    last_err = ValueError("한자 혼입")
                    continue
                if not _feedback_is_korean(feedback):
                    print("[module4] 한국어 미포함 (영어로 응답), 재시도...", file=sys.stderr)
                    last_err = ValueError("한국어 미포함")
                    continue

            return feedback
        except (json.JSONDecodeError, ValueError) as e:
            last_err = e
            continue

    raise ValueError(f"피드백 생성 실패 ({max_retry}회 시도): {last_err}")


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
