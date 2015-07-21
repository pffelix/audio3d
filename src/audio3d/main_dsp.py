# -*- coding: utf-8 -*-
"""
Created on Fri Jun  12 15:45:23 2015

@author: Felix Pfreundtner
"""
import audio3d


def main():
    if __name__ == '__main__':
        # initialize GUI state
        state = audio3d.gui_utils.State()
        # modify GUI state
        state.gui_sp = []
        state.gui_sp.append({"angle": 90, "distance": 0, "path":
                             "./audio_in/sine_1kHz_(44.1,1,16).wav",
                             "normalize": False})
        state.gui_sp.append({"angle": 120, "distance": 1, "path":
                             "./audio_in/electrical_guitar_(44.1,1,"
                             "16).wav", "normalize": True})
        state.gui_settings = {"hrtf_database": "kemar_normal_ear",
                              "inverse_filter_active": True,
                              "bufferblocks": 5}
        state.gui_stop = False
        state.gui_pause = False
        dsp_testobj = audio3d.dsp.Dsp(state)
        dsp_testobj.run()
        print()
if __name__ == '__main__':
    main()
