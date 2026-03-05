"""
Music Program representation.

A piece of music is represented as a "program" — a list of instructions
that can be:
1. Literal note events
2. Pattern references (calls to named patterns with a transposition offset)
3. Sequence operations (repeat, transpose, augment, diminish)

The goal: find the shortest program that generates the original piece.
"""

from dataclasses import dataclass, field
from typing import List, Union, Optional, Tuple, Dict
from music_rep import NoteEvent

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


@dataclass
class Literal:
    """A literal note: pitch + duration."""
    pitch: int
    duration: int

    def __repr__(self):
        return f"{NOTE_NAMES[self.pitch % 12]}{self.pitch // 12}:{self.duration}"


@dataclass
class PatternRef:
    """Reference to a named pattern, possibly transposed and/or time-scaled."""
    name: str
    transpose: int = 0          # semitones
    time_scale: float = 1.0     # 2.0 = augmentation, 0.5 = diminution

    def __repr__(self):
        parts = [self.name]
        if self.transpose != 0:
            parts.append(f"T{self.transpose:+d}")
        if self.time_scale != 1.0:
            parts.append(f"x{self.time_scale}")
        return f"@{'_'.join(parts)}"


@dataclass
class PatternDef:
    """A named pattern definition: a sequence of Literals."""
    name: str
    body: List[Literal]

    @property
    def length(self) -> int:
        return len(self.body)

    def __repr__(self):
        body_str = " ".join(str(lit) for lit in self.body)
        return f"DEF {self.name} = [{body_str}]"


Instruction = Union[Literal, PatternRef]


@dataclass
class MusicProgram:
    """A program that generates music.

    definitions: named patterns (like function definitions)
    instructions: sequence of Literals and PatternRefs (the main body)
    """
    definitions: Dict[str, PatternDef] = field(default_factory=dict)
    instructions: List[Instruction] = field(default_factory=list)

    @property
    def program_size(self) -> int:
        """Total size: definitions + instructions.
        Each literal costs 1 token, each pattern ref costs 1 token,
        each definition costs its body length.
        """
        def_size = sum(d.length for d in self.definitions.values())
        return def_size + len(self.instructions)

    @property
    def expanded_size(self) -> int:
        """Size if we expanded all pattern references back to literals."""
        total = 0
        for inst in self.instructions:
            if isinstance(inst, Literal):
                total += 1
            elif isinstance(inst, PatternRef):
                if inst.name in self.definitions:
                    total += self.definitions[inst.name].length
                else:
                    total += 1
        return total

    @property
    def compression_ratio(self) -> float:
        exp = self.expanded_size
        if exp == 0:
            return 1.0
        return self.program_size / exp

    def expand(self) -> List[NoteEvent]:
        """Execute the program: expand all pattern refs into note events."""
        result = []
        time = 0
        for inst in self.instructions:
            if isinstance(inst, Literal):
                result.append(NoteEvent(inst.pitch, time, inst.duration))
                time += inst.duration
            elif isinstance(inst, PatternRef):
                pat = self.definitions.get(inst.name)
                if pat:
                    for lit in pat.body:
                        p = lit.pitch + inst.transpose
                        d = int(lit.duration * inst.time_scale)
                        result.append(NoteEvent(p, time, d))
                        time += d
        return result

    def __repr__(self):
        lines = ["=== MUSIC PROGRAM ==="]
        lines.append(f"Program size: {self.program_size} tokens "
                     f"(expanded: {self.expanded_size}, ratio: {self.compression_ratio:.2f})")
        lines.append("")
        for d in self.definitions.values():
            lines.append(str(d))
        lines.append("")
        lines.append("BODY:")
        # Print instructions compactly
        line = "  "
        for inst in self.instructions:
            token = str(inst)
            if len(line) + len(token) > 100:
                lines.append(line)
                line = "  "
            line += token + " "
        if line.strip():
            lines.append(line)
        lines.append(f"\nTotal: {len(self.instructions)} instructions, "
                     f"{len(self.definitions)} definitions")
        return "\n".join(lines)


def notes_to_program(notes: List[NoteEvent]) -> MusicProgram:
    """Create an initial (uncompressed) program from a note list."""
    prog = MusicProgram()
    for n in notes:
        prog.instructions.append(Literal(n.pitch, n.duration))
    return prog


