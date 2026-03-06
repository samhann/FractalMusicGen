"""
Variations built on Musical DNA — harmonically coherent, with tension arcs.

Each variation uses real compositional development techniques:
  - Fragmentation: take a piece of a motif and develop it
  - Sequence: repeat a motif at different pitch levels
  - Re-harmonization: same shape, different chord context
  - Combination: merge motif DNA to create new material
  - Augmentation/Diminution: time stretching for drama

All constrained by:
  - Harmonic context: notes must fit the chord/scale
  - Tension curve: the overall build→peak→release shape is preserved
  - Dynamics: velocity follows the energy
"""

from copy import deepcopy
from musical_dna import (
    MusicalDNA, Motif, Atom, Phrase, Section,
    MotifRef, PhraseRef, SectionRef, Transform,
    HarmonicContext, TensionShape,
    build_fur_elise, dna_to_midi, note_name,
    fragment, sequence, augment, invert_motif, combine, harmonize_motif,
    Am, E7, C, G7, F, Dm,
    T, SCALES, CHORDS,
)


def var_sequential_development():
    """
    DEVELOPMENT: Take the trill fragment (just -1,+1) and sequence it
    downward through the scale. Like Beethoven developing a tiny cell
    into a whole passage.

    The 2-note oscillation cell descends step by step:
      E-D# → D-C# → C-B → B-A#
    Then the normal descent resolves it.

    Harmonic logic: stays within E7 → Am, the sequencing follows
    the harmonic minor scale downward. Tension builds through
    repetition, then releases with the descent.
    """
    prog = build_fur_elise()
    prog.title = "V1: Sequential Development (trill cell descends)"

    # Take just the 2-note oscillation core and sequence it downward
    osc_cell = fragment(prog.motifs['osc'], 0, 3, 'osc_cell')  # •, -1, +1

    # Sequence it: each repetition starts 2 semitones lower
    prog.motifs['osc_seq'] = sequence(osc_cell, [0, -2, -2, -2], 'osc_seq')
    prog.motifs['osc_seq'].description = "trill cell sequenced down the scale"
    prog.motifs['osc_seq'].tension = TensionShape.BUILDING

    # Replace osc with the sequenced version in A phrase
    prog.phrases['A_phrase'].elements[0] = MotifRef('osc_seq', start_pitch=76)

    return prog


def var_reharmonized():
    """
    RE-HARMONIZATION: Play the A phrase but shift the harmony from
    Am to Dm (up a 4th). The intervals get snapped to the D minor scale.

    This is how real composers create contrast — same melodic gesture,
    different harmonic color. It sounds familiar but shifted.

    The descent now resolves to D instead of A.
    The arpeggio outlines Dm instead of Am.
    """
    prog = build_fur_elise()
    prog.title = "V2: Re-harmonized (Am → Dm, then back)"

    # Create Dm versions of the motifs
    prog.motifs['osc_dm'] = Motif('osc_dm', [
        Atom(0, T), Atom(-1, T), Atom(+1, T), Atom(-1, T), Atom(+1, T),
    ], harmony=Dm, tension=TensionShape.BUILDING,
       description="trill over Dm (same intervals, new harmonic context)")

    # Dm descent: same shape but to D instead of A
    prog.motifs['desc_dm'] = Motif('desc_dm', [
        Atom(-5, T), Atom(+3, T), Atom(-2, T), Atom(-3, T*3),
    ], harmony=Dm, tension=TensionShape.RELEASING,
       description="descent resolving to D")

    # Dm arpeggio
    prog.motifs['arp_dm'] = Motif('arp_dm', [
        Atom(-9, T), Atom(+3, T), Atom(+5, T), Atom(+2, T*3), Atom(-7, T),
    ], harmony=Dm, tension=TensionShape.BUILDING,
       description="Dm arpeggio")

    # Dm answer (A as leading tone to D)
    prog.motifs['ans_dm'] = Motif('ans_dm', [
        Atom(0, T), Atom(+3, T), Atom(+2, T*3),
        Atom(-8, T), Atom(+7, T), Atom(-2, T), Atom(-2, T*4),
    ], harmony=Dm, tension=TensionShape.RELEASING,
       description="answer phrase in Dm")

    # Create a Dm version of A phrase (transposed up a 4th = +5 semitones)
    prog.phrases['A_dm'] = Phrase('A_dm', [
        MotifRef('osc_dm', start_pitch=81),     # trill on A6 (= E+5)
        MotifRef('desc_dm', start_pitch=81),
        MotifRef('arp_dm', start_pitch=74),     # Dm arpeggio from D5
        MotifRef('ans_dm', start_pitch=73),
        MotifRef('rest', start_pitch=74),
    ], tension=TensionShape.ARCH,
       description="A phrase re-harmonized in Dm")

    # Form: Am, Dm, B(C major contrast), Am — key progression makes sense
    prog.sections['A_dm'] = Section('A_dm', [PhraseRef('A_dm')])

    prog.form = [
        SectionRef('A'),
        SectionRef('A_dm'),     # same gesture, Dm color
        SectionRef('B'),
        SectionRef('A'),        # return home to Am
    ]

    return prog


