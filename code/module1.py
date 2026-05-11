from music21 import converter, note, chord, tempo
import xml.etree.ElementTree as ET
import numpy as np
import sys

def extract_notes_from_musicxml(xml_path):
    try:
        score = converter.parse(xml_path)

        # MetronomeMark로 BPM 추출 시도
        bpm = 120
        for element in score.flatten():
            if isinstance(element, tempo.MetronomeMark):
                if element.number is not None:
                    bpm = float(element.number)
                    break

        # Logic Pro용 sound tempo 태그로 재시도
        if bpm == 120:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            for sound in root.iter('sound'):
                if sound.get('tempo'):
                    bpm = float(sound.get('tempo'))
                    break

        print(f"-> BPM 감지: {bpm}", file=sys.stderr)
        seconds_per_quarter = 60.0 / bpm
        expected_notes = []

        for part in score.parts:
            for element in part.flatten().notesAndRests:
                if isinstance(element, note.Note):
                    try:
                        start_sec = round(float(element.offset) * seconds_per_quarter, 2)
                        duration_sec = round(float(element.duration.quarterLength) * seconds_per_quarter, 3)
                        end_sec = round(start_sec + duration_sec, 2)
                        velocity = int(element.volume.velocity) if element.volume.velocity is not None else 64
                        expected_notes.append({
                            'note': element.nameWithOctave,
                            'pitch': element.pitch.midi,
                            'start': start_sec,
                            'end': end_sec,
                            'duration': duration_sec,
                            'velocity': velocity
                        })
                    except Exception:
                        continue

                elif isinstance(element, chord.Chord):
                    try:
                        start_sec = round(float(element.offset) * seconds_per_quarter, 2)
                        duration_sec = round(float(element.duration.quarterLength) * seconds_per_quarter, 3)
                        end_sec = round(start_sec + duration_sec, 2)
                        for n in element.notes:
                            velocity = int(n.volume.velocity) if n.volume.velocity is not None else 64
                            expected_notes.append({
                                'note': n.nameWithOctave,
                                'pitch': n.pitch.midi,
                                'start': start_sec,
                                'end': end_sec,
                                'duration': duration_sec,
                                'velocity': velocity
                            })
                    except Exception:
                        continue

        expected_notes.sort(key=lambda x: (x['start'], x['pitch']))
        return expected_notes

    except Exception as e:
        print(f"[모듈 1 오류] MusicXML 파일을 읽는 중 문제 발생: {e}", file=sys.stderr)
        return []


def extract_onset_sequence(xml_path):
    try:
        notes = extract_notes_from_musicxml(xml_path)
        if not notes:
            return np.array([]), np.array([])
        return np.array([n['start'] for n in notes]), np.array([n['pitch'] for n in notes])
    except Exception as e:
        print(f"[모듈 1 오류] onset 추출 중 문제 발생: {e}", file=sys.stderr)
        return np.array([]), np.array([])