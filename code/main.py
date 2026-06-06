"""
main.py  —  피아노 연주 자동 평가 시스템 진입점

사용법 (콘솔):
    python main.py                                    # 기본 파일로 실행
    python main.py --sheet data/sheet.xml --audio data/rec.wav

Go 백엔드 연동 (JSON 모드):
    python main.py --sheet <path> --audio <path> --json

환경 변수 (.env 또는 export):
    ANTHROPIC_API_KEY=sk-ant-...   Claude Vision fallback 사용 시 필수
    AUDIVERIS_TIMEOUT=300          Audiveris 최대 대기 시간(초)
"""

# ── .env 자동 로드 ─────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import argparse
import json
import os
import sys

from module1 import extract_notes_from_sheet, get_sheet_bpm, get_last_detected_bpm
from module2 import extract_notes_from_audio
from module3 import compare_notes
from chord_upgrade import verify_missed_notes

AUDIVERIS_TIMEOUT = int(os.environ.get('AUDIVERIS_TIMEOUT', '300'))

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')


# ═════════════════════════════════════════════════════════════════
# 유틸리티
# ═════════════════════════════════════════════════════════════════

def check_file_exists(path, label):
    if not os.path.exists(path):
        print(f"\n[오류] {label} 파일을 찾을 수 없음: {os.path.abspath(path)}", file=sys.stderr)
        parent = os.path.dirname(os.path.abspath(path)) or '.'
        if os.path.isdir(parent):
            print(f"  '{parent}' 안의 파일:", file=sys.stderr)
            for f in sorted(os.listdir(parent)):
                tag = '[폴더]' if os.path.isdir(os.path.join(parent, f)) else '[파일]'
                print(f"    {tag} {f}", file=sys.stderr)
        return False
    return True


def _score_grade(score: float) -> str:
    if score >= 95: return 'S  (완벽)'
    if score >= 85: return 'A  (우수)'
    if score >= 70: return 'B  (양호)'
    if score >= 55: return 'C  (보통)'
    if score >= 40: return 'D  (미흡)'
    return          'F  (불합격)'


def _bar(value: float, total: float, width: int = 20) -> str:
    filled = int(round(value / total * width)) if total else 0
    return '█' * filled + '░' * (width - filled)


def _note_str(n: dict) -> str:
    return f"{n.get('note', '?'):>4}  ({n.get('start', 0):.2f}초)"


def _print_note_list(notes: list, label: str, limit: int = 5) -> None:
    if not notes:
        return
    print(f"\n  [{label}]", file=sys.stderr)
    for n in notes[:limit]:
        print(f"    • {_note_str(n)}", file=sys.stderr)
    if len(notes) > limit:
        print(f"    … 외 {len(notes) - limit}개", file=sys.stderr)


# ═════════════════════════════════════════════════════════════════
# 핵심 파이프라인
# ═════════════════════════════════════════════════════════════════

def run_pipeline(sheet_path: str, audio_path: str, manual_bpm: float | None = None) -> dict:
    """
    악보 + 오디오 → 채점 결과 dict 반환.
    오류 시 {'error': '...'} 반환.
    """
    # 1. 악보 분석
    print('[1단계] 정답 악보 분석 중...', file=sys.stderr)
    sheet_bpm = get_sheet_bpm(sheet_path)
    if sheet_bpm:
        print(f'  BPM 감지: {sheet_bpm}', file=sys.stderr)

    sheet_data = extract_notes_from_sheet(sheet_path, audiveris_timeout=AUDIVERIS_TIMEOUT)
    if not sheet_data:
        return {'error': '악보 추출 실패 (oemer/Claude Vision 모두 실패 또는 지원하지 않는 형식)'}

    if sheet_bpm is None:
        sheet_bpm = get_last_detected_bpm()
        if sheet_bpm:
            print(f'  OMR BPM 감지: {sheet_bpm}', file=sys.stderr)
        else:
            print('  BPM 미감지 → quantize 비활성', file=sys.stderr)

    if manual_bpm is not None:
        sheet_bpm = manual_bpm
        print(f'  BPM 수동 지정: {manual_bpm}', file=sys.stderr)

    print(f'  악보 음표: {len(sheet_data)}개', file=sys.stderr)

    # 2. 연주 분석
    print('[2단계] 연주 오디오 분석 중...', file=sys.stderr)
    audio_data = extract_notes_from_audio(audio_path, bpm=sheet_bpm)
    if not audio_data:
        return {'error': '오디오 트랜스크립션 실패'}
    print(f'  감지된 음표: {len(audio_data)}개', file=sys.stderr)

    # 3. 1차 채점 (5단계 매칭)
    print('[3단계] 채점 중...', file=sys.stderr)
    result = compare_notes(sheet_data, audio_data)

    # 4. 누락 음표 오디오 검증
    print('[4단계] 누락 음표 오디오 검증 중...', file=sys.stderr)
    rescued, truly_missed = verify_missed_notes(
        audio_path,
        result['missed_notes_full'],
        snr_threshold=2.5,
    )

    # 최종 수치
    total         = result['total']
    correct       = result['correct'] + len(rescued)
    final_score   = round(correct / total * 100, 2) if total else 0.0
    missed_count  = len(truly_missed)

    return {
        'score':               final_score,
        'correct':             correct,
        'total':               total,
        'missed_count':        missed_count,
        'wrong_timing_count':  result.get('wide_rescued', 0) + result.get('octave_rescued', 0),
        'extra_count':         result.get('extra_count', 0),
        'avg_timing_deviation': result.get('avg_timing_deviation', 0.0),
        # 상세 매칭 내역 (Go 모델에서 추가 필드로 사용)
        'direct_matched':      result.get('direct_matched', 0),
        'sustain_matched':     result.get('sustain_matched', 0),
        'wide_rescued':        result.get('wide_rescued', 0),
        'octave_rescued':      result.get('octave_rescued', 0),
        'score_aware_rescued': len(rescued),
        # 음표 목록 (최대 5개)
        'missed_notes':        truly_missed[:5],
        'wrong_timing_notes':  result.get('extra_notes', [])[:5],
        'extra_notes':         result.get('extra_notes', [])[:5],
    }


