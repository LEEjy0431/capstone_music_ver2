import os
import sys

# main.py 가 위치한 디렉토리 기준으로 프로젝트 루트 경로를 잡는다.
# 이렇게 하면 어느 cwd에서 실행하든 동일하게 동작한다.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))           # .../capstone_music_ver2/code
PROJECT_ROOT = os.path.dirname(BASE_DIR)                        # .../capstone_music_ver2
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# code 디렉토리를 import path 에 추가 (다른 폴더에서 실행되더라도 module1/2/3 import 가능)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from module1 import extract_notes_from_musicxml
from module2 import extract_notes_from_audio
from module3 import compare_notes


if __name__ == "__main__":
    target_midi_file = os.path.join(DATA_DIR, "piano_sheet_3.xml")
    user_audio_file = os.path.join(DATA_DIR, "piano_record_3.wav")

    # 입력 파일 존재 여부 사전 점검 (없으면 친절한 에러 메시지)
    for path in (target_midi_file, user_audio_file):
        if not os.path.exists(path):
            print(f"[오류] 입력 파일을 찾을 수 없습니다: {path}")
            sys.exit(1)

    print("=== 피아노 연주 자동 평가 시스템 ===\n")

    print("1. 정답 악보(MIDI) 분석 중...")
    sheet_music_data = extract_notes_from_musicxml(target_midi_file)
    if sheet_music_data:
        print(f"-> 총 {len(sheet_music_data)}개의 정답 음표 추출 완료")
        print(f"-> 앞부분 3개 미리보기: {sheet_music_data[:3]}\n")

    print("2. 사용자 연주(WAV) 분석 중...")
    user_performance_data = extract_notes_from_audio(user_audio_file)
    if user_performance_data:
        print(f"-> 총 {len(user_performance_data)}개의 실제 연주 음표 추출 완료")
        print(f"-> 앞부분 3개 미리보기: {user_performance_data[:3]}\n")

    print("3. 채점 중...")
    result = compare_notes(sheet_music_data, user_performance_data)

    print(f"===== 채점 결과 =====")
    print(f"점수:              {result['score']}점 / 100점")
    print(f"정확한 음표:       {result['correct']} / {result['total']}개")
    print(f"누락된 음표:       {result['missed_count']}개")
    print(f"박자 오류:         {result['wrong_timing_count']}개")
    print(f"\n누락 음표 미리보기:    {result['missed_notes']}")
    print(f"박자 오류 미리보기:    {result['wrong_timing_notes']}")
