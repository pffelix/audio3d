# -*- coding: utf-8 -*-
"""
Created on Fri May 22 16:25:01 2015

@author: Felix Pfreundtner
"""
import math

def create_standard_dict(gui_dict):
      for item in gui_dict:
          gui_dict[item]=[]
      return gui_dict    

def set_fft_param(output_fps, gui_dict, wave_param_common):
    # Standard FFT block size colculation dependend on output_fps
    fft_blocksize = 2**(round(math.log(wave_param_common[0]/output_fps, 2)))
    fft_blocktime = fft_blocksize/wave_param_common[0]
    output_fps_real = 1/fft_blocktime
    return fft_blocksize, fft_blocktime, output_fps_real

def initialze_wave_blockbeginend(gui_dict):
    for item in gui_dict:
          gui_dict[item]=[0,float(-1)]
    return gui_dict

def wave_blockbeginend(wave_blockbeginend_dict, wave_param_dict, fft_blocktime):   
    for item in wave_blockbeginend_dict:
        wave_blockbeginend_dict[item][0]=wave_blockbeginend_dict[item][1] + 1
        wave_blockbeginend_dict[item][1]=wave_blockbeginend_dict[item][1] + fft_blocktime*wave_param_dict[item][1] 
    return wave_blockbeginend_dict


