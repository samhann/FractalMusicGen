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
        self.MIDIObject.addTempo(self.track,0,1400)
        self.volume = 100
        self.channel = 0
        self.notes = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
        self.basePitchOfC = 50

    def addNote(self,note,time,duration,octave,volume):
        if note != "S":
            self.MIDIObject.addNote(self.track,self.channel,self.notePitch(note,octave),time,duration,volume)        
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
            volume = noteInfo[3]
            if(note != ''):
                self.addNote(note,trackTime,duration,octave,volume)
            trackTime = trackTime + duration

    def writeMidiToFile(self):
        binfile = open(self.outputFileName, 'wb')
        self.MIDIObject.writeFile(binfile)
        binfile.close()


class Composer(object):

    
    def compose(self,scaleNotes,duration):
        scaleLen = len(scaleNotes)
        counter = 0
        melody = []
        octave = 1

        counter = 0

        # parameters to the random note offset generator
        multiplier =  randint(2,55000)
        noteCounter = randint(20,55000)
        base =  randint(1,51000)
        

        cycle_length = 2**randint(0,3)
        octaveOffset = 0
        octaveMod = 0
        tension = 0
        tension_cycle = randint(1,3)
        tension_direction = 1
        tension_count = 0
        meta_tension_cycle = randint(2,5)
        meta_tension = 0
        meta_tension_direction = 1
        beat_length = 4
        beat_accumulated = 0
        total_meta_cycles = 0
        meta_cycle_max = 10
        cycle_counter = 0
        duration_sequence = generateDurationSequence(cycle_length,beat_length,tension,tension_direction)

        while counter < duration:

            # suppress the note offset lower proportional to tension
            noteMod = 3
            if tension >= 2:
                noteMod = 3

            if tension >= 3:
                noteMod = 2

            if tension >= 5:
                noteMod = 2

            if tension >= 7:
                noteMod = 1

            if tension >=9:
                noteMod = 1

            noteOffset = generateNoteDelta(noteCounter+counter,multiplier,base) / (noteMod)
            # extend durations by even multiples every now and then
            noteDuration = duration_sequence[(noteCounter + counter) % len(duration_sequence)]
            num_cycles = 0
            
            
            #switch things up every now and then ie cycles
            if counter % cycle_length == 0 and counter != 0:
                # this makes a repetition
                if randint(0,10) % 4 == 0:
                    noteCounter = noteCounter - cycle_length - 1
                    counter = counter + 1
                    continue

                octaveOffset = 0 

                # this actually makes the output more varied . Need to see why its required
                if randint(1,10) % 2 == 0 :
                    octaveMod =  (octaveMod + 1) % 3

                # dont get too varied when tension has fallen
                if tension_direction == -1 and tension <= 5:
                    octaveMod = max(0,octaveMod-2)

                tension_count = tension_count + 1
                tension_ended = False

                # When cycle of rising and falling tension is complete
                if tension_count % tension_cycle == 0:

                    #Reset note generator when lowering tension from peak
                    if tension_direction == -1 :
                        # reset the random variables only after a "phrase"
                        tension_ended = True
                        multiplier =  randint(2,1000)
                        noteCounter = randint(1,5000)
                        base =  randint(1,1000)

                        melody.append(("S",finalOctaveOffset,8, 25 + 20*int(tension/9) + randint(4,8)))

                    # Restart tension cycle
                    tension_count = 0
                    tension_direction = tension_direction * -1
                    # This adds long range structure . Starts and ends slow. Can increase randomn upper range if
                    # output is too dull.
                    tension_cycle = meta_tension + randint(1,3)
                    meta_tension = meta_tension + randint(1,2)

                    # same thing as tension but meta
                    if meta_tension_cycle % meta_tension == 0:
                        meta_tension = 0
                        meta_tension_direction = meta_tension_direction * -1
                        meta_tension_cycle = randint(2,5)
                        total_meta_cycles = total_meta_cycles + 1

                    if total_meta_cycles == meta_cycle_max:
                        return melody


                meta_term = meta_tension if meta_tension_direction == 1 else -1*meta_tension

                # this is a hack to force tension back down. Need to see if it can be avoided
                fraction = tension_count / tension_cycle

                tension = (meta_term + (tension + tension_direction*randint(1,2) )) % randint(6,8)
               
                if fraction >= 0.75 and tension_direction == -1:
                    tension = randint(1,3) 
                elif (tension_count + 1) % tension_cycle == 0:
                    tension = randint(1,2)

                # generate note lengths based on cycle length , beat length and tension . beat length not used
                # need to fix to accomodate both odd and even rhythms
                duration_sequence = generateDurationSequence(cycle_length,beat_length,tension,tension_direction)
                
                # Every now and then make the phrases longer or shorter based on the tension
                if num_cycles % randint(2,4) == 0:
                   cycle_length = 2 + 2**randint(0,1) 
                   if tension >= 4:
                        cycle_length = 2**randint(2,4)
                   if tension >= 6:
                        cycle_length = 2**randint(1,3) 
                   if tension >= 7:
                        cycle_length = 2**randint(1,2) 

                   octaveOffset = randint(0,2)
                   tension = 0
                   duration_sequence = generateDurationSequence(cycle_length,beat_length,tension,tension_direction)

                counter = counter + 1
                continue

            finalOctaveOffset = 0 if octaveMod == 0 else (octave + octaveOffset) % octaveMod
            finalOctaveOffset = finalOctaveOffset + 2
            melody.append((scaleNotes[noteOffset % scaleLen],finalOctaveOffset,noteDuration, 30 + 20*int(tension/9) + randint(4,8) + meta_tension))
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

def generateDurationSequence(cycle_length,beat_length,tension,tension_direction):
    base_duration = 2
    # longer notes for lower tension and vice versa
    ascending_rhythm_powers =  [randint(4,5),randint(4,4),randint(3,5),randint(3,4),randint(3,4),randint(2,3),randint(2,3),randint(1,2),randint(1,2)]
    max_power = ascending_rhythm_powers[tension] 
    uniform_beats = [2*randint(1,max_power) for x in range(0,cycle_length)]
    target = 8

    if tension >= 0 and tension <= 2:
        target = 8*randint(1,3)
    else:
        target = 8*randint(1,2)

    counter = 0

    # this is what keeps it on beat. keep generating random note lengths until you get something that
    # lines up with the beat
    while True:
        uniform_beats = [2*randint(1,max_power) for x in range(0,cycle_length)]
        if counter % 5000 == 0:
            target = target/2
        sum_beats = sum(uniform_beats)
        if  sum_beats % target == 0:
            break
    return uniform_beats

majorScaleNotes = ['C','D','E','F','G','A']
pentatonic = ['C','D','E','G','A']
bluesScaleNotes = ['C','D#','F','F#','A#']
arabScaleNotes = ['C','C#','E','F','G','G#']
spanish = ['C', 'C#',  'E'  ,'F'  ,'G' , 'G#' ,'A#']

def composeAndWriteToFile(scale,duration,fileName):
    mozart = Composer()
    testMelody = mozart.compose(scale,duration)
    MIDIGen = MIDIGenerator(fileName)
    MIDIGen.addMelody(testMelody)
    MIDIGen.writeMidiToFile()
    
composeAndWriteToFile(pentatonic,500,"output.mid")
