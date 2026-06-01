"""
module3.py (compare_notes, group_chords) 단위 테스트

실행:
    cd code
    pytest tests/test_module3.py -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from module3 import compare_notes, group_chords


# ── 헬퍼 ──────────────────────────────────────────────────────────────────

def _note(pitch, start, duration=0.5, velocity=64):
    return {
        'note': str(pitch),
        'pitch': pitch,
        'start': start,
        'end': round(start + duration, 3),
        'duration': duration,
        'velocity': velocity,
    }


# ── group_chords ──────────────────────────────────────────────────────────

class TestGroupChords:
    def test_single_note(self):
        notes = [_note(60, 0.0)]
        groups = group_chords(notes)
        assert len(groups) == 1
        assert groups[0][0]['pitch'] == 60

    def test_two_separate_notes(self):
        notes = [_note(60, 0.0), _note(62, 1.0)]
        groups = group_chords(notes)
        assert len(groups) == 2

    def test_chord_within_tolerance(self):
        notes = [_note(60, 0.0), _note(64, 0.03), _note(67, 0.04)]
        groups = group_chords(notes, chord_tolerance=0.05)
        assert len(groups) == 1
        assert len(groups[0]) == 3

    def test_chord_outside_tolerance(self):
        notes = [_note(60, 0.0), _note(64, 0.1)]
        groups = group_chords(notes, chord_tolerance=0.05)
        assert len(groups) == 2

    def test_empty_input(self):
        assert group_chords([]) == []


# ── compare_notes ─────────────────────────────────────────────────────────

class TestCompareNotesPerfectPlay:
    """악보와 연주가 완전히 일치하는 케이스"""

    def setup_method(self):
        self.expected = [_note(60, 0.0), _note(62, 0.5), _note(64, 1.0)]
        self.played = [_note(60, 0.0), _note(62, 0.5), _note(64, 1.0)]
        self.result = compare_notes(self.expected, self.played)

    def test_score_100(self):
        assert self.result['score'] == 100.0

    def test_correct_equals_total(self):
        assert self.result['correct'] == self.result['total']

    def test_no_missed(self):
        assert self.result['missed_count'] == 0

    def test_no_timing_errors(self):
        assert self.result['wrong_timing_count'] == 0

    def test_no_extra(self):
        assert self.result['extra_count'] == 0


class TestCompareNotesMissedAll:
    """연주를 전혀 하지 않은 케이스"""

    def setup_method(self):
        self.expected = [_note(60, 0.0), _note(62, 0.5)]
        self.result = compare_notes(self.expected, [])

    def test_score_zero(self):
        assert self.result['score'] == 0.0

    def test_all_missed(self):
        assert self.result['missed_count'] == 2


class TestCompareNotesTimingError:
    """타이밍이 tolerance 초과인 케이스"""

    def test_timing_error_detected(self):
        expected = [_note(60, 0.0)]
        # 0.5초 늦게 연주 (tolerance=0.2s 초과)
        played = [_note(60, 0.5)]
        result = compare_notes(expected, played, time_tolerance=0.2)
        assert result['wrong_timing_count'] == 1
        assert result['score'] < 100.0

    def test_within_tolerance_counts_as_correct(self):
        expected = [_note(60, 0.0)]
        # 0.1초 늦게 연주 (tolerance=0.2s 이내)
        played = [_note(60, 0.1)]
        result = compare_notes(expected, played, time_tolerance=0.2)
        assert result['correct'] == 1
        assert result['score'] == 100.0


class TestCompareNotesChord:
    """화음(chord) 케이스"""

    def test_full_chord_match(self):
        expected = [_note(60, 0.0), _note(64, 0.0), _note(67, 0.0)]
        played = [_note(60, 0.0), _note(64, 0.0), _note(67, 0.0)]
        result = compare_notes(expected, played)
        assert result['correct'] == 3
        assert result['score'] == 100.0

    def test_partial_chord_match(self):
        expected = [_note(60, 0.0), _note(64, 0.0), _note(67, 0.0)]
        # 67만 누락
        played = [_note(60, 0.0), _note(64, 0.0)]
        result = compare_notes(expected, played)
        assert result['correct'] == 2
        assert result['missed_count'] == 1
        assert round(result['score'], 2) == round(2 / 3 * 100, 2)

    def test_extra_note_in_chord(self):
        expected = [_note(60, 0.0)]
        # 추가 음 포함
        played = [_note(60, 0.0), _note(64, 0.0)]
        result = compare_notes(expected, played)
        assert result['correct'] == 1
        assert result['score'] == 100.0


class TestCompareNotesExtraNote:
    """악보에 없는 음을 추가로 연주한 케이스"""

    def test_extra_count(self):
        expected = [_note(60, 0.0)]
        played = [_note(60, 0.0), _note(72, 2.0)]  # 2초 뒤 추가 음
        result = compare_notes(expected, played)
        assert result['extra_count'] == 1

    def test_score_not_penalized_for_extra(self):
        expected = [_note(60, 0.0)]
        played = [_note(60, 0.0), _note(72, 2.0)]
        result = compare_notes(expected, played)
        assert result['score'] == 100.0


class TestCompareNotesEdgeCases:
    def test_empty_expected(self):
        result = compare_notes([], [_note(60, 0.0)])
        assert result['score'] == 0.0
        assert result['total'] == 0

    def test_both_empty(self):
        result = compare_notes([], [])
        assert result['score'] == 0.0

    def test_avg_timing_deviation(self):
        expected = [_note(60, 0.0), _note(62, 1.0)]
        played = [_note(60, 0.1), _note(62, 1.0)]  # 첫 음만 0.1s 오차
        result = compare_notes(expected, played, time_tolerance=0.2)
        assert result['avg_timing_deviation'] > 0
