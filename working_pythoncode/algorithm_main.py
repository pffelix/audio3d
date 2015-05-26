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
import gui_main_window as gui

<<<<<<< HEAD
# GUI mockup
gui_dict={0: [0,1,"./audio/electrical_guitar_(44.1,16).wav"],
          1: [0,1,"./audio/sine_1kHz_(44.1,16).wav"],
          2: [0,1, "./audio/synthesizer_(44.1,16).wav"]
         }
# Algorithm function get_wave_param mockup         
wave_param_dict={0: [970200, 44100, 16],
                 1: [220500, 44100, 16],
                 2: [139263, 44100, 16]
                } 
                
# Algorithm function get_fft_block mockup; signal_dict will be removed         
signal_dict={} 
sp_block_dict={}             
_, signal_dict[0] = scipy.io.wavfile.read(gui_dict[0][2])              
_, signal_dict[1] = scipy.io.wavfile.read(gui_dict[1][2]) 
_, signal_dict[2] = scipy.io.wavfile.read(gui_dict[2][2])       


#Initialize FFT iteration after GUI call

[fs3,aaa]=scipy.io.wavfile.read(gui_dict[2][2])

#Standard samplerate, sampledepth, output_frames_per_second         
wave_param_common = [44100,16]  
# Determine number of output blocks per second
output_bps = 60  
# Number of Samples of HRTFs (KEMAR Compact=128, KEMAR Full=512)
hrtf_blocksize = 128

# Variable counts number of already convolved blocks, initialized with zero
blockcounter = 0

fft_blocksize, fft_blocktime, sp_blocksize, sp_blocktime, output_bps_real, overlap = alf.get_block_param(output_bps, wave_param_common, hrtf_blocksize)


# Initialize Dictionarys
standard_dict=alf.create_standard_dict(gui_dict)

wave_blockbeginend_dict = alf.initialze_wave_blockbeginend(standard_dict, sp_blocktime, wave_param_dict)

hrtf_filenames_dict = deepcopy(standard_dict)

hrtf_block_dict = deepcopy(standard_dict)

prior_head_angle_dict=deepcopy(standard_dict)


binaural_dict=deepcopy(standard_dict)
for sp in binaural_dict:
    binaural_dict[sp] = np.zeros((fft_blocksize, 2))
    
continue_output=deepcopy(standard_dict)
for sp in continue_output:
    continue_output[sp] = True
    
continue_output_list=deepcopy(standard_dict)

error_list=deepcopy(standard_dict)

outputsignal_sample_number=deepcopy(standard_dict) 

wave_blockbeginend_dict_list=deepcopy(standard_dict)
for sp in wave_blockbeginend_dict_list:
    wave_blockbeginend_dict_list[sp] = []

# Run block iteration  
while any(continue_output.values()) == True and blockcounter < 4000:
    
    #increment number of already convolved blocks
    blockcounter+=1

    # range of frames to be read in iteration from wav files (float numbers needed for adding the correct framesizes to the next iteration)               
    wave_blockbeginend_dict = alf.wave_blockbeginend(wave_blockbeginend_dict, wave_param_dict, sp_blocktime)
    
    # re-initialize binaural output dictionary for all speakers after each block processing
    binaural_block_dict={}
    
    # iterate over all speakers sp
    for sp in gui_dict:
        binaural_block_dict[sp]=np.zeros((fft_blocksize, 2))
        
        # check wheter this block is last block in speaker audio file, set ending of the block to last sample in speaker audio file
        if  alf.rnd(wave_blockbeginend_dict[sp][1]) > float(wave_param_dict[sp][0]-1):
            wave_blockbeginend_dict[sp][1] = float(wave_param_dict[sp][0])
        
        # if speaker audio file still has unplayed samples start convolution 
        if continue_output[sp] == True:
            
            # check whether head position to speaker sp has changed
            if gui_dict[sp][0] != prior_head_angle_dict[sp]:
                
                # if head position has changed load new fitting hrtf file into array
                hrtf_filenames_dict[sp] = alf.get_hrtf_filenames(gui_dict[sp])
                hrtf_block_dict[sp] = alf.get_hrtf(hrtf_filenames_dict[sp], gui_dict[sp])
                # save head position to speaker of this block in prior_head_angle dict
                prior_head_angle_dict[sp] = gui_dict[sp][0]