def var_fragmented_development():
    """
    FRAGMENTATION + COMBINATION: Take the first 3 notes of the trill
    and the first 3 notes of the descent, and weave them together.

    Trill fragment: E D# E (the question)
    Descent fragment: B D C (the partial answer)

    Alternate them, creating a dialogue. Then let the full motifs
    play for resolution.

    Tension: the fragments are unstable (incomplete), building tension.
    The full motifs provide release.
    """
    prog = build_fur_elise()
    prog.title = "V3: Fragmented Dialogue (trill vs descent cells)"

    # Fragment: first 3 atoms of trill
    prog.motifs['osc_frag'] = Motif('osc_frag', [
        Atom(0, T), Atom(-1, T), Atom(+1, T),
    ], harmony=E7, tension=TensionShape.BUILDING,
       description="trill fragment (question)")

    # Fragment: first 3 atoms of descent
    prog.motifs['desc_frag'] = Motif('desc_frag', [
        Atom(-5, T), Atom(+3, T), Atom(-2, T),
    ], harmony=Am, tension=TensionShape.RELEASING,
       description="descent fragment (partial answer)")

    # Dialogue phrase: alternate fragments, then resolve with full motifs
    prog.phrases['dialogue'] = Phrase('dialogue', [
        MotifRef('osc_frag', start_pitch=76),     # trill fragment at E6
        MotifRef('desc_frag', start_pitch=76),     # descent fragment from E6
        MotifRef('osc_frag', start_pitch=74),     # trill fragment at D6 (lower)
        MotifRef('desc_frag', start_pitch=74),     # descent fragment from D6
        MotifRef('osc', start_pitch=76),           # full trill (resolution of question)
        MotifRef('desc', start_pitch=76),          # full descent (complete answer)
        MotifRef('rest', start_pitch=69),
    ], tension=TensionShape.ARCH,
       description="fragment dialogue building to complete statement")

    prog.phrases['resolve'] = Phrase('resolve', [
        MotifRef('arp', start_pitch=69),
        MotifRef('ans', start_pitch=68),
        MotifRef('rest', start_pitch=69),
    ], tension=TensionShape.RELEASING,
       description="resolution with arpeggio and answer")

    prog.sections['dev'] = Section('dev', [
        PhraseRef('dialogue'),
        PhraseRef('resolve'),
    ], description="development through fragmentation")

    prog.form = [
        SectionRef('A'),          # state the theme
        SectionRef('dev'),        # develop it through fragments
        SectionRef('B'),          # contrast
        SectionRef('A'),          # return
    ]

    return prog


