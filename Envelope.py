#%%
# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
import OrcaStra_Lib_v1 as osl
from matplotlib.widgets import Slider, Button, RadioButtons, TextBox, CheckButtons
from matplotlib import patches
from scipy.signal import savgol_filter as sgf
import sounddevice as sd
import copy
import math

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
    
    def gen_savgol_interp(self, numpoints=None, window_ratio=None, poly=None, **kwargs):
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
        
        return sgf(linear_interp, window, poly, **kwargs)
    
    def generate_envelope(self, numpoints=None, method="savgol", **kwargs):
        if method.lower() == "savgol":
            window_ratio=None
            poly=None
            mode=None
            cval=None
            if "window_ratio" in kwargs:
                window_ratio = kwargs["window_ratio"]
            if "poly" in kwargs:
                poly = kwargs["poly"]
            if "mode" in kwargs:
                mode = kwargs["mode"]
            if "cval" in kwargs:
                cval = kwargs["cval"]
                
            envelope = self.gen_savgol_interp(numpoints=numpoints, window_ratio=window_ratio, poly=poly,
                                              mode=mode, cval=cval)
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
        
    
DEFAULT_SLIDER_WIDTH = .02
    
    
    
    
class Envelope_Generator_GUI:
    """ EGG (Envelope Generator GUI)"""
    
    GUI_Num_Counter = 0
    
    def Initiate_Canvas(self):
        #Create main figure and axis
        self.EGG_figure_Name = 'EGG '+str(self.EGG_ID)
        self.EGG_figure = plt.figure(self.EGG_figure_Name ,clear=True, figsize = [13,8])
        self.main_ax = self.EGG_figure.add_axes([0,0,1,1], label="main_ax", 
                    facecolor='white')
        
        #Adjust main axis to be blank
        self.main_ax.margins(x=0)
