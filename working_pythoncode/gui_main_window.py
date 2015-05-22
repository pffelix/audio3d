#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
A Simple sketch of the Gui
author: H. Zhu
"""

import sys
from PyQt4.QtGui import *

class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow,self).__init__()
        self.init_ui()

    def init_ui(self):
        # set scene and view
        scene = QGraphicsScene()
        speaker1 = QGraphicsRectItem()
        speaker1.setRect(0,0,100,100)
        scene.addItem(speaker1)
        view = QGraphicsView(scene)

        # set layout
        layout = QVBoxLayout()
        layout.addWidget(view)
        layout.addWidget(QPushButton('Add Speaker'))
        layout.addWidget(QPushButton('Reset'))

        # set window
        self.setLayout(layout)
        self.resize(640,480)
        self.setWindowTitle('3DAudio')
        self.show()

def main():

    app = QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
