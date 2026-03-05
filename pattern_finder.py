"""
Pattern finder: discovers repeated sequences in music.

Three kinds of matches:
1. Exact: identical pitch sequences at different times
2. Transposed: same intervals, different starting pitch
3. Scaled: same relative durations, possibly different tempo

We work on the interval representation so transposition is free.
"""

from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
from music_rep import NoteEvent, notes_to_intervals


@dataclass
class Pattern:
    """A discovered musical pattern."""
    intervals: Tuple[int, ...]       # interval sequence (transposition-invariant)
    length: int                       # number of notes
    occurrences: List[int]            # indices into the note list where this pattern starts
    duration_ratios: Optional[Tuple[float, ...]] = None  # relative durations (tempo-invariant)

    @property
    def frequency(self) -> int:
        return len(self.occurrences)

    @property
    def compression_value(self) -> int:
        """How many notes we save by abstracting this pattern.
        Each occurrence after the first saves (length - 1) notes
        (we still need 1 token for the pattern reference + 1 for the starting pitch).
        """
        return (self.frequency - 1) * (self.length - 2)

    def __repr__(self):
        return (f"Pattern(intervals={self.intervals}, len={self.length}, "
                f"freq={self.frequency}, compression={self.compression_value})")


def find_exact_patterns(pitches: List[int], min_len: int = 3, max_len: int = 20) -> List[Pattern]:
    """Find repeated exact pitch subsequences using suffix-based approach."""
    n = len(pitches)
    pattern_map: Dict[Tuple[int, ...], List[int]] = defaultdict(list)

    for length in range(min_len, min(max_len + 1, n + 1)):
        for i in range(n - length + 1):
            subseq = tuple(pitches[i:i+length])
            pattern_map[subseq].append(i)

    # Filter to only patterns that appear more than once
    results = []
    for subseq, positions in pattern_map.items():
        if len(positions) > 1:
            # Remove overlapping occurrences (greedy, keep earliest)
            filtered = _remove_overlaps(positions, len(subseq))
            if len(filtered) > 1:
                results.append(Pattern(
                    intervals=subseq,
                    length=len(subseq),
                    occurrences=filtered,
                ))
    return results


def find_transposed_patterns(notes: List[NoteEvent], min_len: int = 3, max_len: int = 20) -> List[Pattern]:
    """Find patterns that are the same up to transposition.

    Works on the interval representation so transposed copies match exactly.
    """
    intervals = notes_to_intervals(notes)
    n = len(intervals)
    pattern_map: Dict[Tuple[int, ...], List[int]] = defaultdict(list)

    for length in range(min_len, min(max_len + 1, n + 1)):
        for i in range(n - length + 1):
            subseq = tuple(intervals[i:i+length])
            pattern_map[subseq].append(i)

    results = []
    for subseq, positions in pattern_map.items():
        if len(positions) > 1:
            filtered = _remove_overlaps(positions, len(subseq) + 1)  # +1 because interval length = note length - 1
            if len(filtered) > 1:
                results.append(Pattern(
                    intervals=subseq,
                    length=len(subseq) + 1,  # number of notes
                    occurrences=filtered,
                ))
    return results


def find_duration_scaled_patterns(notes: List[NoteEvent], min_len: int = 3, max_len: int = 20) -> List[Pattern]:
    """Find patterns with the same intervals AND same relative durations.

    This catches augmentation/diminution — the same motif played faster or slower.
    We normalize durations by dividing by the first duration, then quantize to
    simple ratios.
    """
    intervals = notes_to_intervals(notes)
    n = len(notes)
    pattern_map: Dict[Tuple, List[int]] = defaultdict(list)

    for length in range(min_len, min(max_len + 1, n + 1)):
        for i in range(n - length + 1):
            int_subseq = tuple(intervals[i:i+length-1]) if length > 1 else ()
            durs = [notes[i+j].duration for j in range(length)]
            # Normalize durations relative to first note
            base = durs[0] if durs[0] > 0 else 1
            dur_ratios = tuple(round(d / base, 1) for d in durs)
            key = (int_subseq, dur_ratios)
            pattern_map[key].append(i)

    results = []
    for (int_subseq, dur_ratios), positions in pattern_map.items():
        if len(positions) > 1:
            filtered = _remove_overlaps(positions, length)
            if len(filtered) > 1:
                results.append(Pattern(
                    intervals=int_subseq,
                    length=len(int_subseq) + 1,
                    occurrences=filtered,
                    duration_ratios=dur_ratios,
                ))
    return results


def _remove_overlaps(positions: List[int], span: int) -> List[int]:
    """Greedily remove overlapping occurrences, keeping earliest."""
    if not positions:
        return []
    sorted_pos = sorted(positions)
    result = [sorted_pos[0]]
    for p in sorted_pos[1:]:
        if p >= result[-1] + span:
            result.append(p)
    return result


def rank_patterns(patterns: List[Pattern]) -> List[Pattern]:
    """Rank patterns by compression value (most useful first)."""
    return sorted(patterns, key=lambda p: p.compression_value, reverse=True)


def print_patterns(patterns: List[Pattern], notes: List[NoteEvent], top_n: int = 10):
    """Pretty-print the top patterns with their musical content."""
    NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    ranked = rank_patterns(patterns)[:top_n]
    for i, pat in enumerate(ranked):
        print(f"\n--- Pattern {i+1} ---")
        print(f"  Intervals: {pat.intervals}")
        print(f"  Length: {pat.length} notes, Frequency: {pat.frequency}x, Compression: {pat.compression_value}")
        if pat.duration_ratios:
            print(f"  Duration ratios: {pat.duration_ratios}")
        # Show first occurrence as actual notes
        idx = pat.occurrences[0]
        note_names = []
        for j in range(pat.length):
            if idx + j < len(notes):
                n = notes[idx + j]
                name = NOTE_NAMES[n.pitch % 12] + str(n.octave)
                note_names.append(f"{name}({n.duration})")
        print(f"  Example: {' '.join(note_names)}")
        print(f"  Found at positions: {pat.occurrences}")