def var_augmented_climax():
    """
    AUGMENTATION FOR DRAMA: The final A section plays the trill and descent
    at double speed (diminution), then the arpeggio at double duration
    (augmentation). Creates a rush → hold → release arc.

    Like Beethoven does in development sections: compress the theme,
    then expand the resolution for dramatic weight.

    Harmony stays the same. Tension curve is reshaped: compressed
    buildup → stretched peak → normal release.
    """
    prog = build_fur_elise()
    prog.title = "V4: Augmented Climax (compress then expand)"

    # Fast trill (diminution)
    prog.motifs['osc_fast'] = Motif('osc_fast', [
        Atom(0, T//2), Atom(-1, T//2), Atom(+1, T//2),
        Atom(-1, T//2), Atom(+1, T//2),
        Atom(-1, T//2), Atom(+1, T//2),   # extra repetitions to fill the faster time
        Atom(-1, T//2), Atom(+1, T//2),
    ], harmony=E7, tension=TensionShape.BUILDING,
       description="rapid trill (diminished durations, more repetitions)")

    # Fast descent
    prog.motifs['desc_fast'] = Motif('desc_fast', [
        Atom(-5, T//2), Atom(+3, T//2), Atom(-2, T//2), Atom(-3, T),
    ], harmony=Am, tension=TensionShape.RELEASING,
       description="quick descent")

    # Slow, dramatic arpeggio (augmented)
    prog.motifs['arp_slow'] = Motif('arp_slow', [
        Atom(-9, T*2), Atom(+4, T*2), Atom(+5, T*2), Atom(+2, T*4), Atom(-7, T*2),
    ], harmony=Am, tension=TensionShape.PEAK,
       description="slow, dramatic Am arpeggio (augmented)")

    # Slow answer
    prog.motifs['ans_slow'] = Motif('ans_slow', [
        Atom(0, T*2), Atom(+3, T*2), Atom(+1, T*4),
        Atom(-8, T), Atom(+8, T), Atom(-1, T*2), Atom(-2, T*6),
    ], harmony=Am, tension=TensionShape.RELEASING,
       description="slow, weighted resolution")

    # Climactic A phrase
    prog.phrases['A_climax'] = Phrase('A_climax', [
        MotifRef('osc_fast', start_pitch=76),
        MotifRef('desc_fast', start_pitch=76),
        MotifRef('arp_slow', start_pitch=69),
        MotifRef('ans_slow', start_pitch=68),
        MotifRef('rest', start_pitch=69),
    ], tension=TensionShape.ARCH,
       description="climactic A: rush through trill, linger on arpeggio")

    prog.sections['A_climax'] = Section('A_climax', [PhraseRef('A_climax')])

    prog.form = [
        SectionRef('A'),            # normal statement
        SectionRef('A'),            # repeat (familiarity)
        SectionRef('B'),            # contrast
        SectionRef('A_climax'),     # climactic return
    ]

    return prog


def var_combined_dna():
    """
    COMBINATION: Merge the trill DNA with the arch DNA to create a new
    hybrid motif. The trill's oscillation happens WITHIN the arch's
    ascending/descending shape.

    Each step of the arch gets a mini-trill before moving on.
    It's like the arch is trembling as it rises and falls.

    Tension: follows the arch shape but with more intensity from
    the oscillation.
    """
    prog = build_fur_elise()
    prog.title = "V5: Combined DNA (arch with embedded trills)"

    # Arch with trills: at each step, do a quick oscillation before moving
    prog.motifs['trill_arch'] = Motif('trill_arch', [
        # C with trill
        Atom(0, T), Atom(-1, T//2), Atom(+1, T//2),
        # up to D with trill
        Atom(+2, T), Atom(-1, T//2), Atom(+1, T//2),
        # up to E with trill
        Atom(+2, T), Atom(-1, T//2), Atom(+1, T//2),
        # peak at F (held, no trill — moment of stillness at the peak)
        Atom(+1, T*2),
        # down to E with trill
        Atom(-1, T), Atom(+1, T//2), Atom(-1, T//2),
        # down to D
        Atom(-2, T), Atom(+1, T//2), Atom(-1, T//2),
        # down to C (held)
        Atom(-2, T*2),
        # B and A (releasing, no trills — calm ending)
        Atom(-1, T), Atom(-2, T),
    ], harmony=C, tension=TensionShape.ARCH,
       description="arch shape with oscillation DNA embedded at each step")

    # Replace arch in B section
    prog.phrases['B_phrase'] = Phrase('B_phrase', [
        MotifRef('trill_arch', start_pitch=72),
        MotifRef('step_up', start_pitch=71),
        MotifRef('step_dn', start_pitch=76),
        MotifRef('trill_arch', start_pitch=69),   # arch again, lower
        MotifRef('rest', start_pitch=69),
    ], tension=TensionShape.BUILDING,
       description="B phrase with trill-infused arches")

    prog.phrases['trans'] = Phrase('trans', [
        MotifRef('trill_arch', start_pitch=72),
        MotifRef('rest', start_pitch=69),
    ], tension=TensionShape.RELEASING)

    return prog


def var_sonata_development():
    """
    FULL DEVELOPMENT SECTION: Like a sonata, take the theme apart,
    put it through keys, fragment it, then bring it back.

    Structure:
      Exposition: A phrase (state the theme)
      Development:
        1. Trill sequenced through rising keys (Am → Dm → G → C)
        2. Descent and arp fragments in dialogue
        3. Climactic trill over dominant
      Recapitulation: A phrase returns, slightly augmented
      Coda: Trill slows to nothing

    This has a REAL tension arc: thesis → exploration → crisis → resolution.
    """
    prog = build_fur_elise()
    prog.title = "V6: Sonata Development (full compositional arc)"

    # --- Development materials ---

    # Trill sequenced upward through keys: Am → Dm → G → C
    # Each level rises by a 4th (5 semitones)
    prog.motifs['osc_seq_up'] = sequence(prog.motifs['osc'], [0, +5, +5, +5], 'osc_seq_up')
    prog.motifs['osc_seq_up'].tension = TensionShape.BUILDING
    prog.motifs['osc_seq_up'].description = "trill ascending through keys (Am→Dm→G→C)"

    # Descent fragments in dialogue
    prog.motifs['desc_frag'] = fragment(prog.motifs['desc'], 0, 3, 'desc_frag')
    prog.motifs['desc_frag'].tension = TensionShape.RELEASING

    # Arp fragment (just the rising part)
    prog.motifs['arp_frag'] = fragment(prog.motifs['arp'], 0, 3, 'arp_frag')
    prog.motifs['arp_frag'].tension = TensionShape.BUILDING

    # Climactic trill: more repetitions, on the dominant
    prog.motifs['osc_climax'] = Motif('osc_climax', [
        Atom(0, T), Atom(-1, T//2), Atom(+1, T//2),
        Atom(-1, T//2), Atom(+1, T//2),
        Atom(-1, T//2), Atom(+1, T//2),
        Atom(-1, T//2), Atom(+1, T//2),
        Atom(-1, T//2), Atom(+1, T//2),
        Atom(-1, T), Atom(+1, T),
    ], harmony=E7, tension=TensionShape.PEAK,
       description="climactic trill: intensifying on the dominant")

    # Slow trill for coda
    prog.motifs['osc_slow'] = augment(prog.motifs['osc'], 3.0, 'osc_slow')
    prog.motifs['osc_slow'].tension = TensionShape.RELEASING
    prog.motifs['osc_slow'].description = "dying trill (augmented, fading)"

    # Slow descent for coda
    prog.motifs['desc_slow'] = augment(prog.motifs['desc'], 2.0, 'desc_slow')
    prog.motifs['desc_slow'].tension = TensionShape.RELEASING
    prog.motifs['desc_slow'].description = "slow final descent"

    # --- Development phrases ---

    prog.phrases['dev_rising'] = Phrase('dev_rising', [
        MotifRef('osc_seq_up', start_pitch=76),
        MotifRef('rest', start_pitch=76),
    ], tension=TensionShape.BUILDING,
       description="trill rising through keys")

    prog.phrases['dev_dialogue'] = Phrase('dev_dialogue', [
        MotifRef('arp_frag', start_pitch=69),
        MotifRef('desc_frag', start_pitch=72),
        MotifRef('arp_frag', start_pitch=72),
        MotifRef('desc_frag', start_pitch=76),
        MotifRef('rest', start_pitch=69),
    ], tension=TensionShape.ARCH,
       description="arpeggio and descent fragments in dialogue")

    prog.phrases['dev_climax'] = Phrase('dev_climax', [
        MotifRef('osc_climax', start_pitch=76),
        MotifRef('desc', start_pitch=76),
        MotifRef('rest', start_pitch=69),
    ], tension=TensionShape.PEAK,
       description="climactic trill on dominant → descent")

    prog.phrases['coda'] = Phrase('coda', [
        MotifRef('osc_slow', start_pitch=76),
        MotifRef('desc_slow', start_pitch=76),
        MotifRef('rest', start_pitch=69),
    ], tension=TensionShape.RELEASING,
       description="coda: trill slows and fades")

    # Augmented final A
    prog.phrases['A_broad'] = Phrase('A_broad', [
        MotifRef('osc', start_pitch=76),
        MotifRef('desc', start_pitch=76),
        MotifRef('arp', start_pitch=69),
        MotifRef('ans', start_pitch=68),
        MotifRef('rest', start_pitch=69),
    ], tension=TensionShape.ARCH,
       description="A phrase returning broadly")

    # --- Sections ---

    prog.sections['dev'] = Section('dev', [
        PhraseRef('dev_rising'),
        PhraseRef('dev_dialogue'),
        PhraseRef('dev_climax'),
    ], description="development section")

    prog.sections['recap'] = Section('recap', [
        PhraseRef('A_broad'),
    ], description="recapitulation")

    prog.sections['coda'] = Section('coda', [
        PhraseRef('coda'),
    ], description="coda")

    # --- Form: Exposition → Development → Recap → Coda ---
    prog.form = [
        SectionRef('A'),       # exposition: state the theme
        SectionRef('A'),       # repeat for familiarity
        SectionRef('dev'),     # development: take it apart
        SectionRef('recap'),   # recapitulation: bring it back
        SectionRef('coda'),    # coda: fade away
    ]

    return prog


# ============================================================
# Generate all
# ============================================================

if __name__ == "__main__":
    variations = [
        ("dna_v1_sequential", var_sequential_development),
        ("dna_v2_reharmonized", var_reharmonized),
        ("dna_v3_fragmented", var_fragmented_development),
        ("dna_v4_augmented_climax", var_augmented_climax),
        ("dna_v5_combined", var_combined_dna),
        ("dna_v6_sonata", var_sonata_development),
    ]

    for filename, fn in variations:
        prog = fn()
        print(f"\n{'='*60}")
        print(prog.title)
        path = f"{filename}.mid"
        n = dna_to_midi(prog, path)
        print(f"  → {path} ({n} notes)")
