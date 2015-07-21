import unittest
import audio3d.gui_utils
import sys

class GuiTests(unittest.TestCase):
    """
    H1 -- GuiTests
    ************************
    **Test class for GUI.**
    Athor: Huijiang, Manuela
    """
    def __init__(self, *args, **kwargs):
        # calling the constructor of the super class
        super(GuiTests, self).__init__(*args, **kwargs)
        # initialze GUI State
        self.state = audio3d.gui_utils.State()

    def test_switch_stop_playback_true(self):
        """
        H2 -- test_switch_stop_playback (condition true)
        ===================
        **This tests function switch_stop_playback() from gui_utils.**
        """
        self.state.dsp_stop = False
        self.state.switch_stop_playback()
        sol = self.state.dsp_stop
        error_msg = "test_switch_stop_playback failed!"
        self.assertEqual(sol, True, msg=error_msg)

    def test_switch_stop_playback_false(self):
        """
        H2 -- test_switch_stop_playback (condition false)
        ===================
        **This tests function switch_stop_playback() from gui_utils.**
        """
        self.state.dsp_stop = True
        self.state.switch_stop_playback()
        sol = self.state.dsp_stop
        error_msg = "test_switch_stop_playback failed!"
        self.assertEqual(sol, False, msg=error_msg)

    def test_switch_pause_playback_true(self):
        """
        H2 -- test_switch_pause_playback (condition true)
        ===================
        **This tests function switch_pause_playback() from gui_utils.**
        """
        self.state.dsp_pause = False
        self.state.switch_pause_playback()
        sol = self.state.dsp_pause
        error_msg = "test_switch_pause_playback failed!"
        self.assertEqual(sol, True, msg=error_msg)

    def test_switch_pause_playback_false(self):
        """
        H2 -- test_switch_pause_playback (condition false)
        ===================
        **This tests function switch_pause_playback() from gui_utils.**
        """
        self.state.dsp_pause = True
        self.state.switch_pause_playback()
        sol = self.state.dsp_pause
        error_msg = "test_switch_pause_playback failed!"
        self.assertEqual(sol, False, msg=error_msg)

    def test_get_bound_pos_negative(self):
        """
        H2 -- test_get_bound_pos_negative
        ===================
        **This tests function get_bound_pos() from gui_utils for netative
        values.**
        """
        x = 350
        y = -30
        room = audio3d.gui_utils.Room(self.state)
        solx, soly = audio3d.gui_utils.Room.get_bound_pos(room, x, y)
        res_x = 350
        res_y = 0
        error_msg = "test_get_bound_pos_negative failed!"
        self.assertEqual(solx, res_x, msg=error_msg)
        self.assertEqual(soly, res_y, msg=error_msg)

    def test_get_bound_pos_float(self):
        """
        H2 -- test_get_bound_pos_float
        ===================
        **This tests function get_bound_pos() from gui_utils for float
        values.**
        """
        x = 370
        y = 0.0
        room = audio3d.gui_utils.Room(self.state)
        solx, soly = audio3d.gui_utils.Room.get_bound_pos(room, x, y)
        res_x = 350
        res_y = 0
        error_msg = "test_get_bound_pos_float failed!"
        self.assertEqual(solx, res_x, msg=error_msg)
        self.assertEqual(soly, res_y, msg=error_msg)

    def test_get_abs_pos_zero(self):
        """
        H2 -- test_get_abs_pos_zero
        ===================
        **This tests function get_abs_pos() from gui_utils for zero entries.**
        """
        res = [170, 170]
        room = audio3d.gui_utils.Room(self.state)
        solx, soly = audio3d.gui_utils.Room.get_abs_pos(room, 90, 0)
        error_msg = "test_get_abs_pos_zero failed!"
        self.assertEqual(solx, res[0], msg=error_msg)
        self.assertEqual(soly, res[1], msg=error_msg)

    def test_get_abs_pos_float(self):
        """
        H2 -- test_get_abs_pos_float
        ===================
        **This tests function get_abs_pos() from gui_utils for floats.**
        """
        res = [170, 170]
        room = audio3d.gui_utils.Room(self.state)
        solx, soly = audio3d.gui_utils.Room.get_abs_pos(room, 1.0, 0)
        error_msg = "test_get_abs_pos_float failed!"
        self.assertEqual(solx, res[0], msg=error_msg)
        self.assertEqual(soly, res[1], msg=error_msg)

    def test_get_abs_pos(self):
        """
        H2 -- test_get_abs_pos_float
        ===================
        **This tests function get_abs_pos() from gui_utils.**
        """
        res = [170, 270]
        room = audio3d.gui_utils.Room(self.state)
        solx, soly = audio3d.gui_utils.Room.get_abs_pos(room, 180, 100)
        error_msg = "test_get_abs_pos failed!"
        self.assertEqual(solx, res[0], msg=error_msg)
        self.assertEqual(soly, res[1], msg=error_msg)

if __name__ == '__main__':
    app = audio3d.gui_utils.QtGui.QApplication(sys.argv)
    unittest.main()