#        plt.subplots_adjust(left=0.15, bottom=0.15)     #adjust spacing
        
        self.main_ax.tick_params(
            axis='x',          # changes apply to the x-axis
            which='both',      # both major and minor ticks are affected
            bottom=False,      # ticks along the bottom edge are off
            top=False,         # ticks along the top edge are off
            left=False,
            right=False,
            labelbottom=False) # labels along the bottom edge are off
        
        self.main_ax.tick_params(
            axis='y',          # changes apply to the x-axis
            which='both',      # both major and minor ticks are affected
            left=False,
            right=False,
            labelleft=False) # labels along the bottom edge are off
        
        #Create Lines to plot Dots, linear interp, savgol interp, and modulated sine
        raw_sine = self.Tone.GenSines(SineLength_s=self.Tone_Length)
        
        self.Dot_line, = self.main_ax.plot(self.Env.selectors_x(),self.Env.selectors_y(),'ro')
        
        lin_interp = self.Env.gen_linear_interp(numpoints=len(raw_sine))
        fill_x = lin_interp[0]
        fill_y = lin_interp[1]
        self.fill_line, = self.main_ax.plot(fill_x,fill_y, 'b-')
        
        savgol_y = self.Env.gen_savgol_interp(numpoints=len(raw_sine),
                                              window_ratio=self.savgol_window_ratio, poly=self.savgol_poly,
                                   mode=self.savgol_mode, cval=self.savgol_cval)
        self.savgol_line, = self.main_ax.plot(fill_x, savgol_y, 'g-')
        
        
        self.generated_sine_line, = self.main_ax.plot(fill_x,self.Env.apply_envelope(raw_sine, method=self.envelope_method,
                                   window_ratio=self.savgol_window_ratio, poly=self.savgol_poly,
                                   mode=self.savgol_mode, cval=self.savgol_cval))
        
        self.generated_sine_line.zorder=0
        
        self.main_ax.set_xlim([DEFAULT_MIN_X,DEFAULT_MAX_X])
        self.main_ax.set_ylim([DEFAULT_MIN_Y,DEFAULT_MAX_Y])
        self.main_ax.grid()
        
        self.slider_axes = []
        self.sliders = []
        
        slider_positions_x = self.Env.selectors_x()
        slider_positions_y = self.Env.selectors_y()
        x_num = len(slider_positions_x)
        for i in range(x_num):
            test_slider_ax = self.EGG_figure.add_axes(
                    [slider_positions_x[i]-DEFAULT_SLIDER_WIDTH/2, 0, DEFAULT_SLIDER_WIDTH, 1], 
                                      label="test_slider"+str(i),facecolor='white')
            test_slider_ax.set_frame_on(False)
            test_slider = Slider(test_slider_ax, "", DEFAULT_MIN_Y,DEFAULT_MAX_Y, 
                                 valinit=slider_positions_y[i], orientation='vertical',
                                      visible=False, alpha=0.5)
            test_slider.on_changed(self.Update_Canvas())
            self.slider_axes.append(test_slider_ax)
            self.sliders.append(test_slider)
        
    def Update_Canvas(self):
        def update(val):
            raw_sine = self.Tone.GenSines(SineLength_s=self.Tone_Length)
            updated_y_values = []
            for i in range(len(self.Env.selectors_x())):
                updated_y_values.append(self.sliders[i].val)
            self.Dot_line.set_ydata(updated_y_values)
            
            x_values = self.Env.selectors_x()
            self.Env.update_selectors(np.asarray([x_values, updated_y_values]))
            
            linear_interp = self.Env.gen_linear_interp(numpoints=len(raw_sine))
            updated_y_fill = linear_interp[1]
            x_fill = linear_interp[0]
            self.fill_line.set_ydata(updated_y_fill)
            self.fill_line.set_xdata(x_fill)
            
            updated_savgol = self.Env.gen_savgol_interp(numpoints=len(raw_sine), mode=self.savgol_mode,
                                                        cval=self.savgol_cval,
                                                        window_ratio=self.savgol_window_ratio, poly=self.savgol_poly)
            self.savgol_line.set_ydata(updated_savgol)
            self.savgol_line.set_xdata(x_fill)
            
            self.generated_sine_line.set_ydata(self.Env.apply_envelope(raw_sine, method=self.envelope_method,
                                   window_ratio=self.savgol_window_ratio, poly=self.savgol_poly,
                                   mode=self.savgol_mode, cval=self.savgol_cval))
            self.generated_sine_line.set_xdata(x_fill)
            
            if self.Plot_Wave:
                self.generated_sine_line.set_visible(True)
            else:
                self.generated_sine_line.set_visible(False)
                
            if self.Plot_Savgol:
                self.savgol_line.set_visible(True)
            else:
                self.savgol_line.set_visible(False)
                
            if self.Plot_Linear:
                self.fill_line.set_visible(True)
            else:
                self.fill_line.set_visible(False)
                
            if self.Plot_Selectors:
                self.Dot_line.set_visible(True)
            else:
                self.Dot_line.set_visible(False)
            
            
            self.EGG_figure.canvas.draw_idle()
        
        return update
    
    def __init__(self, figsize=None, facecolor='w', InitEnvelope=Envelope(), InitTone=osl.Tone(),
                 Init_Tone_Length=1, savgol_mode='wrap', savgol_cval=0, savgol_window_ratio=3,
                 savgol_poly=2, envelope_method='savgol'):
        
        self.EGG_ID = Envelope_Generator_GUI.GUI_Num_Counter
        Envelope_Generator_GUI.GUI_Num_Counter += 1
        
        
        self.Env = InitEnvelope
            
        self.Tone = InitTone
        self.savgol_mode = 'wrap'
            
        self.savgol_cval = savgol_cval

        self.savgol_window_ratio = savgol_window_ratio
            
        self.savgol_poly = savgol_poly
        
        self.envelope_method = envelope_method
            
        self.Tone_Length = Init_Tone_Length
        
        self.InitSelectors = copy.copy(self.Env.selectors)
        self.InitTone = copy.copy(self.Tone)
        self.InitTone_Length = copy.copy(Init_Tone_Length)
        
        self.Initiate_Canvas()
        
        self.Plot_Wave = True
        self.Plot_Savgol = True
        self.Plot_Linear = True
        self.Plot_Selectors = True
        
    def Update_Tone(self, NewTone, NewTone_Length):
        self.Tone = NewTone
        self.Tone_Length = NewTone_Length
        self.Update_Canvas()(0)
        
    def Reset_GUI(self, Reset_Tone = False):
        def reset (val):
            if Reset_Tone:
                self.Tone = self.InitTone
                self.Tone_Length = self.InitTone_Length
            
            init_vals = self.InitSelectors[1]
            sliders = self.sliders
            for i in range(len(self.Env.selectors_x())):
                sliders[i].set_val(init_vals[i])
    
            self.Update_Canvas()(0)
            
        return reset
    
    def Play(self, val):
        sd.play(self.generated_sine_line.get_ydata())
        
    def Loop(self, val):
        sd.play(self.generated_sine_line.get_ydata(), loop=True)
        
    def Stop(self, val):
        sd.stop()
        
    def Update_Savgol_Mode(self, new_savgol_mode):
        self.savgol_mode = new_savgol_mode
        self.Update_Canvas()(0)
        
                
            
