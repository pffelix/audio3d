#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
GUI Main Window of Audio 3D Project, Group B
author: H. Zhu, M. Heiss
"""

from PySide.QtCore import *
from PySide.QtGui import *
from gui_utils import *
from dsp import Dsp
import threading
import multiprocessing
from error_handler import *


# head tracker
enable_headtracker = False
# initialization of variables
default_position = [[50, 20], [290, 20], [170, 50],
                    [50, 320], [290, 320], [290, 170]]


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setAcceptDrops(True)
        # set items
        self.audience = Audience()

        # set scene and view
        self.room = Room()
        self.room.setSceneRect(0, 0, 400, 400)
        self.room.addItem(self.audience)

        # set view
        self.view = View(self.room)
        self.view.setFixedSize(400, 400)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # set property window
        self.speaker_property = SpeakerProperty()

        # set plot window
        self.sequence_plot = SequencePlot()
        self.sequence_plot.plot_on.connect(self.update_sequence_dicts)

        self.Dsp_Object = None
        self.play = None
        # return_ex: save whether playback was successful
        self.return_ex = multiprocessing.Queue()
        self.init_ui()
        # return_ex: Playback not run yet -> unsuccessful
        self.return_ex.put(False)

    def init_ui(self):

        # set buttons
        add_speaker_button = QPushButton('Add Speaker')
        reset_button = QPushButton('Reset')
        control_button = QPushButton('Play/Stop')
        pause_button = QPushButton('Pause')
        default_position_button = QPushButton('Default Position')
        self.plot_button = QPushButton('Plot Sequence')
        self.plot_button.setDisabled(True)

        # set_properties
        self.combo_box = QtGui.QComboBox()
        self.combo_box.addItem('kemar_normal_ear')
        self.combo_box.addItem('kemar_big_ear')
        self.combo_box.addItem('kemar_compact')
        self.database_label = QtGui.QLabel('Select Database:')
        self.inverse_box = QtGui.QCheckBox('Inverse Filter')
        self.inverse_box.nextCheckState()
        self.buffersize_label = QtGui.QLabel('Buffer Size:')
        self.buffersize_spin_box = QtGui.QSpinBox()
        self.buffersize_spin_box.setMinimum(0)
        self.buffersize_spin_box.setMaximum(1000)
        self.buffersize_spin_box.setValue(5)

        # set layout
        layout = QtGui.QGridLayout()
        layout.addWidget(self.view, 0, 0, 1, 4)
        layout.addWidget(add_speaker_button, 1, 0, 1, 4)
        layout.addWidget(control_button, 2, 0, 1, 4)
        layout.addWidget(pause_button, 3, 0, 1, 4)
        layout.addWidget(reset_button, 4, 0, 1, 4)
        layout.addWidget(default_position_button, 5, 0, 1, 4)
        layout.addWidget(self.plot_button, 6, 0, 1, 4)
        layout.addWidget(self.database_label, 7, 0, 1, 1)
        layout.addWidget(self.combo_box, 7, 1, 1, 2)
        layout.addWidget(self.inverse_box, 7, 3, 1, 1)
        layout.addWidget(self.buffersize_label, 8, 0, 1, 1)
        layout.addWidget(self.buffersize_spin_box, 8, 1, 1, 1)

        # initialize head tracker, connect signal and slots
        if enable_headtracker:
            self.head_tracker = Headtracker()
            self.update_timer = QTimer()
            self.update_timer.timeout.connect(self.update_head)
            self.update_timer.start(10)

        add_speaker_button.clicked.connect(self.add_speaker)
        reset_button.clicked.connect(self.reset)
        control_button.clicked.connect(self.control)
        pause_button.clicked.connect(self.pause)
        default_position_button.clicked.connect(self.positions)
        self.plot_button.clicked.connect(self.plot_sequence)
        self.combo_box.currentIndexChanged.connect(self.inverse_disable)
#        self.combo_box.currentIndexChanged.connect(self.update_settings_dict)
        self.inverse_box.stateChanged.connect(self.inverse_disable)
#        self.inverse_box.stateChanged.connect(self.update_settings_dict)
#        self.buffersize_spin_box.valueChanged.connect(self.update_settings_dict)

        # set window
        self.setLayout(layout)
        self.setWindowTitle('3D Audio')
        self.show()

    def update_head(self):
        from gui_utils import update_gui_dict, gui_stop, gui_pause
        if gui_stop is False and gui_pause is False:
            self.head_tracker.cal_head_deg()
            update_gui_dict(self.head_tracker.get_head_deg())

    def inverse_disable(self):
        if self.combo_box.currentText() == 'kemar_compact':
            self.inverse_box.setCheckState(False)
        else:
            return

#    def update_settings_dict(self):
#        global gui_settings_dict
#        gui_settings_dict = {
#                "hrtf_database": self.combo_box.currentText(),
#                "inverse_filter_active": self.inverse_box.isChecked(),
#                "bufferblocks": self.buffersize_spin_box.value()}

    @Slot()
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
        self.speaker_property.is_on = True
        self.speaker_property.added.connect(self.change_property)

    def change_property(self):

        from gui_utils import speaker_to_show
        i = speaker_to_show
        x_new = self.speaker_property.posx
        y_new = self.speaker_property.posy
        speaker_list[i].setPos(x_new, y_new)
        speaker_list[i].cal_rel_pos()

    @Slot()
    def add_speaker(self):
        if len(gui_dict) < 6:
            index = len(gui_dict)
            self.speaker_property.added.connect(self.add2scene)

            # calculate current default position
            from gui_utils import audience_pos
            x = default_position[index][0]
            y = default_position[index][1]
            dx = x - audience_pos.x()
            dy = audience_pos.y() - y
            dis = (dx ** 2 + dy ** 2) ** 0.5

            from math import acos, degrees
            deg = degrees(acos(dy / dis))

            if dx < 0:
                deg = 360 - deg

            if deg >= 360:
                deg %= 360

            str_deg = "{:.0f}".format(deg)
            str_dis = "{:.2f}".format(dis / 100)
            self.speaker_property.azimuth_line_edit.setText(str_deg)
            self.speaker_property.distance_line_edit.setText(str_dis)
            self.speaker_property.show()
            self.speaker_property.is_on = True
        else:
            return

    @Slot()
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
            new_speaker.signal_handler.show_property.connect(
                self.show_property)
            self.room.addItem(speaker_list[-1])
            self.view.viewport().update()

        else:
            return

    @Slot()
    def reset(self):
        self.room.clear()
        gui_dict.clear()
        del speaker_list[:]
        new_audience = Audience()
        self.room.addItem(new_audience)
        self.view.viewport().update()

    @Slot()
    def control(self):
        global gui_stop
        global gui_pause
        global gui_settings_dict
        global gui_dict
        # check whether speaker has been selected
        if len(gui_dict) > 0:
            # don't let the playback and convolution start more than one time
            if self.return_ex.empty() is True:
                gui_stop = switch_stop_playback()
                return
            # if playback was stopped as user pressed stop button switch stop
            # variable to playmode
            if self.return_ex.empty() is False and self.return_ex.get() is \
                    True:
                gui_stop = switch_stop_playback()
            print("continue")
            # while not self.return_ex.empty():
            #   self.return_ex.get()
            gui_settings_dict = {
                "hrtf_database": self.combo_box.currentText(),
                "inverse_filter_active": self.inverse_box.isChecked(),
                "bufferblocks": self.buffersize_spin_box.value()}
            self.plot_button.setEnabled(True)
            self.Dsp_Object = Dsp(gui_dict, gui_stop, gui_pause,
                                  gui_settings_dict, self.return_ex)
            self.error_timer = QTimer()
            self.error_timer.timeout.connect(self.show_error)
            self.error_timer.start(100)
            self.play = threading.Thread(
                target=self.Dsp_Object.run)
            self.play.start()
        else:
            msgbox = QMessageBox()
            msgbox.setText("Please add a speaker.")
            msgbox.exec_()

    @Slot()
    def pause(self):
        switch_pause_playback()
        #print(gui_pause)

    @Slot()
    def show_error(self):
        self.error_timer.stop()
        #print(check_error())
        self.error_timer.start(50)

    def positions(self):

        for index, speaker in enumerate(speaker_list):
            x = default_position[index][0]
            y = default_position[index][1]
            speaker_list[index].setPos(x, y)
            speaker_list[index].cal_rel_pos()
        else:
            return

    def plot_sequence(self):
        # print(self.Dsp_Object.DspOut_Object.sp_spectrum_dict)plot_sequence
        from gui_utils import speaker_to_show
        i = speaker_to_show
        print("initialize")

        self.sequence_plot.speaker_spec.set_data(
            self.Dsp_Object.DspOut_Object.sp_spectrum_dict[i][:, 1])
        self.sequence_plot.lhrtf_spec.set_data(
            self.Dsp_Object.DspOut_Object.hrtf_spectrum_dict[i][0][:, 1])
        self.sequence_plot.rhrtf_spec.set_data(
            self.Dsp_Object.DspOut_Object.hrtf_spectrum_dict[i][1][:, 1])

        self.sequence_plot.show()
        self.sequence_plot.is_on = True
        self.sequence_plot.timer.timeout.connect(self.update_sequence_dicts)
        self.sequence_plot.timer.start(50)

    def update_sequence_dicts(self):

        from gui_utils import speaker_to_show
        i = speaker_to_show
        self.sequence_plot.speaker_spec.update_data(
            self.Dsp_Object.DspOut_Object.sp_spectrum_dict[i][:, 1])
        self.sequence_plot.lhrtf_spec.update_data(
            self.Dsp_Object.DspOut_Object.hrtf_spectrum_dict[i][0][:, 1])
        self.sequence_plot.rhrtf_spec.update_data(
            self.Dsp_Object.DspOut_Object.hrtf_spectrum_dict[i][1][:, 1])

    def closeEvent(self, event_q_close_event):
        self.room.clear()
        if enable_headtracker:
            self.update_timer.stop()
        if self.sequence_plot.is_on:
            self.sequence_plot.close()
        if self.speaker_property.is_on:
            self.speaker_property.close()
        if self.play is not None:
            gui_stop_init = switch_stop_playback()
        event_q_close_event.accept()
