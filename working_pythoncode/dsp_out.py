# -*- coding: utf-8 -*-
"""
Created on Fri Jun  5 10:31:01 2015

@author: Felix Pfreundtner
"""

import numpy as np
from scipy.fftpack import fft, ifft, fftfreq
import scipy.io.wavfile
import pyaudio
import matplotlib.pyplot as plt
import time
import math
import ntpath
import os
import collections
import threading
from copy import deepcopy

class DspOut:
    def __init__(self, gui_dict_init, fft_blocksize, sp_blocksize,
                 hopsize, gui_stop_init, gui_pause_init):
        self.sp_spectrum_dict = dict.fromkeys(gui_dict_init, np.zeros((
            fft_blocksize/2, 2), dtype=np.float16))
        self.hrtf_spectrum_dict = dict.fromkeys(gui_dict_init,[ np.zeros((fft_blocksize/2, 2), dtype=np.float16),  np.zeros((fft_blocksize/2, 2), dtype=np.float16)])
        self.binaural_block_dict = dict.fromkeys(gui_dict_init, np.zeros((
            fft_blocksize, 2), dtype=np.int16))
        self.binaural_block_dict_out = dict.fromkeys(gui_dict_init,
            np.zeros((hopsize, 2), dtype=np.int16))
        self.binaural_block_dict_add = dict.fromkeys(gui_dict_init,
            np.zeros((fft_blocksize - hopsize, 2), dtype=np.int16))
        self.binaural_block = np.zeros((sp_blocksize, 2), dtype=np.int16)
        self.binaural = np.zeros((fft_blocksize, 2), dtype=np.int16)
        self.continue_convolution_dict = dict.fromkeys(gui_dict_init, True)
        self.gui_stop = gui_stop_init
        self.gui_pause = gui_pause_init
        self.played_frames_end = 0
        self.continue_convolution_list = dict.fromkeys(gui_dict_init, [])
        self.play_counter = 0
        self.playbuffer = collections.deque()
        self.lock = threading.Lock()

    # @author: Felix Pfreundtner
    def fft_convolve(self, sp_block_sp, hrtf_block_sp_l_r, fft_blocksize,
                     sp_max_gain_sp, hrtf_max_gain_sp_l_r, samplerate,
                     inverse_filter_active, kemar_inverse_filter,
                     hrtf_blocksize, sp_blocksize, sp, l_r):

        # Do for speaker sp zeropadding: zeropad hrtf (left or right input)
        # and speaker (mono input)
        hrtf_block_sp_zeropadded = np.zeros((fft_blocksize, ), dtype=np.int16)
        hrtf_block_sp_zeropadded[0:hrtf_blocksize, ] = hrtf_block_sp_l_r
        sp_block_sp_zeropadded = np.zeros((fft_blocksize, ), dtype = 'int16')
        sp_block_sp_zeropadded[0:sp_blocksize, ] = sp_block_sp

        # bring time domain input to to frequency domain
        hrtf_block_sp_fft = fft(hrtf_block_sp_zeropadded, fft_blocksize)
        sp_block_sp_fft = fft(sp_block_sp_zeropadded, fft_blocksize)

        # save fft magnitude spectrum of sp_block in sp_spectrum and
        # hrtf_block in hrtf_spectrum to be shown by gui
        # create array of all calculated FFT frequencies
        freq_all = fftfreq(fft_blocksize, 1/samplerate)
        # set position of only positive frequencies (neg. frequencies redundant)
        position_freq = np.where(freq_all>=0)
        # set array of only positive FFT frequencies (neg. frequ. redundant)
        freqs = freq_all[position_freq]
        self.sp_spectrum_dict[sp][:, 0] = freqs
        self.hrtf_spectrum_dict[sp][l_r][:, 0] = freqs
        # get magnitued spectrum of sp_block
        sp_magnitude_spectrum = abs(sp_block_sp_fft[position_freq])
        # normalize spectrum to get int16 values
        max_amplitude_output = 32767
        max_amplitude_sp_magnitude_spectrum = np.amax(np.abs(
            sp_magnitude_spectrum))
        if max_amplitude_sp_magnitude_spectrum != 0:
            # get magnitude spectrum of hrtf block
            self.sp_spectrum_dict[sp][:, 1] = sp_magnitude_spectrum / (
                max_amplitude_sp_magnitude_spectrum / sp_max_gain_sp *
                max_amplitude_output)
        hrtf_magnitude_spectrum = abs(hrtf_block_sp_fft[position_freq])
        max_amplitude_hrtf_magnitude_spectrum = np.amax(np.abs(
            hrtf_magnitude_spectrum))
        if max_amplitude_hrtf_magnitude_spectrum != 0:
            self.hrtf_spectrum_dict[sp][l_r][:, 1] =  hrtf_magnitude_spectrum / (max_amplitude_hrtf_magnitude_spectrum / hrtf_max_gain_sp_l_r * max_amplitude_output)
        self.sp_spectrum_dict[sp][0, 1] = 0
        self.hrtf_spectrum_dict[sp][l_r][0, 1] = 0

        # execute convolution of speaker input and hrtf input: multiply
        # complex frequency domain vectors
        binaural_block_sp_frequency = sp_block_sp_fft * hrtf_block_sp_fft

        # if kemar full is selected furthermore convolve with (approximated
        #  1024 samples) inverse impulse response of optimus pro 7 speaker
        if inverse_filter_active:
            binaural_block_sp_frequency = binaural_block_sp_frequency * fft(
                kemar_inverse_filter, fft_blocksize)

        # bring multiplied spectrum back to time domain, disneglected small
        # complex time parts resulting from numerical fft approach
        binaural_block_sp_time  = ifft(binaural_block_sp_frequency,
                                       fft_blocksize).real

        # normalize multiplied spectrum back to 16bit integer, consider
        # maximum amplitude value of sp black and hrtf impulse to get
        # dynamical volume output
        binaural_block_sp_max_gain = 26825636157874 # int(np.amax(np.abs(
        # binaural_block_sp))) # 421014006*10 #
        binaural_block_sp_time = binaural_block_sp_time / (
            binaural_block_sp_max_gain / sp_max_gain_sp /
            hrtf_max_gain_sp_l_r * 32767)
        self.binaural_block_dict[sp][:, l_r] = binaural_block_sp_time.astype(
            np.int16, copy=False)

    # @author: Felix Pfreundtner
    def overlap_add (self, binaural_block_dict_sp, binaural_block_dict_add_sp, fft_blocksize, hopsize):
        binaural_block_dict_out_sp = deepcopy(binaural_block_dict_sp[0:hopsize, :])
        binaural_block_dict_out_sp[:, :] += \
            deepcopy(binaural_block_dict_add_sp[0:hopsize, :])
        add_sp_arraysize = (fft_blocksize - hopsize)
        binaural_block_dict_add_sp_new = np.zeros((add_sp_arraysize, 2), dtype = np.int16)
        binaural_block_dict_add_sp_new[0:add_sp_arraysize - hopsize, :] = deepcopy(binaural_block_dict_add_sp[hopsize:, :])
        binaural_block_dict_add_sp_new[:, :] += deepcopy(binaural_block_dict_sp[hopsize:, :])
        return binaural_block_dict_out_sp, binaural_block_dict_add_sp_new

    # @author: Felix Pfreundtner
    def mix_binaural_block(self, binaural_block_dict_out, hopsize,
                           gui_dict):
        binaural_block = np.zeros((hopsize, 2))
        # maximum distance of a speaker to head in window with borderlength
        # 3.5[m] is sqrt(3.5^2+3.5^2)[m]=3.5*sqrt(2)
        # max([gui_dict[sp][1] for sp in gui_dict])
        distance_max = 3.5 * math.sqrt(2)
        # get total number of speakers from gui_dict
        total_number_of_sp = len(gui_dict)
        for sp in binaural_block_dict_out:
            # get distance speaker to head from gui_dict
            distance_sp = gui_dict[sp][1]
            # sound pressure decreases with distance 1/r
            sp_gain_factor = 1 - distance_sp/distance_max
            # add gained sp block output to a summarized block output of all
            #  speakers
            binaural_block += binaural_block_dict_out[sp] * sp_gain_factor / \
                              total_number_of_sp
        binaural_block = binaural_block.astype(np.int16, copy=False)
        return binaural_block

    # Testfunction overlap
    def overlapp_add_window(self, binaural_block_dict_sp, blockcounter,
                            fft_blocksize, binaural):
        delay = 256
        if blockcounter == 0:
            binaural = np.zeros((fft_blocksize*1500, 2), dtype=np.int16)
        if blockcounter % 2 != 0:
            binaural[blockcounter * delay:blockcounter * delay + 1024, 1] += \
                binaural_block_dict_sp
        else:
            binaural[blockcounter * delay:blockcounter * delay + 1024, 1] += \
                binaural_block_dict_sp
        return binaural

    # @author: Felix Pfreundtner
    def add_to_binaural(self, binaural, binaural_block, blockcounter):
        if blockcounter == 0:
            binaural = binaural_block
        else:
            binaural = np.concatenate((binaural, binaural_block))
        return binaural

    # @author: Felix Pfreundtner
    def writebinauraloutput(self, binaural, wave_param_common, gui_dict):
        if not os.path.exists("./audio_out/"):
            os.makedirs("./audio_out/")
        scipy.io.wavfile.write("./audio_out/binauralmix.wav",
                               wave_param_common[0], binaural)


    # @author: Felix Pfreundtner
    def callback(self, in_data, frame_count, time_info, status):
        if status:
            print("Playback Error: %i" % status)
        played_frames_begin = self.played_frames_end
        self.played_frames_end += frame_count
        self.lock.acquire()
        try:
            data = self.binaural[played_frames_begin:self.played_frames_end, :]
        finally:
            self.lock.release()
        print("Played Block: " + str(self.play_counter))
        self.play_counter+=1
        return data, pyaudio.paContinue

    # @author: Felix Pfreundtner
    def audiooutput(self, channels, samplerate, hopsize):
        pa = pyaudio.PyAudio()
        audiostream = pa.open(format = pyaudio.paInt16,
                              channels = channels,
                              rate = samplerate,
                              output = True,
                              frames_per_buffer = hopsize,
                              stream_callback = self.callback,
                              )
        audiostream.start_stream()
        while audiostream.is_active() or audiostream.is_stopped():
            time.sleep(0.1)
            # handle playback pause
            if self.gui_pause is True:
                audiostream.stop_stream()
            if audiostream.is_stopped() and self.gui_pause is False:
                audiostream.start_stream()
            # handle playblack stop
            if self.gui_stop is True:
                break
        audiostream.stop_stream()
        audiostream.close()
        pa.terminate()
        if any(self.continue_convolution_dict.values()) is True and \
                        self.gui_stop is False:
            print("Error PC to slow - Playback Stopped")
            for sp in self.continue_convolution_dict:
                #self.played_frames_end += sp_blocksize
                self.continue_convolution_dict[sp] is False
        # return continue_convolution_dict
