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

    def test_get_block(self):