# ═════════════════════════════════════════════════════════════════
# 콘솔 출력
# ═════════════════════════════════════════════════════════════════

def print_console_result(result: dict) -> None:
    if 'error' in result:
        print(f"\n[오류] {result['error']}", file=sys.stderr)
        return

    score        = result['score']
    correct      = result['correct']
    total        = result['total']
    missed_count = result['missed_count']
    extra_count  = result['extra_count']
    wrong_timing = result['wrong_timing_count']
    avg_dev      = result['avg_timing_deviation']

    print()
    print('=' * 50)
    print('                 최종 채점 결과')
    print('=' * 50)

    grade = _score_grade(score)
    bar   = _bar(correct, total)
    print(f'\n  점수:  {score:>6.2f}점  /  100점')
    print(f'  등급:  {grade}')
    print(f'  [{bar}]  {correct} / {total}개')

    print()
    print(f'  ├─ 직접 매칭:    {result.get("direct_matched", 0):>3}개')
    print(f'  ├─ 지속음 매칭:  {result.get("sustain_matched", 0):>3}개')
    print(f'  ├─ 와이드 구제:  {result.get("wide_rescued", 0):>3}개')
    print(f'  ├─ 옥타브 구제:  {result.get("octave_rescued", 0):>3}개')
    print(f'  └─ Audio 검증:   {result.get("score_aware_rescued", 0):>3}개')
    print()
    print(f'  누락된 음표:     {missed_count:>3}개')
    print(f'  여분의 음표:     {extra_count:>3}개')
    if wrong_timing:
        print(f'  박자 오차 참고:  {wrong_timing:>3}개  (정답 인정, 박자 다소 어긋남)')
    print(f'\n  평균 타이밍 오차:  {avg_dev:.3f}초')

    _print_note_list(result.get('missed_notes', []),       '누락된 음표')
    _print_note_list(result.get('wrong_timing_notes', []), '타이밍 오차 음표')
    _print_note_list(result.get('extra_notes', []),        '여분의 음표')


# ═════════════════════════════════════════════════════════════════
# 진입점
# ═════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='피아노 연주 자동 평가 시스템')
    parser.add_argument('--sheet', required=True,
                        help='악보 파일 경로 (xml/mxl/mid/png/jpg/jpeg/pdf)')
    parser.add_argument('--audio', required=True,
                        help='연주 WAV 파일 경로')
    parser.add_argument('--bpm',  type=float, default=None,
                        help='BPM 수동 지정 (미입력 시 자동 감지)')
    parser.add_argument('--lang', default='ko', choices=['ko', 'en', 'ja', 'zh'],
                        help='피드백 언어')
    parser.add_argument('--json', dest='json_mode', action='store_true',
                        help='채점 결과를 JSON으로 stdout 출력 (Go 백엔드 연동용)')
    args = parser.parse_args()

    if not check_file_exists(args.sheet, '정답 악보'): sys.exit(1)
    if not check_file_exists(args.audio, '연주 WAV'):  sys.exit(1)

    # ── JSON 모드 (Go subprocess 연동) ────────────────────────
    if args.json_mode:
        # module1/2/3의 print() 로그가 stdout을 오염시키지 않도록
        # 파이프라인 실행 중 stdout → stderr로 리다이렉트
        _real_stdout = sys.stdout
        sys.stdout = sys.stderr
        try:
            result = run_pipeline(args.sheet, args.audio, manual_bpm=args.bpm)
        except Exception as e:
            result = {'error': str(e)}
        finally:
            sys.stdout = _real_stdout
        print(json.dumps(result, ensure_ascii=False))
        if 'error' in result:
            sys.exit(1)
        return

    # ── 콘솔 모드 ─────────────────────────────────────────────
    print('=' * 50)
    print('          피아노 연주 자동 평가 시스템')
    print('=' * 50)

    result = run_pipeline(args.sheet, args.audio, manual_bpm=args.bpm)
    print_console_result(result)

    if 'error' in result:
        sys.exit(1)


if __name__ == '__main__':
    main()
