# -*- coding: utf-8 -*-
#
# Author: Felix Pfreundtner, Matthias Lederle

import unittest
import audio3d.dsp
import audio3d.dsp_in
import audio3d.dsp_out
import numpy as np
import scipy.io.wavfile
import audio3d.gui_utils
import pkg_resources
import copy


class DspTests(unittest.TestCase):
    """
    H1 -- DspTests
    ************************
    **Testclass for all Dsp-Classes (Dsp, DspIn, DspOut) of the project.**

    Authors: Felix Pfreundtner, Matthias Lederle
    """
    def __init__(self, *args, **kwargs):
        # calling the constructor of the super class
        super(DspTests, self).__init__(*args, **kwargs)
        # initialize GUI state
        self.state = audio3d.gui_utils.State()
        # modify GUI state
        self.state.gui_sp = []
        self.state.gui_sp.append({"angle": 90, "distance": 0, "path":
                                  pkg_resources.resource_filename(
                                      "audio3d", "audio_in/Sine_1kHz_(44.1,1,"
                                      "16).wav"), "normalize": False})

        self.state.gui_sp.append({"angle": 10, "distance": 1, "path":
                                  pkg_resources.resource_filename(
                                      "audio3d",
                                      "audio_in/Rhythm_Guitar_1.wav"),
                                  "normalize": True})

        self.state.gui_sp.append({"angle": 120, "distance": 1, "path":
                                  pkg_resources.resource_filename(
                                      "audio3d",
                                      "audio_in/Drums.wav"),
                                  "normalize": True})

        # same speaker input as already speaker 0: check whether there might
        # be redundancy problems in the code
        self.state.gui_sp.append({"angle": 90, "distance": 0, "path":
                                  pkg_resources.resource_filename(
                                      "audio3d", "audio_in/Sine_1kHz_(44.1,1,"
                                      "16).wav"), "normalize": True})

        self.state.gui_settings = {"hrtf_database": "kemar_normal_ear",
                                   "inverse_filter_active": False,
                                   "bufferblocks": 5}

        self.state.gui_stop = False
        self.state.gui_pause = False
        self.dsp_obj = audio3d.dsp.Dsp(self.state)

    def test_rnd_int(self):
        """
        H2 -- test_rnd_int
        ===================
        Tests rnd for one particular number.

        Author: Matthias Lederle
        """
        val = 1.9
        sol = 2
        res = self.dsp_obj.dspin_obj.rnd(val)
        error_msg = "test_rnd_int failed!"
        self.assertEqual(res, sol, msg=error_msg)

    def test_rnd(self):
        """
        H2 -- test_rnd
        ===================
        **Tests rnd for a list of numbers at the same time.**

        Author: Matthias Lederle
        """
        i = 0
        value = [2.55, 7.9, (2 / 3), 0.5, 0.00001, 500.1, -80.1, -1.4142, -9.5]
        res = [None] * len(value)
        sol = [3, 8, 1, 1, 0, 500, -80, -1, -10]
        # value = []
        # value[0] = 2
        # sol = 2
        while i < len(value):
            # res[i] = res.append(self.dspin_obj.rnd(value[i]))
            res[i] = self.dsp_obj.dspin_obj.rnd(value[i])
            i += 1
        error_msg = "test_rnd failed!"
        self.assertListEqual(res, sol, msg=error_msg)

    # @brief Tests equality of the values at position 2 and 200 of the
    #  hamming-window.
    def test_hann_window(self):
        """
        H2 -- test_hann_window
        ===================
        Tests equality of the values at position 2 and 200 of the
        hamming-window.

        Author: Matthias Lederle
        """
        sol_hannwin_2 = 0.00014997
        sol_hannwin_200 = 0.88477
        res = \
            self.dsp_obj.dspin_obj.build_hann_window(sp_blocksize=513)
        errmsg = "Hanning Window not calculated correctly"
        self.assertAlmostEqual(res[2], sol_hannwin_2, 5, msg=errmsg)
        self.assertAlmostEqual(res[200], sol_hannwin_200, 5, msg=errmsg)

    # @brief Tests get_block_param by comparing two lists.
    def test_get_block_param(self):
        """
        H2 -- test_get_block_param
        ===================
        **Tests get_block_param by comparing two lists.**

        Author: Matthias Lederle
        """
        sol = [512, 0.011609977324263039, 0.5, 256]
        res = [None] * 3
        res[0: 3] = self.dsp_obj.dspin_obj.get_block_param()
        errmsg = "Function get_block_param (in DspIn) doesn't work properly"
        self.assertListEqual(res, sol, msg=errmsg)

    def test_init_set_block_begin_end_1(self):
        """
        H2 -- test_init_set_block_begin_end_1
        ===================
        **Compare init_set_block_begin_end() output with correct values for
        initialization of block_begin_end.**

        Author: Felix Pfreundtner
        """
        #
        # initialize -> set back begin end back about one iteration
        # moving size of one step (each iteration)
        step = self.dsp_obj.dspin_obj.hopsize
        result_correct = [0 - step, self.dsp_obj.dspin_obj.sp_blocksize - step]
        result_test = self.dsp_obj.dspin_obj.init_set_block_begin_end()
        errmsg = "block begin end intialization does not have correct " \
                 "position and size"
        self.assertEqual(result_correct, result_test, msg=errmsg)

    def test_init_set_block_begin_end_2(self):
        """
        H2 -- test_init_set_block_begin_end_2
        ===================
        **Tests init_set_block_begin_end by comparing two lists.**

        Author: Matthias Lederle
        """
        res = self.dsp_obj.dspin_obj.init_set_block_begin_end()
        errmsg = "The entries in init_block_begin_end are not symmetric  " \
                 "to 0"
        self.assertTrue(abs(res[0]) == abs(res[1]), msg=errmsg)

    def test_set_block_begin_end(self):
        """
        H2 -- test_set_block_begin_end
        ===================
        **Compare set_block_begin_end() output with correct values for
        the first run() iterations of dsp algorithm.**

        Author: Felix Pfreundtner
        """
        # step between each read block array in position samples is
        step = self.dsp_obj.dspin_obj.hopsize
        result_correct = [[0, self.dsp_obj.dspin_obj.sp_blocksize],
                          [0 + step * 1, self.dsp_obj.dspin_obj.sp_blocksize +
                           step * 1], [0 + step * 2,
                                       self.dsp_obj.dspin_obj.sp_blocksize +
                                       step * 2]]
        result_test = []
        # run 3 iterations
        for blockcounter in range(3):
            # set position
            self.dsp_obj.dspin_obj.set_block_begin_end()
            temp = self.dsp_obj.dspin_obj.block_begin_end
            result_test.append(copy.deepcopy(temp))

        # set self.block_begin_end back to initialize value
        self.dsp_obj.dspin_obj.init_set_block_begin_end()

        errmsg = "first block iterations do not have correct position and " \
                 "size"
        self.assertEqual(result_correct, result_test, msg=errmsg)
    # @brief Tests the values of init_block_begin_end on symmetry to 0

    def test_set_block_begin_end(self):
        """
        H2 -- test_set-block_begin_end
        ===================
        **Tests the set_block_begin_end method for correctness.**

        Author: Matthias Lederle
        """
        truelist = []
        i = 1
        block_begin_end = self.dsp_obj.dspin_obj.block_begin_end
        while i < 10:
            # Between ##### and ##### has to be the same code as in
            # set_block_begin_end-method
            #####
            block_begin_end[0] += int(
                self.dsp_obj.dspin_obj.sp_blocksize *
                (1 - self.dsp_obj.dspin_obj.overlap))
            block_begin_end[1] += int(
                self.dsp_obj.dspin_obj.sp_blocksize *
                (1 - self.dsp_obj.dspin_obj.overlap))
            #####
            if block_begin_end[1] - block_begin_end[0] == \
                    self.dsp_obj.dspin_obj.sp_blocksize:
                bool = True
            else:
                bool = False
            errmsg = "set_block_begin_end does not work properly"
            truelist.append(bool)
            i += 1
        self.assertTrue(truelist, msg=errmsg)

    def test_init_read_sp(self):
        """
        H2 -- test_init_read_sp
        ===================
        **Test whether init_read_sp() gives out the sample samplerate as
        scipy.io.wavfile.read()**

        Author: Felix Pfreundtner
        """

        result_correct = []
        result_test = []
        # for all speakers in self.state.gui_sp
        for sp in range(len(self.state.gui_sp)):
            # get sample rate values produced by scipy.io.wavfile.read()
            temp, _ = \
                scipy.io.wavfile.read(self.state.gui_sp[sp]["path"])
            result_correct.append(temp)
            # get sample rate values produced by init_read_sp()
            result_test.append(self.dsp_obj.dspin_obj.sp_param[sp][1])
        errmsg = "wrong samplerate produced by init_read_sp()"
        self.assertEqual(result_correct, result_test, msg=errmsg)

    def test_read_sp(self):
        """
        H2 -- test_read_sp
        ===================
        **Compare get_sp-method to scipy-method-results.**

        Author: Matthias Lederle
        """
        sp = 1
        scipy_sp_input = {}
        scipy_sp_input[sp] = np.zeros((220672, ), dtype=np.int16)
        scipy_sp_input_raw = {}
        for sp in range(len(self.state.gui_sp)):
            _, scipy_sp_input_raw[sp] = \
                scipy.io.wavfile.read(self.state.gui_sp[sp]["path"])
            lenarray = len(scipy_sp_input_raw[sp])
            # append zeros to scipy_sp_dict_raw to reach that output is
            # divideable by sp_blocksize
            if lenarray % self.dsp_obj.dspin_obj.sp_blocksize != 0:
                scipy_sp_input[sp] = \
                    np.zeros((lenarray +
                              self.dsp_obj.dspin_obj.sp_blocksize -
                              lenarray %
                              self.dsp_obj.dspin_obj.sp_blocksize, ),
                             dtype=np.int16)
                scipy_sp_input[sp][0:lenarray, ] = scipy_sp_input_raw[sp]
            else:
                scipy_sp_input[sp] = scipy_sp_input_raw[sp]
        sol = scipy_sp_input
        res = self.dsp_obj.dspin_obj.read_sp()
        errmsg = "get_sp doesn't get same values as scipy method"
        checklist = [0, 1, 50, 1000, 20000, 100000, 200000, 220671]
        truelist = []
        i = 0
        while i < len(checklist):
            if sol[0][checklist[i]] == res[0][checklist[i]]:
                bool = True
            else:
                bool = False
            truelist.append(bool)
            i += 1
        self.assertTrue(truelist, msg=errmsg)

    def test_hrtf_blocksize(self):
        """
        H2 -- test_hrtf_size
        ===================
        **Test whether hrtf_blocksize is calculated correct by dsp algorithm**

        Author: Felix Pfreundtner
        """

        # Manually set correct standard HRTF Size in Samples
        result_correct = 513
        result_test = self.dsp_obj.dspin_obj.hrtf_blocksize

        errmsg = "wrong hrtf block size calculation"
        self.assertEqual(result_correct, result_test, msg=errmsg)

    def test_fft_blocksize(self):
        """
        H2 -- test_fft_blocksize
        ===================
        **Test whether fft_blocksize is calculated correct by dsp algorithm**

        Author: Felix Pfreundtner
        """

        # Manually set correct standard FFT Block Size in Samples
        result_correct = 1024
        result_test = self.dsp_obj.dspin_obj.fft_blocksize

        errmsg = "wrong fft block size calculation"
        self.assertEqual(result_correct, result_test, msg=errmsg)

    def test_sp_blocksize(self):
        """
        H2 -- test_sp_blocksize
        ===================
        **Test whether sp_blocksize is calculated correct by dsp algorithm**

        Author: Felix Pfreundtner
        """

        # Manually set correct standard Speaker Block Size in Samples
        result_correct = self.dsp_obj.dspin_obj.fft_blocksize + 1 - \
            self.dsp_obj.dspin_obj.hrtf_blocksize
        result_test = self.dsp_obj.dspin_obj.sp_blocksize

        errmsg = "wrong speaker block size calculation"
        self.assertEqual(result_correct, result_test, msg=errmsg)

    def test_overlap(self):
        """
        H2 -- test_overlap
        ===================
        **Test whether overlap is calculated correct by dsp algorithm**

        Author: Felix Pfreundtner
        """

        # Manually set correct standard Overlap in decimal value
        result_correct = 0.5
        result_test = self.dsp_obj.dspin_obj.overlap

        errmsg = "wrong speaker block size calculation"
        self.assertEqual(result_correct, result_test, msg=errmsg)

    def test_hopsize(self):
        """
        H2 -- test_hopsize
        ===================
        **Check whether hopsize is calculated correct by dsp algorithm**

        Author: Felix Pfreundtner
        """

        # Manually set correct standard Hopsize in decimal value
        result_correct = \
            self.dsp_obj.dspin_obj.overlap * \
            self.dsp_obj.dspin_obj.sp_blocksize

        result_test = self.dsp_obj.dspin_obj.hopsize

        errmsg = "wrong speaker block size calculation"
        self.assertEqual(result_correct, result_test, msg=errmsg)

    def test_kemar_inverse_filter(self):
        """
        H2 -- test_kemar_inverse_filter
        ===================
        **Test whether a deactivated kemar compact inverse measurement
        speaker filter in gui leads to an filter full of zeros in dsp
        algorithm ( kemar compact already includes the inverse speaker
        filter)**

        Author: Felix Pfreundtner
        """

        # model activated kemar filter in gu
        self.state.gui_settings["inverse_filter_active"] = False
        self.state.gui_settings["hrtf_database"] = "kemar_compact"

        # create new dsp_in object with modelled gui state
        dsp_in_test_obj = audio3d.dsp_in.DspIn(self.state)
        result_test = dsp_in_test_obj.kemar_inverse_filter

        errmsg = "Inverse Filter just holds zeros"
        self.assertEqual(np.amax(result_test), 0, msg=errmsg)

    def test_get_sp_block_in_file(self):
        """
        H2 -- test_get_sp_block_in_file
        ===================
        **Test whether the read in block size of a speaker for different
        positions in the the whole sp file is correct**

        Author: Felix Pfreundtner
        """
        iteration_number = 5
        result_correct = self.dsp_obj.spn * iteration_number * \
            self.dsp_obj.dspin_obj.sp_blocksize
        result_test = 0
        # run 5 iterations
        for blockcounter in range(iteration_number):
            # set position in speaker file
            self.dsp_obj.dspin_obj.set_block_begin_end()
            for sp in range(self.dsp_obj.spn):
                # get block at position
                _ = self.dsp_obj.dspin_obj.get_sp_block(sp)  # flake8: noqa
                result_test += len(self.dsp_obj.dspin_obj.sp_block[sp])

        # set self.block_begin_end back to initialize value
        self.dsp_obj.dspin_obj.init_set_block_begin_end()

        errmsg = "Wrong block sizes was read in"
        self.assertEqual(result_correct, result_test, msg=errmsg)

    def test_get_sp_block_1_out_of_file(self):
        """
        H2 -- test_get_sp_block_1_out_of_file
        ===================
        **Test whether sp block is zeropadded to sp_blocksize when a block
        position higher than samplenumber (sp_param[sp][0]) is adressed**

        Author: Felix Pfreundtner
        """
        result = True
        for sp in range(self.dsp_obj.spn):
            # set first sample which needs to be read in as the last sample in
            # the wave signal of the speaker
            self.dsp_obj.dspin_obj.block_begin_end[0] = \
                self.dsp_obj.dspin_obj.sp_param[sp][0] - 1
            # last samples which needs to be read in is out of the wave file
            self.dsp_obj.dspin_obj.block_begin_end[1] =  \
                self.dsp_obj.dspin_obj.block_begin_end[0] + \
                self.dsp_obj.dspin_obj.sp_blocksize

            self.dsp_obj.dspin_obj.get_sp_block(sp)
            length = len(self.dsp_obj.dspin_obj.sp_block[sp])
            if length < self.dsp_obj.dspin_obj.sp_blocksize:
                result = False
                break

        # set self.block_begin_end back to initialize value
        self.dsp_obj.dspin_obj.init_set_block_begin_end()

        errmsg = "Wrong block sizes was read in"
        self.assertTrue(result, msg=errmsg)

    def test_normalize(self):
        """
        H2 -- test_normalize
        ===================
        **Test whether the speaker blocks are correctly normalized to
        maximum int 16 amplitude**

        Author: Felix Pfreundtner
        """
        maximum_int16_amplitude = 32767
        iteration_number = 5
        result_test = True
        # run 5 iterations
        for blockcounter in range(iteration_number):
            # set position in speaker file
            self.dsp_obj.dspin_obj.set_block_begin_end()
            for sp in range(self.dsp_obj.spn):
                # set gui normalize state to true
                self.state.gui_sp[sp]["normalize"] = True
                # get block at position
                _ = self.dsp_obj.dspin_obj.get_sp_block(sp)  # flake8: noqa
                # get maximum value of not normalized block
                amp_unnormalized = int(np.amax(abs(
                    self.dsp_obj.dspin_obj.sp_block[sp])))
                # normalize block at position
                self.dsp_obj.dspin_obj.normalize(sp)
                # get maximum value of normalized block
                amp_normalized = int(np.amax(abs(
                    self.dsp_obj.dspin_obj.sp_block[sp])))
                if amp_normalized and amp_unnormalized != 0:
                    division = int(amp_unnormalized / amp_normalized * 1000)
                    compare = \
                        int(self.dsp_obj.dspin_obj.sp_max_amp[
                            sp]/maximum_int16_amplitude * 1000)
                    if division == compare:
                        result_test = True
                    else:
                        result_test = False
                        break

        # set self.block_begin_end back to initialize value
        self.dsp_obj.dspin_obj.init_set_block_begin_end()

        errmsg = "Files were not normalized correctly"
        self.assertTrue(result_test, msg=errmsg)

    def test_set_fftfreq(self):
        """
        H2 -- test_set_fftfreq
        ===================
        **Tests whether calculates the correct number of fft frequency values
         for given input paramaters**

        Author: Felix Pfreundtner
        """
        fft_blocksize = 1024
        samplerate = 44100
        result_correct = (fft_blocksize // 2 + 1) * self.dsp_obj.spn

        self.dsp_obj.dspin_obj.set_fftfreq(fft_blocksize, samplerate)
        result_test = 0
        for sp in range(self.dsp_obj.spn):
            result_test += len(self.state.dsp_sp_spectrum[sp][:, 0])

        errmsg = "Wrong number of frequency points in spectrum"
        self.assertEqual(result_correct, result_test, msg=errmsg)

    def test_overlap_add(self):
        """
        H2 -- test_overlap_add
        ===================
        **Tests whether overlap add algorithm calculates the correct block
        output sizes**

        Author: Felix Pfreundtner
        """
        # standard parameter
        fft_blocksize = 1024
        hopsize = 256

        iteration_number = 5
        length_out_correct = hopsize
        length_add_correct = fft_blocksize - hopsize
        result = True
        # run 5 iterations
        for blockcounter in range(iteration_number):
            # set position in speaker file
            self.dsp_obj.dspin_obj.set_block_begin_end()
            for sp in range(self.dsp_obj.spn):
                # get block at position
                _ = self.dsp_obj.dspin_obj.get_sp_block(sp)  # flake8: noqa
                # get hrtfs for speaker
                self.dsp_obj.dspin_obj.get_hrtf_block_fft(sp)
                # for left and right ear
                for l_r in range(2):
                    # convolve block
                    self.dsp_obj.dspout_obj.sp_binaural_block[sp][:, l_r] = \
                        self.dsp_obj.dspin_obj.fft_convolution(sp, l_r)
                    # apply overlap_add algorithm
                    self.dsp_obj.dspout_obj.overlap_add(fft_blocksize, hopsize,
                                                        sp)
                    # length (now played) out part
                    length_out = len(
                        self.dsp_obj.dspout_obj.sp_binaural_block_out[sp])
                    # length (later played) add part
                    lenght_add = len(
                        self.dsp_obj.dspout_obj.sp_binaural_block_add[sp])

                    if length_out != length_out_correct or lenght_add != \
                            length_add_correct:
                        result = False
                        break

        # set self.block_begin_end back to initialize value
        self.dsp_obj.dspin_obj.init_set_block_begin_end()

        errmsg = "Wrong output of overlap add algorithm"
        self.assertTrue(result, msg=errmsg)

    def test_mix_binaural_block(self):
        """
        **Test whether final binaural block output has a higher amplitude
        than int16 maximum allows, which would lead to clipping in PortAudio**

        Author: Felix Pfreundtner
        """
        # standard parameter
        fft_blocksize = 1024
        hopsize = 256
        maximum_int16_amplitude = 32767

        iteration_number = 300
        result = True
        # run 300 iterations
        for blockcounter in range(iteration_number):
            # set position in speaker file
            self.dsp_obj.dspin_obj.set_block_begin_end()
            for sp in range(self.dsp_obj.spn):

                # set gui maximum volume settings
                self.state.gui_sp[sp]["distance"] = 0
                self.state.gui_sp[sp]["normalize"] = True

                # get block at position
                _ = self.dsp_obj.dspin_obj.get_sp_block(sp)
                # get hrtfs for speaker
                self.dsp_obj.dspin_obj.get_hrtf_block_fft(sp)
                # for left and right ear
                for l_r in range(2):
                    # convolve block
                    self.dsp_obj.dspout_obj.sp_binaural_block[sp][:, l_r] = \
                        self.dsp_obj.dspin_obj.fft_convolution(sp, l_r)
                    # apply overlap_add algorithm
                    self.dsp_obj.dspout_obj.overlap_add(fft_blocksize, hopsize,
                                                        sp)
            # mix all speaker binaural blocks to one binaural block output
            self.dsp_obj.dspout_obj.mix_binaural_block(hopsize)
            amplitude_binaural_block = np.amax(abs(
                self.dsp_obj.dspout_obj.binaural_block))
            if amplitude_binaural_block > maximum_int16_amplitude:
                result = False
                break

        # set self.block_begin_end back to initialize value
        self.dsp_obj.dspin_obj.init_set_block_begin_end()

        errmsg = "To high 16 bit integer amplitude in binaural output -> " \
                 "clipping"
        self.assertTrue(result, msg=errmsg)

        self.dsp_obj.dspout_obj.mix_binaural_block(hopsize)

if __name__ == '__main__':
    unittest.main()
