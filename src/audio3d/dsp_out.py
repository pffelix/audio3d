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
import queue
import pkg_resources


class DspOut:
    """
    H1 -- DspOut
    ************************
    **Contains all Dsp-functions executed after the convolution in the
    dsp.run function.**
    """
    def __init__(self, state_init, fft_blocksize, hopsize):
        self.binaural_block_dict = {sp: np.zeros((
            fft_blocksize, 2), dtype=np.float32) for sp in range(len(
                state_init.gui_sp_dict))}
        self.binaural_block_dict_out = dict.fromkeys(
            state_init.gui_sp_dict, np.zeros((hopsize, 2), dtype=np.float32))
        self.binaural_block_dict_add = dict.fromkeys(
            state_init.gui_sp_dict, np.zeros((fft_blocksize - hopsize, 2),
                                          dtype=np.float32))
        self.binaural_block = np.zeros((hopsize, 2), dtype=np.float32)
        self.binaural = np.zeros((fft_blocksize, 2), dtype=np.int16)
        self.continue_convolution_dict = dict.fromkeys(
            state_init.gui_sp_dict, True)
        self.played_frames_end = 0
        self.played_block_counter = 0
        self.prior_played_block_counter = 0
        self.playbuffer = collections.deque()
        self.lock = threading.Lock()
        self.playback_finished = False
        self.playback_successful = True
        self.playqueue = queue.Queue()

    def overlap_add(self, fft_blocksize, hopsize, sp):
        """
        H2 --
        ===================
        **Applies the overlap-add-method to the signal.**

        Adds the last part of the prior fft-block to calculate the
        overlapp-values (which decrease the desharmonic sounds in the
        output signal.)

        Author: Felix Pfreundtner
        """
        # get current binaural block output of sp
        # 1. take binaural block output of current fft which don't overlap
        # with next blocks
        self.binaural_block_dict_out[sp] = self.binaural_block_dict[sp][
            0:hopsize, :]
        # 2. add relevant still remaining block output of prior ffts to
        # binaural block output of current block

        self.sp_binaural_block_out[sp] += \
            self.sp_binaural_block_add[sp][0:hopsize, :]
        # check if overlap add led to a amplitude higher than int16 max:
        sp_binaural_block_out_sp_max_amp = np.amax(np.abs(
            self.sp_binaural_block_out[sp]))
        # if yes normalize maximum output amplitude to maximum int16 range to
        #  prevent uncontrolled clipping
        if sp_binaural_block_out_sp_max_amp > 32767:
                self.sp_binaural_block_out[sp] /=  \
                    sp_binaural_block_out_sp_max_amp * 32767
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

    def mix_binaural_block(self, hopsize, gui_sp_dict):
        """
        H2 -- mix_binaural_block
        ===================
        ***Calculate the signal for all speakers taking into account the
        distance to the speakers.**

        Author: Felix Pfreundtner
        """
        self.binaural_block = np.zeros((hopsize, 2), dtype=np.float32)
        # maximum distance of a speaker to head in window with borderlength
        # 3.5[m] is sqrt(3.5^2+3.5^2)[m]=3.5*sqrt(2)
        # max([gui_sp_dict[sp][1] for sp in gui_sp_dict])
        distance_max = 3.5 * math.sqrt(2)
        # get total number of speakers from gui_sp_dict
        total_number_of_sp = len(gui_sp_dict)
        for sp in self.binaural_block_dict_out:
            # get distance speaker to head from gui_sp_dict
            distance_sp = gui_sp_dict[sp][1]
            # sound pressure decreases with distance 1/r
            sp_gain_factor = 1 - distance_sp / distance_max
            # add gained sp block output to a summarized block output of all
            # speakers
            self.binaural_block += self.binaural_block_dict_out[sp] * \
                sp_gain_factor / total_number_of_sp
            # if convolution for this speaker will be skipped on the
            # next iteration set binaural_block_out to zeros
            if self.continue_convolution[sp] is False:
                self.sp_binaural_block_out[sp] = np.zeros((hopsize, 2),
                                                          dtype=np.float32)
        sp_binaural_block_sp_time_max_amp = np.amax(np.abs(
            self.sp_binaural_block_out[sp][:, :]))
        if sp_binaural_block_sp_time_max_amp > 35000:
            print(sp_binaural_block_sp_time_max_amp)

    # @brief sends the created binaural block of the dsp thread to the play
    # thread with the playqueue
    # @author Felix Pfreundtner
    def add_to_playqueue(self):
        self.playqueue.put(self.binaural_block.astype(np.int16,
                                                      copy=False).tostring())

    # @brief sends the created binaural block of the dsp thread to the record
    #  queue, which collects all cretaed binaural blocks. Later the queue is
    #  read by writerecordfile().
    # @author Felix Pfreundtner
    def add_to_recordqueue(self):
        self.recordqueue.put(self.binaural_block.astype(np.int16,
                                                        copy=False))

    def callback(self, in_data, frame_count, time_info, status):
        """
        H2 -- callback
        ===================

        Author: Felix Pfreundtner
        """
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
        """
        H2 -- audiooutput
        ===================
        **Streams the calculated files as a output signal.**

        Author: Felix Pfreundtner
        """
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
            if self.dsp_pause is True:
                audiostream.stop_stream()
            if audiostream.is_stopped() and self.dsp_pause is False:
                audiostream.start_stream()
            # handle playblack stop
            if self.dsp_stop is True:
                break
        audiostream.stop_stream()
        audiostream.close()
        pa.terminate()
<<<<<<< HEAD:working_pythoncode/dsp_out.py
        # execute commands when when playback finished successfully
        if any(self.continue_convolution_dict.values()) is True and \
                self.dsp_stop is False:
            print("Error PC to slow - Playback Stopped")
            for sp in self.continue_convolution_dict:
                # self.played_frames_end += sp_blocksize
                self.continue_convolution_dict[sp] = False
            self.playback_successful = False
        self.playback_finished = True
=======

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

    # @brief Writes the whole binaural output as wave file.
    # @author Felix Pfreundtner
    def writerecordfile(self, samplerate, hopsize):
        #if not os.path.exists(pkg_resources.resource_filename("audio3d",
                                                              #"audio_out/")):
            #os.makedirs(pkg_resources.resource_filename("audio3d",
                                                        #"audio_out/"))

        binaural_record = np.zeros((self.recordqueue.qsize() * hopsize, 2),
                                   dtype=np.int16)
        position = 0
        while self.recordqueue.empty() is False:
                binaural_record[position:position+hopsize, :] = \
                    self.recordqueue.get()
                position += hopsize
        self.state.send_error("Audio Recorded to File: " +
                              pkg_resources.resource_filename("audio3d",
                              "audio_out/binauralmix.wav"))
        scipy.io.wavfile.write(pkg_resources.resource_filename("audio3d",
                               "audio_out/binauralmix.wav"), samplerate,
                               binaural_record)
>>>>>>> 584e0e63cd6f7d7bbc59a009febc59d381e39513:src/audio3d/dsp_out.py
