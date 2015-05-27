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
import algorithm_main as alg
import threading

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
        # set property window
        self.speaker_property = SpeakerProperty()

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
        add_speaker_button.clicked.connect(self.add_speaker)
        reset_button.clicked.connect(self.reset)
        control_button.clicked.connect(self.control)

        # set window
        self.setLayout(layout)
        self.setFixedSize(500, 600)
        self.setWindowTitle('3D Audio')
        self.show()

    @pyqtSlot()
    def add_speaker(self):

        self.speaker_property.added.connect(self.add2scene)
        self.speaker_property.show()


    @pyqtSlot()
    def add2scene(self):
        new_speaker = Speaker(len(gui_dict), self.speaker_property.path)
        speaker_list.append(new_speaker)
        self.room.addItem(speaker_list[-1])
        self.view.viewport().update()

    @pyqtSlot()
    def reset(self):

        self.room.clear()

        gui_dict.clear()
        del speaker_list[:]

        new_audience = Audience()
        self.room.addItem(new_audience)
        self.view.viewport().update()

    @pyqtSlot()
    def control(self):
        play = threading.Thread(target=alg.algo)
        play.start()
        
    def closeEvent (self, eventQCloseEvent):
        self.room.clear()
        eventQCloseEvent.accept()


def main():

    w = MainWindow()
    return qApp.exec_()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main()
