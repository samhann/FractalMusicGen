"""
Music representation and MIDI parsing.

We represent music as a flat sequence of NoteEvents, then convert to
a "program" — a list of integer tokens — that our pattern finder operates on.

Pitch is stored as a MIDI pitch number (0-127).
Duration and start times are in ticks (from the MIDI file).
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import mido


@dataclass
class NoteEvent:
    pitch: int          # MIDI pitch 0-127
    start: int          # absolute tick
    duration: int       # length in ticks
    velocity: int = 80

    @property
    def pitch_class(self) -> int:
        return self.pitch % 12

    @property
    def octave(self) -> int:
        return self.pitch // 12

    def transposed(self, semitones: int) -> "NoteEvent":
        return NoteEvent(self.pitch + semitones, self.start, self.duration, self.velocity)


def parse_midi(path: str) -> Tuple[List[NoteEvent], int]:
    """Parse a MIDI file into a list of NoteEvents sorted by start time.

    Returns (notes, ticks_per_beat).
    """
    mid = mido.MidiFile(path)
    notes = []
    for track in mid.tracks:
        abs_time = 0
        active = {}  # pitch -> (start_tick, velocity)
        for msg in track:
            abs_time += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                active[msg.note] = (abs_time, msg.velocity)
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                if msg.note in active:
                    start, vel = active.pop(msg.note)
                    dur = abs_time - start
                    if dur > 0:
                        notes.append(NoteEvent(msg.note, start, dur, vel))
    notes.sort(key=lambda n: (n.start, n.pitch))
    return notes, mid.ticks_per_beat


def notes_to_midi(notes: List[NoteEvent], path: str, ticks_per_beat: int = 480):
    """Write a list of NoteEvents to a MIDI file."""
    mid = mido.MidiFile(ticks_per_beat=ticks_per_beat)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(120), time=0))

    # Build a list of on/off events sorted by time
    events = []
    for n in notes:
        events.append((n.start, 'on', n.pitch, n.velocity))
        events.append((n.start + n.duration, 'off', n.pitch, 0))
    events.sort(key=lambda e: (e[0], 0 if e[1] == 'off' else 1))

    prev_time = 0
    for abs_time, kind, pitch, vel in events:
        delta = abs_time - prev_time
        if kind == 'on':
            track.append(mido.Message('note_on', note=pitch, velocity=vel, time=delta))
        else:
            track.append(mido.Message('note_off', note=pitch, velocity=0, time=delta))
        prev_time = abs_time

    mid.save(path)


def quantize_notes(notes: List[NoteEvent], grid: int) -> List[NoteEvent]:
    """Snap note starts and durations to the nearest grid unit."""
    result = []
    for n in notes:
        qstart = round(n.start / grid) * grid
        qdur = max(grid, round(n.duration / grid) * grid)
        result.append(NoteEvent(n.pitch, qstart, qdur, n.velocity))
    return result


# --- Interval-based representation for pattern matching ---

def notes_to_intervals(notes: List[NoteEvent]) -> List[int]:
    """Convert a monophonic note sequence to a list of pitch intervals.

    This is transposition-invariant: the same melody in different keys
    produces the same interval sequence.
    """
    if len(notes) < 2:
        return []
    return [notes[i+1].pitch - notes[i].pitch for i in range(len(notes) - 1)]


def notes_to_pitch_sequence(notes: List[NoteEvent]) -> List[int]:
    """Extract just the pitches as a list of ints."""
    return [n.pitch for n in notes]


def notes_to_duration_sequence(notes: List[NoteEvent]) -> List[int]:
    """Extract just the durations as a list of ints."""
    return [n.duration for n in notes]


def make_monophonic(notes: List[NoteEvent]) -> List[NoteEvent]:
    """Keep only the highest note at each start time (simple melody extraction)."""
    from collections import defaultdict
    by_start = defaultdict(list)
    for n in notes:
        by_start[n.start].append(n)
    result = []
    for start in sorted(by_start.keys()):
        # pick the highest pitch
        best = max(by_start[start], key=lambda n: n.pitch)
        result.append(best)
    return result
