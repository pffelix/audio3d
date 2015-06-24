__author__ = 'Matthias'

import unittest
import dsp_in
import dsp_out
import mockup


class DspTests(unittest.TestCase):

    def __init__(self):
        self.DspIn_TestObj = dsp_in.DspIn(gui_dict_init, gui_settings_dict_init)
        self.DspOut_TestObj = dsp_out.DspOut(gui_dict_init,
                                             self.DspIn_Object.fft_blocksize,
                                             self.DspIn_Object.sp_blocksize,
                                             self.DspIn_Object.hopsize,
                                             gui_stop_init, gui_pause_init)
        self.mockup = mockup.gui_dict_mockup
        print("A")

    def test_rnd(self):
        print("B")
        value = 2.55
        res = self.DspIn_TestObj.rnd(value)
        error_msg = "test_rnd failed: Function does not properly round 2.55 " \
                    "to 3"
        self.assertEqual(res, 3, msg=error_msg)
    print("C")
#if __name__ == '__main__':
    unittest.main()
    print("D")
