# -*- coding: utf-8 -*-
"""
Created on Fri Jun  12 15:30:53 2015

@author: Felix Pfreundtner
"""
from PyQt4.QtGui import *
import sys
from . import gui_main_window

def main():
    app = QApplication(sys.argv)
    w = gui_main_window.MainWindow()
    return app.exec_()

if __name__ == '__main__':
    main()
