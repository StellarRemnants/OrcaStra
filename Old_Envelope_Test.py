# -*- coding: utf-8 -*-



# =============================================================================
# =============================================================================
# =============================================================================
# # #                        Ye Olde Envelope Test                        # # #
# =============================================================================
# =============================================================================
# =============================================================================




import numpy as np
import matplotlib.pyplot as plt
import OrcaStra_Lib_v1 as osl
from matplotlib.widgets import Slider, Button, RadioButtons
from scipy.signal import savgol_filter as sgf
import sounddevice as sd

#%% Envelope Class
DEFAULT_MIN_X = 0
DEFAULT_MAX_X = 1
DEFAULT_MIN_Y = -1
DEFAULT_MAX_Y = 1
DEFAULT_SELECTORS_NUM = 21
DEFAULT_INTERP_COUNT = 1000
DEFAULT_SELECTORS_X = np.linspace(DEFAULT_MIN_X, DEFAULT_MAX_X, DEFAULT_SELECTORS_NUM)
DEFAULT_SELECTORS_Y = np.ones_like(DEFAULT_SELECTORS_X)*.5
DEFAULT_SELECTORS = np.asarray([DEFAULT_SELECTORS_X, DEFAULT_SELECTORS_Y])

class Envelope:
    
    def __repr__(self):
        return str(self.selectors_y())
    
    def __str__(self):
        return self.__repr__()
    
    def __init__(self, selectors=DEFAULT_SELECTORS):
        self.selectors = selectors
        xcount=len(self.selectors[0,:])
        ycount=len(self.selectors[1,:])
        if xcount != ycount:
            raise ValueError("Unequal number of selector points (x={:g}, y={:g})".format(xcount,ycount))
        
    def update_selectors(self, new_selectors):
        xcount=len(new_selectors[0,:])
        ycount=len(new_selectors[1,:])
        if xcount != ycount:
            raise ValueError("Cannot set new selectors: Unequal number of selector points (x={:g}, y={:g})".format(xcount,ycount))
        else:
            self.selectors = new_selectors
        
    def selectors_x(self):
        return self.selectors[0,:]
    
    def selectors_y(self):
        return self.selectors[1,:]
    
    def selector_count(self):
        return len(self.selectors[0,:])
    
    def gen_linear_interp(self, numpoints=None):
        if numpoints is None:
            numpoints = DEFAULT_INTERP_COUNT
        linear_interp = np.ones(numpoints)
        segment_count = self.selector_count()-1
        interp_ratio = (int)(numpoints/segment_count)
        selectors_y =self.selectors_y()
        for i in range(segment_count-1):
            min_index = i * interp_ratio
            max_index = (i+1) * interp_ratio
            linear_interp[min_index:max_index] = np.linspace(selectors_y[i], selectors_y[i+1], interp_ratio)
        last_index = (segment_count-1) * interp_ratio
        last_segment_count = numpoints-last_index
        final_segment = np.linspace(selectors_y[segment_count-1], selectors_y[-1], last_segment_count)
        linear_interp[last_index:numpoints] = final_segment
        return [np.linspace(self.selectors_x()[0], self.selectors_x()[-1], numpoints),linear_interp]
    
    def gen_savgol_interp(self, numpoints=None, window_ratio=None, poly=None):
        if window_ratio is None:
            window_ratio = 3
        if poly is None:
            poly = 2
            
        linear_interp = self.gen_linear_interp(numpoints)[1]
        segment_count = self.selector_count()-1
        interp_ratio = (int)(len(linear_interp)/segment_count)
        test_window = interp_ratio * window_ratio
        if test_window % 2 == 0:
            window = test_window+1
        else:
            window = test_window
        
        return sgf(linear_interp, window, poly)
    
    def generate_envelope(self, numpoints=None, method="savgol", **kwargs):
        if method.lower() == "savgol":
            window_ratio=None
            poly=None
            if "window_ratio" in kwargs:
                window_ratio = kwargs["window_ratio"]
            if "poly" in kwargs:
                poly = kwargs["poly"]
                
            envelope = self.gen_savgol_interp(numpoints=numpoints, window_ratio=window_ratio, poly=poly)
            return envelope
        elif method.lower() == "linear":
            envelope = self.gen_linear_interp(numpoints)
            return envelope
        else:
            raise ValueError("Unrecognized method selected")
        
    def apply_envelope(self, sine_array, normalize_envelope=False, **kwargs):
        numpoints = len(sine_array)
        generated_envelope = self.generate_envelope(numpoints, **kwargs)
        if normalize_envelope:
            emax = max(generated_envelope)
            emin = min(generated_envelope)
            if abs(emax) > abs(emin):
                scale_factor = abs(emax)
            else:
                scale_factor = abs(emin)
        else:
            scale_factor = 1
        return sine_array*generated_envelope/scale_factor

# %% Old Envelope test
plt.close()
Tenv = Envelope()
fig,ax=plt.subplots()
x = Tenv.selectors_x()
y = Tenv.selectors_y()

T = osl.Tone(NoteNames=["C"], NoteOctaves=[4], Amplitudes=[1])
test_sine = T.GenSines()

numpoints = len(test_sine)

selectors = Tenv.selectors
selectors[1,10] = 0
selectors[1,11] = -1
selectors[1,12:len(selectors[1,:])] = [0]
Tenv.update_selectors(selectors)

fill_x = np.linspace(DEFAULT_MIN_X, DEFAULT_MAX_X, numpoints)
lin_interp = Tenv.gen_linear_interp(numpoints)
savgol_interp = Tenv.gen_savgol_interp(numpoints)

modulated_sine = Tenv.apply_envelope(test_sine)

selector_points, = ax.plot(x,y, 'ro', ls='-')
lin_interp_line, = ax.plot(fill_x, lin_interp[1], 'g-')
savgol_interp_line, = ax.plot(fill_x, savgol_interp, 'b-')
test_sine_line, = ax.plot(fill_x,test_sine, c='cyan')
modulated_sine_line, = ax.plot(fill_x,modulated_sine, 'k-')

test_sine_line.zorder=0
modulated_sine_line.zorder=1
lin_interp_line.zorder=2
savgol_interp_line.zorder=3
selector_points.zorder=4

fig.canvas.draw_idle()

# %%

sd.play(modulated_sine)