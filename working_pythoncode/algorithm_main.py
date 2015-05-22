# -*- coding: utf-8 -*-
"""
Created on Fri May 22 16:27:57 2015

@author: Felix Pfreundtner
"""

import algorithm_functions
import scipy.io.wavfile as wav


#manuell eingegebene Werte, da noch kein Mockup verfügbar
gui_dict={0: [90,2,"./audio/electrical_guitar_(44.1,16).wav"],
          1: [270,1,"./audio/sine_1kHz_(44.1,16).wav"]
         }
         
wave_param_dict={0: [970200, 44100,16],
                 1: [220500, 441,16]
                } 
         
            
#Initialize FFT iteration after GUI call
        
#Standard samplerate, sampledepth         
wave_param_common = [44100,16]  
output_fps = 60                       
iterationcounter = 0
fft_blocksize, fft_blocktime, output_fps_real = algorithm_functions.set_fft_param(output_fps, gui_dict, wave_param_common)
wave_blockbeginend_dict=algorithm_functions.initialze_wave_blockbeginend(gui_dict)


#Run FFT iteration  

#range of frames to be read in iteration from wav files (float numbers needed for interpolation between different frame rates)               
wave_blockbeginend_dict=algorithm_functions.wave_blockbeginend(wave_blockbeginend_dict, wave_param_dict, fft_blocktime)
iterationcounter+=1
          
          