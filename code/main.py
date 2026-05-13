from module1 import extract_notes_from_sheet, get_sheet_bpm
from module2 import extract_notes_from_audio
from module3 import compare_notes
import os


if __name__ == "__main__":
    target_sheet_file = "data/T+Tik Tak Tok.xml"
    user_audio_file = "data/T+Tik Tak Tok.wav"
    
    print("=== 피아노 연주 자동 평가 시스템 ===\n")
    
    # --- 1. 정답 악보 분석 ---
    print("1. 정답 악보 분석 중...")
    
    # BPM 먼저 시도
    sheet_bpm = get_sheet_bpm(target_sheet_file)
    if sheet_bpm:
        print(f"-> BPM 감지 성공: {sheet_bpm}")
    else:
        print(f"-> BPM 감지 실패 → 안전 모드 (quantize 비활성)로 진행")
    
    # 노트 추출
    sheet_music_data = extract_notes_from_sheet(target_sheet_file)
    if not sheet_music_data:
        print("[오류] 정답 악보에서 음표를 추출할 수 없습니다.")
        exit(1)
    
    print(f"-> 총 {len(sheet_music_data)}개의 정답 음표 추출 완료")
    print(f"-> 앞부분 3개: {sheet_music_data[:3]}\n")
    
    # --- 2. 사용자 연주 분석 ---
    print("2. 사용자 연주(WAV) 분석 중...")
    user_performance_data = extract_notes_from_audio(
        user_audio_file,
        bpm=sheet_bpm  # None이면 자동으로 quantize 비활성
    )
    if not user_performance_data:
        print("[오류] 연주 오디오에서 음표를 추출할 수 없습니다.")
        exit(1)
    
    print(f"-> 총 {len(user_performance_data)}개의 실제 연주 음표 추출 완료")
    print(f"-> 앞부분 3개: {user_performance_data[:3]}\n")
    
    # --- 3. 채점 ---
    print("3. 채점 중...")
    result = compare_notes(sheet_music_data, user_performance_data)
    
    # --- 4. 결과 출력 ---
    print(f"\n{'='*40}")
    print(f"            채점 결과")
    print(f"{'='*40}")
    print(f"점수:              {result['score']}점 / 100점")
    print(f"정확한 음표:       {result['correct']} / {result['total']}개")
    print(f"  ├─ 직접 매칭:    {result['direct_matched']}개  (onset 정확)")
    print(f"  ├─ 지속음 매칭:  {result['sustain_matched']}개  (반복음 병합 대응)")
    print(f"  ├─ 와이드 구제:  {result['wide_rescued']}개  (timing 오차 큼)")
    print(f"  └─ 옥타브 구제:  {result['octave_rescued']}개  (옥타브 오인식)")
    print(f"누락된 음표:       {result['missed_count']}개")
    print(f"여분의 음표:       {result['extra_count']}개")
    print(f"평균 timing 오차:  {result['avg_timing_deviation']}초")