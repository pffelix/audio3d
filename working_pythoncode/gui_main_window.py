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

    def __init__(self):
        super(MainWindow,self).__init__()

        self.setAcceptDrops(True)
        # set items
        self.audience = Audience()
        # set scene and view
        self.room = Room()
        self.room.setSceneRect(0,0,400,400)
        self.room.addItem(self.audience)
        # set view
        self.view = View(self.room)

        self.init_ui()

    def init_ui(self):

        # set buttons
        add_speaker_button = QPushButton('Add Speaker')
        reset_button = QPushButton('Reset')
        control_button = QPushButton('Play/Stop')

        # set layout
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(add_speaker_button)
        layout.addWidget(control_button)
        layout.addWidget(reset_button)

        # connect signal and slots
        add_speaker_button.clicked.connect(self.addspeaker)
        reset_button.clicked.connect(self.reset)
        control_button.clicked.connect(self.control)

        # set window
        self.setLayout(layout)
        self.resize(500, 600)
        self.setWindowTitle('3D Audio')
        self.show()

    @pyqtSlot()
    def addspeaker(self):

        file_browser = FileBrowser()
        path = file_browser.getOpenFileName()

        new_speaker = Speaker(1+len(gui_dict), path)
        self.room.addItem(new_speaker)
        self.view.viewport().update()

    @pyqtSlot()
    def reset(self):

        for item in self.room.items():
            self.room.removeItem(item)

        gui_dict.clear()
        del speaker_list[:]

        new_audience = Audience()
        self.room.addItem(new_audience)
        self.view.viewport().update()

    @pyqtSlot()
    def control(self):
        pass


def main():

    app = QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
