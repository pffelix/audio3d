# -*- coding: utf-8 -*-
"""
Created on Fri May 22 16:27:57 2015

@author: Felix Pfreundtner
"""

import numpy as np
import dsp_in
import dsp_out
import gui_utils

class Dsp:
    def __init__(self, gui_dict_init):

        self.continue_output = dict.fromkeys(gui_dict_init, True)
        self.gui_dict = gui_dict_init
        self.prior_head_angle_dict = dict.fromkeys(gui_dict_init, [])
        self.continue_output_list = dict.fromkeys(gui_dict_init, [])
        self.error_list = dict.fromkeys(gui_dict_init, [])
        self.outputsignal_sample_number = dict.fromkeys(gui_dict_init, [])
        self.continue_output = dict.fromkeys(gui_dict_init, True)
        # Variable counts number of already convolved blocks, initialized with zero
        self.blockcounter = 0
        # Create Input Object which contains mono input samples of sources and hrtf impulse responses samples
        self.DspIn_Object = dsp_in.DspIn(gui_dict_init)
        # Create Output Object which contains binaural output samples
        self.DspOut_Object = dsp_out.DspOut(gui_dict_init, self.DspIn_Object.fft_blocksize)

    def run(self):

        # start play buffer
        # play_output=deepcopy(standard_dict)
        # for sp in play_output:
        #    play_output[sp] = False
        # audioutput = threading.Thread(target=alf.startaudio(wave_param_dict[3][0], wave_param_dict[1][0], fft_blocksize))
        # audioutput.start()
        # global gui_dict
        # Run convolution block by block iteration
        while any(self.continue_output.values()) == True:

            #self.gui_dict = gui_utils.gui_dict
            print(self.blockcounter)
            for i, sp in enumerate(self.gui_dict):
                if i==len(self.gui_dict)-1:
                    print(self.gui_dict[sp][0])
                else:
                    print(self.gui_dict[sp][0], end=" ")

            # increment number of already convolved blocks
            self.blockcounter += 1
            # range of frames to be read in iteration from wav files (float numbers needed for adding the correct framesizes to the next iteration)
            self.DspIn_Object.wave_blockbeginend_dict = self.DspIn_Object.wave_blockbeginend(
                self.DspIn_Object.wave_blockbeginend_dict, self.DspIn_Object.wave_param_dict,
                self.DspIn_Object.sp_blocktime)

            # iterate over all speakers sp
            for sp in self.gui_dict:
                self.DspOut_Object.binaural_block_dict[sp] = np.zeros((self.DspIn_Object.fft_blocksize, 2))

                # check wheter this block is last block in speaker audio file, set ending of the block to last sample in speaker audio file
                if self.DspIn_Object.rnd(self.DspIn_Object.wave_blockbeginend_dict[sp][1]) > float(
                                self.DspIn_Object.wave_param_dict[sp][0] - 1):
                    self.DspIn_Object.wave_blockbeginend_dict[sp][1] = float(self.DspIn_Object.wave_param_dict[sp][0])

                # if speaker audio file still has unplayed samples start convolution
                if self.continue_output[sp] == True:

                    # check whether head position to speaker sp has changed
                    if self.gui_dict[sp][0] != self.prior_head_angle_dict[sp]:
                        # if head position has changed load new fitting hrtf file into array
                        self.DspIn_Object.hrtf_filenames_dict[sp] = self.DspIn_Object.get_hrtf_filenames(
                            self.gui_dict[sp])
                        self.DspIn_Object.hrtf_block_dict[sp] = self.DspIn_Object.get_hrtf(
                            self.DspIn_Object.hrtf_filenames_dict[sp], self.gui_dict[sp])
                        # save head position to speaker of this block in prior_head_angle dict
                        self.prior_head_angle_dict[sp] = self.gui_dict[sp][0]
                    # Load current wave block of speaker sp with speaker_blocksize (fft_blocksize-hrtf_blocksize+1)
                    self.DspIn_Object.sp_block_dict[sp], self.error_list[sp] = self.DspIn_Object.get_sp_block_dict(
                        self.DspIn_Object.signal_dict[sp], self.DspIn_Object.wave_blockbeginend_dict[sp],
                        self.DspIn_Object.sp_blocksize, self.error_list[sp])
                    # for the left an right ear channel
                    for l_r in range(2):
                        # convolve hrtf with speaker block input
                        self.DspOut_Object.binaural_block_dict[sp][0:self.DspIn_Object.fft_blocksize,
                        l_r] = self.DspOut_Object.fft_convolve(self.DspIn_Object.sp_block_dict[sp],
                                                               self.DspIn_Object.hrtf_block_dict[sp][:, l_r],
                                                               self.DspIn_Object.fft_blocksize)
                        # apply hamming window to binaural block ouptut
                        # binaural_block_dict[sp][:, l_r]= self.DspOut_Object.apply_hamming_window(binaural_block_dict[sp][:, l_r])

                # add speaker binaural block output to a iterative time based output array
                self.DspOut_Object.binaural_dict[sp], self.outputsignal_sample_number[
                    sp] = self.DspOut_Object.add_to_binaural_dict(self.DspOut_Object.binaural_block_dict[sp],
                                                                  self.DspOut_Object.binaural_dict[sp], int(
                        self.DspIn_Object.rnd(self.DspIn_Object.wave_blockbeginend_dict[sp][0])),
                                                                  self.outputsignal_sample_number[sp])

                # check wheter this block is last block in speaker audio file and stop convolution of speaker audio file
                if self.DspIn_Object.wave_blockbeginend_dict[sp][1] == float(self.DspIn_Object.wave_param_dict[sp][0]):
                    self.continue_output[sp] = False

                # record how long each speaker audio file was convoluted
                self.continue_output_list[sp].append(self.continue_output[sp])
                self.DspIn_Object.wave_blockbeginend_dict_list[sp].extend(self.DspIn_Object.wave_blockbeginend_dict[sp])

                # model speaker position change about 1° per block (0.02s) in clockwise rotation
                # gui_dict[sp][0]+=1
                # if gui_dict[sp][0] >= 360:
                #     gui_dict[sp][0] -= 360

        # resize amplitudes of signal to 16bit integer
        binaural_dict_scaled = self.DspOut_Object.bit_int(self.DspOut_Object.binaural_dict)
        # show plot of the output signal binaural_dict_scaled
        # plt.plot(binaural_dict[1])
        # Write generated output signal binaural_dict_scaled to file
        self.DspOut_Object.writebinauraloutput(binaural_dict_scaled, self.DspIn_Object.wave_param_common, self.gui_dict)


gui_dict_mockup = {0: [120, 1, "./audio_in/electrical_guitar_(44.1,1,16).wav"],
                   1: [220, 1, "./audio_in/sine_1kHz_(44.1,1,16).wav"],
                   2: [0, 1, "./audio_in/synthesizer_(44.1,1,16).wav"]
                   }

# Dsp_objekt = Dsp(gui_dict_mockup)
# Dsp_objekt.run()
# print()
