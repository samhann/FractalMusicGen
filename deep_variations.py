"""
Variations built on the deep hierarchical abstraction.

Each variation manipulates a specific level of the hierarchy:
- Motif level: change the DNA (interval sizes, rhythm)
- Phrase level: reorder or substitute motifs within phrases
- Section level: swap phrase references
- Form level: rearrange sections
- Cross-level: transform motifs while changing form

Because we have the real building blocks, even small changes
produce musically coherent results.
"""

from copy import deepcopy
from deep_abstraction import (
    DeepProgram, Motif, Atom, Phrase, Section,
    MotifRef, PhraseRef, SectionRef, Transform,
    build_fur_elise_deep, deep_program_to_midi, note_name,
)

T = 240  # eighth note


def variation_wider_trill():
    """
    MOTIF-LEVEL: Change the oscillation from half-step (-1,+1) to whole-step (-2,+2).
    Everything else stays the same.
    Musical effect: the trill becomes more dramatic, almost bluesy.
    """
    prog = build_fur_elise_deep()
    prog.title = "V1: Wider Trill (whole step oscillation)"

    prog.motifs['osc'] = Motif('osc', [
        Atom(0, T),
        Atom(-2, T),   # whole step down instead of half
        Atom(+2, T),   # whole step up
        Atom(-2, T),
        Atom(+2, T),
    ], description="whole-step oscillation")

    return prog


def variation_inverted_desc():
    """
    MOTIF-LEVEL: Invert the descent motif — instead of falling to A,
    it rises. The trill resolves upward instead of downward.
    Musical effect: hopeful, ascending quality instead of melancholic.
    """
    prog = build_fur_elise_deep()
    prog.title = "V2: Inverted Descent (resolution goes up)"

    # Original desc: -5, +3, -2, -3 (net: -7, falling)
    # Inverted:      +5, -3, +2, +3 (net: +7, rising)
    prog.motifs['desc'] = Motif('desc', [
        Atom(+5, T),
        Atom(-3, T),
        Atom(+2, T),
        Atom(+3, T*3),
    ], description="ascending resolution (inverted)")

    return prog


def variation_augmented_osc():
    """
    MOTIF-LEVEL: Double the durations of the oscillation.
    The trill becomes slow and deliberate.
    Musical effect: contemplative, like the piece is waking up slowly.
    """
    prog = build_fur_elise_deep()
    prog.title = "V3: Slow Oscillation (augmented trill)"

    prog.motifs['osc'] = Motif('osc', [
        Atom(0, T*2),
        Atom(-1, T*2),
        Atom(+1, T*2),
        Atom(-1, T*2),
        Atom(+1, T*2),
    ], description="augmented oscillation (slow trill)")

    return prog


def variation_phrase_reorder():
    """
    PHRASE-LEVEL: Rearrange the A phrase.
    Original: osc → desc → arp → ans → rest
    New:      arp → osc → desc → ans → rest
    Start with the arpeggio, THEN do the trill, THEN descend.
    Musical effect: the arpeggio announces, trill embellishes, descent resolves.
    """
    prog = build_fur_elise_deep()
    prog.title = "V4: Reordered A Phrase (arpeggio first)"

    prog.phrases['A_phrase'] = Phrase('A_phrase', [
        MotifRef('arp', start_pitch=69),      # start with arpeggio
        MotifRef('osc', start_pitch=64),      # trill on E5 (lower, after arp ends on E5)
        MotifRef('desc', start_pitch=64),     # descend from E5
        MotifRef('ans', start_pitch=56),      # answer
        MotifRef('rest', start_pitch=57),     # rest
    ], description="reordered: arpeggio → trill → descent → answer")

    return prog


def variation_osc_everywhere():
    """
    PHRASE-LEVEL: Replace the B section's step_up motifs with the trill.
    The oscillation colonizes the B section too.
    Musical effect: the whole piece is suffused with the trill DNA.
    """
    prog = build_fur_elise_deep()
    prog.title = "V5: Oscillation Everywhere (trill invades B section)"

    prog.phrases['B_phrase'] = Phrase('B_phrase', [
        MotifRef('arch', start_pitch=72),
        MotifRef('osc', start_pitch=71),     # trill instead of step_up
        MotifRef('osc', start_pitch=71, transform=Transform(transpose=5)),  # trill transposed
        MotifRef('osc', start_pitch=76, transform=Transform(invert=True)),  # inverted trill
        MotifRef('osc', start_pitch=69),     # trill on A
    ], description="B phrase with oscillation replacing steps")

    return prog


