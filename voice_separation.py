"""
Voice separation: split a polyphonic MIDI stream into distinct voices.

Strategy:
- Group simultaneous notes into chords
- Separate by register (bass vs treble)
- Within each register, connect notes by proximity (nearest pitch continuation)
"""

from typing import List, Dict, Tuple
from collections import defaultdict
from music_rep import NoteEvent


def separate_by_register(notes: List[NoteEvent], split_pitch: int = 60) -> Tuple[List[NoteEvent], List[NoteEvent]]:
    """Simple split: notes below split_pitch go to bass, above to treble."""
    bass = [n for n in notes if n.pitch < split_pitch]
    treble = [n for n in notes if n.pitch >= split_pitch]
    return treble, bass


def group_simultaneous(notes: List[NoteEvent], tolerance: int = 10) -> List[List[NoteEvent]]:
    """Group notes that start within `tolerance` ticks of each other."""
    if not notes:
        return []
    sorted_notes = sorted(notes, key=lambda n: n.start)
    groups = []
    current = [sorted_notes[0]]
    for n in sorted_notes[1:]:
        if n.start - current[0].start <= tolerance:
            current.append(n)
        else:
            groups.append(current)
            current = [n]
    groups.append(current)
    return groups


def extract_melody_line(notes: List[NoteEvent]) -> List[NoteEvent]:
    """Extract the top voice from a stream of notes.

    At each time position, take the highest note. Connect by nearest pitch
    when there's ambiguity.
    """
    groups = group_simultaneous(notes)
    melody = []
    for group in groups:
        # Take the highest pitch in each simultaneous group
        top = max(group, key=lambda n: n.pitch)
        melody.append(top)
    return melody


def extract_bass_line(notes: List[NoteEvent]) -> List[NoteEvent]:
    """Extract the bottom voice from a stream of notes."""
    groups = group_simultaneous(notes)
    bass = []
    for group in groups:
        bottom = min(group, key=lambda n: n.pitch)
        bass.append(bottom)
    return bass


def separate_voices_by_proximity(notes: List[NoteEvent], n_voices: int = 2) -> List[List[NoteEvent]]:
    """Separate into n voices by pitch proximity continuation.

    Uses a greedy algorithm: at each time step, assign each note to the
    voice whose previous note is closest in pitch.
    """
    groups = group_simultaneous(notes)
    voices = [[] for _ in range(n_voices)]
    last_pitch = [60 + i * 12 for i in range(n_voices)]  # initial spread

    for group in groups:
        # Sort notes by pitch (low to high)
        group_sorted = sorted(group, key=lambda n: n.pitch)

        # If fewer notes than voices, assign to closest voice
        if len(group_sorted) <= n_voices:
            assigned = set()
            for note in group_sorted:
                # Find closest unassigned voice
                best_voice = min(
                    [v for v in range(n_voices) if v not in assigned],
                    key=lambda v: abs(note.pitch - last_pitch[v])
                )
                voices[best_voice].append(note)
                last_pitch[best_voice] = note.pitch
                assigned.add(best_voice)
        else:
            # More notes than voices: assign lowest to voice 0, highest to voice n-1, etc.
            for i, note in enumerate(group_sorted[:n_voices]):
                voices[i].append(note)
                last_pitch[i] = note.pitch

    return voices
