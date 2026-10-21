import numpy as np
import librosa
import soundfile as sf
import pretty_midi
import tempfile
import os
from piano_transcription_inference import PianoTranscription, sample_rate


def quantize_time(t, grid=0.05):
    """t초를 grid 단위로 반올림"""
    return round(round(t / grid) * grid, 3)


def extract_notes_from_audio(audio_path, bpm=None, quantize=None, pre_roll_sec=0.1,
                             min_velocity=30, min_duration=0.03):
    """
    WAV 오디오에서 음표 추출.

    Args:
        bpm:          정답 악보의 BPM. None이면 quantize 자동 비활성.
        quantize:     None → bpm 있으면 True, 없으면 False
                      True → bpm 필수 (없으면 비활성 fallback)
                      False → raw 모델 출력 그대로 사용
        pre_roll_sec: 첫 음 누락 방지용 무음 패딩 (초)
        min_velocity: 이 값 미만의 음표는 유령 음표로 제거 (0~127, 기본 30)
                      너무 높이면 약하게 친 음표도 제거되므로 주의
        min_duration: 이 값(초) 미만의 음표는 노이즈로 제거 (기본 0.03초)
    """
    played_notes = []

    # === Quantize 자동 모드 결정 ===
    if quantize is None:
        quantize = bpm is not None

    if quantize and bpm is None:
        print("[경고] quantize=True 이지만 BPM이 없음 → 비활성으로 fallback")
        quantize = False

    if quantize:
        sec_per_quarter = 60.0 / bpm
        grid = sec_per_quarter / 4
        print(f"-> Quantize 활성 (BPM={bpm}, 16분음표 grid={grid:.4f}s)")
    else:
        print(f"-> Quantize 비활성 (raw onset 사용, 모델 정확도에 의존)")

    print(f"-> 필터: velocity < {min_velocity} 또는 duration < {min_duration}s 제거")

    try:
        # === 오디오 로드 ===
        y, sr = sf.read(audio_path)
        if y.ndim == 2:
            y = np.mean(y, axis=1)
        if sr != sample_rate:
            y = librosa.resample(y, orig_sr=sr, target_sr=sample_rate)

        # 첫 음 누락 방지용 pre-roll padding
        pre_roll_samples = int(pre_roll_sec * sample_rate)
        y = np.concatenate([np.zeros(pre_roll_samples), y])

        # === 트랜스크립션 실행 ===
        transcriptor = PianoTranscription(device='cpu')
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tmp:
            tmp_mid_path = tmp.name
        transcriptor.transcribe(y, tmp_mid_path)
        midi = pretty_midi.PrettyMIDI(tmp_mid_path)
        if os.path.exists(tmp_mid_path):
            os.unlink(tmp_mid_path)

        if not midi.instruments:
            return []

        all_notes = []
        for inst in midi.instruments:
            all_notes.extend(inst.notes)

        # === 노트 후처리 ===
        filtered_count = 0
        for note in all_notes:
            # pre-roll 시간 보정
            start = float(note.start) - pre_roll_sec
            end   = float(note.end)   - pre_roll_sec

            # 패딩 영역 노이즈 무시
            if end <= 0:
                continue
            start = max(start, 0.0)

            # ── 유령 음표 필터 ──────────────────────────────
            # velocity: 모델이 감지한 음의 세기 (0~127)
            if int(note.velocity) < min_velocity:
                filtered_count += 1
                continue

            # Quantize 적용
            if quantize:
                start = quantize_time(start, grid)
                end   = quantize_time(end, grid)

            duration = round(end - start, 3)

            # 너무 짧은 음표 제거
            if duration < min_duration:
                filtered_count += 1
                continue

            played_notes.append({
                'note':     librosa.midi_to_note(note.pitch),
                'pitch':    note.pitch,
                'start':    round(start, 3),
                'end':      round(end, 3),
                'duration': duration,
                'velocity': int(note.velocity),
            })

        if filtered_count:
            print(f"-> 유령 음표 {filtered_count}개 제거됨")

        played_notes.sort(key=lambda x: (x['start'], x['pitch']))
        return played_notes

    except Exception as e:
        print(f"[Module 2 Error] {e}")
        return played_notes


def extract_onset_sequence(audio_path, bpm=120):
    """DTW 정렬을 위한 onset 시퀀스 추출"""
    notes = extract_notes_from_audio(audio_path, bpm=bpm, quantize=True)
    if not notes:
        return np.array([]), np.array([])

    onsets  = np.array([n['start'] for n in notes])
    pitches = np.array([n['pitch'] for n in notes])
    return onsets, pitches