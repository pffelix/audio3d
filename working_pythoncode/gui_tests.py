# -*- coding: utf-8 -*-
"""
Created on Thu Jul  2 13:46:25 2015

@author: mh
"""

import unittest
import gui_utils
import sys


class GuiTests(unittest.TestCase):
    def setUp(self):
        self.state = gui_utils.State()

    # @brief tests function switch_stop_playback() from gui_utils
    def test_switch_stop_playback(self):
        sol = self.state.switch_stop_playback()
        error_msg = "test_switch_stop_playback failed!"
        self.assertEqual(sol, True, msg=error_msg)

    # @brief tests function switch_pause_playbac() from gui_utils
    def test_switch_pause_playback(self):
        sol = self.state.switch_pause_playback()
        error_msg = "test_switch_pause_playback failed!"
        self.assertEqual(sol, True, msg=error_msg)

    # @brief tests function get_bound_pos() from gui_utils
    def test_get_bound_pos_negative(self):
        x = 350
        y = -30
        solx, soly = gui_utils.get_bound_pos(x, y)
        res_x = 350
        res_y = 0
        error_msg = "test_get_bound_pos_negative failed!"
        self.assertEqual(solx, res_x, msg=error_msg)
        self.assertEqual(soly, res_y, msg=error_msg)

    # @brief tests function get_bound_pos() from gui_utils
    def test_get_bound_pos_float(self):
        x = 370
        y = 0.0
        solx, soly = gui_utils.get_bound_pos(x, y)
        res_x = 350
        res_y = 0
        error_msg = "test_get_bound_pos_float failed!"
        self.assertEqual(solx, res_x, msg=error_msg)
        self.assertEqual(soly, res_y, msg=error_msg)

    # @brief tests function get_abs_pos() from gui_utils
    def test_get_abs_pos_zero(self):
        res = [170, 170]
        solx, soly = self.state.get_abs_pos(90, 0)
        error_msg = "test_get_abs_pos_zero failed!"
        self.assertEqual(solx, res[0], msg=error_msg)
        self.assertEqual(soly, res[1], msg=error_msg)

    # @brief tests function get_abs_pos() from gui_utils
    def test_get_abs_pos_float(self):
        res = [170, 170]
        solx, soly = self.state.get_abs_pos(1.0, 0)
        error_msg = "test_get_abs_pos_float failed!"
        self.assertEqual(solx, res[0], msg=error_msg)
        self.assertEqual(soly, res[1], msg=error_msg)

    # @brief tests function get_abs_pos() from gui_utils
    def test_get_abs_pos(self):
        res = [170, 270]
        solx, soly = self.state.get_abs_pos(180, 100)
        error_msg = "test_get_abs_pos failed!"
        self.assertEqual(solx, res[0], msg=error_msg)
        self.assertEqual(soly, res[1], msg=error_msg)


if __name__ == '__main__':
    app = gui_utils.QtGui.QApplication(sys.argv)
    unittest.main()
