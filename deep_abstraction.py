"""
Deep hierarchical abstraction of music.

Instead of one level of patterns, we decompose recursively:
  Level 0: Raw notes
  Level 1: Motifs (trill, descent, arpeggio, arch)
  Level 2: Phrases (motif combinations like trill+descent+arpeggio = P1)
  Level 3: Sections (phrase sequences like A = P1+P2+rest)
  Level 4: Form (section arrangement like ABA)

Each level is described in terms of the level below it,
plus transformations (transpose, invert, augment, retrograde).
"""

from dataclasses import dataclass, field
from typing import List, Union, Optional, Dict, Tuple
from copy import deepcopy
from music_rep import NoteEvent, notes_to_midi

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def note_name(pitch):
    return f"{NOTE_NAMES[pitch % 12]}{pitch // 12}"


@dataclass
class Atom:
    """The smallest unit: a pitch interval + duration."""
    interval: int     # semitones relative to previous note (0 for first note)
    duration: int     # in ticks

    def __repr__(self):
        if self.interval == 0:
            return f"•:{self.duration}"
        return f"{self.interval:+d}:{self.duration}"


@dataclass
class Motif:
    """A named atomic pattern — the building block."""
    name: str
    atoms: List[Atom]
    description: str = ""

    @property
    def size(self):
        return len(self.atoms)

    def intervals(self):
        return tuple(a.interval for a in self.atoms[1:])

    def __repr__(self):
        atoms_str = " ".join(str(a) for a in self.atoms)
        desc = f" # {self.description}" if self.description else ""
        return f"motif {self.name} = [{atoms_str}]{desc}"


@dataclass
class Transform:
    """A transformation applied to a motif or phrase."""
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
    """Reference to a motif with a transformation."""
    name: str
    start_pitch: int       # absolute starting pitch
    transform: Transform = field(default_factory=Transform)

    def __repr__(self):
        return f"{self.name}@{note_name(self.start_pitch)}{self.transform}"


@dataclass
class Phrase:
    """A named sequence of motif references — mid-level structure."""
    name: str
    elements: List[MotifRef]
    description: str = ""

    def __repr__(self):
        elems = " → ".join(str(e) for e in self.elements)
        desc = f" # {self.description}" if self.description else ""
        return f"phrase {self.name} = [{elems}]{desc}"


@dataclass
class PhraseRef:
    """Reference to a phrase with a transformation."""
    name: str
    transform: Transform = field(default_factory=Transform)

    def __repr__(self):
        return f"{self.name}{self.transform}"


@dataclass
class Section:
    """A named sequence of phrase references — high-level structure."""
    name: str
    elements: List[PhraseRef]
    description: str = ""

    def __repr__(self):
        elems = " → ".join(str(e) for e in self.elements)
        desc = f" # {self.description}" if self.description else ""
        return f"section {self.name} = [{elems}]{desc}"


@dataclass
class SectionRef:
    """Reference to a section."""
    name: str
    transform: Transform = field(default_factory=Transform)

    def __repr__(self):
        return f"{self.name}{self.transform}"


@dataclass
class DeepProgram:
    """The full hierarchical representation."""
    title: str
    motifs: Dict[str, Motif] = field(default_factory=dict)
    phrases: Dict[str, Phrase] = field(default_factory=dict)
    sections: Dict[str, Section] = field(default_factory=dict)
    form: List[SectionRef] = field(default_factory=list)

    @property
    def total_symbols(self):
        """Total program size at all levels."""
        m = sum(m.size for m in self.motifs.values())
        p = sum(len(p.elements) for p in self.phrases.values())
        s = sum(len(s.elements) for s in self.sections.values())
        f = len(self.form)
        return m + p + s + f

    def expand(self) -> List[NoteEvent]:
        """Expand the entire hierarchy into NoteEvents."""
        notes = []
        time = 0
        for sec_ref in self.form:
            section = self.sections[sec_ref.name]
            for phrase_ref in section.elements:
                phrase = self.phrases[phrase_ref.name]
                for motif_ref in phrase.elements:
                    motif = self.motifs[motif_ref.name]
                    pitch = motif_ref.start_pitch + phrase_ref.transform.transpose + sec_ref.transform.transpose

                    # Get the atoms, possibly transformed
                    atoms = list(motif.atoms)
                    if motif_ref.transform.invert:
                        atoms = [Atom(-a.interval, a.duration) for a in atoms]
                    if motif_ref.transform.retrograde:
                        atoms = list(reversed(atoms))

                    time_scale = motif_ref.transform.time_scale * phrase_ref.transform.time_scale * sec_ref.transform.time_scale

                    for atom in atoms:
                        pitch += atom.interval
                        dur = int(atom.duration * time_scale)
                        notes.append(NoteEvent(pitch, time, dur))
                        time += dur
        return notes

    def __repr__(self):
        lines = [f"=== {self.title} ==="]
        lines.append(f"Total symbols: {self.total_symbols}")
        lines.append("")
        lines.append("--- MOTIFS (atomic building blocks) ---")
        for m in self.motifs.values():
            lines.append(f"  {m}")
        lines.append("")
        lines.append("--- PHRASES (motif combinations) ---")
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


