# -*- coding: utf-8 -*-
"""
Created on Fri May 22 16:27:57 2015

@author: Felix Pfreundtner
"""

import algorithm_functions as alf
from copy import deepcopy
import numpy as np

import scipy.io.wavfile
import matplotlib.pyplot as plt

# GUI mockup
gui_dict={0: [272,1,"./audio/electrical_guitar_(44.1,16).wav"],
          1: [2.45,1,"./audio/sine_1kHz_(44.1,16).wav"]
         }
# Algorithm function get_wave_param mockup         
wave_param_dict={0: [970200, 44100,16],
                 1: [220500, 44100,16]
                } 
# Algorithm function get_fft_block mockup         
signal_dict={} 
sp_block_dict={}             
_, signal_dict[0] = scipy.io.wavfile.read(gui_dict[0][2])              
_, signal_dict[1] = scipy.io.wavfile.read(gui_dict[1][2])       

 
 
#Initialize FFT iteration after GUI call
        



#Standard samplerate, sampledepth, output_frames_per_second         
wave_param_common = [44100,16]  
# Determine number of output frames per second
output_fps = 60  
#Overlap FFT in Prozent
overlap=90         
iterationcounter = 1

fft_blocksize, fft_blocktime, output_fps_real = alf.set_fft_param(output_fps, wave_param_common)


# Initialize Dictionarys
standard_dict=alf.create_standard_dict(gui_dict)
wave_blockbeginend_dict = alf.initialze_wave_blockbeginend(standard_dict, overlap, fft_blocktime, wave_param_dict)
convolved_dict=deepcopy(standard_dict)
for sp in convolved_dict:
    convolved_dict[sp] = np.zeros((fft_blocksize, 2))
    
continue_output=deepcopy(standard_dict)
continue_output_list=deepcopy(standard_dict)
for sp in continue_output:
    continue_output[sp] = True
outputsignal_sample_number=deepcopy(standard_dict) 

wave_blockbeginend_dict_list=deepcopy(standard_dict)
for sp in continue_output:
    wave_blockbeginend_dict_list[sp] = []

# Run block iteration  
while any(continue_output.values()) == True and iterationcounter<270 :
    
    # Get current hrtf file dependend on input angle for every sp
    hrtf_filenames_dict = alf.get_hrtf_filenames(standard_dict, gui_dict)
    hrtf_block_dict = alf.get_hrtf(hrtf_filenames_dict, standard_dict, gui_dict)
    # range of frames to be read in iteration from wav files (float numbers needed for adding the correct framesizes to the next iteration)               
    wave_blockbeginend_dict = alf.wave_blockbeginend(wave_blockbeginend_dict, wave_param_dict, fft_blocktime, overlap)
    convolved_block_dict={}
    
    for sp in gui_dict:
        convolved_block_dict[sp]=np.zeros((fft_blocksize, 2))
        
        # check wheter this block is last block in speaker audio file, set ending of the block to last sample in speaker audio file
        if  wave_blockbeginend_dict[sp][1] > wave_param_dict[sp][0]-1:
            wave_blockbeginend_dict[sp][1] = float(wave_param_dict[sp][0])
        
        # if speaker audio file still has unplayed samples start convolution 
        if continue_output[sp] == True:
            # Read wave samples with fft block framesize for every speaker
            sp_block_dict[sp] = signal_dict[sp][int(alf.normal_round(wave_blockbeginend_dict[sp][0])):int(alf.normal_round(wave_blockbeginend_dict[sp][1]))]
            # for the left an right ear channel
            for l_r in range(2):
                # convolve hrtf with speaker block input
                convolved_block_dict[sp][0:fft_blocksize, l_r] = alf.convolve(sp_block_dict[sp], hrtf_block_dict[sp][:,l_r], fft_blocksize)
                # apply hamming window to binaural block ouptut
                convolved_block_dict[sp][:, l_r]= alf.apply_hamming_window(convolved_block_dict[sp][:, l_r])
                # add speaker binaural block output to a iterative time based output array
                
        convolved_dict[sp], outputsignal_sample_number[sp]=alf.create_convolved_dict(convolved_block_dict[sp], convolved_dict[sp], int(alf.normal_round(wave_blockbeginend_dict[sp][0])), outputsignal_sample_number[sp])

        
        # check wheter this block is last block in speaker audio file and stop convolution of speaker audio file
        if wave_blockbeginend_dict[sp][1] == wave_param_dict[sp][0]:
            continue_output[sp] = False
            
        # record how long each speaker audio file was convoluted            
        continue_output_list[sp].append(continue_output[sp])
        wave_blockbeginend_dict_list[sp].extend(wave_blockbeginend_dict[sp])
        
        
    iterationcounter+=1
    
   
# Write generated binaural sound to file
convolved_dict_scaled = alf.bit_int(convolved_dict)       
alf.writebinauraloutput(convolved_dict_scaled, wave_param_common, gui_dict)
