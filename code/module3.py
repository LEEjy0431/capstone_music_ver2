import numpy as np
from collections import defaultdict


def _estimate_global_offset(expected, played, sample_limit=30):
    """글로벌 시간 오프셋 추정 (중앙값 기반)."""
    exp_by_pitch = defaultdict(list)
    play_by_pitch = defaultdict(list)
    for n in expected:
        exp_by_pitch[n['pitch']].append(n['start'])
    for n in played:
        play_by_pitch[n['pitch']].append(n['start'])

    diffs = []
    for pitch, es_list in exp_by_pitch.items():
        if pitch not in play_by_pitch:
            continue
        ps_list = play_by_pitch[pitch]
        for es in es_list[:sample_limit]:
            closest = min(ps_list, key=lambda x: abs(x - es))
            d = closest - es
            if abs(d) <= 1.5:
                diffs.append(d)
    return float(np.median(diffs)) if diffs else 0.0


def _empty_result(missed=None):
    missed = missed or []
    return {
        'score': 0.0, 'correct': 0, 'total': len(missed),
        'missed_count': len(missed), 'extra_count': 0,
        'sustain_matched': 0, 'wide_rescued': 0, 'octave_rescued': 0,
        'avg_timing_deviation': 0.0,
        'missed_notes': missed[:5], 'extra_notes': [],
    }


