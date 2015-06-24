__author__ = 'Matthias'
import unittest
import dsp_in
import dsp_out

gui_dict_mockup = {0: [90, 0, "./audio_in/sine_1kHz_(44.1,1,"
                               "16).wav", False]
                 #0: [120, 1, "./audio_in/electrical_guitar_(44.1,1,16).wav", True]
                 #0: [0, 1, "./audio_in/synthesizer_(44.1,1,16).wav",
                 #  True]
                  }
gui_settings_dict_mockup = {"hrtf_database": "kemar_normal_ear",
         "inverse_filter_active": True,
         "bufferblocks": 5}
gui_stop_mockup = False
gui_pause_mockup = False

DspIn_TestObj = dsp_in.DspIn(gui_dict_mockup,gui_settings_dict_mockup)
DspOut_TestObj = dsp_out.DspOut(gui_dict_mockup,
                                     DspIn_TestObj.fft_blocksize,
                                     DspIn_TestObj.sp_blocksize,
                                     DspIn_TestObj.hopsize,
                                     DspIn_TestObj, gui_pause_mockup)


class DspTests(unittest.TestCase):

    def test_rnd(self):
        print("B")
        value = 2.4
        res = DspIn_TestObj.rnd(value)
        error_msg = "test_rnd failed: Function does not properly round 2.55 " \
                    "to 3"
        self.assertEqual(res, 3, msg=error_msg)

if __name__ == '__main__':
    unittest.main()
