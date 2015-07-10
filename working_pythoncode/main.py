# -*- coding: utf-8 -*-
"""
Created on Fri Jun  12 15:30:53 2015

@author: Felix Pfreundtner
"""
from PySide.QtGui import PySide.QtGui
import sys
import gui_main_window


def main():
    gui_main_window.MainWindow()
    return qApp.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main()
