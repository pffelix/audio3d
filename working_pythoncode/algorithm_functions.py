# -*- coding: utf-8 -*-
"""
Created on Fri May 22 16:25:01 2015

@author: Felix Pfreundtner
"""
import math
from copy import deepcopy
import scipy.io.wavfile


# @author: Felix Pfreundtner
def create_standard_dict(gui_dict):
    standard_dict=deepcopy(gui_dict)
    for source in standard_dict:
        standard_dict[source]=[]
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
    for source in wave_blockbeginend_dict:
          wave_blockbeginend_dict[source]=[-(fft_blocktime*wave_param_dict[source][1])*(1-overlap/100),0]
    return wave_blockbeginend_dict
    
# @author: Felix Pfreundtner
def wave_blockbeginend(wave_blockbeginend_dict, wave_param_dict, fft_blocktime,overlap):   
    for source in wave_blockbeginend_dict:
        wave_blockbeginend_dict[source][0]=wave_blockbeginend_dict[source][0] + (fft_blocktime*wave_param_dict[source][1])*(1-overlap/100)
        wave_blockbeginend_dict[source][1]=wave_blockbeginend_dict[source][0] + (fft_blocktime*wave_param_dict[source][1])-1
    return wave_blockbeginend_dict

# @author: Felix Pfreundtner
def get_hrtf_filenames(standard_dict, gui_dict):   
    hrtf_filenames_dict=deepcopy(standard_dict)
    for source in hrtf_filenames_dict:
        rounddifference = gui_dict[source][0] % 5
        if rounddifference == 0:
            if gui_dict[source][0] <= 180:
                azimuthangle=gui_dict[source][0]
            else:
                azimuthangle=360 - gui_dict[source][0]
        else:
            if gui_dict[source][0] <= 180:
                if rounddifference < 2.5:
                    azimuthangle = round(gui_dict[source][0] - rounddifference) 
                else:
                    azimuthangle = round(gui_dict[source][0] + 5 - rounddifference)
            else:  
                if rounddifference < 2.5:
                    azimuthangle = 360 - round(gui_dict[source][0] - rounddifference)
                else:    
                    azimuthangle = 360 - round(gui_dict[source][0] + 5 - rounddifference)    
        hrtf_filenames_dict[source] = ["./kemar/compact/elev0/H0e"+str(azimuthangle).zfill(3)+"a.wav"]
    return hrtf_filenames_dict

# @author: Felix Pfreundtner
def get_hrtf(hrtf_filenames_dict, standard_dict, gui_dict):
    hrtf_dict=deepcopy(standard_dict)
    for source in hrtf_filenames_dict:
        for hrtf_filename in hrtf_filenames_dict[source]:
            _, hrtf_input = scipy.io.wavfile.read(hrtf_filename)
            if gui_dict[source][0] <= 180:
                hrtf_dict[source]=hrtf_input
            else:
                hrtf_input[:,[0, 1]] = hrtf_input[:,[1, 0]]
                hrtf_dict[source]=hrtf_input
    return hrtf_dict    
    
    