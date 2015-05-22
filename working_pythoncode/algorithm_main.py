# -*- coding: utf-8 -*-
"""
Created on Fri May 22 16:27:57 2015

@author: Felix Pfreundtner
"""

import algorithm_functions
import scipy.io.wavfile as wav


#manuell eingegebene Werte, da noch kein Mockup verfügbar
gui_dict={0: [4.9,2,"./audio/electrical_guitar_(44.1,16).wav"],
          1: [182.7,1,"./audio/sine_1kHz_(44.1,16).wav"]
         }
         
wave_param_dict={0: [970200, 44100,16],
                 1: [220500, 44100,16]
                } 
         
            
#Initialize FFT iteration after GUI call
        
#Standard samplerate, sampledepth, output_frames_per_second         
wave_param_common = [44100,16]  
standard_dict=algorithm_functions.create_standard_dict(gui_dict)
output_fps = 60  
                     
iterationcounter = 0
fft_blocksize, fft_blocktime, output_fps_real = algorithm_functions.set_fft_param(output_fps, wave_param_common)
wave_blockbeginend_dict=algorithm_functions.initialze_wave_blockbeginend(standard_dict)


#Run FFT iteration  

#range of frames to be read in iteration from wav files (float numbers needed for interpolation between different frame rates)               
wave_blockbeginend_dict = algorithm_functions.wave_blockbeginend(wave_blockbeginend_dict, wave_param_dict, fft_blocktime)
hrtf_filenames_dict = algorithm_functions.get_hrtf_filenames(standard_dict, gui_dict)
hrtf_dict = algorithm_functions.get_hrtf(hrtf_filenames_dict, standard_dict, gui_dict)

iterationcounter+=1




          