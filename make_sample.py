"""
Create sample MIDI files with real musical structure for analysis.

1. Für Elise (A section and partial B section) - clear ABA form with sequences
2. Beethoven 5th opening - motif development and transposition
"""

from music_rep import NoteEvent, notes_to_midi

T = 480  # ticks per beat

# ============================================================
# Für Elise - Piano reduction
# ============================================================
# The A section melody: E5 D#5 E5 D#5 E5 B4 D5 C5 A4 ...
# This repeats several times with the same accompaniment pattern

def fur_elise():
    notes = []
    t = 0
    eighth = T // 2

    # --- A section melody (right hand) ---
    def a_section_melody(start):
        """The iconic Für Elise A section melody."""
        e = eighth
        pitches_durs = [
            # "E D# E D# E B D C A" motif
            (76, e), (75, e), (76, e), (75, e), (76, e),
            (71, e), (74, e), (72, e),
            (69, e*3),  # A held
            # "C E A B" response
            (60, e), (64, e), (69, e),
            (71, e*3),  # B held
            # "E G# B C" response
            (64, e), (68, e), (71, e),
            (72, e*3),  # C held
            # back to the motif
            (64, e), (76, e), (75, e), (76, e), (75, e), (76, e),
            (71, e), (74, e), (72, e),
            (69, e*3),
            # "C E A B" again
            (60, e), (64, e), (69, e),
            (71, e*3),
            # ending of A: "E C B A"
            (64, e), (72, e), (71, e),
            (69, e*4),  # A held longer (half note)
        ]
        result = []
        pos = start
        for pitch, dur in pitches_durs:
            result.append(NoteEvent(pitch, pos, dur, 80))
            pos += dur
        return result, pos

    # --- A section bass (left hand) - arpeggiated chords ---
    def a_section_bass(start):
        e = eighth
        # Simplified bass: chord roots and fifths
        bass_pattern = [
            # Am chord under melody
            (45, e*3), (52, e*3), (57, e*3),
            # E chord
            (40, e*3), (52, e*3), (56, e*3),
            # Am chord
            (45, e*3), (52, e*3), (57, e*3),
            # E chord
            (40, e*3), (52, e*3), (56, e*3),
            # Am again
            (45, e*3), (52, e*3), (57, e*3),
            # E chord
            (40, e*3), (52, e*3), (56, e*3),
            # Am to end
            (45, e*3), (52, e*3), (57, e*3),
            (45, e*4),
        ]
        result = []
        pos = start
        for pitch, dur in bass_pattern:
            result.append(NoteEvent(pitch, pos, dur, 50))
            pos += dur
        return result, pos

    # --- B section (contrasting middle section) ---
    def b_section_melody(start):
        """B section: more lyrical, in F major."""
        e = eighth
        q = T  # quarter
        pitches_durs = [
            # F major melody
            (72, q), (74, e), (76, e), (77, q), (76, e), (74, e),
            (72, q), (71, e), (69, e), (71, q), (72, e), (74, e),
            (76, q*2),
            # Sequence: same melody transposed down a step (Dm)
            (71, q), (72, e), (74, e), (76, q), (74, e), (72, e),
            (71, q), (69, e), (67, e), (69, q), (71, e), (72, e),
            (74, q*2),
            # Back to F, building up
            (72, q), (74, e), (76, e), (77, q), (76, e), (74, e),
            (72, q), (71, e), (69, e), (71, e), (72, e),
            (69, q*3),  # resolve to A
        ]
        result = []
        pos = start
        for pitch, dur in pitches_durs:
            result.append(NoteEvent(pitch, pos, dur, 75))
            pos += dur
        return result, pos

    # Build the full piece: A A B A (typical ternary form)
    melody1, t1 = a_section_melody(t)
    bass1, _ = a_section_bass(t)
    notes += melody1 + bass1
    t = t1 + T  # small gap

    # Second A (exact repeat)
    melody2, t2 = a_section_melody(t)
    bass2, _ = a_section_bass(t)
    notes += melody2 + bass2
    t = t2 + T

    # B section
    b_mel, t3 = b_section_melody(t)
    notes += b_mel
    t = t3 + T

    # Third A (da capo)
    melody3, t4 = a_section_melody(t)
    bass3, _ = a_section_bass(t)
    notes += melody3 + bass3

    return notes


