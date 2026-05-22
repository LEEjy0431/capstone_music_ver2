from module1 import extract_notes_from_sheet, get_sheet_bpm, get_last_detected_bpm
from module2 import extract_notes_from_audio
from module3 import compare_notes
from chord_upgrade import verify_missed_notes
import os
import sys


def check_file_exists(path, label):
    if not os.path.exists(path):
        print(f"\n[오류] {label} 파일을 찾을 수 없음: {os.path.abspath(path)}")
        parent = os.path.dirname(os.path.abspath(path)) or '.'
        if os.path.isdir(parent):
            print(f"  '{parent}' 안의 파일:")
            for f in sorted(os.listdir(parent)):
                tag = '[D]' if os.path.isdir(os.path.join(parent, f)) else '[F]'
                print(f"    {tag} {f}")
        return False
    return True


if __name__ == '__main__':

    # ── 파일 경로 설정 ──────────────────────────
    # 직접 수정하거나, 실행 시 인자로 넘길 수 있습니다.
    # 예: python main.py data/sheet.xml data/record.wav
    if len(sys.argv) == 3:
        target_sheet_file = sys.argv[1]
        user_audio_file   = sys.argv[2]
    else:
        target_sheet_file = 'data/T+Tik Tak Tok.xml'
        user_audio_file   = 'data/T+Tik Tak Tok.wav'

    print('=== 피아노 연주 자동 평가 시스템 ===\n')

    if not check_file_exists(target_sheet_file, '정답 악보'): exit(1)
    if not check_file_exists(user_audio_file,   '연주 WAV'):  exit(1)

    # ── 1. 정답 악보 분석 ──────────────────────
    print('1. 정답 악보 분석 중...')

    sheet_bpm = get_sheet_bpm(target_sheet_file)
    if sheet_bpm:
        print(f'-> BPM 감지 성공: {sheet_bpm}')
    else:
        print('-> BPM 감지 실패 → 악보 분석 후 결정')

    sheet_music_data = extract_notes_from_sheet(target_sheet_file)
    if not sheet_music_data:
        print('[오류] 정답 악보 추출 실패'); exit(1)

    # 이미지/PDF 입력이면 Claude Vision이 BPM을 감지했을 수 있음
    if sheet_bpm is None:
        sheet_bpm = get_last_detected_bpm()
        if sheet_bpm:
            print(f'-> Claude Vision BPM 감지: {sheet_bpm}')
        else:
            print('-> BPM 감지 실패 → 안전 모드 (quantize 비활성)')

    print(f'-> 총 {len(sheet_music_data)}개 음표\n')

    # ── 2. 연주 WAV 분석 ───────────────────────
    print('2. 연주 WAV 분석 중 (트랜스크립션)...')
    user_performance_data = extract_notes_from_audio(user_audio_file, bpm=sheet_bpm)
    if not user_performance_data:
        print('[오류] 연주 오디오 추출 실패'); exit(1)
    print(f'-> 총 {len(user_performance_data)}개 음표\n')

    # ── 3. 1차 채점 ─────────────────────────────
    print('3. 1차 채점 (5단계 매칭)...')
    result = compare_notes(sheet_music_data, user_performance_data)
    primary_score = result['score']
    print(f'-> 1차 점수: {primary_score}점\n')

    # ── 4. Score-aware 검증 ─────────────────────
    print('4. Score-aware audio 검증...')
    rescued, truly_missed = verify_missed_notes(
        user_audio_file,
        result['missed_notes_full'],
        snr_threshold=2.5
    )

    result['correct']            += len(rescued)
    result['missed_count']        = len(truly_missed)
    result['missed_notes']        = truly_missed[:5]
    result['score']               = round(result['correct'] / result['total'] * 100, 2)
    result['score_aware_rescued'] = len(rescued)

    # ── 5. 결과 출력 ────────────────────────────
    print(f"\n{'='*44}")
    print(f"             최종 채점 결과")
    print(f"{'='*44}")
    print(f"점수:              {result['score']}점 / 100점")
    print(f"  (1차 {primary_score} → +{round(result['score'] - primary_score, 2)})")
    print(f"정확한 음표:       {result['correct']} / {result['total']}개")
    print(f"  ├─ 직접 매칭:    {result['direct_matched']}개")
    print(f"  ├─ 지속음 매칭:  {result['sustain_matched']}개")
    print(f"  ├─ 와이드 구제:  {result['wide_rescued']}개")
    print(f"  ├─ 옥타브 구제:  {result['octave_rescued']}개")
    print(f"  └─ Audio 검증:   {result['score_aware_rescued']}개")
    print(f"실제 누락:         {result['missed_count']}개")
    print(f"여분의 음표:       {result['extra_count']}개")
    print(f"평균 timing 오차:  {result['avg_timing_deviation']}초")

    if result['missed_notes']:
        print(f"\n[실제로 안 친 음표]")
        for n in result['missed_notes']:
            print(f"  - {n.get('note','?')} (pitch={n['pitch']}) "
                  f"@ {n['start']}s  [SNR={n.get('verify_snr','?')}]")