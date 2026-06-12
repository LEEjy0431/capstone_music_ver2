import librosa
import numpy as np


def _compute_cqt(audio_path, sr_target=22050, hop_length=512):
    """전체 audio의 Constant-Q Transform을 한 번만 계산."""
    y, sr = librosa.load(audio_path, sr=sr_target, mono=True)
    # 피아노 음역: A0 (MIDI 21) ~ C8 (MIDI 108) = 88건반
    cqt = np.abs(librosa.cqt(
        y, sr=sr, hop_length=hop_length,
        n_bins=88, bins_per_octave=12,
        fmin=librosa.note_to_hz('A0')
    ))
    times = librosa.frames_to_time(
        np.arange(cqt.shape[1]), sr=sr, hop_length=hop_length
    )
    return cqt, times


def _harmonic_evidence(cqt_segment, pitch):
    """
    피아노 음의 fundamental + 2/3/4 배음의 에너지를 가중합.
    실제로 그 음이 울리고 있다면 이들이 모두 강해야 함.
    """
    p_idx = pitch - 21
    if p_idx < 0 or p_idx >= 88:
        return 0.0

    # (가중치, semitone offset)
    weights_offsets = [
        (1.0, 0),    # 기본음
        (0.6, 12),   # 2배음 (한 옥타브 위)
        (0.4, 19),   # 3배음 (옥타브+5도)
        (0.25, 24),  # 4배음 (두 옥타브 위)
    ]
    total, w_sum = 0.0, 0.0
    for w, offset in weights_offsets:
        bin_idx = p_idx + offset
        if 0 <= bin_idx < 88:
            energy = cqt_segment[bin_idx].max()
            total += w * energy
            w_sum += w
    return total / (w_sum + 1e-8)


def _noise_floor(cqt_segment, pitch):
    """주변 +/- 3~4 semitone bin의 중앙값 (배경 노이즈 기준)."""
    p_idx = pitch - 21
    if p_idx < 0 or p_idx >= 88:
        return 1e-8

    # 인접 ±1 semitone은 CQT bleeding 때문에 제외
    ref_bins = []
    for delta in [-4, -3, -2, 2, 3, 4]:
        ref_idx = p_idx + delta
        if 0 <= ref_idx < 88:
            ref_bins.append(cqt_segment[ref_idx].mean())
    return float(np.median(ref_bins)) if ref_bins else 1e-8


def verify_missed_notes(audio_path, missed_notes,
                        snr_threshold=2.5,
                        context_pad_sec=0.05,
                        verbose=True):
    """
    트랜스크립션이 놓친 음표를 CQT 기반으로 직접 검증.
    
    Args:
        snr_threshold: pitch evidence / noise floor 비율 임계값.
                       2.5 = 실험적 보수 값. 너무 낮으면 false positive↑.
        context_pad_sec: 시간 구간 양쪽 padding.
    
    Returns:
        rescued: SNR이 임계값 이상 → 실제로 연주된 음 (잘못 놓친 것)
        truly_missed: SNR 부족 → 진짜 안 친 음
    """
    if not missed_notes:
        return [], []

    cqt, times = _compute_cqt(audio_path)

    rescued = []
    truly_missed = []

    for note in missed_notes:
        pitch = note['pitch']
        t0 = max(0, note['start'] - context_pad_sec)
        t1 = note['end'] + context_pad_sec

        f0 = int(np.searchsorted(times, t0))
        f1 = int(np.searchsorted(times, t1))
        if f1 <= f0:
            truly_missed.append(note)
            continue

        segment = cqt[:, f0:f1]
        if segment.shape[1] == 0:
            truly_missed.append(note)
            continue

        evidence = _harmonic_evidence(segment, pitch)
        noise = _noise_floor(segment, pitch)
        snr = evidence / (noise + 1e-8)

        marked = {**note, 'verify_snr': round(float(snr), 2)}
        if snr >= snr_threshold:
            rescued.append(marked)
        else:
            truly_missed.append(marked)

    return rescued, truly_missed