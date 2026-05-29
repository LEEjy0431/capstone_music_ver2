import os
import sys

from module1 import extract_notes_from_sheet, get_sheet_bpm, get_last_detected_bpm
from module2 import extract_notes_from_audio
from module3 import compare_notes
from chord_upgrade import verify_missed_notes

def check_file_exists(path, label):
    if not os.path.exists(path):
        print(f"\n[오류] {label} 파일을 찾을 수 없음: {os.path.abspath(path)}")
        parent = os.path.dirname(os.path.abspath(path)) or '.'
        if os.path.isdir(parent):
            print(f"  '{parent}' 안의 파일:")
            for f in sorted(os.listdir(parent)):
                tag = '[폴더]' if os.path.isdir(os.path.join(parent, f)) else '[파일]'
                print(f"    {tag} {f}")
        return False
    return True


def _score_grade(score: float) -> str:
    """점수 → 등급 문자열."""
    if score >= 95: return 'S  (완벽)'
    if score >= 85: return 'A  (우수)'
    if score >= 70: return 'B  (양호)'
    if score >= 55: return 'C  (보통)'
    if score >= 40: return 'D  (미흡)'
    return          'F  (불합격)'


def _bar(value: float, total: float, width: int = 20) -> str:
    """간단한 텍스트 진행 바."""
    filled = int(round(value / total * width)) if total else 0
    return '█' * filled + '░' * (width - filled)


def _note_str(n: dict) -> str:
    """음표 하나를 읽기 쉬운 문자열로."""
    return f"{n.get('note', '?'):>4}  ({n.get('start', 0):.2f}초)"


def _print_note_list(notes: list, label: str, limit: int = 5) -> None:
    if not notes:
        return
    shown = notes[:limit]
    print(f"\n  [{label}]")
    for n in shown:
        print(f"    • {_note_str(n)}")
    if len(notes) > limit:
        print(f"    … 외 {len(notes) - limit}개")

if __name__ == '__main__':

    manual_bpm = None
    if len(sys.argv) >= 3:
        target_sheet_file = sys.argv[1]
        user_audio_file   = sys.argv[2]
        if len(sys.argv) >= 4:
            try:
                manual_bpm = float(sys.argv[3])
            except ValueError:
                print(f'[경고] BPM 인자 "{sys.argv[3]}"이 숫자가 아닙니다. 자동 감지를 사용합니다.')
    else:
        target_sheet_file = 'data/piano_sheet_3.pdf'
        user_audio_file   = 'data/piano_record_3.wav'

    print('=' * 50)
    print('          피아노 연주 자동 평가 시스템')
    print('=' * 50)

    if not check_file_exists(target_sheet_file, '정답 악보'): sys.exit(1)
    if not check_file_exists(user_audio_file,   '연주 WAV'):  sys.exit(1)

    # ── 1. 악보 분석 ──────────────────────────────────────────
    print('\n[1단계] 정답 악보 분석 중...')
    sheet_bpm = get_sheet_bpm(target_sheet_file)
    if sheet_bpm:
        print(f'  BPM 감지: {sheet_bpm}')
    else:
        print('  BPM 감지 실패 → OMR 분석 후 결정')

    sheet_music_data = extract_notes_from_sheet(target_sheet_file)
    if not sheet_music_data:
        print('\n[오류] 정답 악보 추출 실패')
        sys.exit(1)

    if sheet_bpm is None:
        sheet_bpm = get_last_detected_bpm()
        if sheet_bpm:
            print(f'  OMR BPM 감지: {sheet_bpm}')
        else:
            print('  BPM 감지 실패 → 안전 모드 (quantize 비활성)')

    if manual_bpm is not None:
        print(f'  BPM 수동 지정: {manual_bpm} (감지값 {sheet_bpm} 무시)')
        sheet_bpm = manual_bpm

    print(f'  악보 음표 수: {len(sheet_music_data)}개')

    # ── 2. 연주 분석 ──────────────────────────────────────────
    print('\n[2단계] 연주 오디오 분석 중...')
    user_performance_data = extract_notes_from_audio(user_audio_file, bpm=sheet_bpm)
    if not user_performance_data:
        print('[오류] 연주 오디오 추출 실패')
        sys.exit(1)
    print(f'  감지된 음표 수: {len(user_performance_data)}개')

    # ── 3. 채점 ───────────────────────────────────────────────
    print('\n[3단계] 채점 중...')
    result = compare_notes(sheet_music_data, user_performance_data)

    # ── 4. 검증 ───────────────────────────────────────────────
    print('\n[4단계] 누락 음표 오디오 검증 중...')
    rescued, truly_missed = verify_missed_notes(
        user_audio_file,
        result['missed_notes_full'],
        snr_threshold=2.5,
    )

    # ── 최종 수치 계산 ────────────────────────────────────────
    # 와이드/옥타브 구제 음표도 정답으로 인정 (result['correct']에 이미 포함됨)
    total        = result['total']
    correct      = result['correct'] + len(rescued)
    wrong_timing = result['wide_rescued'] + result['octave_rescued']  # 정답이지만 박자 오차 있음 (참고용)
    missed_count = len(truly_missed)
    extra_count  = result['extra_count']
    final_score  = round(correct / total * 100, 2) if total else 0.0
    avg_dev      = result['avg_timing_deviation']

    wrong_timing_notes = result.get('wrong_timing_notes', [])
    extra_notes        = result.get('extra_notes', [])

    # ── 결과 출력 ─────────────────────────────────────────────
    print()
    print('=' * 50)
    print('                 최종 채점 결과')
    print('=' * 50)

    # 점수 & 등급
    grade = _score_grade(final_score)
    bar   = _bar(correct, total)
    print(f'\n  점수:  {final_score:>6.2f}점  /  100점')
    print(f'  등급:  {grade}')
    print(f'  [{bar}]  {correct} / {total}개')

    # 항목별 요약
    print()
    print(f'     연주한 음표:      {correct:>3}개  / {total}개')
    print(f'     누락된 음표:      {missed_count:>3}개  (안 친 음표)')
    print(f'     여분의 음표:      {extra_count:>3}개  (악보에 없는 음표)')
    if wrong_timing:
        print(f'  ⚠️   박자 오차 참고:  {wrong_timing:>3}개  (정답 인정, 단 박자가 다소 어긋남)')
    print(f'\n  평균 타이밍 오차:  {avg_dev:.3f}초')

    # 음표 목록
    _print_note_list(truly_missed,       '누락된 음표')
    _print_note_list(wrong_timing_notes, '타이밍 오차 음표')
    _print_note_list(extra_notes,        '여분의 음표')