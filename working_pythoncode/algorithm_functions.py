# -*- coding: utf-8 -*-
"""
Created on Fri May 22 16:25:01 2015

@author: Felix Pfreundtner
"""
import math
from copy import deepcopy

import numpy as np
import scipy
from scipy.fftpack import rfft, irfft
from scipy.signal import fftconvolve
import scipy.io.wavfile



# @author: Felix Pfreundtner
def create_standard_dict(gui_dict):
    standard_dict=deepcopy(gui_dict)
    for sp in standard_dict:
        standard_dict[sp]=[]
    return standard_dict   
    
# @author: Felix Pfreundtner
# function does a normal school arithmetic round (Round half away from zero)
# different to pythons rounding method (Round half to even)
def normal_round(value):
    if value >=0:
       if  value-math.floor(value) < 0.5:
           value=math.floor(value)
       else:
           value=math.ceil(value)
    else:
       if  value-math.floor(value) <= 0.5:
           value=math.floor(value)
       else:
           value=math.ceil(value)
    return value    
    
# @author: Felix Pfreundtner
def set_fft_param(output_fps, wave_param_common):
    # Standard FFT block size colculation dependend on output_fps
    fft_blocksize = 2**(round(math.log(wave_param_common[0]/output_fps, 2)))
    fft_blocktime = fft_blocksize/wave_param_common[0]
    output_fps_real = 1/fft_blocktime
    return fft_blocksize, fft_blocktime, output_fps_real

# @author: Felix Pfreundtner
def initialze_wave_blockbeginend(standard_dict, overlap, fft_blocktime, wave_param_dict):
    wave_blockbeginend_dict=deepcopy(standard_dict)   
    for sp in wave_blockbeginend_dict:
          wave_blockbeginend_dict[sp]=[-(fft_blocktime*wave_param_dict[sp][1])*(1-overlap/100),0]
    return wave_blockbeginend_dict
    
# @author: Felix Pfreundtner
def wave_blockbeginend(wave_blockbeginend_dict, wave_param_dict, fft_blocktime,overlap):   
    for sp in wave_blockbeginend_dict:
        wave_blockbeginend_dict[sp][0]=wave_blockbeginend_dict[sp][0] + (fft_blocktime*wave_param_dict[sp][1])*(1-overlap/100)
        wave_blockbeginend_dict[sp][1]=wave_blockbeginend_dict[sp][0] + (fft_blocktime*wave_param_dict[sp][1])
    return wave_blockbeginend_dict

# @author: Felix Pfreundtner
def get_hrtf_filenames(standard_dict, gui_dict):   
    hrtf_filenames_dict=deepcopy(standard_dict)
    for sp in hrtf_filenames_dict:
        rounddifference = gui_dict[sp][0] % 5
        if rounddifference == 0:
            if gui_dict[sp][0] <= 180:
                azimuthangle=gui_dict[sp][0]
            else:
                azimuthangle=360 - gui_dict[sp][0]
        else:
            if gui_dict[sp][0] <= 180:
                if rounddifference < 2.5:
                    azimuthangle = round(gui_dict[sp][0] - rounddifference) 
                else:
                    azimuthangle = round(gui_dict[sp][0] + 5 - rounddifference)
            else:  
                if rounddifference < 2.5:
                    azimuthangle = 360 - round(gui_dict[sp][0] - rounddifference)
                else:    
                    azimuthangle = 360 - round(gui_dict[sp][0] + 5 - rounddifference)    
        hrtf_filenames_dict[sp] = ["./kemar/compact/elev0/H0e"+str(azimuthangle).zfill(3)+"a.wav"]
    return hrtf_filenames_dict

# @author: Felix Pfreundtner
def get_hrtf(hrtf_filenames_dict, standard_dict, gui_dict):
    hrtf_dict=deepcopy(standard_dict)
    for sp in hrtf_filenames_dict:
        for hrtf_filename in hrtf_filenames_dict[sp]:
            _, hrtf_input = scipy.io.wavfile.read(hrtf_filename)
            if gui_dict[sp][0] <= 180:
                hrtf_dict[sp]=hrtf_input
            else:
                hrtf_input[:,[0, 1]] = hrtf_input[:,[1, 0]]
                hrtf_dict[sp]=hrtf_input
                
    return hrtf_dict    
    
    
# @author: Felix Pfreundtner
def convolve(sp_block, hrtf_block, fft_blocksize):
    
    hrtf_zeropadding = np.zeros((fft_blocksize-len(hrtf_block),),dtype='float')
    hrtf_block_blocksize = np.concatenate((hrtf_block.astype(float, copy=False),hrtf_zeropadding))
    sp_zeropadding = np.zeros((fft_blocksize-len(sp_block),),dtype='float')
    sp_block_blocksize = np.concatenate((sp_block.astype(float, copy=False),sp_zeropadding))
    
    convolved_block=fftconvolve(sp_block_blocksize, hrtf_block.astype(float, copy=False), mode='same')
    return convolved_block
    
# @author: Felix Pfreundtner
def apply_hamming_window(inputsignal):
    hamming_window = [0.53836 - 0.46164*math.cos(2*math.pi*t/(len(inputsignal) - 1)) for t in range(len(inputsignal))]
    hamming_window = np.asarray(hamming_window, dtype=np.float64)
    inputsignal = inputsignal * hamming_window
    return inputsignal
    

# @author: Felix Pfreundtner
def bit_int(convolved_dict):
    convolved_dict_scaled={}
    for sp in convolved_dict:
        convolved_dict_scaled[sp] = np.zeros((len(convolved_dict[sp]), 2), dtype=np.int16)
        for l_r in range(2):
            maximum_value=np.max(np.abs(convolved_dict[sp][:, l_r]))
            if maximum_value != 0:
                convolved_dict_scaled[sp][:, l_r] = convolved_dict[sp][:, l_r]/maximum_value * 32767
                convolved_dict_scaled[sp] = convolved_dict_scaled[sp].astype(np.int16, copy=False)
  
    return convolved_dict_scaled

# @author: Felix Pfreundtner
def create_convolved_dict(convolved_block_dict, convolved_dict, begin_block, outputsignal_sample_number):
    outputsignal_sample_number= len(convolved_dict)   
    convolved_dict[begin_block : outputsignal_sample_number, :] += convolved_block_dict[0 : (outputsignal_sample_number - begin_block), :]
    convolved_dict=np.concatenate((convolved_dict, convolved_block_dict[(outputsignal_sample_number - begin_block):, :]))
    outputsignal_sample_number= len(convolved_dict)
    
    return convolved_dict, outputsignal_sample_number

# @author: Felix Pfreundtner
def writebinauraloutput(convolved_dict_scaled, wave_param_common, gui_dict):
    for sp in convolved_dict_scaled:
        scipy.io.wavfile.write(gui_dict[sp][2] + "binauraloutput.wav" , wave_param_common[0], convolved_dict_scaled[sp])    
        