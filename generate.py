# By Samhan Salahuddin
# 25th November 2016

from midiutil.MidiFile import MIDIFile
from random import randint
from random import randrange


class MIDIGenerator(object):

    def __init__(self,fileName):
        self.outputFileName = fileName
        self.MIDIObject = MIDIFile(1)
        self.track = 0
        self.MIDIObject.addTrackName(self.track,0,"Sample Track")
        self.MIDIObject.addTempo(self.track,0,350)
        #74 is flute
        self.MIDIObject.addProgramChange(self.track,0, 0, 74)
        self.volume = 100
        self.channel = 0
        self.notes = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
        self.basePitchOfC = 50

    def addNote(self,note,time,duration,octave):
        if note != "S":
            self.MIDIObject.addNote(self.track,self.channel,self.notePitch(note,octave),time,duration,self.volume)        
        else:
            self.MIDIObject.addNote(self.track,self.channel,50,time,duration,0)        


    def addChord(self,notes,time,duration):
        for noteInfo in notes:
            note = noteInfo[0]
            octave = noteInfo[1]
            self.MIDIObject.addNote(self.track,self.channel,self.notePitch(note,octave),time,duration,self.volume)

    def notePitch(self,note,octave):
        return self.notes.index(note) + self.basePitchOfC + (12 * octave)

    def addMelody(self,melody):
        trackTime = 0
        for noteInfo in melody:
            note = noteInfo[0]
            octave = noteInfo[1]
            duration = noteInfo[2]
            if(note != ''):
                self.addNote(note,trackTime,duration,octave)
            trackTime = trackTime + duration

    def writeMidiToFile(self):
        binfile = open(self.outputFileName, 'wb')
        self.MIDIObject.writeFile(binfile)
        binfile.close()


class Composer(object):

    
    def compose(self,scaleNotes,rhythmIntervals,duration):
        scaleLen = len(scaleNotes)
        counter = 0
        melody = []
        octave = 1

        counter = 0
        octaveOffset = 0

        multiplier =  randint(2,55000)
        noteCounter = randint(20,55000)
        base =  randint(1,51000)
        cycle_length = 2**randint(0,3)
        prevOffset = 0
        octaveOffset = 0
        octaveMod = 0
        tension = 0
        tension_cycle = randint(1,2)
        tension_direction = 1
        tension_count = 0

        while counter < duration:

            noteOffset = tension + generateNoteDelta(noteCounter+counter,multiplier,base)/2
            # extend durations by even multiples every now and then
            noteDuration = rhythmIntervals[counter % len(rhythmIntervals)] * (2**(noteOffset%2))
            # doesnt make sense to do this on every note but removing this makes the output worse. need to investigate
            cycle_length = 2**randint(2,6)
            num_cycles = 0

            #switch things up every now and then ie cycles

            if counter % cycle_length == 0 and counter != 0:

                if randint(0,10) % 3 == 0:
                    noteCounter = noteCounter - cycle_length - 1
                    counter = counter + 1

                    if len(melody) >= 1:
                        last = melody.pop()
                        melody.append((last[0],last[1],last[2]+noteDuration + randint(0,1)))    

                    melody.append(("S",octave + octaveOffset,noteDuration + noteDuration))
                
                    continue

                octaveOffset = 1 if octaveOffset == 0 else 0

                # this actually makes the output more varied 
                if randint(1,3) % 2 == 0:
                    octaveMod =  (octaveMod + 1) % 3

                tension_count = tension_count + 1
                tension_ended = False

                if tension_count % tension_cycle == 0:
                    if tension_direction == -1 :
                        # reset the random variables only after a "phrase"
                        tension_ended = True
                        multiplier =  randint(2,1000)
                        noteCounter = randint(1,5000)
                        base =  randint(1,1000)

                    tension_count = 0
                    tension_direction = tension_direction * -1
                    tension_cycle = randint(1,3)


                tension = (tension + tension_direction*randint(1,3) ) % 4

                
                if num_cycles % randint(2,4) == 0:
                   cycle_length = 2**randint(2,6) 
                   intervals = [1,1,1,1]
                   octaveOffset = randint(0,2)
                   tension = 0

                if len(melody) >= 1:
                    last = melody.pop()
                    melody.append((last[0],last[1],last[2]+noteDuration + 1))    

                if tension_ended:
                    melody.append(("S",octave + octaveOffset,noteDuration + 2 ) )
                counter = counter + 1
                continue

            finalOctaveOffset = 0 if octaveMod == 0 else (octave + octaveOffset) % octaveMod
            finalOctaveOffset = finalOctaveOffset + 2
            # some random silences
            if counter % 2**randint(2,4) == 0:
                if len(melody) >= 1:
                    last = melody.pop()
                    melody.append((last[0],last[1],last[2]+noteDuration + noteDuration))    
                
            else:
                melody.append((scaleNotes[noteOffset % scaleLen],finalOctaveOffset,noteDuration))
            counter = counter + 1

        return melody
            


def numberToBase(n, b):
    if n == 0:
        return [0]
    digits = []
    while n:
        digits.append(int(n % b))
        n /= b
    return digits[::-1]

def sumOfDigits(num):
    result = 0
    for digit in num:
        result = result + int(digit)

    return result

def generateNoteDelta(counter,base,multiplier):
    return sumOfDigits(numberToBase((counter * multiplier),base))

def composeAndWriteToFile(scale,intervals,duration,fileName):
    mozart = Composer()
    testMelody = mozart.compose(scale,intervals,duration)
    MIDIGen = MIDIGenerator(fileName)
    MIDIGen.addMelody(testMelody)
    MIDIGen.writeMidiToFile()


    
intervals = [1,1,1,1];
majorScaleNotes = ['C','D','E','F','G','A']
pentatonic = ['C','D','E','G','A']
bluesScaleNotes = ['C','D#','F','F#','A#']
arabScaleNotes = ['C','C#','E','F','G','G#']
spanish = ['C', 'C#',  'E'  ,'F'  ,'G' , 'G#' ,'A#']

composeAndWriteToFile(majorScaleNotes,intervals,500,"output.mid")