def build_fur_elise_deep() -> DeepProgram:
    """
    Build the deep hierarchical abstraction of Für Elise by hand,
    based on analyzing the patterns discovered by the refactoring loop.

    I looked at P1's 14 notes and saw:
      - notes 0-4: trill oscillation (-1,+1,-1,+1)
      - notes 4-8: descent (-5,+3,-2,-3) = falling through chord tones
      - notes 8-13: arpeggio up Am chord + cadential B-E

    P2 is an answer phrase: rise to C, drop to E, descend C-B-A

    P3 is a symmetric arch: up (+2,+2,+1) then down (-1,-2,-2,-1,-2)

    The B section middle material is a stepwise sequence.
    """
    T = 240  # eighth note

    prog = DeepProgram(title="Für Elise — Deep Abstraction")

    # ===== MOTIFS =====

    # The oscillation cell: the DNA of Für Elise
    # Just two atoms: step down, step up (repeated to make the trill)
    prog.motifs['osc'] = Motif('osc', [
        Atom(0, T),    # starting note
        Atom(-1, T),   # half step down
        Atom(+1, T),   # half step up
        Atom(-1, T),   # half step down
        Atom(+1, T),   # half step up
    ], description="oscillation cell (the trill)")

    # The descent: dropping through chord tones to land on A
    prog.motifs['desc'] = Motif('desc', [
        Atom(-5, T),   # down to B (from E)
        Atom(+3, T),   # up to D
        Atom(-2, T),   # down to C
        Atom(-3, T*3), # down to A (held)
    ], description="descending resolution to tonic")

    # The arpeggio: Am chord spelled out (A C E A) then B E
    prog.motifs['arp'] = Motif('arp', [
        Atom(-9, T),   # jump down to C5 (from A5)
        Atom(+4, T),   # up to E5
        Atom(+5, T),   # up to A5
        Atom(+2, T*3), # up to B5 (held)
        Atom(-7, T),   # down to E5
    ], description="Am arpeggio + cadential drop")

    # The answer: G#-B-C, then E-C-B-A (resolving)
    prog.motifs['ans'] = Motif('ans', [
        Atom(0, T),    # G#
        Atom(+3, T),   # B
        Atom(+1, T*3), # C (held)
        Atom(-8, T),   # drop to E
        Atom(+8, T),   # back to C
        Atom(-1, T),   # B
        Atom(-2, T*4), # A (held long)
    ], description="answer/resolution phrase")

    # The arch: ascending then descending scale
    prog.motifs['arch'] = Motif('arch', [
        Atom(0, T*2),  # C (held)
        Atom(+2, T),   # D
        Atom(+2, T),   # E
        Atom(+1, T*2), # F (held)
        Atom(-1, T),   # E
        Atom(-2, T),   # D
        Atom(-2, T*2), # C (held)
        Atom(-1, T),   # B
        Atom(-2, T),   # A
    ], description="symmetric arch (scale up then down)")

    # Stepwise rise: used in B section transitions
    prog.motifs['step_up'] = Motif('step_up', [
        Atom(0, T*2),  # root (held)
        Atom(+2, T),   # step
        Atom(+2, T),   # step
        Atom(+2, T*4), # step (held)
    ], description="stepwise ascending")

    # Stepwise fall
    prog.motifs['step_dn'] = Motif('step_dn', [
        Atom(0, T*2),
        Atom(-2, T),
        Atom(-2, T),
        Atom(-2, T*2),
    ], description="stepwise descending")

    # Rest / pause
    prog.motifs['rest'] = Motif('rest', [
        Atom(0, T*4),
    ], description="pause")

    # ===== PHRASES =====

    # The A phrase: trill + descent + arpeggio + answer
    # This is the original P1 + P2 + rest
    prog.phrases['A_phrase'] = Phrase('A_phrase', [
        MotifRef('osc', start_pitch=76),     # trill on E6
        MotifRef('desc', start_pitch=76),    # descend from E6 to A5
        MotifRef('arp', start_pitch=69),     # Am arpeggio from A5
        MotifRef('ans', start_pitch=68),     # answer from G#5
        MotifRef('rest', start_pitch=69),    # rest on A
    ], description="complete A phrase (trill → descent → arpeggio → answer → rest)")

    # The B phrase: arch + stepwise sequences
    prog.phrases['B_phrase'] = Phrase('B_phrase', [
        MotifRef('arch', start_pitch=72),           # arch from C6
        MotifRef('step_up', start_pitch=71),        # step up from B5
        MotifRef('step_up', start_pitch=71),        # step up from B5 (2nd time)
        MotifRef('step_dn', start_pitch=76),        # step down from E6
        MotifRef('step_up', start_pitch=69),        # step up from A5
    ], description="B phrase (arch + ascending/descending sequences)")

    # Transition: arch + link back to A
    prog.phrases['trans'] = Phrase('trans', [
        MotifRef('arch', start_pitch=72),
        MotifRef('rest', start_pitch=69),
    ], description="transition (arch + rest)")

    # ===== SECTIONS =====

    prog.sections['A'] = Section('A', [
        PhraseRef('A_phrase'),
    ], description="A section")

    prog.sections['B'] = Section('B', [
        PhraseRef('B_phrase'),
        PhraseRef('trans'),
    ], description="B section (contrasting middle)")

    # ===== FORM =====
    # ABA form
    prog.form = [
        SectionRef('A'),
        SectionRef('A'),
        SectionRef('B'),
        SectionRef('A'),
    ]

    return prog


def deep_program_to_midi(prog: DeepProgram, path: str, tpb: int = 480):
    notes = prog.expand()
    notes_to_midi(notes, path, ticks_per_beat=tpb)
    return len(notes)


if __name__ == "__main__":
    prog = build_fur_elise_deep()
    print(prog)

    n = deep_program_to_midi(prog, "deep_fur_elise.mid")
    print(f"\nExpanded to {n} notes → deep_fur_elise.mid")
