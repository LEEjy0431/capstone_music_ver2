import os
import sys
import json
from openai import OpenAI

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

    system = (
        f"You are an expert piano teacher providing constructive and encouraging feedback.\n"
        f"Based on the performance analysis data, generate specific and motivating feedback.\n"
        f"You MUST respond ONLY in {lang_name} ({lang}).\n"
        f"You MUST respond ONLY in valid JSON with exactly this structure, no extra text:\n"
        '{\n'
        '  "overall": "2-3 sentence overall evaluation",\n'
        '  "pitch": "1-2 sentence pitch accuracy feedback",\n'
        '  "rhythm": "1-2 sentence rhythm/beat feedback",\n'
        '  "timing": "1-2 sentence timing feedback",\n'
        '  "tips": ["improvement tip 1", "improvement tip 2", "improvement tip 3"],\n'
        '  "encouragement": "1 sentence encouraging message"\n'
        '}'
    )

    user = (
        f"Piano performance analysis result:\n"
        f"- Final score: {score.get('score', 0):.1f} / 100\n"
        f"- Correct notes: {score.get('correct', 0)} / {score.get('total', 0)}\n"
        f"- Missed notes: {score.get('missed_count', 0)}\n"
        f"- Timing errors: {score.get('wrong_timing_count', 0)}\n"
        f"- Extra (unintended) notes: {score.get('extra_count', 0)}\n"
        f"- Average timing deviation: {score.get('avg_timing_deviation', 0):.3f} seconds\n\n"
        f"Generate the feedback JSON based on this data."
    )

    return system, user


def generate_feedback(score: dict, lang: str = "ko") -> dict:
    """
    module3 채점 결과를 받아 GPT 기반 피드백을 생성한다.

    Args:
        score: module3.compare_notes() 반환값
        lang: 피드백 언어 코드 (ko / en / ja / zh)

    Returns:
        { overall, pitch, rhythm, timing, tips, encouragement }
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

    client = OpenAI(api_key=api_key)
    system_prompt, user_prompt = _build_prompt(score, lang)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.7,
    )

    raw = response.choices[0].message.content
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"GPT 응답 JSON 파싱 실패: {e}\nraw: {raw}") from e


# 단독 실행 테스트
if __name__ == "__main__":
    sample_score = {
        "score": 83.5,
        "correct": 67,
        "total": 80,
        "missed_count": 8,
        "wrong_timing_count": 5,
        "extra_count": 2,
        "avg_timing_deviation": 0.087,
    }
    lang = sys.argv[1] if len(sys.argv) > 1 else "ko"
    result = generate_feedback(sample_score, lang)
    print(json.dumps(result, ensure_ascii=False, indent=2))
