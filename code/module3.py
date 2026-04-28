import numpy as np


def group_chords(notes, chord_tolerance=0.05):
    """
    start 시간이 chord_tolerance 안에 들어오면 같은 화음 그룹으로 묶는다.
    """
    if not notes:
        return []

    notes = sorted(notes, key=lambda x: (x['start'], x['pitch']))

    grouped = []
    current_group = [notes[0]]

    for n in notes[1:]:
        if abs(n['start'] - current_group[0]['start']) <= chord_tolerance:
            current_group.append(n)
        else:
            grouped.append(current_group)
            current_group = [n]

    grouped.append(current_group)
    return grouped


def compare_notes(expected_notes, played_notes, time_tolerance=0.2, chord_tolerance=0.05):
    """
    화음(Chord) 단위 매칭 기반 채점.
    - 같은 시간대 음들을 chord로 묶어서 비교한다.
    - chord 내 음들은 pitch set으로 비교한다.
    """

    expected_groups = group_chords(expected_notes, chord_tolerance=chord_tolerance)
    played_groups = group_chords(played_notes, chord_tolerance=chord_tolerance)

    correct = 0
    missed = []
    wrong_timing = []
    timing_deviations = []

    used_played = set()

    for exp_group in expected_groups:
        exp_start = exp_group[0]['start']
        exp_pitches = set([n['pitch'] for n in exp_group])

        best_match = None
        best_diff = float('inf')
        best_idx = -1

        for idx, play_group in enumerate(played_groups):
            if idx in used_played:
                continue

            play_start = play_group[0]['start']
            diff = abs(exp_start - play_start)

            if diff < best_diff:
                best_diff = diff
                best_match = play_group
                best_idx = idx

        # timing tolerance 밖이면 timing error or missed
        if best_match is None:
            missed.extend(exp_group)
            continue

        if best_diff > time_tolerance:
            wrong_timing.append({
                'note': [n['pitch'] for n in exp_group],
                'expected_time': exp_start,
                'played_time': best_match[0]['start'],
                'diff': round(best_diff, 3)
            })
            missed.extend(exp_group)
            continue

        used_played.add(best_idx)
        timing_deviations.append(best_diff)

        play_pitches = set([n['pitch'] for n in best_match])

        # chord 비교: 교집합 개수만큼 correct 처리
        matched_pitches = exp_pitches.intersection(play_pitches)
        correct += len(matched_pitches)

        # chord에서 빠진 음은 missed 처리
        missing_pitches = exp_pitches - play_pitches
        for p in missing_pitches:
            missed.append({
                'note': p,
                'pitch': p,
                'start': exp_start,
                'end': exp_group[0]['end'],
                'duration': exp_group[0]['duration'],
                'velocity': exp_group[0]['velocity']
            })

    # extra note 처리
    wrong_notes = []
    for idx, group in enumerate(played_groups):
        if idx not in used_played:
            wrong_notes.extend(group)

    total = len(expected_notes)
    score = round((correct / total) * 100, 2) if total > 0 else 0
    avg_timing_dev = round(float(np.mean(timing_deviations)), 3) if timing_deviations else 0

    return {
        'score': score,
        'correct': correct,
        'total': total,
        'missed_count': len(missed),
        'wrong_timing_count': len(wrong_timing),
        'extra_count': len(wrong_notes),
        'avg_timing_deviation': avg_timing_dev,
        'missed_notes': missed[:5],
        'wrong_timing_notes': wrong_timing[:5],
        'extra_notes': wrong_notes[:5]
    }