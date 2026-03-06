"""
Musical DNA: deep abstraction + harmonic awareness + tension curves + dynamics.

The previous deep_abstraction.py captured the SHAPE of the music (intervals,
rhythm) but not the LOGIC (why those shapes work). This adds:

1. HARMONY: Each motif lives within a chord context. Variations must respect
   the harmonic function — you can change notes, but they must belong to
   the right chord/scale at that moment.

2. TENSION CURVE: Each motif has a tension profile (building, releasing,
   peak, stable). The overall piece has a tension arc. Variations must
   preserve this arc shape.

3. DYNAMICS: Velocity follows the tension curve — louder at peaks,
   softer at rest. Real music breathes.

4. DEVELOPMENT: Instead of blind substitution, use real compositional
   techniques — fragmentation, sequence, inversion, augmentation,
   combination — all constrained by harmony and tension.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum
from copy import deepcopy
import math

from music_rep import NoteEvent, notes_to_midi


NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
T = 240  # eighth note in ticks


def note_name(pitch):
    return f"{NOTE_NAMES[pitch % 12]}{pitch // 12}"


# ============================================================
# HARMONY
# ============================================================

# Scale definitions (pitch classes, relative to root)
SCALES = {
    'minor':         [0, 2, 3, 5, 7, 8, 10],
    'harmonic_minor': [0, 2, 3, 5, 7, 8, 11],
    'major':         [0, 2, 4, 5, 7, 9, 11],
    'dorian':        [0, 2, 3, 5, 7, 9, 10],
    'mixolydian':    [0, 2, 4, 5, 7, 9, 10],
    'chromatic':     list(range(12)),
}

# Chord definitions (pitch classes relative to root)
CHORDS = {
    'm':    [0, 3, 7],        # minor triad
    'M':    [0, 4, 7],        # major triad
    '7':    [0, 4, 7, 10],    # dominant 7th
    'm7':   [0, 3, 7, 10],    # minor 7th
    'dim':  [0, 3, 6],        # diminished
    'aug':  [0, 4, 8],        # augmented
}


@dataclass
class HarmonicContext:
    """The harmonic environment for a motif."""
    root: int                  # pitch class (0=C, 9=A, etc.)
    chord_type: str            # key into CHORDS
    scale_type: str            # key into SCALES

    @property
    def chord_tones(self) -> List[int]:
        return [(self.root + pc) % 12 for pc in CHORDS[self.chord_type]]

    @property
    def scale_tones(self) -> List[int]:
        return [(self.root + pc) % 12 for pc in SCALES[self.scale_type]]

    def is_chord_tone(self, pitch: int) -> bool:
        return (pitch % 12) in self.chord_tones

    def is_scale_tone(self, pitch: int) -> bool:
        return (pitch % 12) in self.scale_tones

    def nearest_chord_tone(self, pitch: int) -> int:
        """Snap a pitch to the nearest chord tone."""
        pc = pitch % 12
        octave = pitch // 12
        best = min(self.chord_tones, key=lambda ct: min(abs(ct - pc), 12 - abs(ct - pc)))
        # Preserve octave as closely as possible
        candidate = octave * 12 + best
        if abs(candidate - pitch) > 6:
            candidate += 12 if candidate < pitch else -12
        return candidate

    def nearest_scale_tone(self, pitch: int) -> int:
        """Snap a pitch to the nearest scale tone."""
        pc = pitch % 12
        octave = pitch // 12
        best = min(self.scale_tones, key=lambda st: min(abs(st - pc), 12 - abs(st - pc)))
        candidate = octave * 12 + best
        if abs(candidate - pitch) > 6:
            candidate += 12 if candidate < pitch else -12
        return candidate

    def __repr__(self):
        return f"{NOTE_NAMES[self.root]}{self.chord_type}({self.scale_type})"


# Für Elise harmonic contexts
Am = HarmonicContext(9, 'm', 'harmonic_minor')   # A minor
E7 = HarmonicContext(4, '7', 'harmonic_minor')   # E dominant 7 (dominant of Am)
C  = HarmonicContext(0, 'M', 'major')            # C major (relative major)
G7 = HarmonicContext(7, '7', 'major')            # G dominant 7 (dominant of C)
F  = HarmonicContext(5, 'M', 'major')            # F major (subdominant)
Dm = HarmonicContext(2, 'm', 'minor')            # D minor


# ============================================================
# TENSION
# ============================================================

class TensionShape(Enum):
    """The tension profile of a motif."""
    BUILDING = "building"       # tension increases: suspense, anticipation
    RELEASING = "releasing"     # tension decreases: resolution, rest
    PEAK = "peak"               # high tension throughout: climax
    STABLE = "stable"           # low, even tension: grounding
    ARCH = "arch"               # rises then falls: a complete gesture


@dataclass
class TensionPoint:
    """A point on the tension curve."""
    position: float    # 0.0 to 1.0 within the piece
    level: float       # 0.0 (rest) to 1.0 (maximum tension)


def tension_shape_to_curve(shape: TensionShape, n_points: int = 5) -> List[float]:
    """Convert a tension shape to a series of values."""
    if shape == TensionShape.BUILDING:
        return [i / (n_points - 1) for i in range(n_points)]
    elif shape == TensionShape.RELEASING:
        return [1.0 - i / (n_points - 1) for i in range(n_points)]
    elif shape == TensionShape.PEAK:
        return [0.8 + 0.2 * math.sin(math.pi * i / (n_points - 1)) for i in range(n_points)]
    elif shape == TensionShape.STABLE:
        return [0.3] * n_points
    elif shape == TensionShape.ARCH:
        return [math.sin(math.pi * i / (n_points - 1)) for i in range(n_points)]
    return [0.5] * n_points


# ============================================================
# ATOMS & MOTIFS (with harmony + tension)
# ============================================================

@dataclass
class Atom:
    interval: int
    duration: int

    def __repr__(self):
        if self.interval == 0:
            return f"•:{self.duration}"
        return f"{self.interval:+d}:{self.duration}"


@dataclass
class Motif:
    name: str
    atoms: List[Atom]
    harmony: HarmonicContext
    tension: TensionShape
    description: str = ""

    @property
    def size(self):
        return len(self.atoms)

    @property
    def total_duration(self):
        return sum(a.duration for a in self.atoms)

    def intervals(self):
        return [a.interval for a in self.atoms]

    def __repr__(self):
        atoms_str = " ".join(str(a) for a in self.atoms)
        return f"motif {self.name} [{self.harmony}|{self.tension.value}] = [{atoms_str}]  # {self.description}"


# ============================================================
# PHRASES & FORM (same structure as before, but harmony-aware)
# ============================================================

@dataclass
class Transform:
    transpose: int = 0
    invert: bool = False
    retrograde: bool = False
    time_scale: float = 1.0

    def __repr__(self):
        parts = []
        if self.transpose != 0:
            parts.append(f"T{self.transpose:+d}")
        if self.invert:
            parts.append("inv")
        if self.retrograde:
            parts.append("ret")
        if self.time_scale != 1.0:
            parts.append(f"x{self.time_scale}")
        return "." + ".".join(parts) if parts else ""

    @property
    def is_identity(self):
        return self.transpose == 0 and not self.invert and not self.retrograde and self.time_scale == 1.0


@dataclass
class MotifRef:
    name: str
    start_pitch: int
    transform: Transform = field(default_factory=Transform)

    def __repr__(self):
        return f"{self.name}@{note_name(self.start_pitch)}{self.transform}"


@dataclass
class Phrase:
    name: str
    elements: List[MotifRef]
    tension: TensionShape = TensionShape.ARCH
    description: str = ""

    def __repr__(self):
        elems = " → ".join(str(e) for e in self.elements)
        return f"phrase {self.name} [{self.tension.value}] = [{elems}]"


@dataclass
class PhraseRef:
    name: str
    transform: Transform = field(default_factory=Transform)

    def __repr__(self):
        return f"{self.name}{self.transform}"


@dataclass
class Section:
    name: str
    elements: List[PhraseRef]
    description: str = ""

    def __repr__(self):
        elems = " → ".join(str(e) for e in self.elements)
        return f"section {self.name} = [{elems}]"


@dataclass
class SectionRef:
    name: str
    transform: Transform = field(default_factory=Transform)

    def __repr__(self):
        return f"{self.name}{self.transform}"


# ============================================================
# THE PROGRAM
# ============================================================

@dataclass
class MusicalDNA:
    title: str
    motifs: Dict[str, Motif] = field(default_factory=dict)
    phrases: Dict[str, Phrase] = field(default_factory=dict)
    sections: Dict[str, Section] = field(default_factory=dict)
    form: List[SectionRef] = field(default_factory=list)

    def expand(self, with_dynamics=True) -> List[NoteEvent]:
        """Expand hierarchy to NoteEvents with velocity dynamics."""
        notes = []
        time = 0

        # First pass: collect all notes with their motif tension info
        note_tensions = []

        for sec_ref in self.form:
            section = self.sections[sec_ref.name]
            for phrase_ref in section.elements:
                phrase = self.phrases[phrase_ref.name]
                phrase_notes = []

                for mi, motif_ref in enumerate(phrase.elements):
                    motif = self.motifs[motif_ref.name]
                    pitch = motif_ref.start_pitch + phrase_ref.transform.transpose + sec_ref.transform.transpose

                    atoms = list(motif.atoms)
                    if motif_ref.transform.invert:
                        atoms = [Atom(-a.interval, a.duration) for a in atoms]
                    if motif_ref.transform.retrograde:
                        atoms = list(reversed(atoms))

                    ts = (motif_ref.transform.time_scale *
                          phrase_ref.transform.time_scale *
                          sec_ref.transform.time_scale)

                    # Get tension curve for this motif
                    tcurve = tension_shape_to_curve(motif.tension, len(atoms))

                    for ai, atom in enumerate(atoms):
                        pitch += atom.interval
                        dur = int(atom.duration * ts)
                        t = tcurve[ai]
                        note_tensions.append((pitch, time, dur, t, motif.tension))
                        time += dur

        # Second pass: compute velocity from tension
        if not note_tensions:
            return notes

        total_dur = sum(nt[2] for nt in note_tensions)
        cumulative = 0

        # Build a global tension curve: combine local motif tension with
        # a large-scale arch for the whole piece
        for pitch, start, dur, local_tension, shape in note_tensions:
            # Global position (0 to 1)
            global_pos = cumulative / total_dur if total_dur > 0 else 0
            cumulative += dur

            # Global tension: a gentle arch over the whole piece
            global_tension = 0.3 + 0.4 * math.sin(math.pi * global_pos)

            # Combine: local tension drives the dynamics, global provides shape
            combined = 0.6 * local_tension + 0.4 * global_tension

            if with_dynamics:
                # Map tension 0-1 to velocity 45-110
                vel = int(45 + combined * 65)
                vel = max(40, min(120, vel))
            else:
                vel = 80

            notes.append(NoteEvent(pitch, start, dur, vel))

        return notes

    def __repr__(self):
        lines = [f"=== {self.title} ==="]
        lines.append("")
        lines.append("--- MOTIFS ---")
        for m in self.motifs.values():
            lines.append(f"  {m}")
        lines.append("")
        lines.append("--- PHRASES ---")
        for p in self.phrases.values():
            lines.append(f"  {p}")
        lines.append("")
        lines.append("--- SECTIONS ---")
        for s in self.sections.values():
            lines.append(f"  {s}")
        lines.append("")
        lines.append("--- FORM ---")
        lines.append("  " + " | ".join(str(f) for f in self.form))
        return "\n".join(lines)


# ============================================================
# BUILD FÜR ELISE WITH FULL MUSICAL DNA
# ============================================================

def build_fur_elise() -> MusicalDNA:
    """
    Für Elise with harmonic context and tension annotation.

    Harmonic analysis:
      A section: E7 → Am → Am → E7 → Am
        - Trill is on E (dominant), creating tension over E7
        - Descent resolves to A (tonic) = release
        - Arpeggio outlines Am chord = stability
        - Answer phrase: G#=leading tone (E7 tension) → resolves to Am

      B section: C → G7 → Am → E7 → Am
        - Arch is in C major = bright, stable
        - Steps rise through G → Am → back to E dominant

    Tension arc:
      A section: BUILDING (trill) → RELEASING (descent) → BUILDING (arpeggio) → RELEASING (answer)
      B section: ARCH (symmetric) → BUILDING (sequences) → RELEASING (transition)
    """
    prog = MusicalDNA(title="Für Elise — Full Musical DNA")

    # ===== MOTIFS with harmony + tension =====

    prog.motifs['osc'] = Motif('osc', [
        Atom(0, T), Atom(-1, T), Atom(+1, T), Atom(-1, T), Atom(+1, T),
    ], harmony=E7, tension=TensionShape.BUILDING,
       description="trill: E-D# oscillation over dominant E7")

    prog.motifs['desc'] = Motif('desc', [
        Atom(-5, T), Atom(+3, T), Atom(-2, T), Atom(-3, T*3),
    ], harmony=Am, tension=TensionShape.RELEASING,
       description="descent: resolving through Am to tonic A")

    prog.motifs['arp'] = Motif('arp', [
        Atom(-9, T), Atom(+4, T), Atom(+5, T), Atom(+2, T*3), Atom(-7, T),
    ], harmony=Am, tension=TensionShape.BUILDING,
       description="Am arpeggio: spelling out the tonic chord")

    prog.motifs['ans'] = Motif('ans', [
        Atom(0, T), Atom(+3, T), Atom(+1, T*3),
        Atom(-8, T), Atom(+8, T), Atom(-1, T), Atom(-2, T*4),
    ], harmony=Am, tension=TensionShape.RELEASING,
       description="answer: G#(leading tone)→C(tonic area)→descent to A")

    prog.motifs['arch'] = Motif('arch', [
        Atom(0, T*2), Atom(+2, T), Atom(+2, T), Atom(+1, T*2),
        Atom(-1, T), Atom(-2, T), Atom(-2, T*2), Atom(-1, T), Atom(-2, T),
    ], harmony=C, tension=TensionShape.ARCH,
       description="arch: C major scale up to F then back down")

    prog.motifs['step_up'] = Motif('step_up', [
        Atom(0, T*2), Atom(+2, T), Atom(+2, T), Atom(+2, T*4),
    ], harmony=Am, tension=TensionShape.BUILDING,
       description="stepwise ascent: building energy")

    prog.motifs['step_dn'] = Motif('step_dn', [
        Atom(0, T*2), Atom(-2, T), Atom(-2, T), Atom(-2, T*2),
    ], harmony=Am, tension=TensionShape.RELEASING,
       description="stepwise descent: releasing energy")

    prog.motifs['rest'] = Motif('rest', [
        Atom(0, T*4),
    ], harmony=Am, tension=TensionShape.STABLE,
       description="pause: breathing room")

    # ===== PHRASES with tension shapes =====

    prog.phrases['A_phrase'] = Phrase('A_phrase', [
        MotifRef('osc', start_pitch=76),
        MotifRef('desc', start_pitch=76),
        MotifRef('arp', start_pitch=69),
        MotifRef('ans', start_pitch=68),
        MotifRef('rest', start_pitch=69),
    ], tension=TensionShape.ARCH,
       description="A phrase: tension builds (trill), releases (descent), rebuilds (arp), resolves (answer)")

    prog.phrases['B_phrase'] = Phrase('B_phrase', [
        MotifRef('arch', start_pitch=72),
        MotifRef('step_up', start_pitch=71),
        MotifRef('step_up', start_pitch=71),
        MotifRef('step_dn', start_pitch=76),
        MotifRef('step_up', start_pitch=69),
    ], tension=TensionShape.BUILDING,
       description="B phrase: contrasting major mode, building through sequences")

    prog.phrases['trans'] = Phrase('trans', [
        MotifRef('arch', start_pitch=72),
        MotifRef('rest', start_pitch=69),
    ], tension=TensionShape.RELEASING,
       description="transition: arch settles back for A return")

    # ===== SECTIONS =====

    prog.sections['A'] = Section('A', [PhraseRef('A_phrase')], description="A section")
    prog.sections['B'] = Section('B', [PhraseRef('B_phrase'), PhraseRef('trans')],
                                  description="B section")

    # ===== FORM =====
    prog.form = [SectionRef('A'), SectionRef('A'), SectionRef('B'), SectionRef('A')]

    return prog


# ============================================================
# DEVELOPMENT TECHNIQUES
# (Harmonically-aware transformations)
# ============================================================

def fragment(motif: Motif, start: int, length: int, new_name: str = None) -> Motif:
    """Extract a fragment of a motif. Like taking just the first 3 notes of the trill."""
    atoms = motif.atoms[start:start+length]
    name = new_name or f"{motif.name}_frag"
    return Motif(name, atoms, motif.harmony, motif.tension, f"fragment of {motif.name}")


def sequence(motif: Motif, transpositions: List[int], new_name: str = None) -> Motif:
    """Repeat a motif at different transposition levels.
    Like taking the trill and doing it at E, then D, then C.
    Each transposition is applied cumulatively to the intervals."""
    all_atoms = []
    for i, trans in enumerate(transpositions):
        for j, atom in enumerate(motif.atoms):
            if i == 0 and j == 0:
                all_atoms.append(Atom(atom.interval, atom.duration))
            elif j == 0:
                # First atom of subsequent repetition: add transposition to connect
                all_atoms.append(Atom(atom.interval + trans, atom.duration))
            else:
                all_atoms.append(Atom(atom.interval, atom.duration))
    name = new_name or f"{motif.name}_seq"
    return Motif(name, all_atoms, motif.harmony, motif.tension,
                 f"sequence of {motif.name} at [{','.join(f'{t:+d}' for t in transpositions)}]")


def augment(motif: Motif, time_factor: float, new_name: str = None) -> Motif:
    """Stretch durations. Factor > 1 = slower, < 1 = faster."""
    atoms = [Atom(a.interval, int(a.duration * time_factor)) for a in motif.atoms]
    name = new_name or f"{motif.name}_aug"
    return Motif(name, atoms, motif.harmony, motif.tension,
                 f"{motif.name} x{time_factor}")


def invert_motif(motif: Motif, new_name: str = None) -> Motif:
    """Invert all intervals. Ascending becomes descending."""
    atoms = [Atom(-a.interval, a.duration) for a in motif.atoms]
    name = new_name or f"{motif.name}_inv"
    # Inversion flips the tension shape
    new_tension = motif.tension
    if motif.tension == TensionShape.BUILDING:
        new_tension = TensionShape.RELEASING
    elif motif.tension == TensionShape.RELEASING:
        new_tension = TensionShape.BUILDING
    return Motif(name, atoms, motif.harmony, new_tension,
                 f"inversion of {motif.name}")


def combine(motif_a: Motif, motif_b: Motif, bridge_interval: int = 0,
            new_name: str = None) -> Motif:
    """Combine two motifs with a bridging interval between them."""
    atoms = list(motif_a.atoms)
    # Bridge atom connects the last note of A to the first note of B
    if bridge_interval != 0:
        bridge = [Atom(bridge_interval, T)]
        atoms.extend(bridge)
    atoms.extend(motif_b.atoms)
    name = new_name or f"{motif_a.name}+{motif_b.name}"
    return Motif(name, atoms, motif_a.harmony, TensionShape.ARCH,
                 f"{motif_a.name} combined with {motif_b.name}")


def harmonize_motif(motif: Motif, new_harmony: HarmonicContext,
                    new_name: str = None) -> Motif:
    """Re-harmonize a motif: snap its intervals to fit the new chord/scale.
    This is the key to coherent variation — change the harmony, not random intervals."""
    # Build the pitch sequence from intervals
    pitches = [60]  # arbitrary start, we only care about relative
    for atom in motif.atoms:
        pitches.append(pitches[-1] + atom.interval)

    # Snap each pitch to the nearest scale tone of the new harmony
    new_pitches = [new_harmony.nearest_scale_tone(p) for p in pitches]

    # Rebuild atoms from the new pitch sequence
    new_atoms = []
    for i, atom in enumerate(motif.atoms):
        new_interval = new_pitches[i+1] - new_pitches[i] if i < len(motif.atoms) - 1 else 0
        if i == 0:
            new_interval = new_pitches[1] - new_pitches[0] if len(new_pitches) > 1 else 0
            new_atoms.append(Atom(new_interval, atom.duration))
        else:
            new_interval = new_pitches[i+1] - new_pitches[i] if i+1 < len(new_pitches) else 0
            new_atoms.append(Atom(new_interval, atom.duration))

    name = new_name or f"{motif.name}_{new_harmony}"
    return Motif(name, new_atoms, new_harmony, motif.tension,
                 f"{motif.name} reharmonized to {new_harmony}")


def snap_to_harmony(notes: List[NoteEvent], harmony: HarmonicContext,
                    prefer_chord_tones: bool = True) -> List[NoteEvent]:
    """Post-process: snap notes to the nearest scale/chord tones."""
    result = []
    for n in notes:
        if prefer_chord_tones:
            new_pitch = harmony.nearest_chord_tone(n.pitch)
        else:
            new_pitch = harmony.nearest_scale_tone(n.pitch)
        result.append(NoteEvent(new_pitch, n.start, n.duration, n.velocity))
    return result


# ============================================================
# EXPORT
# ============================================================

def dna_to_midi(prog: MusicalDNA, path: str, tpb: int = 480,
                with_dynamics: bool = True):
    notes = prog.expand(with_dynamics=with_dynamics)
    notes_to_midi(notes, path, ticks_per_beat=tpb)
    return len(notes)


if __name__ == "__main__":
    prog = build_fur_elise()
    print(prog)
    n = dna_to_midi(prog, "fur_elise_dna.mid")
    print(f"\nExpanded to {n} notes → fur_elise_dna.mid")
