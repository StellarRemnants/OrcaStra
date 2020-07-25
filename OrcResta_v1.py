# -*- coding: utf-8 -*-
"""
Created on Sat Jul 11 20:29:34 2020

@author: Mercury
"""

import sounddevice as sd
import matplotlib.pyplot as plt
import numpy as np
import numpy
import pdb

A_FREQ = 440
SMPR = 44100
NOTENAMES = {
    "A":0,
    "A#":1,
    "B":2,
    "C":-9,
    "C#":-8,
    "D":-7,
    "D#":-6,
    "E":-5,
    "F":-4,
    "F#":-3,
    "G":-2,
    "G#":-1,
    }

ProperNoteOrder = [    
    "C",
    "C#",
    "D",
    "D#",
    "E",
    "F",
    "F#",
    "G",
    "G#",
    "A",
    "A#",
    "B",
    ]

def Note_Frequency(Name, Octave, Verbose=0):
    if Name.upper() in NOTENAMES:
        NoteRank = NOTENAMES[Name]
        ModifiedOctave = Octave-4
        ScaleFactor = 2.**((ModifiedOctave+(NoteRank/12)))
        Frequency = ScaleFactor * A_FREQ
        return Frequency
    else:
        raise ValueError("Note name not recognized.")
        
class Note:
    def __init__(self, NoteName=None, NoteOctave=None, Frequency=None, Verbose=0):
        if Frequency is not None:
            if Verbose:
                print("Frequency is not None, assigning frequency directly")
            self.name = None
            self.octave = None
            self.Freq = Frequency
        elif NoteName is not None and NoteOctave is not None:
            self.name = NoteName
            self.octave = NoteOctave
            self.Freq = None
        else:
            raise ValueError("Note Name and Octave must be specified if Frequency is not.")
        
        if Verbose:
            print("name:", self.name, "  ocatave:", self.octave, "  Freq:", self.Freq)
        
    def Frequency(self, Verbose=0):
        if Verbose:
            print("self.Freq: ", self.Freq)
        if self.Freq is None:
            return Note_Frequency(self.name, self.octave)
        else:
            return self.Freq
    
    
class Tone:
    def __init__(self, **kwargs):
        
        NoteListSupplied = False
        FrequenciesSupplied = False
        AmplitudesSupplied = False
        
        if "NoteNames" in kwargs:
            NoteNames = kwargs["NoteNames"]
        else:
            NoteNames = []
        if "NoteOctaves" in kwargs:
            NoteOctaves = kwargs["NoteOctaves"]
        else:
            NoteOctaves = []
        if "NoteList" in kwargs:
            NoteList = kwargs["NoteList"]
            NoteListSupplied = True
        if "Amplitudes" in kwargs:
            Amplitudes = kwargs["Amplitudes"]
            AmplitudesSupplied = True
        if "Frequencies" in kwargs:
            Frequencies = kwargs["Frequencies"]
            FrequenciesSupplied = True
        if "Verbose" in kwargs:
            Verbose=kwargs["Verbose"]
        else:
            Verbose=0
            
        if Verbose:
            print(kwargs)
            
        if NoteListSupplied:
            if Verbose:
                print("NoteList Provided")
            self.NoteList = NoteList
        elif FrequenciesSupplied:
            if Verbose:
                print("Frequencies Supplied")
            NoteList = []
            for frequency in Frequencies:
                if Verbose:
                    print("Generating Note with frequency", frequency)
                NoteList.append(Note(Frequency=frequency))
            self.NoteList=NoteList
        else:
            if Verbose:
                print("NoteList not Provided, generating Notes")
            if len(NoteNames) != len(NoteOctaves):
                raise ValueError("NoteNames length does not equal NoteOctaves length")
            else:
                NoteList = []
                for counter in range(len(NoteNames)):
                    notename = NoteNames[counter]
                    octave = NoteOctaves[counter]
                    if Verbose:
                        print("Generating Note", notename, octave)
                    note = Note(notename, octave)
                    if Verbose:
                        print("name:", note.name, "  ocatave:", note.octave, "  Freq:", note.Freq)
                    NoteList.append(note)
                self.NoteList = NoteList
                
        if AmplitudesSupplied:
            self.Amplitudes = Amplitudes
        else:
            self.Amplitudes = np.ones_like(self.NoteList)
        
    def GenSines(self, SineLength_s = .5, compose = True, Verbose=0):
        samplecount = (int)(SMPR*SineLength_s)
        t = np.linspace(0,SineLength_s,samplecount)
        SineList = []
        counter = 0
        for note in self.NoteList:
            if Verbose:
                print("name:", note.name, "  ocatave:", note.octave, "  Freq:", note.Freq)
            nF = note.Frequency()
            note_sine = np.sin(t*nF*2*np.pi)*self.Amplitudes[counter]
            SineList.append(note_sine)
            counter += 1
            
        if compose:
            ReturnSine = np.zeros(samplecount)
            for note_sine in SineList:
                ReturnSine += note_sine
            return ReturnSine
        else:
            return SineList
        
#%% 
Notes = ["C", "E", "G", "C", "E", "G"]
Octaves = [4,4,4,5,5,5]
Amplitudes = [.2,.2,.2,.2,.2,.2]

C_Chord = Tone(NoteNames=Notes, NoteOctaves=Octaves, Amplitudes=Amplitudes, Verbose=0)

ret_sines = C_Chord.GenSines(SineLength_s=1, Verbose=0)
        

sd.play(ret_sines, samplerate=SMPR)

#%% 

Frequencies = [440, 220, 880]
Amplitudes = [.5, .25, .25]

Chord = Tone(Frequencies=Frequencies, Amplitudes=Amplitudes, Verbose=1)

ret_sines = Chord.GenSines(SineLength_s=1, Verbose=1)
        

sd.play(ret_sines, samplerate=SMPR)
        
#%% check that notes are generated correctly
TripletList = []
FrequencyList = []
NameList = []
for order in range(1,8):
    for notename in ProperNoteOrder:
        freq = Note_Frequency(notename, order)
        triplet = (notename, order, freq)
        TripletList.append(triplet)
        NameList.append(notename+str(order))
        FrequencyList.append(freq)
        
print(TripletList)

fig,ax = plt.subplots()
ax.scatter(NameList, FrequencyList)


