
import unittest
from mock import patch
import sys
from gui_main_window import *

class TestHeadtracker(unittest.TestCase):

    def setUp(self):
        self.state = State()

    @patch('gui_utils.Headtracker.get_head_deg')
    def test_head_deg(self, get_head_deg):
        app = QApplication(sys.argv)

        get_head_deg.return_value = 30
        sp = Speaker(self.state, 1, 'unknown')
        sp.cal_rel_pos(get_head_deg())
        result = self.state.gui_dict[1][0]
        self.assertEqual(result, 285)

    @patch('gui_utils.Headtracker.get_head_deg')
    def test_over_360(self, get_head_deg):

        get_head_deg.return_value = 320
        sp = Speaker(self.state, 1, 'unknown')
        sp.cal_rel_pos(get_head_deg())
        result = self.state.gui_dict[1][0]
        self.assertEqual(result, 355)