def find_best_abstraction(prog: MusicProgram, min_len: int = 3, max_len: int = 20) -> Optional[Tuple[str, PatternDef, List[Tuple[int, int, float]]]]:
    """Find the single best pattern to extract from the program body.

    Returns (name, pattern_def, [(position, transpose, time_scale), ...])
    or None if no worthwhile abstraction exists.

    This considers:
    1. Exact matches (same pitches, same durations)
    2. Transposed matches (same intervals, same durations)
    3. Time-scaled matches (same intervals, proportional durations)
    """
    # Work only on literal sequences (skip existing pattern refs)
    literals = []
    lit_positions = []
    for i, inst in enumerate(prog.instructions):
        if isinstance(inst, Literal):
            literals.append(inst)
            lit_positions.append(i)

    if len(literals) < min_len:
        return None

    # Extract intervals and duration ratios for comparison
    best_saving = 0
    best_result = None

    for length in range(min_len, min(max_len + 1, len(literals) + 1)):
        # Build a map from (interval_tuple, dur_ratio_tuple) -> list of (position_in_literals, base_pitch, base_dur)
        pattern_map = {}

        for i in range(len(literals) - length + 1):
            chunk = literals[i:i+length]
            # Intervals (transposition-invariant)
            intervals = tuple(chunk[j+1].pitch - chunk[j].pitch for j in range(length - 1))
            # Duration ratios (time-scale-invariant)
            base_dur = chunk[0].duration if chunk[0].duration > 0 else 1
            dur_ratios = tuple(round(c.duration / base_dur, 2) for c in chunk)

            key = (intervals, dur_ratios)
            if key not in pattern_map:
                pattern_map[key] = []
            pattern_map[key].append((i, chunk[0].pitch, chunk[0].duration))

        for (intervals, dur_ratios), occurrences in pattern_map.items():
            if len(occurrences) < 2:
                continue

            # Remove overlapping occurrences
            filtered = [occurrences[0]]
            for occ in occurrences[1:]:
                if occ[0] >= filtered[-1][0] + length:
                    filtered.append(occ)

            if len(filtered) < 2:
                continue

            # Savings: we define the pattern once (costs `length` tokens),
            # then each occurrence costs 1 token instead of `length`.
            # Net saving = freq * length - (length + freq) = (freq - 1) * length - freq
            #            = freq * (length - 1) - length
            freq = len(filtered)
            saving = freq * (length - 1) - length
            # Must save at least something
            if saving > best_saving:
                best_saving = saving
                # Build the pattern definition from the first occurrence
                first_idx, first_pitch, first_dur = filtered[0]
                base_chunk = literals[first_idx:first_idx + length]
                body = [Literal(lit.pitch, lit.duration) for lit in base_chunk]

                # Calculate transpose and time_scale for each occurrence
                occ_params = []
                for (idx, pitch, dur) in filtered:
                    transpose = pitch - first_pitch
                    time_scale = dur / first_dur if first_dur > 0 else 1.0
                    occ_params.append((lit_positions[idx], transpose, time_scale))

                name = f"P{len(prog.definitions) + 1}"
                pat_def = PatternDef(name, body)
                best_result = (name, pat_def, occ_params)

    return best_result


def apply_abstraction(prog: MusicProgram, name: str, pat_def: PatternDef,
                      occurrences: List[Tuple[int, int, float]]) -> MusicProgram:
    """Apply an abstraction: replace literal sequences with pattern references."""
    new_prog = MusicProgram()
    new_prog.definitions = dict(prog.definitions)
    new_prog.definitions[name] = pat_def

    # Mark positions to replace
    replace_ranges = {}  # start_pos -> (transpose, time_scale)
    for (pos, transpose, time_scale) in occurrences:
        replace_ranges[pos] = (transpose, time_scale)

    i = 0
    while i < len(prog.instructions):
        if i in replace_ranges:
            transpose, time_scale = replace_ranges[i]
            new_prog.instructions.append(PatternRef(name, transpose, time_scale))
            i += pat_def.length
        else:
            new_prog.instructions.append(prog.instructions[i])
            i += 1

    return new_prog


def refactor_loop(notes: List[NoteEvent], max_iterations: int = 20, min_saving: int = 2, verbose: bool = True) -> MusicProgram:
    """The main refactoring loop.

    Repeatedly find the best abstraction and apply it until no more
    worthwhile abstractions exist.
    """
    prog = notes_to_program(notes)
    if verbose:
        print(f"Initial program size: {prog.program_size} tokens")

    for iteration in range(max_iterations):
        result = find_best_abstraction(prog)
        if result is None:
            if verbose:
                print(f"\nIteration {iteration + 1}: No more abstractions found.")
            break

        name, pat_def, occurrences = result
        saving = len(occurrences) * (pat_def.length - 1) - pat_def.length

        if saving < min_saving:
            if verbose:
                print(f"\nIteration {iteration + 1}: Best saving is only {saving}, stopping.")
            break

        prog = apply_abstraction(prog, name, pat_def, occurrences)

        if verbose:
            print(f"\nIteration {iteration + 1}: Extracted {name}")
            print(f"  Pattern: {pat_def}")
            print(f"  Occurrences: {len(occurrences)}x (saving {saving} tokens)")
            print(f"  Program size: {prog.program_size} tokens (ratio: {prog.compression_ratio:.2f})")

    if verbose:
        print(f"\n{'='*60}")
        print(prog)

    return prog
