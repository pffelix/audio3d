#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
A Simple sketch of the Gui
author: H. Zhu
"""

import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from gui_utils import *

class MainWindow(QWidget):

    speaker_list = []

    def __init__(self):
        super(MainWindow,self).__init__()
        self.setAcceptDrops(True)
        self.init_ui()

    def init_ui(self):

        def addspeaker():

            new_speaker = Item()
            new_speaker.setPos(0, 0)
            self.speaker_list.append(new_speaker)
            scene.addItem(new_speaker)
            view.viewport().update()

        # set items
        speaker = Item()
        speaker.setPos(0, 0)
        self.speaker_list.append(speaker)

        # set scene and view
        scene = Room()
        scene.setSceneRect(0,0,250,250)
        scene.addItem(speaker)
        view = View(scene)

        # set buttons
        add_speaker_button = AddSpeakerButton()

        # set layout
        layout = QVBoxLayout()
        layout.addWidget(view)
        layout.addWidget(add_speaker_button)
        layout.addWidget(QPushButton('Reset'))

        # connect signal and slots
        add_speaker_button.clicked.connect(addspeaker)
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
