# -*- coding: utf-8 -*-
"""
Created on Fri May 22 16:27:57 2015

@author: Felix Pfreundtner
"""

import algorithm_functions as alf
from copy import deepcopy
import numpy as np

import scipy.io.wavfile

# GUI mockup
gui_dict={0: [272,1,"./audio/electrical_guitar_(44.1,16).wav"],
          1: [192.45,1,"./audio/sine_1kHz_(44.1,16).wav"]
         }
# Algorithm function get_wave_param mockup         
wave_param_dict={0: [970200, 44100,16],
                 1: [220500, 44100,16]
                } 
# Algorithm function get_fft_block mockup         
fft_block_complete_signal_dict={} 
fft_block_dict={}             
_, fft_block_complete_signal_dict[0] = scipy.io.wavfile.read(gui_dict[0][2])              
_, fft_block_complete_signal_dict[1] = scipy.io.wavfile.read(gui_dict[1][2])       

 
 
#Initialize FFT iteration after GUI call
        
#Standard samplerate, sampledepth, output_frames_per_second         
wave_param_common = [44100,16]  
standard_dict=alf.create_standard_dict(gui_dict)

output_fps = 60  
#Overlap FFT in Prozent
overlap=0         
iterationcounter = 200

fft_blocksize, fft_blocktime, output_fps_real = alf.set_fft_param(output_fps, wave_param_common)
wave_blockbeginend_dict = alf.initialze_wave_blockbeginend(standard_dict, overlap, fft_blocktime, wave_param_dict)



# Run convolution iteration  
while iterationcounter <=215:
    # Get current hrtf file dependend on input angle for every source
    hrtf_filenames_dict = alf.get_hrtf_filenames(standard_dict, gui_dict)
    hrtf_dict = alf.get_hrtf(hrtf_filenames_dict, standard_dict, gui_dict)


    # Read wave samples with fft block framesize for every source

    # range of frames to be read in iteration from wav files (float numbers needed for adding the correct framesizes to the next iteration)               
    # @matthias: for reading the wave file from sample a to b you need to round the constraints from wave_blockbeginend_dict{sp#,[ a, b]: -> int(alf.normal_round(a)) and int(alf.normal_round(b))
    wave_blockbeginend_dict = alf.wave_blockbeginend(wave_blockbeginend_dict, wave_param_dict, fft_blocktime, overlap)

    # convolve hrtfs with sources
    if iterationcounter == 1:
        convolved_dict={}
        convolved_block_dict={}  

    for source in fft_block_complete_signal_dict:
        # Algorithm function get_fft_block mockup  
        fft_block_dict[source] = fft_block_complete_signal_dict[source][int(alf.normal_round(wave_blockbeginend_dict[source][0])):int(alf.normal_round(wave_blockbeginend_dict[source][1]))]
    
        # convolve hrtfs with sources
        if iterationcounter == 1:
            convolved_dict[source] = np.empty((len(fft_block_complete_signal_dict[source]), 2))
        convolved_block_dict[source]=np.zeros((fft_blocksize, 2))
        for left_right in range(2):
            convolved_block_dict[source][:, left_right] = alf.convolve(fft_block_dict[source], hrtf_dict[source][:,left_right], fft_blocksize)
            convolved_dict[source][wave_blockbeginend_dict[source][0]:wave_blockbeginend_dict[source][1], left_right] = convolved_block_dict[source][:, left_right]

    iterationcounter+=1

    
# Write generated binaural sound to file
convolved_dict_scaled = alf.bit_int(convolved_dict)       
alf.writebinauraloutput(convolved_dict_scaled, wave_param_common, gui_dict)
