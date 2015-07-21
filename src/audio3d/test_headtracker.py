
import unittest
from mock import patch
import sys
import audio3d.gui_main_window
import audio3d.gui_utils


class TestHeadtracker(unittest.TestCase):
    """
    H1 -- TestHeadtracker
    ************************
    **Test class for the headtracker integration.**
    Athor: Huijiang
    """

    def setUp(self):
        self.state = gui_utils.State()

    @patch('gui_utils.Headtracker.get_head_deg')
    def test_head_deg(self, get_head_deg):
        """
        H2 -- test_head_deg
        ===================
        **This tests wheter the azimuthal angle is correctly converted for the
        position of a speaker item.**
        """

        get_head_deg.return_value = 30
        sp = gui_utils.Speaker(self.state, 0, 'unknown')
        sp.cal_rel_pos(get_head_deg())
        result = self.state.gui_sp[0]['angle']
        self.assertEqual(result, 285)

    @patch('gui_utils.Headtracker.get_head_deg')
    def test_over_360(self, get_head_deg):
        """
        H2 -- test_head_deg
        ===================
        **This tests whether the azimuthal angle is correctly applied if the
        angle would result in something greater than 360°.**
        """

        get_head_deg.return_value = 320
        sp = gui_utils.Speaker(self.state, 0, 'unknown')
        sp.cal_rel_pos(get_head_deg())
        result = self.state.gui_sp[0]['angle']
        self.assertEqual(result, 355)

if __name__ == '__main__':
    app = gui_main_window.QtGui.QApplication(sys.argv)
    unittest.main()
