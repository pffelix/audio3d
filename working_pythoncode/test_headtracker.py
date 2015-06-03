
import unittest
from mock import patch

from gui_utils import *
from gui_main_window import *

class TestHeadtracker(unittest.TestCase):

    @patch('gui_utils.Headtracker.get_head_deg')
    def test_cal_rel_pos(self,get_head_deg):

        app = QApplication(sys.argv)
        get_head_deg.return_value = 30
        sp = Speaker(1,'unknown')
        sp.cal_rel_pos()
        result = gui_dict[1][0]
        self.assertEqual(result, 345)
