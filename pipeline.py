"""
Main pipeline: Analyze → Abstract → Generate

Usage:
    python pipeline.py <input.mid> [--variations N] [--style STYLE]

This is the entry point that:
1. Parses a MIDI file
2. Separates voices
3. Runs the refactoring loop to discover abstractions
4. Prints the compressed program representation
5. Generates N variations using the discovered abstractions
"""

import sys
import argparse
from music_rep import parse_midi, quantize_notes, notes_to_midi
from voice_separation import separate_by_register, extract_melody_line, extract_bass_line
from music_program import notes_to_program, refactor_loop
from generate_variations import (
    generate_variation, program_to_midi, add_development_section,
)

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def note_name(pitch):
    return f"{NOTE_NAMES[pitch % 12]}{pitch // 12}"


def run_pipeline(input_path, n_variations=3, style="free", verbose=True):
    if verbose:
        print(f"\n{'#'*70}")
        print(f"# FRACTAL MUSIC ANALYSIS PIPELINE")
        print(f"# Input: {input_path}")
        print(f"{'#'*70}")

    # 1. Parse
    notes, tpb = parse_midi(input_path)
    grid = tpb // 4
    if verbose:
        print(f"\nParsed {len(notes)} notes, {tpb} ticks/beat")

    # 2. Separate voices
    treble, bass = separate_by_register(notes, split_pitch=60)
    melody = extract_melody_line(treble)
    melody = quantize_notes(melody, grid)
    if verbose:
        print(f"Melody: {len(melody)} notes")
        print(f"Bass: {len(bass)} notes")

    # 3. Refactor melody
    if verbose:
        print(f"\n{'='*60}")
        print("DISCOVERING ABSTRACTIONS IN MELODY")
        print(f"{'='*60}")
    melody_prog = refactor_loop(melody, verbose=verbose)

    # 4. Refactor bass
    bass_prog = None
    if bass:
        bass_line = extract_bass_line(bass)
        bass_line = quantize_notes(bass_line, grid)
        if len(bass_line) > 3:
            if verbose:
                print(f"\n{'='*60}")
                print("DISCOVERING ABSTRACTIONS IN BASS")
                print(f"{'='*60}")
            bass_prog = refactor_loop(bass_line, verbose=verbose)

    # 5. Show the program
    if verbose:
        print(f"\n{'='*60}")
        print("FINAL COMPRESSED PROGRAM")
        print(f"{'='*60}")
        print(melody_prog)

    # 6. Generate variations
    if verbose:
        print(f"\n{'='*60}")
        print(f"GENERATING {n_variations} VARIATIONS (style: {style})")
        print(f"{'='*60}")

    base_name = input_path.rsplit('.', 1)[0]
    for i in range(n_variations):
        var_prog = generate_variation(melody_prog, style=style)
        out_path = f"{base_name}_variation_{i+1}.mid"
        n_notes = program_to_midi(var_prog, out_path, tpb)
        if verbose:
            print(f"\n  Variation {i+1}: {out_path}")
            print(f"    Program size: {var_prog.program_size} tokens")
            print(f"    Expanded to {n_notes} notes")
            print(f"    Definitions: {len(var_prog.definitions)}")
            # Show a summary of changes
            for j, inst in enumerate(var_prog.instructions):
                if isinstance(inst, type(melody_prog.instructions[0])) if j < len(melody_prog.instructions) else True:
                    pass

    # 7. Also write the original expanded back (for verification)
    verify_path = f"{base_name}_reconstructed.mid"
    verify_notes = melody_prog.expand()
    notes_to_midi(verify_notes, verify_path, tpb)
    if verbose:
        print(f"\n  Reconstructed original: {verify_path} ({len(verify_notes)} notes)")

    return melody_prog, bass_prog


def main():
    parser = argparse.ArgumentParser(description="Fractal Music Analysis Pipeline")
    parser.add_argument("input", help="Input MIDI file")
    parser.add_argument("--variations", "-n", type=int, default=3, help="Number of variations to generate")
    parser.add_argument("--style", "-s", default="free",
                       choices=["subtle", "rhythmic", "harmonic", "structural", "developmental", "free"],
                       help="Variation style")
    parser.add_argument("--quiet", "-q", action="store_true")
    args = parser.parse_args()
    run_pipeline(args.input, args.variations, args.style, verbose=not args.quiet)


if __name__ == "__main__":
    main()
