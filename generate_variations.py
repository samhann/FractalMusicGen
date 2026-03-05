"""
Variation generator: use discovered abstractions to create new versions of a piece.

Given a MusicProgram with extracted patterns, we can generate variations by:
1. Reordering pattern references (structural variation)
2. Changing transpositions (harmonic variation)
3. Changing time scales (rhythmic variation)
4. Substituting one pattern for another (thematic variation)
5. Developing patterns (fragmentation, inversion, retrograde)
"""

import random
from typing import List, Optional
from copy import deepcopy
from music_rep import NoteEvent, notes_to_midi
from music_program import (
    MusicProgram, PatternDef, PatternRef, Literal, Instruction,
    notes_to_program, refactor_loop,
)


def vary_transpositions(prog: MusicProgram, max_shift: int = 5, probability: float = 0.3) -> MusicProgram:
    """Randomly shift transpositions of pattern references."""
    new_prog = deepcopy(prog)
    for i, inst in enumerate(new_prog.instructions):
        if isinstance(inst, PatternRef) and random.random() < probability:
            shift = random.randint(-max_shift, max_shift)
            new_prog.instructions[i] = PatternRef(
                inst.name, inst.transpose + shift, inst.time_scale
            )
    return new_prog


def vary_time_scales(prog: MusicProgram, scales: List[float] = None,
                     probability: float = 0.2) -> MusicProgram:
    """Randomly change time scales of pattern references."""
    if scales is None:
        scales = [0.5, 0.75, 1.0, 1.5, 2.0]
    new_prog = deepcopy(prog)
    for i, inst in enumerate(new_prog.instructions):
        if isinstance(inst, PatternRef) and random.random() < probability:
            new_prog.instructions[i] = PatternRef(
                inst.name, inst.transpose, random.choice(scales)
            )
    return new_prog


def reorder_sections(prog: MusicProgram, section_size: int = 4) -> MusicProgram:
    """Divide the instruction body into sections and shuffle them."""
    new_prog = deepcopy(prog)
    insts = new_prog.instructions
    sections = [insts[i:i+section_size] for i in range(0, len(insts), section_size)]
    random.shuffle(sections)
    new_prog.instructions = [inst for section in sections for inst in section]
    return new_prog


def develop_pattern(pat_def: PatternDef) -> PatternDef:
    """Create a developed version of a pattern through fragmentation or inversion."""
    body = list(pat_def.body)
    technique = random.choice(['fragment', 'invert', 'retrograde', 'augment_fragment'])

    if technique == 'fragment' and len(body) > 3:
        # Take a fragment and repeat it
        start = random.randint(0, len(body) - 3)
        fragment = body[start:start+3]
        new_body = fragment * 2 + body[start+3:]
    elif technique == 'invert':
        # Invert intervals: if note went up, make it go down
        base_pitch = body[0].pitch
        new_body = [body[0]]
        for j in range(1, len(body)):
            interval = body[j].pitch - body[j-1].pitch
            inverted_pitch = new_body[j-1].pitch - interval
            new_body.append(Literal(inverted_pitch, body[j].duration))
    elif technique == 'retrograde':
        # Play the pattern backwards
        new_body = list(reversed(body))
    else:  # augment_fragment
        # Take first half and double its durations
        half = len(body) // 2
        new_body = [Literal(lit.pitch, lit.duration * 2) for lit in body[:half]]

    return PatternDef(pat_def.name + "_dev", new_body)


def substitute_patterns(prog: MusicProgram, probability: float = 0.2) -> MusicProgram:
    """Randomly substitute one pattern for another in the program."""
    new_prog = deepcopy(prog)
    pat_names = list(new_prog.definitions.keys())
    if len(pat_names) < 2:
        return new_prog

    for i, inst in enumerate(new_prog.instructions):
        if isinstance(inst, PatternRef) and random.random() < probability:
            other = random.choice([n for n in pat_names if n != inst.name])
            new_prog.instructions[i] = PatternRef(other, inst.transpose, inst.time_scale)
    return new_prog


def add_development_section(prog: MusicProgram) -> MusicProgram:
    """Add a development section that transforms existing patterns."""
    new_prog = deepcopy(prog)

    # Create developed versions of existing patterns
    dev_patterns = {}
    for name, pat_def in prog.definitions.items():
        dev = develop_pattern(pat_def)
        dev_patterns[dev.name] = dev

    new_prog.definitions.update(dev_patterns)

    # Build a development section from the new patterns
    dev_section = []
    for dev_name, dev_pat in dev_patterns.items():
        # Use the developed pattern at various transpositions
        for t in [0, 3, 5, 7]:
            dev_section.append(PatternRef(dev_name, t))

    # Insert development section in the middle
    mid = len(new_prog.instructions) // 2
    new_prog.instructions = (
        new_prog.instructions[:mid]
        + dev_section
        + new_prog.instructions[mid:]
    )
    return new_prog


def generate_variation(prog: MusicProgram, style: str = "free") -> MusicProgram:
    """Generate a variation of the program.

    Styles:
    - 'subtle': small transposition changes, keep structure
    - 'rhythmic': change time scales, keep pitches
    - 'harmonic': change transpositions significantly
    - 'structural': reorder sections
    - 'developmental': add development section with pattern transformations
    - 'free': combine multiple techniques
    """
    if style == 'subtle':
        return vary_transpositions(prog, max_shift=2, probability=0.2)
    elif style == 'rhythmic':
        return vary_time_scales(prog, probability=0.4)
    elif style == 'harmonic':
        return vary_transpositions(prog, max_shift=7, probability=0.5)
    elif style == 'structural':
        return reorder_sections(prog, section_size=3)
    elif style == 'developmental':
        return add_development_section(prog)
    else:  # free
        result = prog
        if random.random() < 0.5:
            result = vary_transpositions(result, max_shift=3, probability=0.3)
        if random.random() < 0.3:
            result = vary_time_scales(result, probability=0.2)
        if random.random() < 0.3:
            result = add_development_section(result)
        return result


def program_to_midi(prog: MusicProgram, path: str, tpb: int = 480):
    """Expand a program and write it to MIDI."""
    notes = prog.expand()
    notes_to_midi(notes, path, ticks_per_beat=tpb)
    return len(notes)