Test_Tone = osl.Tone(Frequencies=[110, 220], Amplitudes=[1,1])
Test_egg = Envelope_Generator_GUI(InitTone=Test_Tone)
        
# %%
        
class EGG_Control_Panel:
    
    def __init__(self, Egg):
        
        
# =============================================================================
#         Initialize Egg
# =============================================================================
        
        self.Egg = Egg
        
        
# =============================================================================
#         Initialize Figure and Main Axis
# =============================================================================
        
        self.figure = plt.figure(num=self.Egg.EGG_figure_Name+" Control Panel", figsize=[5.5,8], clear=True)
        self.main_ax = self.figure.add_axes([0,0,1,1], label="main_ax", facecolor='white')
        
        self.main_ax.tick_params(
            axis='x',          # changes apply to the x-axis
            which='both',      # both major and minor ticks are affected
            bottom=False,      # ticks along the bottom edge are off
            top=False,         # ticks along the top edge are off
            left=False,
            right=False,
            labelbottom=False) # labels along the bottom edge are off
        
        self.main_ax.tick_params(
            axis='y',          # changes apply to the x-axis
            which='both',      # both major and minor ticks are affected
            left=False,
            right=False,
            labelleft=False) # labels along the bottom edge are off
        
        self.main_ax.margins(x=0)
        self.main_ax.set_xlim([0,1])
        self.main_ax.set_ylim([0,1])
        
# =============================================================================
#       Create Buttons
# =============================================================================
        
        Button_width = .2
        Button_height = .06
        Edge_width = 0.05
        Button_spacing = 0.03
        Top_gap = 0
        Bottom_Gap = .5
        Left_gap = 0
        Right_gap = 0
        
        Button_count = 0
        
        Button_Box = patches.Rectangle((Edge_width/2, Edge_width+Bottom_Gap), 1-Edge_width, 1-Bottom_Gap-1.5*Edge_width)
#        Button_Box = patches.Rectangle((0.15, 0.5), .25, .25)
        self.main_ax.add_patch(Button_Box)
        
        max_buttons_per_column = (int)(
            math.floor((1+Button_spacing-2*Edge_width-Top_gap-Bottom_Gap)/(Button_height+Button_spacing)))
        
        max_buttons_per_row = (int)(
            math.floor((1+Button_spacing-2*Edge_width-Left_gap-Right_gap)/(Button_width+Button_spacing)))
        
        def Button_params():
            column_number = math.floor(Button_count/max_buttons_per_column)
            row_number = Button_count - max_buttons_per_column * column_number
            
            
            left = Edge_width+Left_gap+((Button_width+Button_spacing)*column_number)
            bottom = 1-Edge_width-Top_gap-Button_height-(Button_height+Button_spacing)*row_number
            
            if Button_count > max_buttons_per_column*max_buttons_per_row:
                raise Exception("TOO MANY BUTTONS!!!")
            
            return [left,bottom,Button_width, Button_height]
            
        
        self.Reset_Button_ax = self.figure.add_axes(Button_params(), label="Reset_Button_ax", 
                                                    facecolor='white')
        Button_count += 1
        
        self.Reset_Button = Button(self.Reset_Button_ax, label="Reset",)
        self.Reset_Button.on_clicked(self.Egg.Reset_GUI(Reset_Tone=True))
        
        
        self.Play_Button_ax = self.figure.add_axes(Button_params(), label="Play_Button_ax", 
                                                    facecolor='white')
        Button_count += 1
        self.Play_Button = Button(self.Play_Button_ax, label="Play",)
        self.Play_Button.on_clicked(self.Egg.Play)
        
        
        self.Loop_Button_ax = self.figure.add_axes(Button_params(), label="Loop_Button_ax", 
                                                    facecolor='white')
        Button_count += 1
        self.Loop_Button = Button(self.Loop_Button_ax, label="Loop",)
        self.Loop_Button.on_clicked(self.Egg.Loop)
        
        
        self.Stop_Button_ax = self.figure.add_axes(Button_params(), label="Stop_Button_ax", 
                                                    facecolor='white')
        Button_count += 1
        self.Stop_Button = Button(self.Stop_Button_ax, label="Stop",)
        self.Stop_Button.on_clicked(self.Egg.Stop)
        
        
        