def compare_notes(expected_notes, played_notes,
                  onset_tolerance=0.15,
                  wide_tolerance=0.40,
                  octave_tolerance=0.30,
                  enable_global_align=True,
                  enable_wide_rescue=True,
                  enable_octave_rescue=True,
                  verbose=True):
    """
    5단계 매칭으로 트랜스크립션 모델 오류를 사후 구제.

    1) 직접 onset 매칭   : 같은 pitch, |Δt| ≤ onset_tolerance, 1:1
    2) 지속음 매칭       : 긴 played가 expected를 덮음 (병합된 반복음)
    3) 와이드 onset 구제 : 같은 pitch, |Δt| ≤ wide_tolerance (timing 오차 큰 케이스)
    4) 옥타브 구제       : 같은 pitch class, 다른 옥타브 (모델의 옥타브 오인식)
    5) 나머지는 누락(missed)
    """
    if not expected_notes:
        return _empty_result()
    if not played_notes:
        return _empty_result(missed=expected_notes)

    # === 글로벌 시간 오프셋 보정 ===
    played = played_notes
    if enable_global_align:
        offset = _estimate_global_offset(expected_notes, played_notes)
        if abs(offset) > 0.03:
            if verbose:
                print(f"-> 글로벌 시간 오프셋: {offset:+.3f}s (자동 보정)")
            played = [
                {**n,
                 'start': round(n['start'] - offset, 3),
                 'end':   round(n['end']   - offset, 3)}
                for n in played_notes
            ]

    # === 인덱스 구축 ===
    played_by_pitch = defaultdict(list)
    played_by_pc = defaultdict(list)   # pitch class (옥타브 무관)
    for idx, p in enumerate(played):
        played_by_pitch[p['pitch']].append(idx)
        played_by_pc[p['pitch'] % 12].append(idx)

    matched_played = set()
    sustain_used_count = {}
    correct_notes = []
    timing_devs = []
    counts = {'direct': 0, 'sustain': 0, 'wide': 0, 'octave': 0}

    # ====================================
    # 1단계: 직접 onset 매칭 (가장 정확, 1:1)
    # ====================================
    pool1 = []
    for exp in expected_notes:
        candidates = played_by_pitch.get(exp['pitch'], [])
        best_idx, best_diff = -1, float('inf')
        for idx in candidates:
            if idx in matched_played:
                continue
            diff = abs(played[idx]['start'] - exp['start'])
            if diff <= onset_tolerance and diff < best_diff:
                best_diff = diff
                best_idx = idx

        if best_idx >= 0:
            matched_played.add(best_idx)
            correct_notes.append(exp)
            timing_devs.append(best_diff)
            counts['direct'] += 1
        else:
            pool1.append(exp)

    # ====================================
    # 2단계: 지속음 매칭 (병합된 반복음)
    # ====================================
    pool2 = []
    for exp in pool1:
        candidates = played_by_pitch.get(exp['pitch'], [])
        matched = False
        for idx in candidates:
            p = played[idx]
            p_dur = p['end'] - p['start']
            if not (p['start'] - onset_tolerance <= exp['start'] <= p['end'] + onset_tolerance):
                continue
            if not ((p_dur >= exp['duration'] * 1.4) or (p_dur >= 0.20)):
                continue
            if sustain_used_count.get(idx, 0) >= 8:
                continue
            sustain_used_count[idx] = sustain_used_count.get(idx, 0) + 1
            correct_notes.append(exp)
            timing_devs.append(abs(p['start'] - exp['start']))
            counts['sustain'] += 1
            matched = True
            break
        if not matched:
            pool2.append(exp)

    # ====================================
    # 3단계: 와이드 onset 구제 (같은 pitch, 넓은 timing)
    # ====================================
    pool3 = []
    if enable_wide_rescue:
        for exp in pool2:
            candidates = played_by_pitch.get(exp['pitch'], [])
            best_idx, best_diff = -1, float('inf')
            for idx in candidates:
                if idx in matched_played or sustain_used_count.get(idx, 0) > 0:
                    continue
                diff = abs(played[idx]['start'] - exp['start'])
                if diff <= wide_tolerance and diff < best_diff:
                    best_diff = diff
                    best_idx = idx
            if best_idx >= 0:
                matched_played.add(best_idx)
                correct_notes.append(exp)
                timing_devs.append(best_diff)
                counts['wide'] += 1
            else:
                pool3.append(exp)
    else:
        pool3 = pool2

    # ====================================
    # 4단계: 옥타브 구제 (pitch class만 같음)
    # ====================================
    missed = []
    if enable_octave_rescue:
        for exp in pool3:
            pc = exp['pitch'] % 12
            candidates = played_by_pc.get(pc, [])
            best_idx, best_score = -1, float('inf')
            for idx in candidates:
                if idx in matched_played or sustain_used_count.get(idx, 0) > 0:
                    continue
                p = played[idx]
                if p['pitch'] == exp['pitch']:
                    continue  # 이미 1/3단계에서 시도됨
                diff = abs(p['start'] - exp['start'])
                if diff > octave_tolerance:
                    continue
                oct_diff = abs(p['pitch'] - exp['pitch']) // 12
                score_val = diff + oct_diff * 0.05  # 옥타브 차이 클수록 페널티
                if score_val < best_score:
                    best_score = score_val
                    best_idx = idx
            if best_idx >= 0:
                matched_played.add(best_idx)
                correct_notes.append(exp)
                timing_devs.append(abs(played[best_idx]['start'] - exp['start']))
                counts['octave'] += 1
            else:
                missed.append(exp)
    else:
        missed.extend(pool3)

    # ====================================
    # Extras 검출 (매칭 안 된 played 중 expected에 그 pitch가 인근에 없는 것)
    # ====================================
    expected_by_pitch = defaultdict(list)
    for n in expected_notes:
        expected_by_pitch[n['pitch']].append(n)

    extras = []
    for idx, p in enumerate(played):
        if idx in matched_played or sustain_used_count.get(idx, 0) > 0:
            continue
        has_nearby = any(
            abs(e['start'] - p['start']) <= onset_tolerance * 2
            for e in expected_by_pitch.get(p['pitch'], [])
        )
        if not has_nearby:
            extras.append(p)

    correct = len(correct_notes)
    total = len(expected_notes)
    score = round((correct / total) * 100, 2) if total > 0 else 0.0
    avg_dev = round(float(np.mean(timing_devs)), 3) if timing_devs else 0.0

    if verbose:
        print(f"-> 매칭 내역: 직접={counts['direct']}, 지속음={counts['sustain']}, "
              f"와이드={counts['wide']}, 옥타브={counts['octave']}")

    return {
        'score': score,
        'correct': correct,
        'total': total,
        'missed_count': len(missed),
        'extra_count': len(extras),
        'direct_matched': counts['direct'],
        'sustain_matched': counts['sustain'],
        'wide_rescued': counts['wide'],
        'octave_rescued': counts['octave'],
        'avg_timing_deviation': avg_dev,
        'missed_notes': missed[:5],
        'missed_notes_full': missed,         # ✅ 추가 (module4가 사용)
        'extra_notes': extras[:5],
    }