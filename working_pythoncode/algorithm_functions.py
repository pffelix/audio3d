# -*- coding: utf-8 -*-
"""
Created on Fri May 22 16:25:01 2015

@author: Felix Pfreundtner
"""
import math
from copy import deepcopy

import numpy as np
import scipy
from scipy.fftpack import rfft, irfft, fft, ifft
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
def rnd(value):
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
def get_block_param(output_bps, wave_param_common, hrtf_blocksize):
    # Standard FFT block size colculation dependend on output_fps
    fft_blocksize = 2**(round(math.log(wave_param_common[0]/output_bps, 2)))
    fft_blocktime = fft_blocksize/wave_param_common[0]
    sp_blocksize = fft_blocksize-hrtf_blocksize+1
    sp_blocktime = sp_blocksize/wave_param_common[0]
    output_bps_real = 1/fft_blocktime
    output_overlap = (fft_blocksize-sp_blocksize)/fft_blocksize*100 # in %
    
    return fft_blocksize, fft_blocktime, sp_blocksize, sp_blocktime, output_bps_real

# @author: Felix Pfreundtner
def initialze_wave_blockbeginend(standard_dict, sp_blocktime, wave_param_dict):
    wave_blockbeginend_dict=deepcopy(standard_dict) 
    for sp in wave_blockbeginend_dict:
        wave_blockbeginend_dict[sp]=[-(sp_blocktime*wave_param_dict[sp][1]),0]
    return wave_blockbeginend_dict
    
# @author: Felix Pfreundtner
def wave_blockbeginend(wave_blockbeginend_dict, wave_param_dict, sp_blocktime):   
    for sp in wave_blockbeginend_dict:
        wave_blockbeginend_dict[sp][0]=wave_blockbeginend_dict[sp][0] + (sp_blocktime*wave_param_dict[sp][1])
        wave_blockbeginend_dict[sp][1]=wave_blockbeginend_dict[sp][0] + (sp_blocktime*wave_param_dict[sp][1])
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
def get_sp_block_dict(signal_dict_sp, wave_blockbeginend_dict_sp, sp_blocksize, error_list_sp):    
    sp_block_dict_sp=signal_dict_sp[int(rnd(wave_blockbeginend_dict_sp[0])):int(rnd(wave_blockbeginend_dict_sp[1]))]
    # if last block of speaker input signal
    if len(sp_block_dict_sp) == sp_blocksize:
        error_list_sp.append("correct blocksize")
       
    elif len(sp_block_dict_sp) < sp_blocksize:
        error_list_sp.append("block smaller than correct blocksize")
        add_zeros_to_block = np.zeros((sp_blocksize-len(sp_block_dict_sp),),dtype='int16')
        sp_block_dict_sp = np.concatenate((sp_block_dict_sp, add_zeros_to_block))
    else:
        error_list_sp.append("error block size doesn't match")
    return sp_block_dict_sp, error_list_sp
    
# @author: Felix Pfreundtner
def fft_convolve(sp_block_sp, hrtf_block_sp_l_r, fft_blocksize):
    
    hrtf_zeros = np.zeros((fft_blocksize-len(hrtf_block_sp_l_r),),dtype='float')
    hrtf_block_sp_zeropadded = np.concatenate((hrtf_block_sp_l_r.astype(float, copy=False),hrtf_zeros))
    sp_zeros = np.zeros((fft_blocksize-len(sp_block_sp),),dtype='float')
    sp_block_sp_zeropadded = np.concatenate((sp_block_sp.astype(float, copy=False),sp_zeros))
    
    # bring time domain to to frequency domain
    hrtf_block_sp_frequency = fft(hrtf_block_sp_zeropadded, fft_blocksize)
    sp_block_sp_frequency = fft(sp_block_sp_zeropadded, fft_blocksize)
    
    # execute convulotion of speaker input and hrtf input: multiply complex frequency domain vectors
    binaural_block_sp_frequency = sp_block_sp_frequency * hrtf_block_sp_frequency
    
    # bring multiplied spectrum back to time domain, disneglected small complex time parts resulting from numerical fft approach
    binaural_block_sp = ifft(binaural_block_sp_frequency, fft_blocksize).real
    
    return binaural_block_sp
    
# @author: Felix Pfreundtner
def apply_hamming_window(inputsignal):
    hamming_window = [0.53836 - 0.46164*math.cos(2*math.pi*t/(len(inputsignal) - 1)) for t in range(len(inputsignal))]
    hamming_window = np.asarray(hamming_window, dtype=np.float64)
    inputsignal = inputsignal * hamming_window
    return inputsignal
    

# @author: Felix Pfreundtner
def bit_int(binaural_dict):
    binaural_dict_scaled={}
    for sp in binaural_dict:
        binaural_dict_scaled[sp] = np.zeros((len(binaural_dict[sp]), 2), dtype=np.int16)
        for l_r in range(2):
            maximum_value=np.max(np.abs(binaural_dict[sp][:, l_r]))
            if maximum_value != 0:
                binaural_dict_scaled[sp][:, l_r] = binaural_dict[sp][:, l_r]/maximum_value * 32767
                binaural_dict_scaled[sp] = binaural_dict_scaled[sp].astype(np.int16, copy=False)
  
    return binaural_dict_scaled

# @author: Felix Pfreundtner
def create_binaural_dict(binaural_block_dict, binaural_dict, begin_block, outputsignal_sample_number):
    outputsignal_sample_number= len(binaural_dict)   
    binaural_dict[begin_block : outputsignal_sample_number, :] += binaural_block_dict[0 : (outputsignal_sample_number - begin_block), :]
    binaural_dict=np.concatenate((binaural_dict, binaural_block_dict[(outputsignal_sample_number - begin_block):, :]))
    outputsignal_sample_number= len(binaural_dict)
    
    return binaural_dict, outputsignal_sample_number

# @author: Felix Pfreundtner
def writebinauraloutput(binaural_dict_scaled, wave_param_common, gui_dict):
    for sp in binaural_dict_scaled:
        scipy.io.wavfile.write(gui_dict[sp][2] + "binauraloutput.wav" , wave_param_common[0], binaural_dict_scaled[sp])    
        