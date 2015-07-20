# -*- coding: utf-8 -*-
"""
Created on Fri Jun  5 10:31:01 2015

@author: Felix Pfreundtner
"""

import numpy as np
import scipy.io.wavfile
import pyaudio
import time
import math
import os
import collections
import threading
import queue


class DspOut:
    def __init__(self, state_init, fft_blocksize, hopsize):
        self.state = state_init
        # Number of all speakers
        self.spn = len(self.state.gui_sp)
        self.sp_binaural_block = [np.zeros((
            fft_blocksize, 2), dtype=np.float32) for sp in range(self.spn)]
        self.sp_binaural_block_out = [np.zeros((hopsize, 2), dtype=np.float32)
                                      for sp in range(self.spn)]
        self.sp_binaural_block_add = [np.zeros((fft_blocksize - hopsize, 2),
                                      dtype=np.float32) for sp in range(
            self.spn)]
        self.binaural_block = np.zeros((hopsize, 2), dtype=np.float32)
        self.binaural = np.zeros((fft_blocksize, 2), dtype=np.int16)
        self.continue_convolution = [True for sp in range(self.spn)]
        self.played_frames_end = 0
        self.played_block_counter = 0
        self.prior_played_block_counter = 0
        self.playbuffer = collections.deque()
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
        self.sp_binaural_block_out[sp] = self.sp_binaural_block[sp][
            0:hopsize, :]
        # 2. add relevant still remaining block output of prior ffts to
        # binaural block output of current block
        self.sp_binaural_block_out[sp][:, :] += \
            self.sp_binaural_block_add[sp][0:hopsize, :]
        # create a new array to save remaining block output of current fft
        # and add it to the still remaining block output of prior ffts
        # 1. create new array binaural_block_add_sp_new with size (
        # fft_blocksize - hopsize)
        add_sp_arraysize = (fft_blocksize - hopsize)
        sp_binaural_block_add_sp_new = np.zeros((add_sp_arraysize, 2),
                                                dtype=np.float32)
        # 2. take still remaining block output of prior ffts and add it to
        # the zero array on front position
        sp_binaural_block_add_sp_new[0:add_sp_arraysize - hopsize, :] = \
            self.sp_binaural_block_add[sp][hopsize:, :]
        # 3. take remaining block output of current fft and add it to the
        # array on back position
        sp_binaural_block_add_sp_new[:, :] += \
            self.sp_binaural_block[sp][hopsize:, :]
        self.sp_binaural_block_add[sp] = sp_binaural_block_add_sp_new

    # @brief Calculate the signal for all speakers taking into account the
    # distance to the speakers.
    # @author Felix Pfreundtner
    def mix_binaural_block(self, hopsize):
        self.binaural_block = np.zeros((hopsize, 2), dtype=np.float32)
        # maximum distance of a speaker to head in window with borderlength
        # 3.5[m] is sqrt(3.5^2+3.5^2)[m]=3.5*sqrt(2)
        # max([gui_sp[sp][1] for sp in gui_sp])
        distance_max = 3.5 * math.sqrt(2)
        for sp in range(self.spn):
            # get distance speaker to head from gui_sp
            distance_sp = self.state.gui_sp[sp]["distance"]
            # sound pressure decreases with distance 1/r
            sp_gain_factor = 1 - distance_sp / distance_max
            # add gained sp block output to a summarized block output of all
            # speakers
            self.binaural_block += self.sp_binaural_block_out[sp] * \
                sp_gain_factor / self.spn
            # if convolution for this speaker will be skipped on the
            # next iteration set binaural_block_out to zeros
            if self.continue_convolution[sp] is False:
                self.sp_binaural_block_out[sp] = np.zeros((hopsize, 2),
                                                          dtype=np.float32)
        self.binaural_block = self.binaural_block.astype(np.float32,
                                                         copy=False)

    # @brief Concatenates the current block to the binaural signal.
    # @author Felix Pfreundtner
    def add_to_queue(self, blockcounter):
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
    def writebinauraloutput(self, binaural, samplerate):
        if not os.path.exists("./audio_out/"):
            os.makedirs("./audio_out/")
        scipy.io.wavfile.write("./audio_out/binauralmix.wav", samplerate,
                               binaural)

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
        # start portaudio audio stream
        audiostream.start_stream()
        # as long as stream is active (enough input) or audiostream has been
        # stopped by user
        while audiostream.is_active() or audiostream.is_stopped():
            time.sleep(0.5)
            # handle playblack pause: stop portaudio audio playback again
            if self.state.dsp_pause is True:
                audiostream.stop_stream()
            # handle playblack continue: start portaudio audio playback again
            if audiostream.is_stopped() and self.state.dsp_pause is False:
                audiostream.start_stream()
            # handle playblack stop: break while loop
            if self.state.dsp_stop is True:
                break
        # stop portaudio playback
        audiostream.stop_stream()
        audiostream.close()
        pa.terminate()

        # if stop button was not pressed
        if self.state.dsp_stop is False:
            # when not the whole input has been convolved
            if any(self.continue_convolution) is True:
                self.state.send_error("Error PC to slow - Playback Stopped")
                # set playback to unsuccessful
                self.playback_successful = False

        # finally mark audio as not paused
        self.state.dsp_pause = False
        # finally mark audio as stopped
        self.state.dsp_stop = True
