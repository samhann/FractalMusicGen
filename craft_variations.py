"""
Hand-crafted variations of Für Elise.

I (Claude) am looking at the compressed program and making specific
musical decisions about how to rearrange, transform, and develop it.

The original program:
  P1 = the iconic trill motif + descending arpeggio (E D# E D# E B D C A C E A B E)
  P2 = the answer phrase (G# B C E C B A)
  P3 = the B-section ascending/descending line (C D E F E D C B A)

  Structure: [P1 P2 rest] [P1 P2 rest] [P3 ... P3 ...] [P1 P2 rest]
             = A          A             B                A
"""

from copy import deepcopy
from music_program import MusicProgram, PatternDef, PatternRef, Literal
from generate_variations import program_to_midi
from music_rep import parse_midi, quantize_notes
from voice_separation import separate_by_register, extract_melody_line
from music_program import refactor_loop

# First, get the original program
notes, tpb = parse_midi('fur_elise.mid')
treble, bass = separate_by_register(notes, split_pitch=60)
melody = extract_melody_line(treble)
melody = quantize_notes(melody, tpb // 4)
orig = refactor_loop(melody, verbose=False)

print("Original program:")
print(orig)
print()

# ============================================================
# VARIATION 1: "Für Elise in D minor"
# Transpose P1 up a perfect 5th (+7 semitones) = D minor
# Keep P2 and P3 relationships, adjust connecting notes
# Musical idea: what if Beethoven wrote it in D minor instead of A minor?
# ============================================================

def variation_1_transposed_key():
    """Whole piece transposed to D minor (up 5 semitones)."""
    prog = deepcopy(orig)
    # Transpose everything up 5 semitones (A minor -> D minor)
    shift = 5
    for i, inst in enumerate(prog.instructions):
        if isinstance(inst, PatternRef):
            prog.instructions[i] = PatternRef(inst.name, inst.transpose + shift, inst.time_scale)
        elif isinstance(inst, Literal):
            prog.instructions[i] = Literal(inst.pitch + shift, inst.duration)
    return prog

# ============================================================
# VARIATION 2: "Inverted Für Elise"
# Invert P1: instead of the trill going E-D#-E-D#-E then descending,
# it goes E-F-E-F-E then ascending. Mirror image.
# Musical idea: what does the motif sound like upside down?
# ============================================================

def variation_2_inverted():
    """Invert P1 — mirror all intervals."""
    prog = deepcopy(orig)
    # Create inverted P1
    p1_body = list(prog.definitions['P1'].body)
    base = p1_body[0].pitch  # E6 = 76
    inverted_body = [p1_body[0]]  # keep first note
    for j in range(1, len(p1_body)):
        original_interval = p1_body[j].pitch - p1_body[j-1].pitch
        inverted_pitch = inverted_body[j-1].pitch - original_interval  # flip the interval
        inverted_body.append(Literal(inverted_pitch, p1_body[j].duration))
    prog.definitions['P1'] = PatternDef('P1', inverted_body)
    return prog

# ============================================================
# VARIATION 3: "Slow meditation"
# Augment P1 (double durations) — play it slowly, contemplatively
# Remove the B section entirely — just A A A, getting slower
# Musical idea: a slow, introspective version
# ============================================================

def variation_3_augmented():
    """Augmented A section only — slow meditation."""
    prog = MusicProgram()
    prog.definitions = deepcopy(orig.definitions)

    # A section at normal speed
    prog.instructions = [
        PatternRef('P1'), PatternRef('P2'), Literal(69, 960),
    ]
    # A section augmented (1.5x slower)
    prog.instructions += [
        PatternRef('P1', time_scale=1.5), PatternRef('P2', time_scale=1.5), Literal(69, 1440),
    ]
    # A section very augmented (2x slower), transposed down an octave
    prog.instructions += [
        PatternRef('P1', transpose=-12, time_scale=2.0),
        PatternRef('P2', transpose=-12, time_scale=2.0),
        Literal(57, 1920),  # low A
    ]
    return prog

# ============================================================
# VARIATION 4: "Development section"
# Take P1's trill fragment (first 5 notes: E D# E D# E) and
# sequence it through different keys, like a Bach invention.
# Then bring back the full P1 to resolve.
# Musical idea: what if Beethoven developed the motif more?
# ============================================================

def variation_4_development():
    """Develop the trill fragment through a circle of keys."""
    prog = MusicProgram()
    prog.definitions = deepcopy(orig.definitions)

    # Define a new pattern: just the trill fragment (first 5 notes of P1)
    trill = orig.definitions['P1'].body[:5]
    prog.definitions['T'] = PatternDef('T', list(trill))

    # Define the descending resolution (last 6 notes of P1)
    resolution = orig.definitions['P1'].body[5:]
    prog.definitions['R'] = PatternDef('R', list(resolution))

    # Start: original A section
    prog.instructions = [
        PatternRef('P1'), PatternRef('P2'), Literal(69, 480),
    ]

    # Development: trill fragment through rising keys
    # Am -> Dm -> G -> C -> F -> Bb -> back to Am
    for semitones in [0, 5, 7, 12, 5, 7, 3, 0]:
        prog.instructions.append(PatternRef('T', transpose=semitones))

    # Resolution: full P1 comes back, feels like coming home
    prog.instructions += [
        Literal(69, 480),  # brief pause on A
        PatternRef('P1'),
        PatternRef('P2'),
        Literal(69, 1920),  # long final A
    ]
    return prog

# ============================================================
# VARIATION 5: "B section exploration"
# The B section (P3) is the ascending/descending scale line.
# Let's take THAT as the main motif and build a piece around it,
# relegating P1 to a brief intro/outro.
# Musical idea: what if the B section was the main theme?
# ============================================================

def variation_5_b_section_focus():
    """Rebuild the piece with P3 as the main theme."""
    prog = MusicProgram()
    prog.definitions = deepcopy(orig.definitions)

    # Brief intro: just P1 once
    prog.instructions = [PatternRef('P1'), Literal(69, 480)]

    # P3 as main theme, through different keys
    prog.instructions += [
        PatternRef('P3'),                    # C major (original)
        Literal(71, 240), Literal(72, 240),  # transition notes
        PatternRef('P3', transpose=5),       # F major
        Literal(76, 240), Literal(77, 240),  # transition
        PatternRef('P3', transpose=-2),      # Bb major
        Literal(69, 240), Literal(71, 240),  # transition
        PatternRef('P3', transpose=7),       # G major
        Literal(69, 480),
    ]

    # P3 in augmentation (slow, majestic)
    prog.instructions += [
        PatternRef('P3', time_scale=2.0),
        Literal(69, 960),
    ]

    # Brief outro: P1 comes back to end it
    prog.instructions += [
        PatternRef('P1'), PatternRef('P2'), Literal(69, 1920),
    ]
    return prog

# ============================================================
# VARIATION 6: "Rhythmic transformation"
# Keep all the pitches of P1 but change the rhythm:
# instead of even eighths + dotted quarter, make it
# a syncopated pattern (short-long-short-long...)
# Musical idea: Für Elise as a dance
# ============================================================

def variation_6_rhythmic():
    """Change P1's rhythm to a dance-like pattern."""
    prog = deepcopy(orig)

    # Rewrite P1 with syncopated rhythm
    p1_body = list(prog.definitions['P1'].body)
    new_body = []
    for j, lit in enumerate(p1_body):
        # Alternate short-long pattern
        if j % 2 == 0:
            new_body.append(Literal(lit.pitch, 120))  # sixteenth
        else:
            new_body.append(Literal(lit.pitch, 360))  # dotted eighth
    prog.definitions['P1'] = PatternDef('P1', new_body)

    # Also make P3 swing
    p3_body = list(prog.definitions['P3'].body)
    new_p3 = []
    for j, lit in enumerate(p3_body):
        if j % 2 == 0:
            new_p3.append(Literal(lit.pitch, 320))  # long
        else:
            new_p3.append(Literal(lit.pitch, 160))  # short
    prog.definitions['P3'] = PatternDef('P3', new_p3)
    return prog


# ============================================================
# Generate all variations
# ============================================================

variations = [
    ("v1_d_minor", variation_1_transposed_key, "Für Elise in D minor"),
    ("v2_inverted", variation_2_inverted, "Inverted Für Elise"),
    ("v3_slow", variation_3_augmented, "Slow meditation"),
    ("v4_development", variation_4_development, "Trill development"),
    ("v5_b_focus", variation_5_b_section_focus, "B section as main theme"),
    ("v6_rhythmic", variation_6_rhythmic, "Dance rhythm"),
]

for filename, fn, description in variations:
    prog = fn()
    path = f"crafted_{filename}.mid"
    n = program_to_midi(prog, path)
    print(f"\n{description}:")
    print(f"  -> {path} ({n} notes)")
    print(f"  Program: {prog.program_size} tokens, {len(prog.definitions)} defs")
    # Show the body structure
    body_str = " ".join(str(inst) for inst in prog.instructions)
    print(f"  Body: {body_str}")