# ============================================================
# Beethoven 5th - Piano reduction of opening
# ============================================================

def beethoven_5th():
    notes = []
    t = 0
    e = T // 2  # eighth note
    q = T       # quarter
    h = T * 2   # half

    def fate_motif(start, base_pitch, short=e, long_dur=h):
        """G G G Eb pattern (3 short + 1 long, drop of minor 3rd)."""
        return [
            NoteEvent(base_pitch, start, short, 90),
            NoteEvent(base_pitch, start + short, short, 90),
            NoteEvent(base_pitch, start + 2*short, short, 90),
            NoteEvent(base_pitch - 4, start + 3*short, long_dur, 100),
        ], start + 3*short + long_dur

    def fate_motif_step(start, base_pitch, short=e, long_dur=h):
        """F F F D pattern (same rhythm, drop of minor 3rd from F)."""
        return [
            NoteEvent(base_pitch, start, short, 85),
            NoteEvent(base_pitch, start + short, short, 85),
            NoteEvent(base_pitch, start + 2*short, short, 85),
            NoteEvent(base_pitch - 3, start + 3*short, long_dur, 95),
        ], start + 3*short + long_dur

    # Exposition
    # mm 1-4: G G G Eb, pause, F F F D
    m, t = fate_motif(t, 67)
    notes += m
    t += q  # fermata/pause

    m, t = fate_motif_step(t, 65)
    notes += m
    t += q

    # mm 5-8: repeat of opening pair
    m, t = fate_motif(t, 67)
    notes += m
    t += e

    m, t = fate_motif_step(t, 65)
    notes += m
    t += q

    # mm 9-12: ascending sequence of the motif
    for transp in [0, 2, 3, 5]:
        m, t = fate_motif(t, 67 + transp)
        notes += m
        t += e

    # mm 13-16: descending sequence
    for transp in [7, 5, 3, 0]:
        m, t = fate_motif(t, 67 + transp)
        notes += m
        t += e

    # mm 17-20: second theme - lyrical, in Eb major
    second_theme = [63, 65, 67, 68, 70, 68, 67, 65, 63, 62, 63, 65, 67]
    for p in second_theme:
        notes.append(NoteEvent(p, t, q, 70))
        t += q

    # mm 21-24: second theme transposed up a 4th
    for p in second_theme:
        notes.append(NoteEvent(p + 5, t, q, 70))
        t += q

    # mm 25-28: fate motif returns, fff, building
    for transp in [0, 0, 2, 2, 4, 4, 5, 5]:
        m, t = fate_motif(t, 67 + transp, short=e//2, long_dur=q)
        notes += m

    # mm 29-32: augmentation (doubled durations)
    m, t = fate_motif(t, 67, short=q, long_dur=h*2)
    notes += m
    t += q

    # mm 33-34: diminution (halved durations) in rapid sequence
    for transp in [0, 3, 5, 7, 0, 3, 5, 7]:
        m, t = fate_motif(t, 67 + transp, short=e//2, long_dur=e)
        notes += m

    # Bass octaves reinforcing key moments
    bass_times = [0]
    for bt in bass_times:
        notes.append(NoteEvent(43, bt, h, 100))  # low G

    return notes


# Generate both files
fur_elise_notes = fur_elise()
notes_to_midi(fur_elise_notes, "fur_elise.mid", ticks_per_beat=T)
print(f"Created fur_elise.mid with {len(fur_elise_notes)} notes")

b5_notes = beethoven_5th()
notes_to_midi(b5_notes, "beethoven5.mid", ticks_per_beat=T)
print(f"Created beethoven5.mid with {len(b5_notes)} notes")
