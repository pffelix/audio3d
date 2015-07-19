# -*- coding: utf-8 -*-

import numpy as np
import dsp_in
import dsp_out
import threading
import time


class Dsp:
    def __init__(self, state_init, return_ex_init):
        self.state = state_init
        # Number of all speakers
        self.spn = len(self.state.gui_sp)
        self.prior_head_angle = [None for sp in range(self.spn)]
        self.return_ex = return_ex_init
        # Set number of bufferblocks between fft block convolution and audio
        # block playback
        self.bufferblocks = state_init.gui_settings["bufferblocks"]
        # Create Input Object which contains mono input samples of sources
        # and hrtf impulse responses samples
        self.dspin_obj = dsp_in.DspIn(state_init)
        # Create Output Object which contains binaural output samples
        self.dspout_obj = dsp_out.DspOut(state_init,
                                         self.dspin_obj.fft_blocksize,
                                         self.dspin_obj.hopsize)
        # Blockcounter initialized to count number of already convolved
        # blocks
        self.blockcounter = 0
        # timer variable which logs how long functions where running
        self.time = {"while": 0, "fft": 0}

    # @brief Runs the dsp algorithm as one process on one cpu core.
    # @details
    # @author Felix Pfreundtner, Matthias Lederle
    def run(self):
        # tell gui that dsp algorithm is running
        self.state.dsp_run = True
        # run the main while loop as long as there are still samples to be
        # read from speaker wave files
        while any(self.dspout_obj.continue_convolution) is True:
            # render new binaural block
            # lock state object
            self.state.mtx_sp.acquire()
            # print the number of already done FFT / Block iterations
            # print("FFT Block " + str(self.blockcounter) + ":")
            # set the begin and end of the speaker wave block which needs to
            # be read in this iteration
            self.dspin_obj.set_block_begin_end()
            # iterate over all active speakers sp
            for sp in range(self.spn):
                # if speaker wave file still has unread samples start
                # convolution, else skip convolution
                if self.dspout_obj.continue_convolution[sp] is True:
                    # check whether head position to speaker sp has changed
                    if self.state.gui_sp[sp]["angle"] !=  \
                            self.prior_head_angle[sp]:
                        # if yes, load new fitting hrtf frequency values
                        self.dspin_obj.get_hrtf_block_fft(sp)
                        # save head position to speaker of this block in
                        # prior_head_angle
                        self.prior_head_angle[sp] = self.state.gui_sp[sp][
                            "angle"]

                    # Load wave block of speaker sp with speaker_blocksize (
                    # fft_blocksize-hrtf_blocksize+1) and current block
                    # begin_end
                    self.dspout_obj.continue_convolution[sp] = \
                        self.dspin_obj.get_sp_block(sp)
                    # plt.plot(self.dspin_obj.sp_block[sp])
                    # plt.show()

                    # normalize sp block if requested
                    self.dspin_obj.normalize(sp)

                    # apply window to sp input in sp_block
                    self.dspin_obj.apply_window_on_sp_block(sp)
                    # for the left and the right ear channel
                    for l_r in range(2):
                        # convolve hrtf with speaker block input to get
                        # binaural stereo block output
                        start = time.time()
                        self.dspout_obj.sp_binaural_block[sp] = \
                            self.dspin_obj.fft_convolution(
                                self.dspout_obj.sp_binaural_block[sp], sp,
                                l_r)
                        self.time["fft"] += time.time() - start

                    # overlap and add binaural stereo block output of
                    # speaker sp to prior binaural stereo block output of
                    # speaker sp
                    self.dspout_obj.overlap_add(
                        self.dspin_obj.fft_blocksize,
                        self.dspin_obj.hopsize, sp)

            # Mix binaural stereo blockoutput of every speaker to one
            # binaural stereo block output having regard to speaker distances
            self.dspout_obj.mix_binaural_block(self.dspin_obj.hopsize)
            # binaural block rendered: unlock state object
            self.state.mtx_sp.release()
            # Add mixed binaural stereo block to a time continuing binaural
            # output of all blocks
            self.dspout_obj.lock.acquire()
            try:
                self.dspout_obj.add_to_queue(
                    self.blockcounter)
            finally:
                self.dspout_obj.lock.release()
            # Begin audio playback if specified number of bufferblocks
            # has been convolved
            if self.blockcounter == self.bufferblocks:
                playthread = threading.Thread(
                    target=self.dspout_obj.audiooutput, args=(
                        self.dspin_obj.wave_param_common[0],
                        self.dspin_obj.hopsize))
                playthread.start()

            # increment block counter of run function when less blocks than
            # than the bufferblocksize has been convolved (playback not
            # started yet). Also increment blockcounter of every convolve
            # process
            if self.blockcounter <= self.bufferblocks:
                self.blockcounter += 1
            # if playback already started
            else:
                start = time.time()
                # wait until the the new block has been played
                while self.dspout_obj.played_block_counter <= \
                        self.dspout_obj.prior_played_block_counter and self.\
                        dspout_obj.playback_finished is False:
                    time.sleep(1 / self.dspin_obj.wave_param_common[0])
                    # print("FFT: " + str(self.blockcounter))
                    # print("wait")
                # increment number of last played block
                self.dspout_obj.prior_played_block_counter += 1
                # increment number of already convolved blocks
                self.blockcounter += 1
                self.time["while"] += time.time() - start
            # handle playback pause
            while self.state.dsp_pause is True:
                time.sleep(0.1)
            # handle playback stop
            if self.state.dsp_stop is True:
                break

        # set correct playback output if stop button was pressed
        if self.state.dsp_stop is True:
            self.dspout_obj.playback_successful = True
        # excecute commands when playback finished successfully
        if self.dspout_obj.playback_successful is True and \
           self.state.dsp_stop is \
                False:
            self.state.dsp_stop = True
        # show plot of the output signal binaural_scaled
        # plt.plot(self.dspout_obj.binaural[:, l_r])
        # plt.show()
        # Write generated output signal binaural_scaled to file
        self.dspout_obj.writebinauraloutput(
            self.dspout_obj.binaural,
            self.dspin_obj.wave_param_common)
        # print out maximum integer amplitude value of whole played binaural
        # output
        print("maximum output amplitude: " + str(np.amax(np.abs(
            self.dspout_obj.binaural))))

        self.return_ex.put(self.dspout_obj.playback_successful)
        # tell gui that dsp algorithm has finished
        self.state.dsp_run = False
        # print timer variables
        print(self.time)
