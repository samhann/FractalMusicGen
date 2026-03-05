"""
Run the full analysis + refactoring pipeline on sample pieces.
"""

from music_rep import parse_midi, quantize_notes
from voice_separation import separate_by_register, extract_melody_line, extract_bass_line
from music_program import notes_to_program, refactor_loop, MusicProgram
from music_rep import notes_to_midi

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def note_name(pitch):
    return f"{NOTE_NAMES[pitch % 12]}{pitch // 12}"

def analyze_piece(path, label):
    print(f"\n{'#'*70}")
    print(f"# {label}")
    print(f"{'#'*70}")

    notes, tpb = parse_midi(path)
    print(f"Total notes: {len(notes)}, ticks/beat: {tpb}")

    # Separate into treble and bass
    treble, bass = separate_by_register(notes, split_pitch=60)
    print(f"Treble: {len(treble)} notes, Bass: {len(bass)} notes")

    # Extract melody from treble
    melody = extract_melody_line(treble)
    grid = tpb // 4
    melody = quantize_notes(melody, grid)
    print(f"Melody (quantized): {len(melody)} notes")

    # Show the melody
    print("\nMelody pitches:")
    for i in range(0, len(melody), 16):
        chunk = melody[i:i+16]
        names = [f"{note_name(n.pitch):4s}" for n in chunk]
        print(f"  [{i:3d}] {' '.join(names)}")

    # Run refactoring loop on melody
    print(f"\n{'='*60}")
    print("REFACTORING MELODY")
    print(f"{'='*60}")
    melody_prog = refactor_loop(melody, verbose=True)

    # Also do bass
    if bass:
        bass_line = extract_bass_line(bass)
        bass_line = quantize_notes(bass_line, grid)
        if len(bass_line) > 3:
            print(f"\n{'='*60}")
            print("REFACTORING BASS")
            print(f"{'='*60}")
            print(f"Bass line: {len(bass_line)} notes")
            bass_prog = refactor_loop(bass_line, verbose=True)

    # Verify: expand the program and compare
    expanded = melody_prog.expand()
    print(f"\nVerification: expanded program has {len(expanded)} notes "
          f"(original: {len(melody)})")

    return melody_prog


print("Analyzing Für Elise...")
fur_elise_prog = analyze_piece("fur_elise.mid", "Für Elise")

print("\n\nAnalyzing Beethoven 5th...")
b5_prog = analyze_piece("beethoven5.mid", "Beethoven 5th")
