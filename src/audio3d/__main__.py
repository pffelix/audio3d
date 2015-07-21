# -*- coding: utf-8 -*-
"""
Created on Fri Jun  12 15:30:53 2015

@author: Felix Pfreundtner
"""
from PySide.QtGui import QApplication
import sys
import audio3d.gui_main_window


def main():
    app = QApplication(sys.argv)
    mainwindow = audio3d.gui_main_window.MainWindow()
    mainwindow.show()
    return app.exec_()

if __name__ == '__main__':
    main()
