# -*- coding: utf-8 -*-
"""
Created on Fri Jun  12 15:45:23 2015

@author: Felix Pfreundtner
"""
from PyQt4.QtGui import *
import sys
import dsp
import multiprocessing

# if you want to start dsp algorithm without gui run dsp_main und uncomment actualization of gui_dict, gui_stop_init and gui_pause_init in dsp.py line 49-51 (# self.gui_dict = gui_utils.gui_dict):
def main():
    if __name__ == '__main__':
        gui_dict_mockup = {0: [90, 0, "./audio_in/sine_1kHz_(44.1,1,16).wav",
                               True],
                           1: [120, 1, "./audio_in/electrical_guitar_(44.1,1,"
                                       "16).wav", True],
                           #2: [0, 1, "./audio_in/synthesizer_(44.1,1,16).wav",
                           # True],
                           # 0: [90, 2, "./audio_in/music_mix_(44.1,2,16).wav", True]
                          }
        gui_settings_dict_mockup = {"hrtf_database": "kemar_compact",
                         "inverse_filter_active": True,
                         "bufferblocks": 5}
        if gui_settings_dict_mockup["hrtf_database"] == "kemar_compact":
            gui_settings_dict_mockup["inverse_filter_active"] = False
        gui_stop_mockup = False
        gui_pause_mockup = False
        return_exe_mockup = multiprocessing.Queue()
        return_exe_mockup.put(False)
        dsp_object = dsp.Dsp(gui_dict_mockup, gui_stop_mockup,
                             gui_pause_mockup, gui_settings_dict_mockup,
                             return_exe_mockup)
        dsp_object.run()
        print()
if __name__ == '__main__':
    main()