'replace here
            # Load current wave block of speaker sp with speaker_blocksize (fft_blocksize-hrtf_blocksize+1)
            sp_block_dict[sp], error_list[sp] = alf.get_sp_block_dict(signal_dict[sp], wave_blockbeginend_dict[sp], sp_blocksize, error_list[sp])
            # for the left an right ear channel
            for l_r in range(2):
                # convolve hrtf with speaker block input
                binaural_block_dict[sp][0:fft_blocksize, l_r] = alf.fft_convolve(sp_block_dict[sp], hrtf_block_dict[sp][:,l_r], fft_blocksize)
                # apply hamming window to binaural block ouptut
                #binaural_block_dict[sp][:, l_r]= alf.apply_hamming_window(binaural_block_dict[sp][:, l_r])
               
        # add speaker binaural block output to a iterative time based output array       
        binaural_dict[sp], outputsignal_sample_number[sp]=alf.add_to_binaural_dict(binaural_block_dict[sp], binaural_dict[sp], int(alf.rnd(wave_blockbeginend_dict[sp][0])), outputsignal_sample_number[sp])

        # check wheter this block is last block in speaker audio file and stop convolution of speaker audio file
        if wave_blockbeginend_dict[sp][1] == float(wave_param_dict[sp][0]):
            continue_output[sp] = False
            
        # record how long each speaker audio file was convoluted            
        continue_output_list[sp].append(continue_output[sp])
        wave_blockbeginend_dict_list[sp].extend(wave_blockbeginend_dict[sp])
        
        # model head position change to speaker for speaker sp
        gui_dict[sp][0]+=0.8
        if gui_dict[sp][0] >= 360:
            gui_dict[sp][0] -= 360


