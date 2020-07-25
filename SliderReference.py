# -*- coding: utf-8 -*-
#%%

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.widgets as widgets
from matplotlib.widgets import Slider, Button, RadioButtons

fig, ax = plt.subplots()                        #create plots
plt.subplots_adjust(left=0.25, bottom=0.25)     #adjust spacing

#sine init
t = np.arange(0.0, 1.0, 0.001)                  
a0 = 5
f0 = 3

#frequency spacing
delta_f = 5.0

#gen sine
s = a0 * np.sin(2 * np.pi * f0 * t)

#line for sine
l, = plt.plot(t, s, lw=2)

#tight margins
ax.margins(x=0)

#create axes with custom color and position for sliders
axcolor = 'lightgoldenrodyellow'
axfreq = plt.axes([0.25, 0.1, 0.65, 0.03], facecolor=axcolor)
axamp = plt.axes([0.25, 0.15, 0.65, 0.03], facecolor=axcolor)

#create sliders (for Slider to be responsive a reference must be retained to it)
sfreq = Slider(axfreq, 'Freq', 0.1, 30.0, valinit=f0, valstep=delta_f)
samp = Slider(axamp, 'Amp', 0.1, 10.0, valinit=a0)

#function to update slider
#takes as an argument a single float (the new value of the slider)
#Slider type has one attribute (.val)
def update(val):
    #get slider values
    amp = samp.val
    freq = sfreq.val
    
    #recalculate sine function
    l.set_ydata(amp*np.sin(2*np.pi*freq*t))
    
    #redraw canvas
    fig.canvas.draw_idle()

#Connect Sliders to slider event
sfreq.on_changed(update)
samp.on_changed(update)

#Create axis and Button for reset button
resetax = plt.axes([0.8, 0.025, 0.1, 0.04])
button = Button(resetax, 'Reset', color=axcolor, hovercolor='0.975')

#Function for reset
def reset(event):
    #Slider.reset() returns slider to initial values (will also trigger .on_changed())
    sfreq.reset()
    samp.reset()
button.on_clicked(reset)

#create axis and RadioButtons for color selection buttons
rax = plt.axes([0.025, 0.5, 0.15, 0.15], facecolor=axcolor)
radio = RadioButtons(rax, ('red', 'blue', 'green'), active=0)

#function for changing the line color that takes the label of the radio button selected as an argument
def colorfunc(label):
    l.set_color(label)
    fig.canvas.draw_idle()
radio.on_clicked(colorfunc)

#draw plot
plt.show()
