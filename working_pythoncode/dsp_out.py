# -*- coding: utf-8 -*-
"""
Created on Fri Jun  5 10:31:01 2015

@author: Felix Pfreundtner
"""

import numpy as np
from scipy.fftpack import fft, ifft
import scipy.io.wavfile
import pyaudio
import time
import math
import ntpath
import os
import collections
import threading

class DspOut:
    def __init__(self, gui_dict_init, fft_blocksize, sp_blocksize):
        self.binaural_block_dict = dict.fromkeys(gui_dict_init, np.zeros((fft_blocksize, 2)))
        self.binaural_block = np.zeros((fft_blocksize, 2), dtype=np.int16)
        self.binaural_dict = dict.fromkeys(gui_dict_init, np.zeros((fft_blocksize, 2)))
        self.binaural = np.zeros((fft_blocksize, 2), dtype=np.int16)
        self.testoutput = np.ones((fft_blocksize, 2), dtype=np.int16)*30000
        self.played_frames_end = 0
        self.continue_convolution_list = dict.fromkeys(gui_dict_init, [])
        self.continue_convolution_dict = dict.fromkeys(gui_dict_init, True)
        self.get_new_block = True
        self.binaural_block_add = np.zeros((sp_blocksize, 2), dtype=np.int16)
        self.play_counter = 0
        self.playbuffer = collections.deque()
        self.lock = threading.Lock()

    # @author: Felix Pfreundtner
    def fft_convolve(self, sp_block_sp, hrtf_block_sp_l_r, fft_blocksize):

        # Do for speaker sp zeropadding: zeropad hrtf (left or right input) and speaker (mono input)
        hrtf_zeros = np.zeros((fft_blocksize-len(hrtf_block_sp_l_r), ), dtype = 'int16')
        hrtf_block_sp_zeropadded = np.concatenate((hrtf_block_sp_l_r, hrtf_zeros))
        sp_zeros = np.zeros((fft_blocksize-len(sp_block_sp), ), dtype = 'int16')
        sp_block_sp_zeropadded = np.concatenate((sp_block_sp, sp_zeros))

        # bring time domain input to to frequency domain
        hrtf_block_sp_frequency = fft(hrtf_block_sp_zeropadded, fft_blocksize)
        sp_block_sp_frequency = fft(sp_block_sp_zeropadded, fft_blocksize)

        # execute convulotion of speaker input and hrtf input: multiply complex frequency domain vectors
        binaural_block_sp_frequency = sp_block_sp_frequency * hrtf_block_sp_frequency

        # bring multiplied spectrum back to time domain, disneglected small complex time parts resulting from numerical fft approach
        binaural_block_sp = ifft(binaural_block_sp_frequency, fft_blocksize).real

        return binaural_block_sp


    # @author: Felix Pfreundtner
    def apply_hamming_window(self, inputsignal):
        hamming_window = [0.53836 - 0.46164*math.cos(2*math.pi*t/(len(inputsignal) - 1)) for t in range(len(inputsignal))]
        hamming_window = np.asarray(hamming_window, dtype=np.float64)
        inputsignal = inputsignal * hamming_window
        return inputsignal



    # @author: Felix Pfreundtner
    def bit_int(self, binaural_dict):
        binaural_dict_scaled={}
        for sp in binaural_dict:
            binaural_dict_scaled[sp] = np.zeros((len(binaural_dict[sp]), 2), dtype=np.int16)
            for l_r in range(2):
                maximum_amplitude=np.amax(np.abs(binaural_dict[sp][:, l_r]))
                if maximum_amplitude != 0:
                    binaural_dict_scaled[sp][:, l_r] = binaural_dict[sp][:, l_r]/maximum_amplitude*32767
                    binaural_dict_scaled[sp] = binaural_dict_scaled[sp].astype(np.int16, copy=False)

        return binaural_dict_scaled

    # @author: Felix Pfreundtner
    def add_to_binaural_dict(self, binaural_block_dict, binaural_dict, begin_block):
        outputsignal_sample_number = len(binaural_dict)
        binaural_dict[begin_block : outputsignal_sample_number, :] += binaural_block_dict[0 : (outputsignal_sample_number - begin_block), :]
        binaural_dict=np.concatenate((binaural_dict, binaural_block_dict[(outputsignal_sample_number - begin_block):, :]))

        return binaural_dict, outputsignal_sample_number

    # @author: Felix Pfreundtner
    def writebinauraloutput(self, binaural_dict_scaled, wave_param_common, gui_dict):
        if not os.path.exists("./audio_out/"):
            os.makedirs("./audio_out/")
        for sp in binaural_dict_scaled:
            scipy.io.wavfile.write("./audio_out/binaural" + ntpath.basename(gui_dict[sp][2]), wave_param_common[0], binaural_dict_scaled[sp])

    # @author: Felix Pfreundtner
    def sp_gain_factor(self, distance_sp, distance_max):
        # sound pressure decreases with distance 1/r
        sp_gain_factor = 1 - distance_sp/distance_max
        return sp_gain_factor

    # @author: Felix Pfreundtner
    def mix_binaural_block(self, binaural_block_dict, binaural_block, gui_dict, wave_block_maximum_amplitude_dict):
        binaural_block = np.zeros((len(binaural_block), 2))

        # maximum distance of a speaker to head in window with borderlength 3.5[m] is sqrt(3.5^2+3.5^2)[m]=3.5*sqrt(2)
        distance_max = 3.5*math.sqrt(2) # max([gui_dict[sp][1] for sp in gui_dict])
        total_number_of_sp = len(gui_dict)
        for sp in binaural_block_dict:
            # normalize to have the maximum int16 amplitude
            if gui_dict[sp][3] == True:
                maximum_amplitude = 32767
            # take maximum amplitude of original wave file of sp block
            else:
                maximum_amplitude = wave_block_maximum_amplitude_dict[sp]
            # get maximum amplitude of convoluted sp + hrtf block
            maximum_amplitude_binaural_block = np.amax(np.abs(binaural_block_dict[sp]))
            if maximum_amplitude_binaural_block != 0:
                binaural_block_dict[sp] = binaural_block_dict[sp] / maximum_amplitude_binaural_block * maximum_amplitude
            # add sp block output to a common block output
            binaural_block += binaural_block_dict[sp]*self.sp_gain_factor(gui_dict[sp][1], distance_max) / total_number_of_sp
        binaural_block = binaural_block.astype(np.int16, copy=False)
        return binaural_block

    # @author: Felix Pfreundtner
    def add_to_binaural(self, binaural_block, binaural, begin_block):
        outputsignal_sample_number = len(binaural)
        binaural[begin_block : outputsignal_sample_number, :] += binaural_block[0 : (outputsignal_sample_number - begin_block), :]
        binaural=np.concatenate((binaural, binaural_block[(outputsignal_sample_number - begin_block):, :]))
        return binaural

    # @author: Felix Pfreundtner
    def callback(self, in_data, frame_count, time_info, status):
        if status:
            print("Playback Error: %i" % status)
        played_frames_begin = self.played_frames_end
        self.played_frames_end += frame_count
        print("Played Block: " + str(int(played_frames_begin/frame_count)))
        self.lock.acquire()
        try:
            data = self.binaural[played_frames_begin:self.played_frames_end, :]
            # data = self.binaural_block_add
        finally:
            self.lock.release()

        print("Played Block: " + str(self.play_counter))
        self.play_counter+=1
        return data, pyaudio.paContinue

    # @author: Felix Pfreundtner
    def audiooutput(self, channels, samplerate, sp_blocksize):
        pa = pyaudio.PyAudio()
        audiostream = pa.open(format = pyaudio.paInt16,
                              channels = channels,
                              rate = samplerate,
                              output = True,
                              frames_per_buffer = sp_blocksize,
                              stream_callback = self.callback,
                              )
        audiostream.start_stream()
        while audiostream.is_active():
            time.sleep(sp_blocksize/samplerate)
        audiostream.stop_stream()
        audiostream.close()
        pa.terminate()
        if any(self.continue_convolution_dict.values()) == True:
            print("Error PC to slow - Playback Stopped")
            for sp in self.continue_convolution_dict:
                #self.played_frames_end += sp_blocksize
                self.continue_convolution_dict[sp] = False
        # return continue_convolution_dict
