# -*- coding: utf-8 -*-
"""
Created on Fri May 22 16:27:57 2015

@author: Felix Pfreundtner
"""

import numpy as np
import dsp_in
import dsp
import dsp_out
import gui_utils
import threading
import multiprocessing
import gui_utils
import time

from error_handler import send_error

import time


class Dsp:
    def __init__(self, gui_dict_init, gui_stop_init, gui_pause_init,
                 gui_settings_dict_init, return_ex_init):
        self.gui_dict = gui_dict_init
        self.gui_settings_dict = gui_settings_dict_init
        self.prior_head_angle_dict = dict.fromkeys(gui_dict_init, [])
        self.return_ex = return_ex_init
        self.outputsignal_sample_number = dict.fromkeys(gui_dict_init, [])
        # Set number of bufferblocks between fft block convolution and audio
        # block playback
        self.bufferblocks = gui_settings_dict_init["bufferblocks"]
        # Create Input Object which contains mono input samples of sources
        # and hrtf impulse responses samples
        self.DspIn_Object = dsp_in.DspIn(gui_dict_init, gui_settings_dict_init)
        # Create Output Object which contains binaural output samples
        self.DspOut_Object = dsp_out.DspOut(gui_dict_init,
                                            self.DspIn_Object.fft_blocksize,
                                            self.DspIn_Object.sp_blocksize,
                                            self.DspIn_Object.hopsize,
                                            gui_stop_init, gui_pause_init)
        # Blockcounter initialized to count number of already convolved
        # blocks
        self.blockcounter = 0

    ## @brief Runs the dsp algorithm as one process on one cpu core.
    # @details
    # @author Felix Pfreundtner, Matthias Lederle
    def run_single_core(self):
        # run the main while loop as long as there are still samples to be
        # read from speaker wave files
        while any(self.DspOut_Object.continue_convolution_dict.values()) \
                is True:
            # actualize variables with gui
            self.gui_dict = gui_utils.gui_dict
            self.DspOut_Object.gui_stop = gui_utils.gui_stop
            self.DspOut_Object.gui_pause = gui_utils.gui_pause
            self.gui_settings_dict = gui_utils.gui_settings_dict
            # print the number of already done FFT / Block iterations
            print("FFT Block " + str(self.blockcounter) + ":")
            # set the begin and end of the speaker wave block which needs to
            # be read in this iteration
            self.DspIn_Object.set_block_begin_end()
            # iterate over all active speakers sp
            for sp in self.gui_dict:
                # reset binaural block output array of speaker sp by filling
                #  it with zeros
                self.DspOut_Object.binaural_block_dict[sp] = np.zeros((
                    self.DspIn_Object.fft_blocksize, 2), dtype=np.int16)
                # if speaker wave file still has unread samples start
                # convolution, else skip convolution
                if self.DspOut_Object.continue_convolution_dict[sp] is True:
                    # check whether head position to speaker sp has changed
                    if self.gui_dict[sp][0] != self.prior_head_angle_dict[sp]:
                        # if head position has changed load new hrtf-settings
                        self.DspIn_Object.hrtf_database, \
                            self.DspIn_Object.hrtf_blocksize, \
                            self.DspIn_Object.kemar_inverse_filter = \
                            self.DspIn_Object.get_hrtf_param(
                                self.gui_settings_dict)
                        # and load fitting hrtf-file as numpy array
                        self.DspIn_Object.get_hrtfs(self.gui_dict[sp], sp)
                        # save head position to speaker of this block in
                        # prior_head_angle_dict
                        self.prior_head_angle_dict[sp] = self.gui_dict[sp][0]

                    # Load wave block of speaker sp with speaker_blocksize (
                    # fft_blocksize-hrtf_blocksize+1) and current block
                    # begin_end
                    self.DspOut_Object.continue_convolution_dict[sp] = \
                        self.DspIn_Object.get_sp_block(sp)
                    #plt.plot(self.DspIn_Object.sp_block_dict[sp])
                    #plt.show()

                    # normalize sp block if requested
                    self.DspIn_Object.normalize(self.gui_dict[sp][3], sp)

                    # apply window to sp input in sp_block_dict
                    self.DspIn_Object.apply_window_on_sp_block(sp)
                    # for the left and the right ear channel
                    for l_r in range(2):
                        # convolve hrtf with speaker block input to get
                        # binaural stereo block output
                        self.DspOut_Object.fft_convolve(
                            self.DspIn_Object.sp_block_dict[sp],
                            self.DspIn_Object.hrtf_block_dict[sp][:, l_r],
                            self.DspIn_Object.fft_blocksize,
                            self.DspIn_Object.sp_max_amp_dict[sp],
                            self.DspIn_Object.hrtf_max_amp_dict[sp][l_r],
                            self.DspIn_Object.wave_param_common[0],
                            self.gui_settings_dict["inverse_filter_active"],
                            self.DspIn_Object.kemar_inverse_filter,
                            self.DspIn_Object.hrtf_blocksize,
                            self.DspIn_Object.sp_blocksize, sp, l_r)
                # model speaker position change about 1° per block (0.02s) in
                # clockwise rotation
                # self.gui_dict[sp][0]+=30
                # if self.gui_dict[sp][0] >= 360:
                    #self.gui_dict[sp][0] -= 360

                # overlap and add binaural stereo block output of speaker sp
                #  to prior binaural stereo block output of speaker sp
                    self.DspOut_Object.overlap_add(
                        self.DspIn_Object.fft_blocksize,
                        self.DspIn_Object.hopsize, sp)

            # Mix binaural stereo blockoutput of every speaker to one
            # binaural stereo block output having regard to speaker distances
            self.DspOut_Object.mix_binaural_block(
                self.DspIn_Object.hopsize,
                self.gui_dict)

            # Add mixed binaural stereo block to a time continuing binaural
            # output of all blocks
            self.DspOut_Object.lock.acquire()
            try:
                self.DspOut_Object.add_to_binaural(
                    self.blockcounter)
            finally:
                self.DspOut_Object.lock.release()
            # Begin audio playback if specified number of bufferblocks
            # has been convolved
            if self.blockcounter == self.bufferblocks:
                startaudiooutput = threading.Thread(
                    target=self.DspOut_Object.audiooutput, args=(
                        self.DspIn_Object.wave_param_common[0],
                        self.DspIn_Object.hopsize))
                startaudiooutput.start()

            # wait until audioplayback finished with current block
            while self.blockcounter - self.DspOut_Object.played_block_counter\
                    > self.bufferblocks and not all(
                    self.DspOut_Object.continue_convolution_dict.values()) \
                    is False:
                time.sleep(1 / self.DspIn_Object.wave_param_common[0])

            # increment number of already convolved blocks
            self.blockcounter += 1

            # handle playback pause
            while self.DspOut_Object.gui_pause is True:
                time.sleep(0.1)
                self.DspOut_Object.gui_pause = gui_utils.gui_pause
            # handle playback stop
            if self.DspOut_Object.gui_stop is True:
                break

        # set correct playback output if stop button was pressed
        if self.DspOut_Object.gui_stop is True:
            self.DspOut_Object.playback_successful = True
        # show plot of the output signal binaural_dict_scaled
        #plt.plot(self.DspOut_Object.binaural[:, l_r])
        #plt.show()
        # Write generated output signal binaural_dict_scaled to file
        self.DspOut_Object.writebinauraloutput(
            self.DspOut_Object.binaural,
            self.DspIn_Object.wave_param_common,
            self.gui_dict)
        self.return_ex.put(self.DspOut_Object.playback_successful)

    ## @brief run dsp algorithm on multiple cores by creating an own process for
    #        every speaker
    # @details
    # @author Felix Pfreundtner
    def run_multi_core(self):
        processes = {}
        binaural_block_dict_out_ex = {}
        hrtf_spectrum_dict_ex = {}
        sp_spectrum_dict_ex = {}
        cotinue_output_ex = {}
        gui_dict_ex = {}
        gui_settings_dict_ex = {}
        blockcounter_sync_ex = multiprocessing.Value('i', 0)
        played_block_counter_last = 0
        playback_successful_ex = multiprocessing.Value('b', True)
        gui_stop_ex = multiprocessing.Value('b', self.DspOut_Object.gui_stop)
        gui_pause_ex = multiprocessing.Value('b', self.DspOut_Object.gui_pause)

        # create a process for every speaker
        for sp in self.gui_dict:
            binaural_block_dict_out_ex[sp] = multiprocessing.Queue()
            hrtf_spectrum_dict_ex[sp] = multiprocessing.Queue()
            sp_spectrum_dict_ex[sp] = multiprocessing.Queue()
            gui_dict_ex[sp] = multiprocessing.Queue()
            gui_settings_dict_ex[sp] = multiprocessing.Queue()

            cotinue_output_ex[sp] = multiprocessing.Value('b', True)
            processes[sp] = multiprocessing.Process(
                target=sp_block_convolution,
                args=(self.gui_dict, self.DspOut_Object.gui_stop,
                      self.DspOut_Object.gui_pause,
                      self.gui_settings_dict,
                      self.return_ex,
                      sp,
                      binaural_block_dict_out_ex[sp],
                      hrtf_spectrum_dict_ex[sp],
                      sp_spectrum_dict_ex[sp],
                      cotinue_output_ex[sp],
                      blockcounter_sync_ex,
                      playback_successful_ex,
                      gui_dict_ex[sp],
                      gui_settings_dict_ex[sp],
                      gui_stop_ex,
                      gui_pause_ex))

        # start all processes
        for sp in processes:
            processes[sp].start()

        # link gui related instance variables to gui global variables
        self.gui_dict = gui_utils.gui_dict
        self.DspOut_Object.gui_stop = gui_utils.gui_stop
        self.DspOut_Object.gui_pause = gui_utils.gui_pause
        self.gui_settings_dict = gui_utils.gui_settings_dict

        while any(self.DspOut_Object.continue_convolution_dict.values()) \
                is True:
            # send speaker processes current gui related variables:
            gui_stop_ex.value = self.DspOut_Object.gui_stop
            gui_pause_ex.value = self.DspOut_Object.gui_pause
            for sp in self.gui_dict:
                gui_dict_ex[sp].put(self.gui_dict[sp])
                gui_settings_dict_ex[sp].put(self.gui_settings_dict)

            # update values from every speaker child process into this function
            for sp in processes:
                self.DspOut_Object.binaural_block_dict_out[sp] = \
                    binaural_block_dict_out_ex[sp].get()
                self.DspOut_Object.sp_spectrum_dict[sp] = \
                    sp_spectrum_dict_ex[sp].get()
                self.DspOut_Object.hrtf_spectrum_dict[sp] = \
                    hrtf_spectrum_dict_ex[sp].get()
                self.DspOut_Object.continue_convolution_dict[sp] = \
                    bool(cotinue_output_ex[sp].value)

            # Mix binaural stereo blockoutput of every speaker to one
            # binaural stereo block output having regard to speaker distances
            self.DspOut_Object.mix_binaural_block(
                self.DspIn_Object.hopsize,
                self.gui_dict)

            # Add mixed binaural stereo block to a time continuing binaural
            # output of all blocks
            self.DspOut_Object.add_to_binaural(self.blockcounter)

            # Begin audio playback if specified number of bufferblocks
            # has been convolved
            if self.blockcounter == self.bufferblocks:
                audiooutput = threading.Thread(
                    target=self.DspOut_Object.audiooutput, args=(
                        self.DspIn_Object.wave_param_common[0],
                        self.DspIn_Object.hopsize))
                audiooutput.start()

            # increment block counter of run function when less blocks than
            # than the bufferblocksize has been convolved (playback not
            # started yet). Also increment blockcounter of every convolve
            # process
            if self.blockcounter <= self.bufferblocks:
                self.blockcounter += 1
                blockcounter_sync_ex.value += 1
            # if playback already started
            else:
                # wait until the difference between run blockcounter and play
                #  blockcounter is smaller than buffersize
                while self.DspOut_Object.played_block_counter <= \
                        played_block_counter_last and \
                        self.DspOut_Object.playback_finished is False:
                    time.sleep(1 / self.DspIn_Object.wave_param_common[0] * 10)
                    #print("wait")
                # increment
                played_block_counter_last += 1
                # increment run blockcounter
                self.blockcounter += 1
                # increment convolve processes blockcounter to start new block
                # convolution
                blockcounter_sync_ex.value += 1

            playback_successful_ex.value =  \
                self.DspOut_Object.playback_successful
            print(self.blockcounter)
        #plt.plot(self.DspOut_Object.binaural[:, :])
        #plt.show()

            # handle playback pause
            while self.DspOut_Object.gui_pause is True:
                time.sleep(0.1)
                self.DspOut_Object.gui_pause = gui_utils.gui_pause
            # handle playback stop
            if self.DspOut_Object.gui_stop is True:
                break

        # set playback_successful == True if stop button was pressed as
        # playback was stopped normal by user
        if self.DspOut_Object.gui_stop is True:
            self.DspOut_Object.playback_successful = True

        # if playback stopped unsuccessful wait until all process finished
        if self.DspOut_Object.gui_stop is False:
            for sp in processes:
                processes[sp].join()
        # print out whether playback was successful
        print("Playback successfull: " + str(
            self.DspOut_Object.playback_successful))
        self.return_ex.put(self.DspOut_Object.playback_successful)


