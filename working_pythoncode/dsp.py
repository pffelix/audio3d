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
import matplotlib.pyplot as plt
import multiprocessing
from dsp_signal_handler import DspSignalHandler

import time

class Dsp:
    def __init__(self, gui_dict_init):

        self.gui_dict = gui_dict_init
        self.prior_head_angle_dict = dict.fromkeys(gui_dict_init, [])
        self.error_list = dict.fromkeys(gui_dict_init, [])
        self.outputsignal_sample_number = dict.fromkeys(gui_dict_init, [])
        # Set number of bufferblocks between fft block convolution and audio block playback
        self.number_of_bufferblocks = 10
        # Create Input Object which contains mono input samples of sources and hrtf impulse responses samples
        self.DspIn_Object = dsp_in.DspIn(gui_dict_init)
        # Create Output Object which contains binaural output samples
        self.DspOut_Object = dsp_out.DspOut(gui_dict_init, self.DspIn_Object.fft_blocksize, self.DspIn_Object.sp_blocksize)
        # Variable counts number of already convolved blocks, initialized with zero
        self.blockcounter = 0

        # Here a signal handler will be created
        # Usage:
        # When error occurs, call the function self.signal_handler.send_error()
        # The only parameter (A String!) is the message you want to send
        self.signal_handler = DspSignalHandler()

    def run(self):
        # start play buffer
        # play_output=deepcopy(standard_dict)
        # for sp in play_output:
        #    play_output[sp] = False
        # audioutput = threading.Thread(target=alf.startaudio(wave_param_dict[3][0], wave_param_dict[1][0], fft_blocksize))
        # audioutput.start()
        # global gui_dict
        # global gui_dict
        # Run convolution block by block iteration
        while any(self.DspOut_Object.continue_convolution_dict.values()) == True:

            # self.gui_dict = gui_utils.gui_dict
            print("FFT Block " + str(self.blockcounter) + ":")
            # for i, sp in enumerate(self.gui_dict):
                # print("sp" + str(sp) + ": " + str(int(self.gui_dict[sp][0])) + ", " + str(self.gui_dict[sp][1]))

            # range of frames to be read in iteration from wav files (float numbers needed for adding the correct framesizes to the next iteration)
            self.DspIn_Object.wave_blockbeginend_dict = self.DspIn_Object.wave_blockbeginend(
                self.DspIn_Object.wave_blockbeginend_dict, self.DspIn_Object.wave_param_dict,
                self.DspIn_Object.sp_blocktime)


            # iterate over all speakers sp
            for sp in self.gui_dict:
                self.DspOut_Object.binaural_block_dict[sp] = np.zeros((self.DspIn_Object.fft_blocksize, 2), dtype=np.int16)

                # check wheter this block is last block in speaker audio file, set ending of the block to last sample in speaker audio file
                if self.DspIn_Object.rnd(self.DspIn_Object.wave_blockbeginend_dict[sp][1]) > float(
                                self.DspIn_Object.wave_param_dict[sp][0] - 1):
                    self.DspIn_Object.wave_blockbeginend_dict[sp][1] = float(self.DspIn_Object.wave_param_dict[sp][0])

                # if speaker audio file still has unplayed samples start convolution
                if self.DspOut_Object.continue_convolution_dict[sp] == True:

                    # check whether head position to speaker sp has changed
                    if self.gui_dict[sp][0] != self.prior_head_angle_dict[sp]:
                        # if head position has changed load new fitting hrtf file into array
                        self.DspIn_Object.hrtf_filenames_dict[sp] = self.DspIn_Object.get_hrtf_filenames(
                            self.gui_dict[sp])
                        self.DspIn_Object.hrtf_block_dict[sp], self.DspIn_Object.hrtf_max_gain_dict[sp] = self.DspIn_Object.get_hrtf(
                            self.DspIn_Object.hrtf_filenames_dict[sp], self.gui_dict[sp])
                        # save head position to speaker of this block in prior_head_angle dict
                        self.prior_head_angle_dict[sp] = self.gui_dict[sp][0]

                    # Load current wave block of speaker sp with speaker_blocksize (fft_blocksize-hrtf_blocksize+1)
                    self.DspIn_Object.sp_block_dict[sp], self.error_list[sp]= self.DspIn_Object.get_sp_block_dict(
                        self.DspIn_Object.signal_dict[sp], self.DspIn_Object.wave_blockbeginend_dict[sp],
                        self.DspIn_Object.sp_blocksize, self.error_list[sp])

                    # normalize sp block if requested
                    self.DspIn_Object.sp_block_dict[sp], self.DspIn_Object.sp_max_gain_dict[sp]  = self.DspIn_Object.normalize(self.DspIn_Object.sp_block_dict[sp], self.gui_dict[sp][3])

                    # for the left an right ear channel
                    for l_r in range(2):
                        # convolve hrtf with speaker block input
                        self.DspOut_Object.binaural_block_dict[sp][0:self.DspIn_Object.fft_blocksize,
                        l_r] = self.DspOut_Object.fft_convolve(self.DspIn_Object.sp_block_dict[sp],
                                                               self.DspIn_Object.hrtf_block_dict[sp][:, l_r],
                                                               self.DspIn_Object.fft_blocksize,
                                                               self.DspIn_Object.sp_max_gain_dict[sp],
                                                               self.DspIn_Object.hrtf_max_gain_dict[sp][l_r])
                        # apply hamming window to binaural block ouptut
                        # self.DspOut_Object.binaural_block_dict[sp][:, l_r]= self.DspOut_Object.apply_hamming_window(self.DspOut_Object.binaural_block_dict[sp][:, l_r])


                # add stereo speaker binaural block output to a time continuinng binaural output for every speaker
                #self.DspOut_Object.binaural_dict[sp], self.outputsignal_sample_number[
                    #sp] = self.DspOut_Object.add_to_binaural_dict(self.DspOut_Object.binaural_block_dict[sp],
                                                                  #self.DspOut_Object.binaural_dict[sp], int(
                        #self.DspIn_Object.rnd(self.DspIn_Object.wave_blockbeginend_dict[sp][0])))

                # check wheter this block is last block in speaker audio file and stop convolution of speaker audio file
                if self.DspIn_Object.wave_blockbeginend_dict[sp][1] == float(self.DspIn_Object.wave_param_dict[sp][0]):
                    self.DspOut_Object.continue_convolution_dict[sp] = False

                # model speaker position change about 1° per block (0.02s) in clockwise rotation
                #self.gui_dict[sp][0]+=30
                #if self.gui_dict[sp][0] >= 360:
                    #self.gui_dict[sp][0] -= 360

            # Mix binaural stereo blockoutput of every speaker to one binaural stereo block having regard to speaker distances
            self.DspOut_Object.binaural_block = self.DspOut_Object.mix_binaural_block(self.DspOut_Object.binaural_block_dict, self.DspIn_Object.fft_blocksize, self.gui_dict)


            # Add mixed binaural stereo blocks to a time continuing binaural output
            self.DspOut_Object.binaural = self.DspOut_Object.add_to_binaural(self.DspOut_Object.binaural_block, self.DspOut_Object.binaural, int(
                        self.DspIn_Object.rnd(self.DspIn_Object.wave_blockbeginend_dict[0][0])))

            self.DspOut_Object.lock.acquire()
            try:
                self.DspOut_Object.binaural_block_add = self.DspOut_Object.binaural[self.DspIn_Object.wave_blockbeginend_dict[0][0]:self.DspIn_Object.wave_blockbeginend_dict[0][1], :]
            finally:
                self.DspOut_Object.lock.release()


            # Begin Audio Playback if specified Number of Bufferblocks has been convolved
            if self.blockcounter == self.number_of_bufferblocks:
                startaudiooutput = threading.Thread(target=self.DspOut_Object.audiooutput, args = (2, self.DspIn_Object.wave_param_common[0], self.DspIn_Object.sp_blocksize))
                startaudiooutput.start()
                # startaudiooutput.join()

            # wait until audioplayback finished with current block
            while self.blockcounter-self.DspOut_Object.play_counter > self.number_of_bufferblocks and not all(self.DspOut_Object.continue_convolution_dict.values()) == False:
                 time.sleep(1/self.DspIn_Object.wave_param_common[0]*100)

            # increment number of already convolved blocks
            self.blockcounter += 1
        # resize amplitudes of signal to 16bit integer
        binaural_dict_scaled = self.DspOut_Object.bit_int(self.DspOut_Object.binaural_dict)
        # show plot of the output signal binaural_dict_scaled
        # plt.plot(self.DspOut_Object.binaural[:, l_r])
        # plt.show()
        # Write generated output signal binaural_dict_scaled to file
        self.DspOut_Object.writebinauraloutput(binaural_dict_scaled, self.DspIn_Object.wave_param_common, self.gui_dict)
        # if startaudiooutput.is_alive():
        #     print("wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww")
        #     time.sleep(5)


