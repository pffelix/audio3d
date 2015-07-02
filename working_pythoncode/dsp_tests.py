__author__ = 'Matthias'
import unittest
import dsp_in
import dsp_out
from unittest.mock import MagicMock
import numpy as np

gui_dict_mockup = \
    {
    0: [90, 0, "./audio_in/sine_1kHz_(44.1,1,16).wav", False]
    #0: [120, 1, "./audio_in/electrical_guitar_(44.1,1,16).wav", True]
    #0: [0, 1, "./audio_in/synthesizer_(44.1,1,16).wav", #  True]
    }

gui_settings_dict_mockup = {"hrtf_database": "kemar_normal_ear",
                            "inverse_filter_active": True,
                            "bufferblocks": 5}
gui_stop_mockup = False
gui_pause_mockup = False
wave_param_common = [44100, 16]
hrtf_blocksize = 513
fft_blocksize = 1024
sp_blocksize = 512
sp_blocktime = 0.011609977324263039
overlap = 0.5
hopsize = 256


DspIn_TestObj = dsp_in.DspIn(gui_dict_mockup, gui_settings_dict_mockup)
DspOut_TestObj = dsp_out.DspOut(gui_dict_mockup,
                                DspIn_TestObj.fft_blocksize,
                                DspIn_TestObj.sp_blocksize,
                                DspIn_TestObj.hopsize,
                                DspIn_TestObj, gui_pause_mockup)
#following calculation of block_begin_end must be equal to the one in the
# function
block_begin_end = np.zeros((2,), dtype=np.int16)


class DspTests(unittest.TestCase):

    def __init__(self):
        self.DspIn_TestObj = dsp_in.DspIn(gui_dict_mockup,
                                          gui_settings_dict_mockup)
        self.DspOut_TestObj = dsp_out.DspOut(gui_dict_mockup,
                                             DspIn_TestObj.fft_blocksize,
                                             DspIn_TestObj.sp_blocksize,
                                             DspIn_TestObj.hopsize,
                                             DspIn_TestObj, gui_pause_mockup)

    # @brief Tests rnd for one particular number.
    def test_rnd_int(self):
        val = 1.9
        sol = 2
        res = DspIn_TestObj.rnd(val)
        error_msg = "test_rnd_int failed!"
        self.assertEqual(res, sol, msg=error_msg)

    # @brief Tests rnd for a list of numbers at the same time.
    def test_rnd(self):
        i = 0
        value = [2.55, 7.9, (2 / 3), 0.5, 0.00001, 500.1, -80.1, -1.4142, -9.5]
        res = [None] * len(value)
        sol = [3, 8, 1, 1, 0, 500, -80, -1, -10]
        # value = []
        #value[0] = 2
        # sol = 2
        while i < len(value):
            #res[i] = res.append(DspIn_TestObj.rnd(value[i]))
            res[i] = DspIn_TestObj.rnd(value[i])
            i += 1
        error_msg = "test_rnd failed!"
        self.assertListEqual(res, sol, msg=error_msg)

    # @brief Tests equality of the values at position 2 and 200 of the
    #  hamming-window.
    def test_hann_window(self):
        sol_hannwin_2 = 0.00014997
        sol_hannwin_200 = 0.88477
        res = DspIn_TestObj.build_hann_window(sp_blocksize=513)
        errmsg = "Hanning Window not calculated correctly"
        self.assertAlmostEqual(res[2], sol_hannwin_2, 5, msg=errmsg)
        self.assertAlmostEqual(res[200], sol_hannwin_200, 5, msg=errmsg)

    # @brief Tests get_block_param by comparing two lists.
    def test_get_block_param(self):
        sol = [512, 0.011609977324263039, 0.5, 256]
        res = [None] * 3
        res[0: 3] = DspIn_TestObj.get_block_param(
            wave_param_common, hrtf_blocksize, fft_blocksize)
        errmsg = "Function get_block_param (in DspIn) doesn't work properly"
        self.assertListEqual(res, sol, msg=errmsg)

    # @brief Tests the values of init_block_begin_end on symmetry to 0
    def test_init_set_block_begin_end(self):
        res = DspIn_TestObj.init_set_block_begin_end(gui_dict_mockup)
        errmsg = "The entries in init_block_begin_end are not symmetric to 0"
        self.assertTrue(abs(res[0]) == abs(res[1]), msg=errmsg)

    # @brief Tests the set_block_begin_end function for correctness.
    # Due to the fact, that the function does not return anything, it has to
    # be copied manually to the section between the ##### below.
    def test_set_block_begin_end(self):
        truelist = []
        i = 1
        block_begin_end = DspIn_TestObj.block_begin_end
        while i < 10:
            # Between ##### and ##### has to be the same code as in
            # set_block_begin_end-function
            #####
            block_begin_end[0] += int(sp_blocksize * (1 - overlap))
            block_begin_end[1] += int(sp_blocksize * (1 - overlap))
            #####
            if block_begin_end[1] - block_begin_end[0] == sp_blocksize:
                bool = True
            else:
                bool = False
            errmsg = "set_block_begin_end does not work properly"
            truelist.append(bool)
            i += 1
        self.assertTrue(truelist, msg=errmsg)


if __name__ == '__main__':
    unittest.main()