## @brief This function is being run in a separate process for each speaker.
# @details The function iterates over every block of the speaker input file,
# convolves it with the current head position related hrtf and sends the
# ouput for each speaker block with a queue to dsp.run.
# @author Felix Pfreundtner
def sp_block_convolution(gui_dict_init,
                         gui_stop_init,
                         gui_pause_init,
                         gui_settings_dict_init,
                         return_ex_init, sp,
                         binaural_block_dict_out_ex_sp,
                         hrtf_spectrum_dict_ex_sp,
                         sp_spectrum_dict_ex_sp,
                         cotinue_output_ex_sp,
                         blockcounter_sync,
                         playback_successful,
                         gui_dict_ex_sp,
                         gui_settings_dict_ex_sp,
                         gui_stop_ex,
                         gui_pause_ex):

    # instantiate new dsp object for speaker
    dsp_obj_sp = dsp.Dsp(gui_dict_init, gui_stop_init, gui_pause_init,
                         gui_settings_dict_init, return_ex_init)

    while dsp_obj_sp.DspOut_Object.continue_convolution_dict[sp] is True and \
            bool(playback_successful.value) is True:
        # if block iteration is smaller than blockcounter in run_multi_core run
        if dsp_obj_sp.blockcounter <= blockcounter_sync.value:

            # update gui related variables from dsp_object:
            dsp_obj_sp.DspOut_Object.gui_stop = bool(gui_stop_ex.value)
            dsp_obj_sp.DspOut_Object.gui_pause = bool(gui_pause_ex.value)
            if gui_dict_ex_sp.empty() is False:
                dsp_obj_sp.gui_dict[sp] = gui_dict_ex_sp.get()
            if gui_settings_dict_ex_sp.empty() is False:
                dsp_obj_sp.gui_settings_dict[sp] = gui_settings_dict_ex_sp.get()

            print("sp " + str(sp) + ": FFT Block " + str(
                dsp_obj_sp.blockcounter) + ":")
            dsp_obj_sp.DspIn_Object.set_block_begin_end()
            # reset binaural block output array of speaker sp by filling
            #  it with zeros
            dsp_obj_sp.DspOut_Object.binaural_block_dict[sp] = np.zeros((
                dsp_obj_sp.DspIn_Object.fft_blocksize, 2), dtype=np.int16)
            # if speaker wave file still has unread samples start
            # convolution, else skip convolution
            if dsp_obj_sp.DspOut_Object.continue_convolution_dict[sp] is True:
                # check whether head position to speaker sp has changed
                if dsp_obj_sp.gui_dict[sp][0] != \
                        dsp_obj_sp.prior_head_angle_dict[sp]:
                    # if head position has changed load new hrtf-settings
                    dsp_obj_sp.DspIn_Object.hrtf_database, \
                        dsp_obj_sp.DspIn_Object.hrtf_blocksize, \
                        dsp_obj_sp.DspIn_Object.kemar_inverse_filter = \
                        dsp_obj_sp.DspIn_Object.get_hrtf_param(
                            dsp_obj_sp.gui_settings_dict)
                    # and load fitting hrtf-file as numpy array
                    dsp_obj_sp.DspIn_Object.get_hrtfs(dsp_obj_sp.gui_dict[
                        sp], sp)
                    # save head position to speaker of this block in
                    # prior_head_angle_dict
                    dsp_obj_sp.prior_head_angle_dict[sp] = \
                        dsp_obj_sp.gui_dict[sp][0]

                # Load wave block of speaker sp with speaker_blocksize (
                # fft_blocksize-hrtf_blocksize+1) and current block
                # begin_end
                dsp_obj_sp.DspOut_Object.continue_convolution_dict[sp] = \
                    dsp_obj_sp.DspIn_Object.get_sp_block(sp)
                #plt.plot(dsp_obj_sp.DspIn_Object.sp_block_dict[sp])
                #plt.show()

                # normalize sp block if requested
                dsp_obj_sp.DspIn_Object.normalize(dsp_obj_sp.gui_dict[sp][
                    3], sp)

                # apply window to sp input in sp_block_dict
                dsp_obj_sp.DspIn_Object.apply_window_on_sp_block(sp)
                # for the left and the right ear channel
                for l_r in range(2):
                    # convolve hrtf with speaker block input to get
                    # binaural stereo block output
                    dsp_obj_sp.DspOut_Object.fft_convolve(
                        dsp_obj_sp.DspIn_Object.sp_block_dict[sp],
                        dsp_obj_sp.DspIn_Object.hrtf_block_dict[sp][:, l_r],
                        dsp_obj_sp.DspIn_Object.fft_blocksize,
                        dsp_obj_sp.DspIn_Object.sp_max_amp_dict[sp],
                        dsp_obj_sp.DspIn_Object.hrtf_max_amp_dict[sp][l_r],
                        dsp_obj_sp.DspIn_Object.wave_param_common[0],
                        dsp_obj_sp.gui_settings_dict["inverse_filter_active"],
                        dsp_obj_sp.DspIn_Object.kemar_inverse_filter,
                        dsp_obj_sp.DspIn_Object.hrtf_blocksize,
                        dsp_obj_sp.DspIn_Object.sp_blocksize, sp, l_r)
            # model speaker position change about 1° per block (0.02s) in
            # clockwise rotation
            # dsp_obj_sp.gui_dict[sp][0]+=30
            # if dsp_obj_sp.gui_dict[sp][0] >= 360:
                #dsp_obj_sp.gui_dict[sp][0] -= 360

            # overlap and add binaural stereo block output of speaker sp
            #  to prior binaural stereo block output of speaker sp
                dsp_obj_sp.DspOut_Object.overlap_add(
                    dsp_obj_sp.DspIn_Object.fft_blocksize,
                    dsp_obj_sp.DspIn_Object.hopsize, sp)

            # send values which are updated very block to control function
            # run_multi_core
            binaural_block_dict_out_ex_sp.put(
                dsp_obj_sp.DspOut_Object.binaural_block_dict_out[sp])
            hrtf_spectrum_dict_ex_sp.put(
                dsp_obj_sp.DspOut_Object.hrtf_spectrum_dict[sp])
            sp_spectrum_dict_ex_sp.put(
                dsp_obj_sp.DspOut_Object.sp_spectrum_dict[sp])
            cotinue_output_ex_sp.value = \
                dsp_obj_sp.DspOut_Object.continue_convolution_dict[sp]
            dsp_obj_sp.blockcounter += 1
        # if block iteration is further than blockcounter in run_multi_core wait
        else:
            time.sleep(1 / dsp_obj_sp.DspIn_Object.wave_param_common[0] * 10)

    print("sp: " + str(sp) + " finished")
