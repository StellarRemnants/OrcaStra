#%%
# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
import OrcaStra_Lib_v1 as osl
from matplotlib.widgets import Slider, Button, RadioButtons
from scipy.signal import savgol_filter as sgf
import sounddevice as sd

#%% Plucked String

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

UseFrequencySource="Generated"

if UseFrequencySource=="Generated":
    h=1;L=2;a=0.15;c=500;m_res=30;
    Frequencies,Amplitudes= plucked_string_harmonics(h,L,a,c,m_res)
    Amplitudes = Amplitudes/max(Amplitudes)
elif UseFrequencySource=="Measured":
    Frequencies = np.array([97.70017934381264, 116.30973731406267, 139.5716847768752, 
                   190.74796919506278, 274.4909800611879, 321.01487498681297, 
                   344.2768224496255, 367.538769912438, 376.84354889756304, 
                   386.1483278826881, 414.0626648380631, 665.2916974364384, 
                   679.248865914126, 702.5108133769385, 749.0347083025636, 
                   762.9918767802511, 1042.1352463340015, 1400.3692372613145, 
                   2786.7813060449416, 2805.3908640151917, 3507.90167739213])
    Amplitudes = np.asarray([72616.32294513933, 84806.33095753826, 337337.74213971646, 
                             115370.22289674733, 106814.66159226831, 135912.5196733485, 
                             1464648.4601937288, 102896.54636000018, 109271.22661635268, 
                             88677.4938148505, 132047.4874624775, 334350.6474405449, 
                             933061.5677795935, 6341957.273185627, 74781.0801724961, 
                             77660.49117514586, 107532.16320146494, 1488850.519197199, 
                             122302.09787766324, 570100.450480315, 311018.5086864224])
    PeakFIndex = np.argmax(Amplitudes)
    PeakF = Frequencies[PeakFIndex]
    Frequencies = Frequencies/PeakF*440
    Amplitudes = Amplitudes/max(Amplitudes)

smpr = 44100
length_s = 1
length_n = (int)(smpr*length_s)
#generated_tone = osl.Tone(
#        NoteNames=["C", "E", "G"],
#        NoteOctaves=[4,4,4],
#        Amplitudes=[1,.5,.5]
#        )
generated_tone = osl.Tone(Frequencies=Frequencies, Amplitudes=Amplitudes)
generated_sine = generated_tone.GenSines(SineLength_s=length_s, sample_rate=smpr)
generated_sine = generated_sine/max(generated_sine)

#%%



min_x=0
max_x=1
x_num=21
min_y=0
max_y=2
slider_width = 0.025

x_spacing = (max_x-min_x)/(x_num-1)
x_values = np.linspace(min_x,max_x, x_num)
y_values = np.ones_like(x_values)*1

fill_num=length_n
fill_x  = np.linspace(min_x,max_x,fill_num)
fill_ratio = (int)((fill_num-1)/(x_num-1))
fill_x_spacing = x_spacing/fill_ratio

def calculate_fill_y(y_values):
    updated_fill_y = np.ones(fill_num)
    segment_count = len(y_values)-1
    for i in range(segment_count):
        min_index = i*fill_ratio
        max_index = (i+1)*fill_ratio
        updated_fill_y[min_index:max_index] = np.linspace(y_values[i], y_values[i+1], fill_ratio)
    updated_fill_y[segment_count*fill_ratio:-1]=y_values[-1]*np.ones_like(updated_fill_y[segment_count*fill_ratio:-1])
    return updated_fill_y

def calculate_savgol(fill_y):
    test_win = fill_ratio*3
    if test_win%2==0:
        window=test_win+1
    else:
        window=test_win
    return sgf(fill_y, window, 2)

def generate_envelope(savgol_line, zero_min=False, one_max=False):
    savgol_y = savgol_line.get_data()[1]
    minimum_y = np.min(savgol_y)
    maximum_y = np.max(savgol_y)
    span = maximum_y-minimum_y
    
    envelope = savgol_y
    if zero_min:
        envelope = envelope-minimum_y
    else:
        envelope = envelope-1
    if one_max:
        envelope = envelope/span
        
    return envelope

def generate_modulated_sine(savgol_line, generated_sine):
    return generated_sine*generate_envelope(savgol_line)

fill_y = calculate_fill_y(y_values)
savgol_y = calculate_savgol(fill_y)

#%% Initialize plot
plt.close()
fig=plt.Figure()
main_ax=plt.axes([0,0,1,1], label="main_ax", facecolor='white')
main_ax.margins(x=0)
plt.subplots_adjust(left=0.15, bottom=0.15)     #adjust spacing

main_ax.tick_params(
    axis='x',          # changes apply to the x-axis
    which='both',      # both major and minor ticks are affected
    bottom=False,      # ticks along the bottom edge are off
    top=False,         # ticks along the top edge are off
    left=False,
    right=False,
    labelbottom=False) # labels along the bottom edge are off

main_ax.tick_params(
    axis='y',          # changes apply to the x-axis
    which='both',      # both major and minor ticks are affected
    left=False,
    right=False,
    labelleft=False) # labels along the bottom edge are off


Dot_line, = main_ax.plot(x_values,y_values,'ro')
fill_line, = main_ax.plot(fill_x,fill_y, 'b-')
savgol_line, = main_ax.plot(fill_x, savgol_y, 'g-')
generated_sine_line, = main_ax.plot(fill_x,np.ones_like(fill_x))
generated_sine_line.zorder=0
main_ax.set_xlim([min_x,max_x])
main_ax.set_ylim([min_y,max_y])
main_ax.grid()


slider_axes = []
sliders = []


def update(val):
    updated_y_values = []
    for i in range(x_num):
        updated_y_values.append(sliders[i].val)
    Dot_line.set_ydata(updated_y_values)
    updated_y_fill = calculate_fill_y(updated_y_values)
    fill_line.set_ydata(updated_y_fill)
    savgol_line.set_ydata(calculate_savgol(updated_y_fill))
    generated_sine_line.set_ydata(generate_modulated_sine(savgol_line, generated_sine)+1)
    fig.canvas.draw_idle()

for i in range(x_num):
    test_slider_ax = plt.axes([i*x_spacing-slider_width/2,0.0,slider_width,1], 
                              label="test_slider",facecolor='white',)
    test_slider_ax.set_frame_on(False)
    test_slider = Slider(test_slider_ax, "", min_y,max_y, valinit=1, orientation='vertical',
                              visible=False, alpha=0.5)
    test_slider.on_changed(update)
    slider_axes.append(test_slider_ax)
    sliders.append(test_slider)

#def update_tone()

# %%
envelope=generate_envelope(savgol_line);sd.play(envelope*generated_sine, samplerate=smpr)


#%%





# %%

fig,ax=plt.subplots()
x=np.linspace(0,1,100)
y=np.ones_like(x)*.5
line,=ax.plot(x,y)
oldline,=ax.plot(x,y,'r--')

ax.set_xlim([0,1])
ax.set_ylim([0,1])

new_x=np.linspace(0,1,200)
new_y=np.ones_like(new_x)*.25
line.set_data(new_x,new_y)
fig.canvas.draw_idle()






