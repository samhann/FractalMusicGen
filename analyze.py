"""
Interactive analysis script.

Loads a MIDI file, runs pattern detection, and prints a detailed view
of what was found — for me (Claude) to reason about and propose abstractions.
"""

import sys
from music_rep import (
    parse_midi, quantize_notes, make_monophonic,
    notes_to_intervals, notes_to_pitch_sequence, notes_to_duration_sequence,
    NoteEvent,
)
from pattern_finder import (
    find_exact_patterns, find_transposed_patterns,
    find_duration_scaled_patterns, rank_patterns, print_patterns,
)

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def note_name(pitch):
    return f"{NOTE_NAMES[pitch % 12]}{pitch // 12}"

def dump_notes(notes, label="Notes"):
    """Print all notes in a readable format."""
    print(f"\n=== {label} ({len(notes)} notes) ===")
    for i, n in enumerate(notes):
        print(f"  [{i:3d}] {note_name(n.pitch):4s}  start={n.start:6d}  dur={n.duration:4d}  vel={n.velocity}")

def dump_pitch_sequence(notes):
    """Print just the pitch sequence compactly."""
    names = [note_name(n.pitch) for n in notes]
    print("\nPitch sequence:")
    # Print in groups of 16
    for i in range(0, len(names), 16):
        chunk = names[i:i+16]
        prefix = f"  [{i:3d}] "
        print(prefix + " ".join(f"{n:4s}" for n in chunk))

def dump_interval_sequence(notes):
    """Print intervals between consecutive notes."""
    intervals = notes_to_intervals(notes)
    print(f"\nInterval sequence ({len(intervals)} intervals):")
    for i in range(0, len(intervals), 20):
        chunk = intervals[i:i+20]
        prefix = f"  [{i:3d}] "
        print(prefix + " ".join(f"{iv:+3d}" for iv in chunk))

def dump_duration_sequence(notes):
    """Print duration pattern."""
    durs = notes_to_duration_sequence(notes)
    print(f"\nDuration sequence:")
    for i in range(0, len(durs), 20):
        chunk = durs[i:i+20]
        prefix = f"  [{i:3d}] "
        print(prefix + " ".join(f"{d:4d}" for d in chunk))

def analyze(path):
    print(f"\n{'='*60}")
    print(f"ANALYZING: {path}")
    print(f"{'='*60}")

    notes, tpb = parse_midi(path)
    print(f"\nTicks per beat: {tpb}")
    print(f"Total notes: {len(notes)}")

    # Separate voices: take melody (highest) for pattern analysis
    melody = make_monophonic(notes)
    print(f"Monophonic melody: {len(melody)} notes")

    # Quantize to 16th note grid
    grid = tpb // 4
    melody_q = quantize_notes(melody, grid)

    # Print the raw data
    dump_pitch_sequence(melody_q)
    dump_interval_sequence(melody_q)
    dump_duration_sequence(melody_q)

    # --- Pattern Analysis ---

    print(f"\n{'='*60}")
    print("EXACT PITCH PATTERNS")
    print(f"{'='*60}")
    pitches = notes_to_pitch_sequence(melody_q)
    exact = find_exact_patterns(pitches, min_len=3, max_len=15)
    exact_ranked = rank_patterns(exact)
    print(f"Found {len(exact)} exact patterns, showing top 15:")
    print_patterns(exact_ranked[:15], melody_q, top_n=15)

    print(f"\n{'='*60}")
    print("TRANSPOSED PATTERNS (interval-based)")
    print(f"{'='*60}")
    transposed = find_transposed_patterns(melody_q, min_len=3, max_len=15)
    trans_ranked = rank_patterns(transposed)
    print(f"Found {len(transposed)} transposed patterns, showing top 15:")
    print_patterns(trans_ranked[:15], melody_q, top_n=15)

    # Summary statistics
    print(f"\n{'='*60}")
    print("COMPRESSION SUMMARY")
    print(f"{'='*60}")
    total_notes = len(melody_q)
    if exact_ranked:
        best = exact_ranked[0]
        print(f"Best exact pattern saves {best.compression_value} notes "
              f"({best.compression_value/total_notes*100:.1f}% of piece)")
    if trans_ranked:
        best_t = trans_ranked[0]
        print(f"Best transposed pattern saves {best_t.compression_value} notes "
              f"({best_t.compression_value/total_notes*100:.1f}% of piece)")

    # Estimate total compression from top non-overlapping patterns
    used_positions = set()
    total_saved = 0
    abstractions = []
    for pat in trans_ranked:
        usable_occs = []
        for occ in pat.occurrences:
            positions = set(range(occ, occ + pat.length))
            if not positions & used_positions:
                usable_occs.append(occ)
                used_positions |= positions
        if len(usable_occs) >= 2:
            saved = (len(usable_occs) - 1) * (pat.length - 2)
            total_saved += saved
            abstractions.append((pat, usable_occs))

    print(f"\nGreedy non-overlapping compression: {total_saved} notes saved "
          f"out of {total_notes} ({total_saved/total_notes*100:.1f}%)")
    print(f"Residual: {total_notes - total_saved} tokens needed")
    print(f"Number of abstractions used: {len(abstractions)}")

    return notes, melody_q, exact_ranked, trans_ranked, abstractions


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "fur_elise.mid"
    analyze(path)
