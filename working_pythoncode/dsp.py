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
        self.sp_spectrum_dict = dict.fromkeys(gui_dict_init, np.zeros((self.DspIn_Object.fft_blocksize/2, 2), dtype=np.float16))
        self.hrtf_spectrum_dict = dict.fromkeys(gui_dict_init, [np.zeros((self.DspIn_Object.fft_blocksize/2, 2), dtype=np.float16), np.zeros((self.DspIn_Object.fft_blocksize/2, 2), dtype=np.float16)])

        # Here a signal handler will be created
        # Usage:
        # When error occurs, call the function self.signal_handler.send_error()
        # The only parameter (A String!) is the message you want to send
        self.signal_handler = DspSignalHandler()

        # @author Matthias Lederle
        # self.blocknumpy = self.DspIn_Object.get_one_block_of_samples(
        #     self.DspIn_Object.gui_dict_init[sp][2],
        #     self.DspIn_Object.wave_blockbeginend_dict[sp],
        #     self.DspIn_Object.wave_param_dict[4],
        #     self.DspIn_Object.wave_param_dict[sp][2],
        #     self.DspIn_Object.wave_param_dict[sp][3],
        #     self.DspIn_Object.wave_param_dict[5],
        #     self.DspIn_Object.wave_param_dict[6]
        # )

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
                        self.DspIn_Object.hrtf_block_dict[sp], self.DspIn_Object.hrtf_max_gain_dict[sp] = self.DspIn_Object.get_hrtfs(self.gui_dict[sp], self.DspIn_Object.hrtf_database)
                        # save head position to speaker of this block in prior_head_angle dict
                        self.prior_head_angle_dict[sp] = self.gui_dict[sp][0]

                    # Load current wave block of speaker sp with speaker_blocksize (fft_blocksize-hrtf_blocksize+1)
                    self.DspIn_Object.sp_block_dict[sp], self.error_list[sp]= self.DspIn_Object.get_sp_block_dict(
                        self.DspIn_Object.signal_dict[sp], self.DspIn_Object.wave_blockbeginend_dict[sp],
                        self.DspIn_Object.sp_blocksize, self.error_list[sp])
                    #instead, now blockwise:
                    # @author Matthias Lederle
                    #self.DspIn_Object.sp_block_dict[sp] = self.blocknumpy

                    # normalize sp block if requested
                    self.DspIn_Object.sp_block_dict[sp], self.DspIn_Object.sp_max_gain_dict[sp]  = self.DspIn_Object.normalize(self.DspIn_Object.sp_block_dict[sp], self.gui_dict[sp][3])

                    # apply window to sp input in sp_block_dict
                    self.DspIn_Object.sp_block_dict[sp]= self.DspIn_Object.apply_window(self.DspIn_Object.sp_block_dict[sp], self.DspIn_Object.hann)

                    # for the left an right ear channel
                    for l_r in range(2):
                        # convolve hrtf with speaker block input
                        self.DspOut_Object.binaural_block_dict[sp][0:self.DspIn_Object.fft_blocksize,l_r], self.sp_spectrum_dict[sp], self.hrtf_spectrum_dict[sp][l_r] = self.DspOut_Object.fft_convolve(self.DspIn_Object.sp_block_dict[sp],self.DspIn_Object.hrtf_block_dict[sp][:, l_r],self.DspIn_Object.fft_blocksize,self.DspIn_Object.sp_max_gain_dict[sp],self.DspIn_Object.hrtf_max_gain_dict[sp][l_r], self.DspIn_Object.wave_param_common[0], self.sp_spectrum_dict[sp], self.hrtf_spectrum_dict[sp][l_r], self.DspIn_Object.hrtf_database, self.DspIn_Object.kemar_inverse_filter)


                # check wheter this block is last block in speaker audio file and stop convolution of speaker audio file
                if self.DspIn_Object.wave_blockbeginend_dict[sp][1] == float(self.DspIn_Object.wave_param_dict[sp][0]):
                    self.DspOut_Object.continue_convolution_dict[sp] = False

                # model speaker position change about 1° per block (0.02s) in clockwise rotation
                #self.gui_dict[sp][0]+=30
                #if self.gui_dict[sp][0] >= 360:
                    #self.gui_dict[sp][0] -= 360

                # overlap samples [0: fft_block_size-sp_block_size] sp block with prior sp block samples [sp_block_size: fft_block_size] and save in binaural_block_dict_out
                # save end of block [sp_block_size: fft_block_size] in binaural_block_dict_add to overlap in the next iteration
                self.DspOut_Object.binaural_block_dict_out[sp], self.DspOut_Object.binaural_block_dict_add[sp] = self.DspOut_Object.overlap_add(self.DspOut_Object.binaural_block_dict[sp], self.DspOut_Object.binaural_block_dict_out[sp], self.DspOut_Object.binaural_block_dict_add[sp], self.DspIn_Object.fft_blocksize, self.DspIn_Object.sp_blocksize)

            # Mix binaural stereo blockoutput of every speaker to one binaural stereo block having regard to speaker distances
            self.DspOut_Object.binaural_block = self.DspOut_Object.mix_binaural_block(self.DspOut_Object.binaural_block_dict_out, self.DspIn_Object.sp_blocksize, self.gui_dict)


            # Add mixed binaural stereo blocks to a time continuing binaural output
            self.DspOut_Object.lock.acquire()
            try:
                self.DspOut_Object.binaural = self.DspOut_Object.add_to_binaural(self.DspOut_Object.binaural, self.DspOut_Object.binaural_block, self.blockcounter)
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

        # show plot of the output signal binaural_dict_scaled
        # plt.plot(self.sp_spectrum_dict[sp][:,0], self.sp_spectrum_dict[sp][:,1])
        # plt.show()
        # Write generated output signal binaural_dict_scaled to file
        self.DspOut_Object.writebinauraloutput(self.DspOut_Object.binaural, self.DspIn_Object.wave_param_common, self.gui_dict)


