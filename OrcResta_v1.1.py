# -*- coding: utf-8 -*-

import OrcaStra_Lib_v1 as Orc
import sounddevice as sd
import numpy as np
import matplotlib.pyplot as plt
from scipy.io.wavfile import read as wav_read
from scipy import fft
import scipy.signal as sig

import matplotlib.widgets as widgets
from matplotlib.widgets import Slider, Button, RadioButtons

# %%

def plucked_string_harmonics(h,L,a,c, m_res=10):
    
    Frequencies = np.zeros(m_res)
    Amplitudes = np.zeros(m_res)
    fpf = c/(2*L)
    apf = 2* L**2 * h / (np.pi**2 * a * (L-a) )
    for i in range(m_res):
        m = i + 1
        amp = m**-2 * np.sin(np.pi * m * a / L)**2 * apf
        freq = m*fpf
        Amplitudes[i] = amp
        Frequencies[i] = freq
    
    return Frequencies, Amplitudes

def ADSR_filter(A,D,S,R,n):
    A_len = (int)(A*n)
    D_len = (int)(D*n)
    R_len = (int)(R*n)
    S_len = n-A_len-D_len-R_len
    
    A_pos = A_len
    D_pos = A_pos+D_len
    S_pos = D_pos+S_len
    R_pos = n
    
    ret = np.ones(n)
    ret[0:A_pos] = np.linspace(0,1,A_len)
    ret[A_pos:D_pos] = np.linspace(1,S,D_len)
    ret[D_pos:S_pos] = np.ones(S_len)*S
    ret[S_pos:R_pos] = np.linspace(S,0,R_len)
    
    return ret

#%%    

h=1;L=1;a=0.15;c=500;m_res=30;
timelen = 1
N = (int)(Orc.SMPR*timelen)
sound_filter = ADSR_filter(0.05,0.05,0.85,0.75,N)


Frequencies,Amplitudes= plucked_string_harmonics(h,L,a,c,m_res)

T = Orc.Tone(Amplitudes=Amplitudes, Frequencies=Frequencies)
sound = T.GenSines(SineLength_s=timelen)
sd.play(sound)
filtered_sound = sound * sound_filter
sd.play(filtered_sound)
sd.wait()

fig,ax=plt.subplots()
ax.plot(sound_filter)
fig,ax=plt.subplots()
ax.plot(filtered_sound)
fig,ax=plt.subplots()
ax.scatter(Frequencies,Amplitudes)
    
#%%
    
file_loc = "/home/stellarremnants/Desktop/Bag_Of_Holding/Universal_Shared/Personal_Projects/OrcResta/OrcaStra/"
file_name="GuitarTest_Stereo.wav"
wav_smpr,wav_file = wav_read(file_loc+file_name)
    
# %%

mono_wav = wav_file[:,0]
real_fft = abs(fft.rfft(mono_wav))
real_freqs = fft.rfftfreq(len(mono_wav), 1./wav_smpr)
Peak_indices = sig.find_peaks(real_fft, height=np.max(real_fft)*0.01)[0]

fig,ax=plt.subplots()
ax.plot(real_freqs, real_fft)

PeakAmplitudes = []
PeakFrequencies = []
for i in Peak_indices:
    PeakAmplitudes.append(real_fft[i])
    PeakFrequencies.append(real_freqs[i])

ax.scatter(PeakFrequencies, PeakAmplitudes)

ampmax = np.max(real_fft)
for i in range(len(PeakAmplitudes)):
    print("{:04.4f} | {:5.0f} |".format(PeakAmplitudes[i]/ampmax, PeakFrequencies[i]), end="")
    if PeakFrequencies[i] > 700:
        print("{:0.5f}".format(PeakFrequencies[i]/702.5108133769385))
    else:
        print("{:0.5f}".format(702.5108133769385/PeakFrequencies[i]))
        
#%%
        
t=np.arange(0,len(mono_wav))


#%%

