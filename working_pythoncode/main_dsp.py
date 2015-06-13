# -*- coding: utf-8 -*-
"""
Created on Fri Jun  12 15:45:23 2015

@author: Felix Pfreundtner
"""
from PyQt4.QtGui import *
import sys
import dsp

# if you want to start dsp algorithm without gui run dsp_main und uncomment actualization of gui_dict in dsp.py line 53 (# self.gui_dict = gui_utils.gui_dict):
def main():
    gui_dict_mockup = {0: [90, 0, "./audio_in/sine_1kHz_(44.1,1,16).wav", False]#,
                       # 0: [120, 1, "./audio_in/electrical_guitar_(44.1,1,16).wav", True]#,
                       #2: [0, 1, "./audio_in/synthesizer_(44.1,1,16).wav", True]
                      }
    dsp_object = dsp.Dsp(gui_dict_mockup)
    dsp_object.run()
    print()
if __name__ == '__main__':
    main()