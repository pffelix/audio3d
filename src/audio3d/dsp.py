# -*- coding: utf-8 -*-
#
# Author: Felix Pfreundtner, Matthias Lederle

import audio3d.dsp_in
import audio3d.dsp_out
import threading
import time


class Dsp:
    """
    Dsp
    ************************
    **Main class of the project's Digital Signal Processing part.

    | This class holds variables and methods which enable the build of the
    binaural output. It holds one instance of the DspIn and DspOut class.
    | The run() function is called by GUI Main Window as Thread and generates
    block by block a binaural audio output and sends it to a playback queue
    which is read by a PortAudio Callback Thread. To reach a higher
    performance the __init__ of the DspIn and DspOut class perform many time
    intensive calculations before starting the run() function of this class. **
    """
    def __init__(self, state_init):
        """
        __init__
        ===================
        ** __init__ is called by GUI MainWindow and creates all variables which
        are relevant for the run()method's while loop. It also creates one
        instance of the DspIn and DspOut class,  which provides all functions
        and variables need to generate the binaural block output **

        Authors: Felix Pfreundtner, Matthias Lederle
        """
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
        run
        ===================
        **Runs the dsp algorithm. The method ist called as single processing
        thread from gui_main_window. It uses a while loop, which generates
        block by block a mixed binaural output for multiple input speaker
        wave files. For this 3 hrtf databases can be chosen in Gui Main
        Window. After the block buffer size, which can be specified in
        gui_main_window, it generates a second thread which starts the playback
        of the generated binaural blocks with PortAudio. The algorithm
        can be stopped and paused through GUI Main Window by using a shared
        state object, which is controlled by mutex access**

        | The steps of the while loop are:
        | 1. Lock variables which are accessible through state class by gui and
          dsp algorithm
        | 2. Set the common begin and end sample position in the speaker wave
          files input which needs to be read in this iteration.
        | 3. Iterate over all speakers sp.
          4. Read in current fitting hrtf for left and right ear and speaker
          block input
          5. Convolve hrtfs with speaker block input using fft and overlap add
        | 6. Mix binaural stereo blockoutput of every speaker to one binaural
          stereo block output having regard to speaker distances.
        | 7. Add mixed binaural stereo block to play queue
        | 8. Unlock shared variables.
        | 9. Read play queue by PortAudio playback thread
        | 10. If selected in GUI: records the binaural output to a wave file
        | 11. Finish DSP Algorithm, reset play and pause button

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
