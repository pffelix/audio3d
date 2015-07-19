
import unittest
from mock import patch
import sys
import gui_main_window
import gui_utils


class TestHeadtracker(unittest.TestCase):

    def setUp(self):
        self.state = gui_utils.State()

    @patch('gui_utils.Headtracker.get_head_deg')
    def test_head_deg(self, get_head_deg):

        get_head_deg.return_value = 30
        sp = gui_utils.Speaker(self.state, 1, 'unknown')
        sp.cal_rel_pos(get_head_deg())
        result = self.state.gui[1][0]
        self.assertEqual(result, 285)

    @patch('gui_utils.Headtracker.get_head_deg')
    def test_over_360(self, get_head_deg):

        get_head_deg.return_value = 320
        sp = gui_utils.Speaker(self.state, 1, 'unknown')
        sp.cal_rel_pos(get_head_deg())
        result = self.state.gui[1][0]
        self.assertEqual(result, 355)

if __name__ == '__main__':
    app = gui_main_window.QtGui.QApplication(sys.argv)
    unittest.main()
