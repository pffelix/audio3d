# -*- coding: utf-8 -*-
"""
Created on Fri Jun  5 10:30:53 2015

@author: Felix Pfreundtner
"""

import scipy.io.wavfile
import struct
import numpy as np
import math

class DspIn:
    def __init__(self, gui_dict_init):
        self.wave_param_dict = dict.fromkeys(gui_dict_init, [])
        self.hrtf_filenames_dict = dict.fromkeys(gui_dict_init, [])
        self.hrtf_block_dict = dict.fromkeys(gui_dict_init, [])
        self.hrtf_max_gain_dict = dict.fromkeys(gui_dict_init, [])
        self.sp_max_gain_dict = dict.fromkeys(gui_dict_init, [])
        self.wave_blockbeginend_dict_list = dict.fromkeys(gui_dict_init, [])
        self.wave_blockbeginend_dict = dict.fromkeys(gui_dict_init, [])
        self.signal_dict = {}
        self.sp_block_dict = {}
        # Standard samplerate, sampledepth
        self.wave_param_common = [44100, 16]
        # Determine number of output blocks per second
        self.fft_blocksize = 512
        # Number of Samples of HRTFs (KEMAR Compact=128, KEMAR Full=512)
        self.hrtf_blocksize = 128
        self.sp_blocksize, self.sp_blocktime, self.overlap = self.get_block_param(self.wave_param_common, self.hrtf_blocksize, self.fft_blocksize)
        for sp in self.wave_param_dict:
            # Read in whole Wave File of Speaker sp into signal_dict[sp] and write Wave Parameter samplenumber, samplefrequency and bitdepth (Standard 16bit) into wave_param_dict[sp]
            self.samplerate_sp, self.signal_dict[sp] = scipy.io.wavfile.read(gui_dict_init[sp][2])
            self.wave_param_dict[sp].extend([len(self.signal_dict[sp]), self.samplerate_sp, 16, 1])
            # get samplerate from header in .wav-file of all speakers
            self.wave_param_dict[sp][1], self.wave_param_dict[sp][2], self.wave_param_dict[sp][3] = self.get_samplerate_bits_nochannels(gui_dict_init[sp][2])
        self.wave_blockbeginend_dict = self.initialze_wave_blockbeginend(self.wave_blockbeginend_dict, self.sp_blocktime, self.wave_param_dict)

    # @author: Felix Pfreundtner
    # function does a normal school arithmetic round (Round half away from zero)
    # different to pythons round() method (Round half to even)
    def rnd(self, value):
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
    def get_block_param(self, wave_param_common, hrtf_blocksize, fft_blocksize):
        sp_blocksize = fft_blocksize-hrtf_blocksize+1
        sp_blocktime = sp_blocksize/wave_param_common[0]
        overlap = (fft_blocksize-sp_blocksize)/fft_blocksize*100 # in %
        return sp_blocksize, sp_blocktime, overlap

        # @author: Matthias Lederle
    def get_samplerate_bits_nochannels(self, filename):
        file = open(filename, 'rb')
        _big_endian = False
        # check whether file is RIFX or RIFF
        str1 = file.read(4)
        if str1 == b'RIFX':
            _big_endian = True
        if _big_endian:
            fmt = '>'
        else:
            fmt = '<'
        file.seek(22)
        nochannels = struct.unpack(fmt+"H", file.read(2))[0]
        samplerate = struct.unpack(fmt+"I", file.read(4))[0]
        file.seek(34)
        bits = struct.unpack(fmt+"H", file.read(2))[0]
        file.close()
        return samplerate, bits, nochannels

    # @author: Felix Pfreundtner
    def initialze_wave_blockbeginend(self, wave_blockbeginend_dict,sp_blocktime, wave_param_dict):
        for sp in wave_blockbeginend_dict:
            wave_blockbeginend_dict[sp]=[-(sp_blocktime*wave_param_dict[sp][1]),0]
        return wave_blockbeginend_dict

    # @author: Felix Pfreundtner
    def wave_blockbeginend(self, wave_blockbeginend_dict, wave_param_dict, sp_blocktime):
        for sp in wave_blockbeginend_dict:
            wave_blockbeginend_dict[sp][0]=wave_blockbeginend_dict[sp][0] + (sp_blocktime*wave_param_dict[sp][1])
            wave_blockbeginend_dict[sp][1]=wave_blockbeginend_dict[sp][0] + (sp_blocktime*wave_param_dict[sp][1])
        return wave_blockbeginend_dict

    # @author: Felix Pfreundtner
    def get_hrtf_filenames(self, gui_dict_sp):
        rounddifference = gui_dict_sp[0] % 5
        if rounddifference == 0:
            if gui_dict_sp[0] <= 180:
                azimuthangle = self.rnd(gui_dict_sp[0])
            else:
                azimuthangle = self.rnd(360 - gui_dict_sp[0])
        else:
            if gui_dict_sp[0] <= 180:
                if rounddifference < 2.5:
                    azimuthangle = self.rnd(gui_dict_sp[0] - rounddifference)
                else:
                    azimuthangle = self.rnd(gui_dict_sp[0] + 5 - rounddifference)
            else:
                if rounddifference < 2.5:
                    azimuthangle = 360 - self.rnd(gui_dict_sp[0] - rounddifference)
                else:
                    azimuthangle = 360 - self.rnd(gui_dict_sp[0] + 5 - rounddifference)
        hrtf_filenames_dict_sp = "./kemar/compact/elev0/H0e" + str(azimuthangle).zfill(3) + "a.wav"
        return hrtf_filenames_dict_sp

    # @author: Felix Pfreundtner
    def get_hrtf(self, hrtf_filenames_dict_sp, gui_dict_sp):
        _, hrtf_input = scipy.io.wavfile.read(hrtf_filenames_dict_sp)
        if gui_dict_sp[0] <= 180:
            hrtf_block_dict_sp=hrtf_input
        else:
            hrtf_input[:,[0, 1]] = hrtf_input[:,[1, 0]]
            hrtf_block_dict_sp=hrtf_input
        hrtf_max_gain_sp=[]
        hrtf_max_gain_sp.append(np.amax(np.abs(hrtf_block_dict_sp[:, 0])))
        hrtf_max_gain_sp.append(np.amax(np.abs(hrtf_block_dict_sp[:, 1])))
        return hrtf_block_dict_sp, hrtf_max_gain_sp

    # @author: Felix Pfreundtner
    def get_sp_block_dict(self, signal_dict_sp, wave_blockbeginend_dict_sp, sp_blocksize, error_list_sp):
        sp_block_dict_sp=signal_dict_sp[int(self.rnd(wave_blockbeginend_dict_sp[0])):int(self.rnd(wave_blockbeginend_dict_sp[1]))]
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
    def normalize(self, sp_block_dict_sp, normalize_flag_sp):
        if normalize_flag_sp:
            # take maximum amplitude of original wave file of sp block
            max_amplitude_input = np.amax(np.abs(sp_block_dict_sp))
            if max_amplitude_input != 0:
                # normalize to have the maximum int16 amplitude
                max_amplitude_output = 32767
                sp_block_dict_sp = sp_block_dict_sp / (max_amplitude_input / max_amplitude_output)
                sp_block_dict_sp = sp_block_dict_sp.astype(np.int16, copy=False)
        sp_max_gain_sp = np.amax(np.abs(sp_block_dict_sp[:,]))
        return sp_block_dict_sp, sp_max_gain_sp


