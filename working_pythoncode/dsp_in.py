# -*- coding: utf-8 -*-
"""
Created on Fri Jun  5 10:30:53 2015

@author: Felix Pfreundtner
"""

import scipy.io.wavfile
import struct
import numpy as np
import math
import matplotlib.pyplot as plt
from dsp_signal_handler import DspSignalHandler

class DspIn:
    def __init__(self, gui_dict_init):
        self.sp_param = dict.fromkeys(gui_dict_init, [])
        self.hrtf_block_dict = dict.fromkeys(gui_dict_init, [])
        self.hrtf_max_gain_dict = dict.fromkeys(gui_dict_init, [])
        self.sp_max_gain_dict = dict.fromkeys(gui_dict_init, [])
        self.wave_blockbeginend_dict_list = dict.fromkeys(gui_dict_init, [])
        self.signal_dict = {}
        self.sp_block_dict = {}
        # Standard samplerate, sampledepth
        self.wave_param_common = [44100, 16]
        # Determine number of output blocks per second
        self.fft_blocksize = 1024
        self.hrtf_databases = ["kemar_full_normal_ear", "kemar_full_big_ear", "kemar_compact"]
        self.hrtf_database = self.hrtf_databases[0]
        self.kemar_inverse_filter, self.hrtf_blocksize = self.get_hrtf_param()
        # Number of Samples of HRTFs (KEMAR Compact=128, KEMAR Full=512)
        self.sp_blocksize, self.sp_blocktime, self.overlap = self.get_block_param(self.wave_param_common, self.hrtf_blocksize, self.fft_blocksize)
        # get samplerate from header in .wav-file of all speakers
        self.sp_param = self.initialize_get_block(gui_dict_init)
        self.block_begin_end = self.init_set_block_begin_end(gui_dict_init)
        self.hamming = self.buid_hamming_window(self.sp_blocksize)
        self.cosine = self.buid_cosine_window(self.sp_blocksize)
        self.hann = self.build_hann_window(self.sp_blocksize)


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
        overlap = (fft_blocksize-sp_blocksize)/fft_blocksize # in decimal 0.
        # overlap = 0
        return sp_blocksize, sp_blocktime, overlap


    # @author: Felix Pfreundtner
    def init_set_block_begin_end(self, gui_dict):
        block_begin_end=[int(-(self.sp_blocksize)*(1-self.overlap)),int((self.sp_blocksize)*(self.overlap))]
        return block_begin_end

    # @author: Felix Pfreundtner
    def set_block_begin_end(self):
        self.block_begin_end[0] = self.block_begin_end[0] + int(self.sp_blocksize*(1-self.overlap))
        self.block_begin_end[1] = self.block_begin_end[1] + int(self.sp_blocksize*(1-self.overlap))

    # @author: Felix Pfreundtner
    def get_hrtf_param(self):
        if self.hrtf_database == "kemar_full_normal_ear" or  self.hrtf_database == "kemar_full_big_ear":
            # wave hrtf size 512 samples: zeropad hrtf to 513 samples to reach even sp_blocksize which is integer divisible by 2 (50% overlap needed -> sp_blocksize/2)
            hrtf_blocksize = 513
            # get inverse minimum phase impulse response response of kemar measurement speaker optimus pro 7 and truncate to fft_blocksize
            _, kemar_inverse_filter = scipy.io.wavfile.read("./kemar/full/headphones+spkr/Opti-minphase.wav")
            kemar_inverse_filter = kemar_inverse_filter[0:self.fft_blocksize, ]
        if self.hrtf_database == "kemar_compact":
            # wave hrtf size 128 samples: zeropad hrtf to 129 samples to reach even sp_blocksize which is integer divisible by 2 (50% overlap needed -> sp_blocksize/2)
            hrtf_blocksize = 129
            # no inverse speaker impulse response of measurement speaker needed (is already integrated in wave files of kemar compact hrtfs)
            kemar_inverse_filter = np.zeros((self.fft_blocksize,), dtype = np.int16)
        return kemar_inverse_filter, hrtf_blocksize


    # @author: Felix Pfreundtner
    def get_hrtfs(self, gui_dict_sp, hrtf_database):
        if hrtf_database == "kemar_compact":
            # get filmename of the relevant hrtf
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

            # get samples of the relevant hrtf for each ear in numpy array (l,r)
            _, hrtf_input = scipy.io.wavfile.read(hrtf_filenames_dict_sp)
            hrtf_block_dict_sp = np.zeros((self.hrtf_blocksize, 2), dtype = np.int16)
            if gui_dict_sp[0] <= 180:
                hrtf_block_dict_sp[0:128,0] = hrtf_input
            else:
                hrtf_input[:,[0, 1]] = hrtf_input[:,[1, 0]]
                hrtf_block_dict_sp[0:128,0] = hrtf_input
            self.kemar_inv_filter = np.ones((1024,))
            hrtf_max_gain_sp=[]
            hrtf_max_gain_sp.append(np.amax(np.abs(hrtf_block_dict_sp[:, 0])))
            hrtf_max_gain_sp.append(np.amax(np.abs(hrtf_block_dict_sp[:, 1])))

        if hrtf_database == "kemar_full_normal_ear" or hrtf_database == "kemar_full_big_ear":
            # get filmename of the relevant hrtf for each ear
            rounddifference = gui_dict_sp[0] % 5
            if rounddifference == 0:
                azimuthangle_ear = self.rnd(gui_dict_sp[0])
            else:
                if rounddifference < 2.5:
                    azimuthangle_ear = self.rnd(gui_dict_sp[0] - rounddifference)
                else:
                    azimuthangle_ear = self.rnd(gui_dict_sp[0] + 5 - rounddifference)
            if azimuthangle_ear >= 180:
                azimuthangle_other_ear = azimuthangle_ear - 180
            else:
                azimuthangle_other_ear = azimuthangle_ear + 180

            if hrtf_database == "kemar_full_normal_ear":
                hrtf_filenames_dict_sp_l = "./kemar/full/elev0/L0e" + str(azimuthangle_ear).zfill(3) + "a.wav"
                hrtf_filenames_dict_sp_r = "./kemar/full/elev0/L0e" + str(azimuthangle_other_ear).zfill(3) + "a.wav"
            else:
                hrtf_filenames_dict_sp_r = "./kemar/full/elev0/R0e" + str(azimuthangle_ear).zfill(3) + "a.wav"
                hrtf_filenames_dict_sp_l = "./kemar/full/elev0/R0e" + str(azimuthangle_other_ear).zfill(3) + "a.wav"

            # get samples of the relevant hrtf for each ear in numpy array (l,r)
            _, hrtf_input_l = scipy.io.wavfile.read(hrtf_filenames_dict_sp_l)
            _, hrtf_input_r = scipy.io.wavfile.read(hrtf_filenames_dict_sp_r)
            hrtf_block_dict_sp = np.zeros((self.hrtf_blocksize, 2), dtype = np.int16)
            hrtf_block_dict_sp[0:512,0] = hrtf_input_l[:,]
            hrtf_block_dict_sp[0:512,1] = hrtf_input_r[:,]
            hrtf_max_gain_sp=[]
            hrtf_max_gain_sp.append(np.amax(np.abs(hrtf_block_dict_sp[:, 0])))
            hrtf_max_gain_sp.append(np.amax(np.abs(hrtf_block_dict_sp[:, 1])))
        return hrtf_block_dict_sp, hrtf_max_gain_sp


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


    # @author: Felix Pfreundtner
    def buid_hamming_window(self, sp_blocksize):
        N = sp_blocksize
        hamming_window = np.zeros((N,), dtype=np.float16)
        for n in range(N):
            hamming_window[n,] = 0.54 - 0.46*math.cos(2*math.pi*n/ (N+1))
        return hamming_window

    def build_hann_window(self, sp_blocksize):
        N = sp_blocksize
        hann_window = np.zeros((N,), dtype=np.float16)
        for n in range(N):
            hann_window[n,] = 0.5*(1 - math.cos(2*math.pi*n/(N)))
        add = np.zeros((2000,))
        return hann_window

    # @author: Felix Pfreundtner
    def buid_cosine_window(self, sp_blocksize):
        N = sp_blocksize
        cosine_window = np.zeros((N,), dtype=np.float16)
        for n in range(N):
            cosine_window[n,] = math.sin(math.pi*n / (N - 1))
        return cosine_window


    # @author: Felix Pfreundtner
    def apply_window(self, sp_block_sp, windowsignal):
        sp_block_sp = sp_block_sp * windowsignal
        sp_block_sp = sp_block_sp.astype(np.int16, copy=False)
        return sp_block_sp

    # @author: Matthias Lederle
    def initialize_get_block(self, gui_dict):
        properties_of_speakers = dict.fromkeys(gui_dict, [None] *7)
        for sp in gui_dict:
            file = open(gui_dict[sp][2], 'rb')
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
            # properties_of_speakers[sp][0] is number of samples
            properties_of_speakers[sp][3] = struct.unpack(fmt+"H", file.read(2))[0] #nochannels
            properties_of_speakers[sp][1] = struct.unpack(fmt+"I", file.read(4))[0] #samplerate
            file.seek(34)
            properties_of_speakers[sp][2] = struct.unpack(fmt+"H", file.read(2))[0] #bits
            #return samplerate, bits, nochannels
            file.seek(0)
            _big_endian = False
            # check endianness (whether file is RIFX or RIFF)
            str1 = file.read(4)
            if str1 == b'RIFX':
                _big_endian = True
            if _big_endian:
                properties_of_speakers[sp][4] = '>'
            else:
                properties_of_speakers[sp][4] = '<'
            # get to know where actual sample data begins and how big data-chunk is
            file.seek(36)
            counter = 0
            checkbytes = b'aaaa'
            # go to byte, where data actually starts
            while checkbytes != b'data':
                file.seek(-2, 1)
                checkbytes = file.read(4)
                counter += 1
                # print(checkbytes, counter)
            properties_of_speakers[sp][5] = struct.unpack(properties_of_speakers[sp][4] + 'i',
                                                          file.read(4))[0] # = data_chunk_size
            properties_of_speakers[sp][0] = int(properties_of_speakers[sp][5] /
                                               (properties_of_speakers[sp][
                                                    2]/8*properties_of_speakers[sp][3]))


            properties_of_speakers[sp][6] = 40 + (counter * 2) #no of total header_size
            file.close()

        return properties_of_speakers

    def get_block(self, filename, begin_block, end_block, properties_of_speakers_sp, blocklength):

        fmt = properties_of_speakers_sp[4]
        bits = properties_of_speakers_sp[2]
        nochannels = properties_of_speakers_sp[3]
        data_chunk_size = properties_of_speakers_sp[5]
        total_header_size = properties_of_speakers_sp[6]

        file = open(filename, 'rb')
        blocknumpy = np.zeros((blocklength, ), dtype = np.int16)
        end_of_file = False
        bitfactor = int(bits / 8)
        first_byte_of_block = total_header_size + (begin_block * bitfactor * nochannels)
        last_byte_of_block = total_header_size + (end_block * bitfactor * nochannels)
        last_byte_of_file = total_header_size + data_chunk_size
        file.seek(first_byte_of_block)
        # choose correct specifier depending on bits/sample
        if bitfactor == 1:
            specifier = "B"
        elif bitfactor == 2:
            specifier = "h"
        else:
            print("Specifier for this number of bits/sample is not defined!")
        # if mono, write blocknumpy
        if nochannels == 1:
            if last_byte_of_block < last_byte_of_file:
                i = 0
                while i < blocklength:
                    blocknumpy[i, ] = struct.unpack(fmt + specifier, file.read(bitfactor))[0]
                    i += 1
            else: #last block to be filled individually
                remaining_samples = int((last_byte_of_file - first_byte_of_block)/(bitfactor*nochannels))
                i = 0
                while i < remaining_samples:
                    blocknumpy[i, ] = struct.unpack(fmt + specifier, file.read(bitfactor))[0]
                    i += 1
                end_of_file = True
        # If stereo, make mono and write blocknumpy
        elif nochannels == 2:
            # First: Write left and right signal in independent lists
            samplelist_of_one_block_left = []
            samplelist_of_one_block_right = []
            remaining_samples = 10000  # random value that cant be reached by (data_chunk_size - current_last_byte, see below)
            if last_byte_of_block < last_byte_of_file:
                i = 0
                while i < blocklength:
                    left_int = struct.unpack(fmt + specifier, file.read(bitfactor))[0]
                    right_int = struct.unpack(fmt + specifier, file.read(bitfactor))[0]
                    samplelist_of_one_block_left.append(left_int)
                    samplelist_of_one_block_right.append(right_int)
                    i += 1
            else:  # (if current_last_byte >= data_chunk_size:
                remaining_samples = int((last_byte_of_file - first_byte_of_block)/(bitfactor*nochannels))
                i = 0
                while i < remaining_samples:
                    left_int = struct.unpack(fmt + specifier, file.read(bitfactor))[0]
                    right_int = struct.unpack(fmt + specifier, file.read(bitfactor))[0]
                    samplelist_of_one_block_left.append(left_int)
                    samplelist_of_one_block_right.append(right_int)
                    i += 1
                end_of_file = True

            # Second: Interpolate and merge the two lists and write in blocknumpy
            if remaining_samples == 10000:
                i = 0
                while i < blocklength:
                    mean_value = int((samplelist_of_one_block_left[i] + samplelist_of_one_block_right[i]) / 2)
                    blocknumpy[i, ] = mean_value
                    i += 1
            else:
                i = 0
                while i < remaining_samples:
                    mean_value = int((samplelist_of_one_block_left[i] + samplelist_of_one_block_right[i]) / 2)
                    blocknumpy[i, ] = mean_value
                    i += 1
                end_of_file = True
        else:
            print("Signal is neither mono nor stereo (nochannels != 1 or 2) and can't be processed!")

        file.close()

        return blocknumpy#, end_of_file <-- will be added later!!!