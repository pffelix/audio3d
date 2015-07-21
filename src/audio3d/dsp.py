# -*- coding: utf-8 -*-
#
# Author: Felix Pfreundtner, Matthias Lederle

import audio3d.dsp_in
import audio3d.dsp_out
import threading
import time


class Dsp:
    """
    H1 -- Dsp
    ************************
    **Main class of the project's Digital Signal Processing part.**
    """
    def __init__(self, state_init):
        self.state = state_init
        # Number of all speakers
        self.spn = len(self.state.gui_sp)
        # Azimuth head angle which was convolved in prior iteration for every
        # speaker
        self.prior_head_angle = [None for sp in range(self.spn)]
        # Set number of bufferblocks between fft block convolution and audio
        # block playback
        self.bufferblocks = state_init.gui_settings["bufferblocks"]
        # Create Input Object which contains mono input samples of sources
        # and hrtf impulse responses samples
        self.dspin_obj = audio3d.dsp_in.DspIn(state_init)
        # Create Output Object which contains binaural output samples
        self.dspout_obj = audio3d.dsp_out.DspOut(state_init,
                                                 self.dspin_obj.fft_blocksize,
                                                 self.dspin_obj.hopsize)
        # Blockcounter initialized to count number of already convolved
        # blocks
        self.blockcounter = 0

    def run(self):
        """
        H2 -- run
        ===================
        **Runs the dsp algorithm as one process on one cpu core as a big
        while-loop**

        | The steps of the loop are:
        | 1. Lock shared variables.
        | 2. Set the begin and end of the speaker wave block which needs to
          be read in this iteration.
        | 3. Iterate over all active speakers sp.
        | 4. Mix binaural stereo blockoutput of every speaker to one binaural
          stereo block output having regard to speaker distances.
        | 5. Mix binaural stereo blockoutput of every speaker.
        | 6. Add mixed binaural stereo block to play queue.
        | 7. Unlock shared variables.
        | 8. Synchronize with PortAudio Playback Thread
        | 9. Finish DSP Algorithm.

        Authors: Felix Pfreundtner, Matthias Lederle
        """
        # tell gui that dsp algorithm is running
        self.state.dsp_run = True
        # run the main while loop as long as there are still samples to be
        # read from speaker wave files
        while any(self.dspout_obj.continue_convolution) is True:
            # render new binaural block

            # lock shared variables: gui should not change any input
            # parameter during the creation of one block
            self.state.mtx_sp.acquire()
            self.state.mtx_settings.acquire()
            self.state.mtx_error.acquire()
            self.state.mtx_run.acquire()
            self.state.mtx_stop.acquire()
            self.state.mtx_pause.acquire()

            # handle playback stop
            if self.state.dsp_stop is True:
                # audio playback is stopped: release all shared variables
                self.state.mtx_sp.release()
                self.state.mtx_settings.release()
                self.state.mtx_error.release()
                self.state.mtx_run.release()
                self.state.mtx_stop.release()
                self.state.mtx_pause.release()
                # break convolution while loop
                break

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
                        self.dspout_obj.sp_binaural_block[sp][:, l_r] = \
                            self.dspin_obj.fft_convolution(sp, l_r)

                    # overlap and add binaural stereo block output of
                    # speaker sp to prior binaural stereo block output of
                    # speaker sp
                    self.dspout_obj.overlap_add(self.dspin_obj.fft_blocksize,
                                                self.dspin_obj.hopsize, sp)

            # Mix binaural stereo blockoutput of every speaker to one
            # binaural stereo block output having regard to speaker distances
            self.dspout_obj.mix_binaural_block(self.dspin_obj.hopsize)

            # Add mixed binaural stereo block to play queue which is read by
            # PortAudio Play Thread
            self.dspout_obj.add_to_playqueue()

            # If record box is checked: Add mixed binaural stereo block to a
            # time record queue which is later saved to file by
            # writerecordfile()
            if self.state.gui_settings["record"] is True:
                self.dspout_obj.add_to_recordqueue()

            # rendering of binaural block finshed:

            # unlock shared variables: block was created succesffuly,
            # gui can change parameters now before the next block creation
            # starts
            self.state.mtx_sp.release()
            self.state.mtx_settings.release()
            self.state.mtx_error.release()
            self.state.mtx_run.release()
            self.state.mtx_stop.release()
            self.state.mtx_pause.release()

            # Synchronize with PortAudio Playback Thread:

            # Create PortAudio playback thread if specified number of
            # bufferblocks has been convolved
            if self.blockcounter == self.bufferblocks:
                playthread = threading.Thread(
                    target=self.dspout_obj.audiooutput, args=(
                        self.dspin_obj.samplerate,
                        self.dspin_obj.hopsize))
                # Start PortAudio playback thread
                playthread.start()

            # when less blocks than the bufferblocksize has been convolved (
            # playback thread not started yet).
            if self.blockcounter <= self.bufferblocks:
                # increment number of already convolved block iterations
                self.blockcounter += 1
            else:
                # wait until the the new block has been played
                while self.dspout_obj.played_block_counter <= \
                        self.dspout_obj.prior_played_block_counter and \
                        self.state.dsp_stop is False:
                    time.sleep(1 / self.dspin_obj.samplerate * 10)
                # increment number of last played block
                self.dspout_obj.prior_played_block_counter += 1
                # increment number of already convolved block iterations
                self.blockcounter += 1

            # handle playback pause
            while self.state.dsp_pause is True:
                time.sleep(0.1)

        # Finish DSP Algorithm:

        # If record box is checked: Read record queue and write WAVE File
        if self.state.gui_settings["record"] is True:
            self.dspout_obj.writerecordfile(self.dspin_obj.samplerate,
                                            self.dspin_obj.hopsize)
        # mark dsp algorithm as finished
        self.state.dsp_run = False