# =============================================================================
#       Create Misc. Box  
# =============================================================================
        
        Misc_Box = patches.Rectangle((Edge_width/2, Edge_width/2), 1-Edge_width, Bottom_Gap, color='g')
        self.main_ax.add_patch(Misc_Box)
        
        self.Plot_Toggle_ax = self.figure.add_axes([Edge_width, Edge_width, .25, .18], 
                                                   label="Plot_Toggle_ax", facecolor='white')
        self.Plot_Toggle = CheckButtons(ax=self.Plot_Toggle_ax, labels=[
                                                "Plot Wave",
                                                "Plot Savgol",
                                                "Plot Linear",
                                                "Plot Selectors"
                                         ], actives = [True,True,True,True])
        def Update_Plot_Toggle(val):
            Toggle_Bools = self.Plot_Toggle.get_status()
            self.Egg.Plot_Wave = Toggle_Bools[0]
            self.Egg.Plot_Savgol = Toggle_Bools[1]
            self.Egg.Plot_Linear = Toggle_Bools[2]
            self.Egg.Plot_Selectors = Toggle_Bools[3]
            self.Egg.Update_Canvas()(0)
        self.Plot_Toggle.on_clicked(Update_Plot_Toggle)
    
    
        self.Savgol_Mode_Select_ax = self.figure.add_axes([Edge_width, Edge_width+.25, .25, .18], 
                                                   label="Savgol_Mode_Select_ax", facecolor='white')
        self.Savgol_Mode_Select = RadioButtons(self.Savgol_Mode_Select_ax, labels = [
                "wrap","mirror", "nearest", "constant", 
                ])
        def Update_Savgol_Mode_Select(val):
            active_mode = self.Savgol_Mode_Select.value_selected
            self.Egg.Update_Savgol_Mode(active_mode)
        self.Savgol_Mode_Select.on_clicked(Update_Savgol_Mode_Select)
        
        
Test_ecp = EGG_Control_Panel(Test_egg)
        
# %%



# %%
sd.play(Test_egg.generated_sine_line.get_ydata())

print(Test_egg.Env.selectors_y(), Test_egg.InitSelectors[1])

#%%
NewTone = osl.Tone(NoteNames=["C", "C", "C"], NoteOctaves=[4,5,6], Amplitudes=[1,1,1])
NewTone_Length = 1
Test_egg.Update_Tone(NewTone=NewTone, NewTone_Length=NewTone_Length)
sd.play(Test_egg.generated_sine_line.get_ydata())
print(Test_egg.Env.selectors_y(), Test_egg.InitSelectors[1])

# %% 
Test_egg.Reset_GUI(Reset_Tone=True)

# %%
sd.stop()
#%%
sd.play(Test_egg.generated_sine_line.get_ydata(), loop=False)

# %%

Test_egg.savgol_window_ratio = 3
Test_egg.savgol_poly = 1
Test_egg.savgol_mode = 'constant'
Test_egg.savgol_cval = 0
Test_egg.Update_Canvas()(0)