# resize amplitudes of signal to 16bit integer    
binaural_dict_scaled = alf.bit_int(binaural_dict)    
# show plot of the output signal binaural_dict_scaled   
plt.plot(binaural_dict[1])   
# Write generated output signal binaural_dict_scaled to file
alf.writebinauraloutput(binaural_dict_scaled, wave_param_common, gui_dict)
=======
def algo():

    # GUI mockup
    # gui_dict={0: [0,1,"./audio/electrical_guitar_(44.1,16).wav"],
    #           1: [0,1,"./audio/sine_1kHz_(44.1,16).wav"],
    #           2: [0,1, "./audio/synthesizer_(44.1,16).wav"]
    #          }
    gui_dict = gui.gui_dict
    # Algorithm function get_wave_param mockup
    wave_param_dict={0: [970200, 44100, 16],
                     1: [220500, 44100, 16],
                     2: [139263, 44100, 16]
                    }

    # Algorithm function get_fft_block mockup
    signal_dict={}
    print(gui_dict[0][2])
    sp_block_dict={}
    _, signal_dict[0] = scipy.io.wavfile.read(gui_dict[0][2])
    _, signal_dict[1] = scipy.io.wavfile.read(gui_dict[1][2])
    _, signal_dict[2] = scipy.io.wavfile.read(gui_dict[2][2])


    #Initialize FFT iteration after GUI call

    [fs3,aaa]=scipy.io.wavfile.read(gui_dict[2][2])

    #Standard samplerate, sampledepth, output_frames_per_second
    wave_param_common = [44100,16]
    # Determine number of output blocks per second
    output_bps = 60
    # Number of Samples of HRTFs (KEMAR Compact=128, KEMAR Full=512)
    hrtf_blocksize = 128

    # Variable counts number of already convolved blocks, initialized with zero
    blockcounter = 0

    fft_blocksize, fft_blocktime, sp_blocksize, sp_blocktime, output_bps_real, overlap = alf.get_block_param(output_bps, wave_param_common, hrtf_blocksize)


    # Initialize Dictionarys
    standard_dict=alf.create_standard_dict(gui_dict)

    wave_blockbeginend_dict = alf.initialze_wave_blockbeginend(standard_dict, sp_blocktime, wave_param_dict)

    hrtf_filenames_dict = deepcopy(standard_dict)

    hrtf_block_dict = deepcopy(standard_dict)

    prior_head_angle_dict=deepcopy(standard_dict)


    binaural_dict=deepcopy(standard_dict)
    for sp in binaural_dict:
        binaural_dict[sp] = np.zeros((fft_blocksize, 2))

    continue_output=deepcopy(standard_dict)
    for sp in continue_output:
        continue_output[sp] = True

    continue_output_list=deepcopy(standard_dict)

    error_list=deepcopy(standard_dict)

    outputsignal_sample_number=deepcopy(standard_dict)

    wave_blockbeginend_dict_list=deepcopy(standard_dict)
    for sp in wave_blockbeginend_dict_list:
        wave_blockbeginend_dict_list[sp] = []

    # Run block iteration
    while any(continue_output.values()) == True and blockcounter < 4000:

        #increment number of already convolved blocks
        blockcounter+=1

        # range of frames to be read in iteration from wav files (float numbers needed for adding the correct framesizes to the next iteration)
        wave_blockbeginend_dict = alf.wave_blockbeginend(wave_blockbeginend_dict, wave_param_dict, sp_blocktime)

        # re-initialize binaural output dictionary for all speakers after each block processing
        binaural_block_dict={}

        # iterate over all speakers sp
        for sp in gui_dict:
            binaural_block_dict[sp]=np.zeros((fft_blocksize, 2))

            # check wheter this block is last block in speaker audio file, set ending of the block to last sample in speaker audio file
            if  alf.rnd(wave_blockbeginend_dict[sp][1]) > float(wave_param_dict[sp][0]-1):
                wave_blockbeginend_dict[sp][1] = float(wave_param_dict[sp][0])

            # if speaker audio file still has unplayed samples start convolution
            if continue_output[sp] == True:

                # check whether head position to speaker sp has changed
                if gui_dict[sp][0] != prior_head_angle_dict[sp]:

                    # if head position has changed load new fitting hrtf file into array
                    hrtf_filenames_dict[sp] = alf.get_hrtf_filenames(gui_dict[sp])
                    hrtf_block_dict[sp] = alf.get_hrtf(hrtf_filenames_dict[sp], gui_dict[sp])
                    # save head position to speaker of this block in prior_head_angle dict
                    prior_head_angle_dict[sp] = gui_dict[sp][0]

                # Load current wave block of speaker sp with speaker_blocksize (fft_blocksize-hrtf_blocksize+1)
                sp_block_dict[sp], error_list[sp] = alf.get_sp_block_dict(signal_dict[sp], wave_blockbeginend_dict[sp], sp_blocksize, error_list[sp])
                # for the left an right ear channel
                for l_r in range(2):
                    # convolve hrtf with speaker block input
                    binaural_block_dict[sp][0:fft_blocksize, l_r] = alf.fft_convolve(sp_block_dict[sp], hrtf_block_dict[sp][:,l_r], fft_blocksize)
                    # apply hamming window to binaural block ouptut
                    #binaural_block_dict[sp][:, l_r]= alf.apply_hamming_window(binaural_block_dict[sp][:, l_r])

            # add speaker binaural block output to a iterative time based output array
            binaural_dict[sp], outputsignal_sample_number[sp]=alf.add_to_binaural_dict(binaural_block_dict[sp], binaural_dict[sp], int(alf.rnd(wave_blockbeginend_dict[sp][0])), outputsignal_sample_number[sp])

            # check wheter this block is last block in speaker audio file and stop convolution of speaker audio file
            if wave_blockbeginend_dict[sp][1] == float(wave_param_dict[sp][0]):
                continue_output[sp] = False

            # record how long each speaker audio file was convoluted
            continue_output_list[sp].append(continue_output[sp])
            wave_blockbeginend_dict_list[sp].extend(wave_blockbeginend_dict[sp])

            # model head position change to speaker for speaker sp
            gui_dict[sp][0]+=0.8
            if gui_dict[sp][0] >= 360:
                gui_dict[sp][0] -= 360


    # resize amplitudes of signal to 16bit integer
    binaural_dict_scaled = alf.bit_int(binaural_dict)
    # show plot of the output signal binaural_dict_scaled
    plt.plot(binaural_dict[1])
    # Write generated output signal binaural_dict_scaled to file
    alf.writebinauraloutput(binaural_dict_scaled, wave_param_common, gui_dict)
>>>>>>> c1ce5650082a64e02ed9947ca04b631a94d2337d
