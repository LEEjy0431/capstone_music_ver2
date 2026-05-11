# module2.py (piano_transcription_inference 기반)

import numpy as np
import librosa
import soundfile as sf
import pretty_midi
import tempfile
import os
import sys

from piano_transcription_inference import PianoTranscription, sample_rate


def quantize_time(t, grid=0.05):
    """t초를 grid 단위로 반올림"""
    return round(round(t / grid) * grid, 3)


def extract_notes_from_audio(audio_path, bpm=120, quantize=True):

    played_notes = []

    try:
        # WAV 로드 (mono 변환)
        y, sr = sf.read(audio_path)
        if y.ndim == 2:
            y = np.mean(y, axis=1)

        # sample_rate(기본 16000)로 resample
        if sr != sample_rate:
            y = librosa.resample(y, orig_sr=sr, target_sr=sample_rate)

        # transcription 모델 준비
        transcriptor = PianoTranscription(device='cpu')  # GPU 있으면 'cuda'

        # 임시 midi 파일로 출력
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tmp:
            tmp_mid_path = tmp.name

        transcriptor.transcribe(y, tmp_mid_path)

        # midi 읽기
        midi = pretty_midi.PrettyMIDI(tmp_mid_path)

        # 임시 파일 삭제
        if os.path.exists(tmp_mid_path):
            os.unlink(tmp_mid_path)

        if not midi.instruments:
            return []

        # 여러 instrument가 생길 수 있으므로 전부 합침
        all_notes = []
        for inst in midi.instruments:
            all_notes.extend(inst.notes)

        # BPM 기반 grid 계산 (16분음표 기준)
        sec_per_quarter = 60.0 / bpm
        grid = sec_per_quarter / 4  # 16th note

        for note in all_notes:
            start = float(note.start)
            end = float(note.end)

            if quantize:
                start = quantize_time(start, grid)
                end = quantize_time(end, grid)

            duration = round(end - start, 3)
            if duration < 0.05:
                continue

            note_name = librosa.midi_to_note(note.pitch)

            played_notes.append({
                'note': note_name,
                'pitch': note.pitch,
                'start': round(start, 3),
                'end': round(end, 3),
                'duration': duration,
                'velocity': int(note.velocity)
            })

        played_notes.sort(key=lambda x: (x['start'], x['pitch']))
        return played_notes

    except Exception as e:
        print(f"[Module 2 Error] piano_transcription_inference 처리 중 문제 발생: {e}", file=sys.stderr)
        return played_notes


def extract_onset_sequence(audio_path, bpm=120):
    """
    DTW 정렬을 위한 onset 시퀀스 추출
    """
    notes = extract_notes_from_audio(audio_path, bpm=bpm, quantize=True)
    if not notes:
        return np.array([]), np.array([])

    onsets = np.array([n['start'] for n in notes])
    pitches = np.array([n['pitch'] for n in notes])
    return onsets, pitches