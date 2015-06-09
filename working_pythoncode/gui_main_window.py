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
from dsp import Dsp
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
        self.view.setFixedSize(400,400)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # set property window
        self.speaker_property = SpeakerProperty()
        self.speaker_property.closed.connect(self.property_closed)

        self.init_ui()

    def init_ui(self):

        # set buttons
        add_speaker_button = QPushButton('Add Speaker')
        reset_button = QPushButton('Reset')
        control_button = QPushButton('Play/Stop')
        default_position_button = QPushButton('Default Position')

        # set layout
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(add_speaker_button)
        layout.addWidget(control_button)
        layout.addWidget(reset_button)
        layout.addWidget(default_position_button)

        # connect signal and slots
        add_speaker_button.clicked.connect(self.add_speaker)
        reset_button.clicked.connect(self.reset)
        control_button.clicked.connect(self.control)
        default_position_button.clicked.connect(self.positions)

        # set window
        self.setLayout(layout)
        self.setWindowTitle('3D Audio')
        self.show()

    @pyqtSlot()
    def show_property(self):

        from gui_utils import speaker_to_show
        i = speaker_to_show
        path = str(gui_dict[i][2])
        azimuth = str(gui_dict[i][0])
        dist = str(gui_dict[i][1])
        self.speaker_property.path_line_edit.setText(path)
        self.speaker_property.azimuth_line_edit.setText(azimuth)
        self.speaker_property.distance_line_edit.setText(dist)
        self.speaker_property.show()
        self.speaker_property.added.connect(self.change_property)

    def change_property(self):

        from gui_utils import speaker_to_show
        i = speaker_to_show
        x_new = self.speaker_property.posx
        y_new = self.speaker_property.posy
        speaker_list[i].setPos(x_new, y_new)
        speaker_list[i].cal_rel_pos()

    def property_closed(self):

        self.speaker_property.added.disconnect()
        self.speaker_property.clear()

    @pyqtSlot()
    def add_speaker(self):

        self.speaker_property.added.connect(self.add2scene)
        self.speaker_property.azimuth_line_edit.setText('315.0')
        self.speaker_property.distance_line_edit.setText('2.4')
        self.speaker_property.show()

    @pyqtSlot()
    def add2scene(self):

        if len(gui_dict) < 6:

            # read in data
            index = len(gui_dict)
            path = self.speaker_property.path
            x = self.speaker_property.posx
            y = self.speaker_property.posy

            # create new speaker
            if self.speaker_property.normalize_box.isChecked():
                new_speaker = Speaker(index, path, x, y, True)
            else:   
                new_speaker = Speaker(index, path, x, y)
            new_speaker.signal_handler.show_property.connect(self.show_property)
            self.room.addItem(speaker_list[-1])
            self.view.viewport().update()

            # # clean up
            # self.speaker_property.added.disconnect()
            # self.speaker_property.clear()
        else:
            return

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
        self.dsp_object = Dsp(gui_dict)
        self.dsp_object.signal_handler.error_occur.connect(self.show_error)
        play = threading.Thread(target=self.dsp_object.run)
        play.start()
        print()

    @pyqtSlot()
    def show_error(self):
        print(self.dsp_object.signal_handler.error_message)

    def positions(self):
        n = len(gui_dict)
        if n == 0:
            return
        elif n == 1:
            speaker_list[0].setPos(170, 50)
            speaker_list[0].cal_rel_pos()
        elif n == 2:
            speaker_list[0].setPos(100, 50)
            speaker_list[1].setPos(240, 50)
            speaker_list[0].cal_rel_pos()
            speaker_list[1].cal_rel_pos()
        elif n == 3:
            speaker_list[0].setPos(170, 50)
            speaker_list[1].setPos(50, 20)
            speaker_list[2].setPos(290, 20)
            speaker_list[0].cal_rel_pos()
            speaker_list[1].cal_rel_pos()
            speaker_list[2].cal_rel_pos()
        elif n == 4:
            speaker_list[0].setPos(50, 20)
            speaker_list[1].setPos(290, 20)
            speaker_list[2].setPos(290, 320)
            speaker_list[3].setPos(50, 320)
            speaker_list[0].cal_rel_pos()
            speaker_list[1].cal_rel_pos()
            speaker_list[2].cal_rel_pos()
            speaker_list[3].cal_rel_pos()
        elif n == 5:
            speaker_list[0].setPos(50, 20)
            speaker_list[1].setPos(290, 20)
            speaker_list[2].setPos(290, 320)
            speaker_list[3].setPos(50, 320)
            speaker_list[4].setPos(170, 50)
            speaker_list[0].cal_rel_pos()
            speaker_list[1].cal_rel_pos()
            speaker_list[2].cal_rel_pos()
            speaker_list[3].cal_rel_pos()
            speaker_list[4].cal_rel_pos()
        elif n == 6:
            speaker_list[0].setPos(50, 20)
            speaker_list[1].setPos(290, 20)
            speaker_list[2].setPos(290, 320)
            speaker_list[3].setPos(50, 320)
            speaker_list[4].setPos(170, 50)
            speaker_list[5].setPos(290, 170)
            speaker_list[0].cal_rel_pos()
            speaker_list[1].cal_rel_pos()
            speaker_list[2].cal_rel_pos()
            speaker_list[3].cal_rel_pos()
            speaker_list[4].cal_rel_pos()
            speaker_list[5].cal_rel_pos()
        else:
            return

    def closeEvent (self, eventQCloseEvent):
        self.room.clear()
        eventQCloseEvent.accept()


def main():

    w = MainWindow()
    return qApp.exec_()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main()