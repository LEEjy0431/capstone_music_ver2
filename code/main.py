from module1 import extract_notes_from_musicxml
from module2 import extract_notes_from_audio
from module3 import compare_notes


if __name__ == "__main__":
    target_midi_file = "data/piano_sheet_3.xml"
    user_audio_file = "data/piano_record_3.wav"    
    
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