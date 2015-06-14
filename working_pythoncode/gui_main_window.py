#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
A Simple sketch of the Gui
author: H. Zhu
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from gui_utils import *
from dsp import Dsp
import threading

default_position = [[50, 20],[290, 20],[170, 50],[50, 320],[290, 320],[290, 170]]


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
        azimuth = "{:.0f}".format(gui_dict[i][0])
        dist = "{:.2f}".format(gui_dict[i][1])
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
        index = len(gui_dict)
        self.speaker_property.added.connect(self.add2scene)

        # calculate current default position
        from gui_utils import audience_pos
        x = default_position[index][0]
        y = default_position[index][1]
        dx = x - audience_pos.x()
        dy = audience_pos.y() - y
        dis = (dx**2+dy**2)**0.5

        from math import acos, degrees
        deg = degrees(acos(dy/dis))

        if dx < 0:
            deg = 360 - deg

        if deg >= 360:
            deg %= 360

        str_deg = "{:.0f}".format(deg)
        str_dis = "{:.2f}".format(dis/100)
        self.speaker_property.azimuth_line_edit.setText(str_deg)
        self.speaker_property.distance_line_edit.setText(str_dis)
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

        for index,speaker in enumerate(speaker_list):
            x = default_position[index][0]
            y = default_position[index][1]
            speaker_list[index].setPos(x,y)
            speaker_list[index].cal_rel_pos()
        else:
            return

    def closeEvent (self, eventQCloseEvent):
        self.room.clear()
        eventQCloseEvent.accept()