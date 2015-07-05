# -*- coding: utf-8 -*-
"""
Created on Fri Jun  5 10:31:01 2015

@author: Felix Pfreundtner
"""

import numpy as np
from scipy.fftpack import fft, ifft, fftfreq
import scipy.io.wavfile
import pyaudio
import time
import math
import ntpath
import os
import collections
import threading
from copy import deepcopy
from error_handler import send_error
import queue

class DspOut:
    def __init__(self, gui_dict_init, fft_blocksize, sp_blocksize,
                 hopsize, gui_stop_init, gui_pause_init):
        self.binaural_block_dict = dict.fromkeys(gui_dict_init, np.zeros((
            fft_blocksize, 2), dtype=np.float32))
        self.binaural_block_dict_out = dict.fromkeys(gui_dict_init, np.zeros(
            (hopsize, 2), dtype=np.float32))
        self.binaural_block_dict_add = dict.fromkeys(gui_dict_init, np.zeros(
            (fft_blocksize - hopsize, 2), dtype=np.float32))
        self.binaural_block = np.zeros((hopsize, 2), dtype=np.float32)
        self.binaural = np.zeros((fft_blocksize, 2), dtype=np.int16)
        self.continue_convolution_dict = dict.fromkeys(gui_dict_init, True)
        self.gui_stop = gui_stop_init
        self.gui_pause = gui_pause_init
        self.played_frames_end = 0
        self.played_block_counter = 0
        self.prior_played_block_counter = 0
        self.playbuffer = collections.deque()
        self.lock = threading.Lock()
        self.playback_finished = False
        self.playback_successful = True
        self.playqueue = queue.Queue()


    # @brief Applies the overlap-add-method to the signal.
    # @details Adds the last part of the prior fft-block to calculate the
    # overlapp-values (which decrease the desharmonic sounds in the output
    # signal.)
    # @author Felix Pfreundtner
    def overlap_add(self, fft_blocksize, hopsize, sp):
        # get current binaural block output of sp
        # 1. take binaural block output of current fft which don't overlap
        # with next blocks
        self.binaural_block_dict_out[sp] = self.binaural_block_dict[sp][
                                           0:hopsize, :]
        # 2. add relevant still remaining block output of prior ffts to
        # binaural block output of current block
        self.binaural_block_dict_out[sp][:, :] += \
            self.binaural_block_dict_add[sp][0:hopsize, :]
        # create a new array to save remaining block output of current fft
        # and add it to the still remaining block output of prior ffts
        # 1. create new array binaural_block_dict_add_sp_new with size (
        # fft_blocksize - hopsize)
        add_sp_arraysize = (fft_blocksize - hopsize)
        binaural_block_dict_add_sp_new = np.zeros((add_sp_arraysize, 2),
                                                  dtype=np.float32)
        # 2. take still remaining block output of prior ffts and add it to
        # the zero array on front position
        binaural_block_dict_add_sp_new[0:add_sp_arraysize - hopsize,
                                       :] = \
            self.binaural_block_dict_add[sp][hopsize:, :]
        # 3. take remaining block output of current fft and add it to the
        # array on back position
        binaural_block_dict_add_sp_new[:, :] += \
            self.binaural_block_dict[sp][hopsize:, :]
        self.binaural_block_dict_add[sp] = binaural_block_dict_add_sp_new

    # @brief Calculate the signal for all speakers taking into account the
    # distance to the speakers.
    # @author Felix Pfreundtner
    def mix_binaural_block(self, hopsize, gui_dict):
        self.binaural_block = np.zeros((hopsize, 2), dtype=np.float32)
        # maximum distance of a speaker to head in window with borderlength
        # 3.5[m] is sqrt(3.5^2+3.5^2)[m]=3.5*sqrt(2)
        # max([gui_dict[sp][1] for sp in gui_dict])
        distance_max = 3.5 * math.sqrt(2)
        # get total number of speakers from gui_dict
        total_number_of_sp = len(gui_dict)
        for sp in self.binaural_block_dict_out:
            # get distance speaker to head from gui_dict
            distance_sp = gui_dict[sp][1]
            # sound pressure decreases with distance 1/r
            sp_gain_factor = 1 - distance_sp / distance_max
            # add gained sp block output to a summarized block output of all
            # speakers
            self.binaural_block += self.binaural_block_dict_out[sp] * \
                sp_gain_factor / total_number_of_sp
            # if convolution for this speaker will be skipped on the
            # next iteration set binaural_block_dict_out to zeros
            if self.continue_convolution_dict[sp] is False:
                self.binaural_block_dict_out[sp] = np.zeros((hopsize, 2),
                                                            dtype=np.float32)
        self.binaural_block = self.binaural_block.astype(np.float32, copy=False)


    # @brief Adds the newly calculated blocks to a dict that contains all the
    #  blocks calculated before.
    # @retval <binaural> A dict of all the output-blocks of the signal added
    #  to one another up to the current block.
    # another up to the current
    # @author Felix Pfreundtner
    def overlapp_add_window(self, binaural_block_dict_sp, blockcounter,
                            fft_blocksize, binaural):
        delay = 256
        if blockcounter == 0:
            binaural = np.zeros((fft_blocksize * 1500, 2), dtype=np.float32)
        if blockcounter % 2 != 0:
            binaural[blockcounter * delay:blockcounter * delay + 1024, 1] += \
                binaural_block_dict_sp
        else:
            binaural[blockcounter * delay:blockcounter * delay + 1024, 1] += \
                binaural_block_dict_sp
        return binaural

    # @brief Concatenates the current block to the binaural signal.
    # @author Felix Pfreundtner
    def add_to_binaural(self, blockcounter):
        # if blockcounter == 0:
        #     self.binaural = self.binaural_block.astype(np.int16, copy=False)
        #     q.put(self.binaural_block.astype(np.int16, copy=False))
        # else:
        #     self.binaural = np.concatenate((self.binaural,
        #                                     self.binaural_block.astype(
        #                                         np.int16, copy=False)))
        self.playqueue.put(self.binaural_block.astype(np.int16,
                                                      copy=False).tostring())

    # @brief Writes the binaural output signal.
    # @author Felix Pfreundtner
    def writebinauraloutput(self, binaural, wave_param_common, gui_dict):
        if not os.path.exists("./audio_out/"):
            os.makedirs("./audio_out/")
        scipy.io.wavfile.write("./audio_out/binauralmix.wav",
                               wave_param_common[0], binaural)

    # @brief
    # @author Felix Pfreundtner
    def callback(self, in_data, frame_count, time_info, status):
        if status:
            print("Playback Error: %i" % status)
        # played_frames_begin = self.played_frames_end
        # self.played_frames_end += frame_count
        if self.playqueue.empty() is False:
            data = self.playqueue.get()
            returnflag = pyaudio.paContinue
        else:
            data = bytes([0])
            returnflag = pyaudio.paComplete
        # data = self.binaural[played_frames_begin:self.played_frames_end, :]
        # print("Played Block: " + str(self.played_block_counter))
        self.played_block_counter += 1
        # print("Play: " + str(self.played_block_counter))
        return data, returnflag

    # @brief Streams the calculated files as a output signal.
    # @author Felix Pfreundtner
    def audiooutput(self, samplerate, hopsize):
        pa = pyaudio.PyAudio()
        audiostream = pa.open(format=pyaudio.paInt16,
                              channels=2,
                              rate=samplerate,
                              output=True,
                              frames_per_buffer=hopsize,
                              stream_callback=self.callback,
                              )
        audiostream.start_stream()
        while audiostream.is_active() or audiostream.is_stopped():
            time.sleep(1)
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
        # execute commands when when playback finished successfully
        if any(self.continue_convolution_dict.values()) is True and \
                self.gui_stop is False:
            print("Error PC to slow - Playback Stopped")
            for sp in self.continue_convolution_dict:
                # self.played_frames_end += sp_blocksize
                self.continue_convolution_dict[sp] = False
            self.playback_successful = False
        self.playback_finished = True
