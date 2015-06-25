__author__ = 'Matthias'
import unittest
import dsp_in
import dsp_out

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

DspIn_TestObj = dsp_in.DspIn(gui_dict_mockup,gui_settings_dict_mockup)
DspOut_TestObj = dsp_out.DspOut(gui_dict_mockup,
                                DspIn_TestObj.fft_blocksize,
                                DspIn_TestObj.sp_blocksize,
                                DspIn_TestObj.hopsize,
                                DspIn_TestObj, gui_pause_mockup)


class DspTests(unittest.TestCase):

    # def __init__(self):
    #     self.DspIn_TestObj = dsp_in.DspIn(gui_dict_mockup,
    #                                       gui_settings_dict_mockup)
    #     self.DspOut_TestObj = dsp_out.DspOut(gui_dict_mockup,
    #                                          DspIn_TestObj.fft_blocksize,
    #                                          DspIn_TestObj.sp_blocksize,
    #                                          DspIn_TestObj.hopsize,
    #                                          DspIn_TestObj, gui_pause_mockup)

    def test_rnd_int(self):
        val = 1.9
        sol = 2
        res = DspIn_TestObj.rnd(val)
        error_msg = "test_rnd_int failed!"
        self.assertEqual(res, sol, msg=error_msg)

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

    def test_hann_window(self):
        sol_hannwin_2 = 0.00014997
        sol_hannwin_200 = 0.88477
        res = DspIn_TestObj.build_hann_window(sp_blocksize=513)
        errmsg = "Hanning Window not calculated correctly"
        self.assertAlmostEqual(res[2], sol_hannwin_2, 5, msg=errmsg)
        self.assertAlmostEqual(res[200], sol_hannwin_200, 5, msg=errmsg)

    def test_get_block_param(self):
        sol = [512, 0.011609977324263039, 0.5, 256]
        res = [None] * 3
        #res[0], res[1], res[2], res[3]\
        res[0: 3] = DspIn_TestObj.get_block_param(
            wave_param_common, hrtf_blocksize, fft_blocksize)
        errmsg = "Function get_block_param (in DspIn) doesn't work properly"
        self.assertListEqual(res, sol, msg=errmsg)

if __name__ == '__main__':
    unittest.main()