def variation_rondo():
    """
    FORM-LEVEL: Change from ABA to ABACABA (rondo form).
    Add a new C section that uses the trill at different transpositions.
    Musical effect: more expansive, like a proper rondo.
    """
    prog = build_fur_elise_deep()
    prog.title = "V6: Rondo Form (ABACABA)"

    # Create C section: development of the trill through keys
    prog.phrases['C_phrase'] = Phrase('C_phrase', [
        MotifRef('osc', start_pitch=76),                              # trill on E6 (home)
        MotifRef('desc', start_pitch=76, transform=Transform(transpose=5)),   # desc transposed up 5
        MotifRef('osc', start_pitch=76, transform=Transform(transpose=7)),    # trill up a 5th
        MotifRef('desc', start_pitch=76, transform=Transform(transpose=7)),
        MotifRef('osc', start_pitch=76, transform=Transform(transpose=3)),    # trill up minor 3rd
        MotifRef('desc', start_pitch=76, transform=Transform(transpose=3)),
        MotifRef('rest', start_pitch=69),
    ], description="development: trill+descent through rising keys")

    prog.sections['C'] = Section('C', [
        PhraseRef('C_phrase'),
    ], description="C section (trill development)")

    prog.form = [
        SectionRef('A'),
        SectionRef('B'),
        SectionRef('A'),
        SectionRef('C'),
        SectionRef('A'),
        SectionRef('B'),
        SectionRef('A'),
    ]

    return prog


def variation_minimal():
    """
    CROSS-LEVEL: Strip everything down to just the oscillation and arch.
    Slow it down. Minimalist version — the essence of the piece.
    Musical effect: Philip Glass meets Beethoven.
    """
    prog = build_fur_elise_deep()
    prog.title = "V7: Minimalist (just osc + arch, slowed)"

    # Slow oscillation
    prog.motifs['osc'] = Motif('osc', [
        Atom(0, T*3),
        Atom(-1, T*3),
        Atom(+1, T*3),
        Atom(-1, T*3),
        Atom(+1, T*3),
    ], description="slow oscillation")

    # Slow arch
    prog.motifs['arch'] = Motif('arch', [
        Atom(0, T*4),
        Atom(+2, T*2),
        Atom(+2, T*2),
        Atom(+1, T*4),
        Atom(-1, T*2),
        Atom(-2, T*2),
        Atom(-2, T*4),
        Atom(-1, T*2),
        Atom(-2, T*2),
    ], description="slow arch")

    # Minimal phrase: just osc + arch + rest
    prog.phrases['min_phrase'] = Phrase('min_phrase', [
        MotifRef('osc', start_pitch=76),
        MotifRef('arch', start_pitch=72),
        MotifRef('rest', start_pitch=69),
    ], description="minimal phrase")

    prog.sections['M'] = Section('M', [
        PhraseRef('min_phrase'),
    ])

    # Repeat the minimal phrase at different transpositions
    prog.form = [
        SectionRef('M'),
        SectionRef('M', Transform(transpose=5)),
        SectionRef('M'),
        SectionRef('M', Transform(transpose=-5)),
        SectionRef('M'),
    ]

    return prog


# ============================================================
# Generate all variations
# ============================================================

if __name__ == "__main__":
    variations = [
        ("deep_v1_wider_trill", variation_wider_trill),
        ("deep_v2_inverted_desc", variation_inverted_desc),
        ("deep_v3_slow_osc", variation_augmented_osc),
        ("deep_v4_reordered", variation_phrase_reorder),
        ("deep_v5_osc_everywhere", variation_osc_everywhere),
        ("deep_v6_rondo", variation_rondo),
        ("deep_v7_minimal", variation_minimal),
    ]

    for filename, fn in variations:
        prog = fn()
        print(f"\n{'='*60}")
        print(prog)
        path = f"{filename}.mid"
        n = deep_program_to_midi(prog, path)
        print(f"\n  → {path} ({n} notes)")
