#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
A Simple sketch of the Gui
author: H. Zhu
"""

import sys
from PyQt4.QtGui import *


def main():

    app = QApplication(sys.argv)

    # set scene and view
    scene = QGraphicsScene()
    rect = QGraphicsRectItem()
    rect.setRect(0,0,100,100)
    scene.addItem(rect)
    view = QGraphicsView(scene)

    # set window and layout
    window = QWidget()
    layout = QVBoxLayout()
    window.setLayout(layout)
    layout.addWidget(view)
    layout.addWidget(QPushButton('Add Speaker'))
    layout.addWidget(QPushButton('Reset'))
    window.resize(640,480)
    window.setWindowTitle('3DAudio')
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
