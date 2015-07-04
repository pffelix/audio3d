# -*- coding: utf-8 -*-
"""
Created on Fri May 22 16:27:57 2015

@author: Felix Pfreundtner
"""

import numpy as np
import dsp_in
import dsp_out
import threading
import multiprocessing
import time
import matplotlib.pyplot as plt


class Dsp:
    def __init__(self, state,
                 gui_settings_dict_init, return_ex_init):
        self.state = state
        self.gui_dict = state.gui_dict
        self.gui_settings_dict = gui_settings_dict_init
        self.prior_head_angle_dict = dict.fromkeys(state.gui_dict, [])
        self.return_ex = return_ex_init
        self.outputsignal_sample_number = dict.fromkeys(state.gui_dict, [])
        # Set number of bufferblocks between fft block convolution and audio
        # block playback
        self.bufferblocks = gui_settings_dict_init["bufferblocks"]
        # Create Input Object which contains mono input samples of sources
        # and hrtf impulse responses samples
        self.dspin_obj = dsp_in.DspIn(state.gui_dict, gui_settings_dict_init)
        # Create Output Object which contains binaural output samples
        self.dspout_obj = dsp_out.DspOut(state.gui_dict,
                                         self.dspin_obj.fft_blocksize,
                                         self.dspin_obj.sp_blocksize,
                                         self.dspin_obj.hopsize,
                                         state.gui_stop, state.gui_pause)
        # magnitude spectrum of current wave block for every speaker
        self.sp_spectrum_dict = dict.fromkeys(state.gui_dict, np.zeros((
            self.dspin_obj.fft_blocksize // 2 + 1, 2), dtype=np.float16))
        # magnitude spectrum of current left and right hrtf for every speaker
        self.hrtf_spectrum_dict = dict.fromkeys(state.gui_dict, [np.zeros((
            self.dspin_obj.fft_blocksize // 2 + 1, 2), dtype=np.float16),
            np.zeros((self.dspin_obj.fft_blocksize // 2 + 1, 2),
                     dtype=np.float16)])
        # Blockcounter initialized to count number of already convolved
        # blocks
        self.blockcounter = 0

    # @brief Runs the dsp algorithm as one process on one cpu core.
    # @details
    # @author Felix Pfreundtner, Matthias Lederle
    def run(self):
        # tell gui that dsp algorithm is running
        self.state.dsp_run = True
        # run the main while loop as long as there are still samples to be
        # read from speaker wave files
        while any(self.dspout_obj.continue_convolution_dict.values()) \
                is True:
            # actualize variables with gui
            self.dspout_obj.gui_stop = self.state.gui_stop
            self.dspout_obj.gui_pause = self.state.gui_pause
            # print the number of already done FFT / Block iterations
            # print("FFT Block " + str(self.blockcounter) + ":")
            # set the begin and end of the speaker wave block which needs to
            # be read in this iteration
            self.dspin_obj.set_block_begin_end()
            # iterate over all active speakers sp
            for sp in self.gui_dict:
                # if speaker wave file still has unread samples start
                # convolution, else skip convolution
                if self.dspout_obj.continue_convolution_dict[sp] is True:
                    # check whether head position to speaker sp has changed
                    if self.gui_dict[sp][0] != self.prior_head_angle_dict[sp]:
                        # if yes, load new fitting hrtf frequency values
                        self.dspin_obj.get_hrtf_block_fft(self.gui_dict[sp], sp)
                        # save head position to speaker of this block in
                        # prior_head_angle_dict
                        self.prior_head_angle_dict[sp] = self.gui_dict[sp][0]

                    # Load wave block of speaker sp with speaker_blocksize (
                    # fft_blocksize-hrtf_blocksize+1) and current block
                    # begin_end
                    self.dspout_obj.continue_convolution_dict[sp] = \
                        self.dspin_obj.get_sp_block(sp)
                    # plt.plot(self.dspin_obj.sp_block_dict[sp])
                    # plt.show()

                    # normalize sp block if requested
                    self.dspin_obj.normalize(self.gui_dict[sp][3], sp)

                    # apply window to sp input in sp_block_dict
                    self.dspin_obj.apply_window_on_sp_block(sp)
                    # for the left and the right ear channel
                    for l_r in range(2):
                        # convolve hrtf with speaker block input to get
                        # binaural stereo block output
                        self.dspout_obj.binaural_block_dict[sp], \
                        self.sp_spectrum_dict[sp],\
                        self.hrtf_spectrum_dict[sp][l_r] = \
                        self.dspin_obj.fft_convolution(self.sp_spectrum_dict
                                                       [sp],
                                                       self.hrtf_spectrum_dict[
                                                           sp][l_r],
                                                       self.dspout_obj.
                                                       binaural_block_dict[
                                                           sp], sp, l_r)
                        # model speaker position change about 1° per block
                        # (0.02s) in
                        # clockwise rotation
                        # self.gui_dict[sp][0]+=30
                        # if self.gui_dict[sp][0] >= 360:
                        # self.gui_dict[sp][0] -= 360

                        # overlap and add binaural stereo block output of
                        # speaker sp
                        #  to prior binaural stereo block output of speaker sp
                    self.dspout_obj.overlap_add(
                        self.dspin_obj.fft_blocksize,
                        self.dspin_obj.hopsize, sp)

            # Mix binaural stereo blockoutput of every speaker to one
            # binaural stereo block output having regard to speaker distances
            self.dspout_obj.mix_binaural_block(
                self.dspin_obj.hopsize,
                self.gui_dict)

            # Add mixed binaural stereo block to a time continuing binaural
            # output of all blocks
            self.dspout_obj.lock.acquire()
            try:
                self.dspout_obj.add_to_binaural(
                    self.blockcounter)
            finally:
                self.dspout_obj.lock.release()
            # Begin audio playback if specified number of bufferblocks
            # has been convolved
            if self.blockcounter == self.bufferblocks:
                startaudiooutput = threading.Thread(
                    target=self.dspout_obj.audiooutput, args=(
                        self.dspin_obj.wave_param_common[0],
                        self.dspin_obj.hopsize))
                startaudiooutput.start()

            # increment block counter of run function when less blocks than
            # than the bufferblocksize has been convolved (playback not
            # started yet). Also increment blockcounter of every convolve
            # process
            if self.blockcounter <= self.bufferblocks:
                self.blockcounter += 1
            # if playback already started
            else:
                # wait until the the new block has been played
                while self.dspout_obj.played_block_counter <= \
                        self.dspout_obj.prior_played_block_counter and self.\
                        dspout_obj.playback_finished is False:
                    time.sleep(1 / self.dspin_obj.wave_param_common[0] * 10)
                    # print("wait")
                # increment number of last played block
                self.dspout_obj.prior_played_block_counter += 1
                # increment number of already convolved blocks
                self.blockcounter += 1

            # handle playback pause
            while self.dspout_obj.gui_pause is True:
                time.sleep(0.1)
                self.dspout_obj.gui_pause = self.state.gui_pause
            # handle playback stop
            if self.dspout_obj.gui_stop is True:
                break

        # set correct playback output if stop button was pressed
        if self.dspout_obj.gui_stop is True:
            self.dspout_obj.playback_successful = True
        # excecute commands when playback finished successfully
        if self.dspout_obj.playback_successful is True and \
                        self.dspout_obj.gui_stop is \
                False:
            self.state.gui_stop = True
        # show plot of the output signal binaural_dict_scaled
        # plt.plot(self.dspout_obj.binaural[:, l_r])
        # plt.show()
        # Write generated output signal binaural_dict_scaled to file
        self.dspout_obj.writebinauraloutput(
            self.dspout_obj.binaural,
            self.dspin_obj.wave_param_common,
            self.gui_dict)
        # print out maximum integer amplitude value of whole played binaural
        # output
        print("maximum output amplitude: " + str(np.amax(np.abs(self.dspout_obj.
                                                          binaural))))

        self.return_ex.put(self.dspout_obj.playback_successful)
        # tell gui that dsp algorithm has finished
        self.state.dsp_run = False
