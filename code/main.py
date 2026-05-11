import sys
import json
import argparse

from module1 import extract_notes_from_musicxml
from module2 import extract_notes_from_audio
from module3 import compare_notes


def run_analysis(sheet_path, audio_path):
    sheet_data = extract_notes_from_musicxml(sheet_path)
    audio_data = extract_notes_from_audio(audio_path)
    return compare_notes(sheet_data, audio_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="피아노 연주 자동 평가 시스템")
    parser.add_argument("--sheet", default="data/piano_sheet_3.xml", help="악보 파일 경로 (MusicXML)")
    parser.add_argument("--audio", default="data/piano_record_3.wav", help="연주 오디오 파일 경로 (WAV)")
    parser.add_argument("--json", dest="json_mode", action="store_true", help="결과를 JSON으로 출력 (Go 연동용)")
    args = parser.parse_args()

    if args.json_mode:
        # Go subprocess가 stdout에서 JSON만 읽으므로 다른 출력 없이 JSON만 출력
        try:
            result = run_analysis(args.sheet, args.audio)
            print(json.dumps(result, ensure_ascii=False))
        except Exception as e:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
            sys.exit(1)
    else:
        print("=== 피아노 연주 자동 평가 시스템 ===\n")

        print("1. 정답 악보(MIDI) 분석 중...")
        sheet_data = extract_notes_from_musicxml(args.sheet)
        if sheet_data:
            print(f"-> 총 {len(sheet_data)}개의 정답 음표 추출 완료")
            print(f"-> 앞부분 3개 미리보기: {sheet_data[:3]}\n")

        print("2. 사용자 연주(WAV) 분석 중...")
        audio_data = extract_notes_from_audio(args.audio)
        if audio_data:
            print(f"-> 총 {len(audio_data)}개의 실제 연주 음표 추출 완료")
            print(f"-> 앞부분 3개 미리보기: {audio_data[:3]}\n")

        print("3. 채점 중...")
        result = compare_notes(sheet_data, audio_data)

        print("===== 채점 결과 =====")
        print(f"점수:              {result['score']}점 / 100점")
        print(f"정확한 음표:       {result['correct']} / {result['total']}개")
        print(f"누락된 음표:       {result['missed_count']}개")
        print(f"박자 오류:         {result['wrong_timing_count']}개")
        print(f"\n누락 음표 미리보기:    {result['missed_notes']}")
        print(f"박자 오류 미리보기:    {result['wrong_timing_notes']}")
