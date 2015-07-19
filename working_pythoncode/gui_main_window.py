#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
GUI Main Window of Audio 3D Project, Group B
author: H. Zhu, M. Heiss
"""

from PySide import QtCore, QtGui
from math import acos, degrees
import gui_utils
from dsp import Dsp
import threading
import multiprocessing


class MainWindow(QtGui.QWidget):
    """
    H1 -- MainWindow
    ************************
    The class implements the main window of the GUI as a container for all components
    including graphical view, buttons, property/plot window. 
    """

    def __init__(self):
        """
        H2 -- Main Window Constructor
        ===================
        ** Initialize the main window of the GUI**

        """
        super(MainWindow, self).__init__()
        self.setAcceptDrops(True)

        # set items
        self.state = gui_utils.State()
        self.audience = gui_utils.Audience(self.state)
        self.default_speaker_position = [[50, 20], [290, 20], [170, 50],
                                         [50, 320], [290, 320], [170, 290],
                                         [50, 120], [290, 120], [50, 220],
                                         [290, 220]]
        # set scene and view
        self.room = gui_utils.Room(self.state)
        self.room.setSceneRect(0, 0, 400, 400)
        self.room.addItem(self.audience)

        # set view
        self.view = gui_utils.View(self.state, self.room)
        self.view.setFixedSize(400, 400)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # set property window
        self.speaker_property = gui_utils.SpeakerProperty(self.state)

        # set plot window
        self.sequence_plot = gui_utils.SequencePlot()
        self.sequence_plot.plot_on.connect(self.update_sequence_dicts)

        self.dsp_obj = None
        self.dsp_thread = None
        # return_ex: save whether playback was successful
        self.return_ex = multiprocessing.Queue()
        self.init_ui()
        # return_ex: Playback not run yet -> unsuccessful
        self.return_ex.put(False)

    def init_ui(self):

        """
        H2 -- init_ui
        ===================
        **Initialize UI Components**

        Buttons, combo boxes and the graphical view will be added.
        Signal/Slots will be connected.

        """

        # set buttons
        add_speaker_button = QtGui.QPushButton('Add Speaker')
        reset_button = QtGui.QPushButton('Reset')
        play_button = QtGui.QPushButton('Play/Stop')
        pause_button = QtGui.QPushButton('Pause/Continue')
        default_position_button = QtGui.QPushButton('Default Position')
        self.plot_button = QtGui.QPushButton('Plot Sequence')
        self.plot_button.setDisabled(True)

        # set_properties
        self.combo_box = QtGui.QComboBox()
        self.combo_box.addItem('kemar_normal_ear')
        self.combo_box.addItem('kemar_big_ear')
        self.combo_box.addItem('kemar_compact')
        self.database_label = QtGui.QLabel('Select Database:')
        self.inverse_box = QtGui.QCheckBox('Inverse Filter')
        self.buffersize_label = QtGui.QLabel('Buffer Size:')
        self.buffersize_spin_box = QtGui.QSpinBox()
        self.buffersize_spin_box.setMinimum(0)
        self.buffersize_spin_box.setMaximum(1000)
        self.buffersize_spin_box.setValue(30)

        # set layout
        layout = QtGui.QGridLayout()
        layout.addWidget(self.view, 0, 0, 1, 4)
        layout.addWidget(add_speaker_button, 1, 0, 1, 4)
        layout.addWidget(play_button, 2, 0, 1, 4)
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
        if self.state.enable_headtracker:
            self.head_tracker = gui_utils.Headtracker()
            self.update_headtracker_timer = QtCore.QTimer()
            self.update_headtracker_timer.timeout.connect(self.update_head)
            self.update_headtracker_timer.start(10)

        # initialize timer for error checking
        self.error_timer = QtCore.QTimer()
        self.error_timer.timeout.connect(self.state.check_error)
        self.error_timer.start(100)

        add_speaker_button.clicked.connect(self.add_speaker)
        reset_button.clicked.connect(self.reset)
        play_button.clicked.connect(self.play)
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
        """
        H2 -- update_head
        ===================
        **Update head tracker data**

        Azimuth degree will be obtained from the head tracker if it is enabled.
        During the playback it will constantly call the update_gui_sp_dict to
        adjust the positional data according to the current head position.

        """
        self.state.mtx_run.acquire()
        if self.state.dsp_run is True:
            self.head_tracker.cal_head_deg()
            self.update_gui_sp_dict(self.head_tracker.get_head_deg())
        self.state.mtx_run.release()

    def update_gui_sp_dict(self, deg):
        """
        H2 -- update_gui_sp_dict
        ===================
        **Adjust the positional data given the azimuth from the head tracker**

        """
        self.state.mtx_run.acquire()
        if self.dsp_run is True:
            for speaker in self.speaker_list:
                speaker.cal_rel_pos(deg)
        self.state.mtx_run.release()

    def inverse_disable(self):
        """
        H2 -- inverse_disabl
        ===================
        **Disable inverse filter if kemar compact data bank is applied**

        """
        if self.combo_box.currentText() == 'kemar_compact':
            self.inverse_box.setCheckState(QtCore.Qt.Unchecked)
        else:
            return

    @QtCore.Slot()
    def show_property(self):
        """
        H2 -- show_property
        ===================
        **This function will be called when the speaker icon is double clicked**

        Read the information of the selected speaker and show it in the property
        window.

        """
        i = self.state.speaker_to_show
        self.state.mtx_sp.acquire()
        path = str(self.state.gui_sp_dict[i][2])
        azimuth = "{:.0f}".format(self.state.gui_sp_dict[i][0])
        dist = "{:.2f}".format(self.state.gui_sp_dict[i][1])
        if self.state.gui_sp_dict[i][3] is True:
            self.speaker_property.normalize_box.setCheckState(
                QtCore.Qt.Checked)
        else:
            self.speaker_property.normalize_box.setCheckState(
                QtCore.Qt.Unchecked)
        self.state.mtx_sp.release()
        self.speaker_property.path_line_edit.setText(path)
        self.speaker_property.azimuth_line_edit.setText(azimuth)
        self.speaker_property.distance_line_edit.setText(dist)
        self.speaker_property.show()
        self.speaker_property.is_on = True
        self.speaker_property.added.connect(self.change_property)

    def change_property(self):
        """
        H2 -- change_property
        ===================
        **This function will be called when the confirm button is clicked**

        Take the changes in the property window and update the information of the speaker.

        """
        i = self.state.speaker_to_show
        x_new = self.speaker_property.posx
        y_new = self.speaker_property.posy
        path_new = self.speaker_property.path
        self.state.speaker_list[i].setPos(x_new, y_new)
        self.state.speaker_list[i].path = path_new
        self.state.speaker_list[i].cal_rel_pos()
        self.state.mtx_sp.acquire()
        if self.speaker_property.normalize_box.isChecked():
            self.state.gui_sp_dict[i][3] = True
        else:
            self.state.gui_sp_dict[i][3] = False
        self.state.mtx_sp.release()

    @QtCore.Slot()
    def add_speaker(self):
        """
        H2 -- add_speaker
        ===================
        **This function will be called when the add button is clicked**

        Show the property window for adding new speaker when the total number of
        speakers is fewer than 10.

        """
        if len(self.state.gui_sp_dict) < 10:
            index = len(self.state.gui_sp_dict)
            self.speaker_property.added.connect(self.add2scene)

            # calculate current default position
            audience_pos = self.state.audience_pos
            x = self.default_speaker_position[index][0]
            y = self.default_speaker_position[index][1]
            dx = x - audience_pos.x()
            dy = audience_pos.y() - y
            dis = (dx ** 2 + dy ** 2) ** 0.5

            deg = degrees(acos(dy / dis))

            if dx < 0:
                deg = 360 - deg

            if deg >= 360:
                deg %= 360

            str_deg = "{:.0f}".format(deg)
            str_dis = "{:.2f}".format(dis / 100)
            self.speaker_property.normalize_box.setCheckState(
                QtCore.Qt.Checked)
            self.speaker_property.azimuth_line_edit.setText(str_deg)
            self.speaker_property.distance_line_edit.setText(str_dis)
            self.speaker_property.show()
            self.speaker_property.is_on = True
        else:
            return

    @QtCore.Slot()
    def add2scene(self):
        """
        H2 -- add2scene
        ===================
        **This function will be called when the confirm button is clicked**

        Create new speaker object according to the data from property window
        and add it to the graphical scene.

        """
        if len(self.state.gui_sp_dict) < 10:
            # read in data
            index = len(self.state.gui_sp_dict)
            path = self.speaker_property.path
            x = self.speaker_property.posx
            y = self.speaker_property.posy
            # create new speaker
            if self.speaker_property.normalize_box.isChecked():
                new_speaker = gui_utils.Speaker(
                    self.state, index, path, x, y, True)
            else:
                new_speaker = gui_utils.Speaker(self.state, index, path, x, y)
            new_speaker.signal_handler.show_property.connect(
                self.show_property)
            self.room.addItem(self.state.speaker_list[-1])
            self.view.viewport().update()
        else:
            return

    @QtCore.Slot()
    def reset(self):
        """
        H2 -- reset
        ===================
        **This will delete all the existed speakers**

        """
        self.state.mtx_run.acquire()
        self.state.mtx_sp.acquire()
        if self.state.dsp_run is True:
            pass

        else:
            self.room.clear()
            self.state.gui_sp_dict.clear()
            del self.state.speaker_list[:]
            new_audience = gui_utils.Audience(self.state)
            self.room.addItem(new_audience)
            self.view.viewport().update()
        self.state.mtx_run.release()
        self.state.mtx_sp.release()

    @QtCore.Slot()
    def play(self):
        """
        H2 -- play
        ===================
        **This will start/stop the sount output**

        Dsp object will be initialized if it is not already. Every click will
        switch the status of play or stop.

        """
        # check whether speaker has been selected
        if len(self.state.gui_sp_dict) == 0:
            msgbox = QtGui.QMessageBox()
            msgbox.setText("Please add a speaker.")
            msgbox.exec_()
        else:
            # don't let the playback and convolution start more than one time
            if self.return_ex.empty() is True:
                self.state.switch_stop_playback()
                return
            # if playback was stopped as user pressed stop button switch stop
            # variable to playmode
            if self.return_ex.empty() is False and self.return_ex.get() is \
                    True:
                self.state.switch_stop_playback()
            print("continue")
            # while not self.return_ex.empty():
            #   self.return_ex.get()

            # update gui_settings_dict
            self.state.gui_settings_dict["hrtf_database"] = \
                self.combo_box.currentText()
            self.state.gui_settings_dict["inverse_filter_active"] = \
                self.inverse_box.isChecked()
            self.state.gui_settings_dict["bufferblocks"] = \
                self.buffersize_spin_box.value()
            self.plot_button.setEnabled(True)

            self.dsp_obj = Dsp(self.state,
                               self.return_ex)
            # start dsp thread
            self.dspthread = threading.Thread(
                target=self.dsp_obj.run)
            self.dspthread.start()

    @QtCore.Slot()
    def pause(self):
        """
        H2 -- pause
        ===================
        **This will pause/resume the sount output**

        """
        self.state.switch_pause_playback()

    def positions(self):
        """
        H2 -- positions
        ===================
        **This function will set all the speakers to their default position**

        """

        for index, speaker in enumerate(self.state.speaker_list):
            x = self.default_speaker_position[index][0]
            y = self.default_speaker_position[index][1]
            self.state.speaker_list[index].setPos(x, y)
            self.state.speaker_list[index].cal_rel_pos()
        else:
            return

    def plot_sequence(self):
        """
        H2 -- plot_sequence
        ===================
        **This will show the plot window**

        Plotting information will be obtained from the data exchange object.
        """
        sp = self.state.speaker_to_show
        print("initialize")

        self.sequence_plot.speaker_spec.initialize_data(
            self.state.sp_spectrum_dict[sp][:, 0],
            self.state.sp_spectrum_dict[sp][:, 1])
        self.sequence_plot.lhrtf_spec.initialize_data(
            self.state.hrtf_spectrum_dict[sp][0][:, 0],
            self.state.hrtf_spectrum_dict[sp][0][:, 1])
        self.sequence_plot.rhrtf_spec.initialize_data(
            self.state.hrtf_spectrum_dict[sp][1][:, 0],
            self.state.hrtf_spectrum_dict[sp][1][:, 1])
        self.sequence_plot.show()
        self.sequence_plot.is_on = True
        self.sequence_plot.timer.timeout.connect(self.update_sequence_dicts)
        self.sequence_plot.timer.start(50)

    def update_sequence_dicts(self):
        """
        H2 -- update_sequence_dicts
        ===================
        **This updates the plotting information every 50ms**

        """
        sp = self.state.speaker_to_show
        self.sequence_plot.speaker_spec.update_data(
            self.state.sp_spectrum_dict[sp][:, 0],
            self.state.sp_spectrum_dict[sp][:, 1])
        self.sequence_plot.lhrtf_spec.update_data(
            self.state.hrtf_spectrum_dict[sp][0][:, 0],
            self.state.hrtf_spectrum_dict[sp][0][:, 1])
        self.sequence_plot.rhrtf_spec.update_data(
            self.state.hrtf_spectrum_dict[sp][1][:, 0],
            self.state.hrtf_spectrum_dict[sp][1][:, 1])

    def closeEvent(self, event_q_close_event):  # flake8: noqa
        """
        H2 -- closeEvent
        ===================
        **Qt built-in virtual function to close the program safely**

        Header tracker will not be updated, plot/property window will be closed
        The sound output will be stopped.
        """
        self.room.clear()
        if self.state.enable_headtracker:
            self.update_headtracker_timer.stop()
        if self.sequence_plot.is_on:
            self.sequence_plot.close()
        if self.speaker_property.is_on:
            self.speaker_property.close()
        # if self.dspthread is not None and self.state.dsp_stop is False \
        #         or self.dspthread is not None and self.state.dsp_run is True:
        #     self.state.switch_stop_playback()
        # if self.dspthread is not None and self.state.dsp_pause is True:

        if self.dsp_obj is not None:
            # stop dsp Thread
            self.state.mtx_pause.acquire()
            self.state.dsp_pause = False
            self.state.mtx_pause.release()
            self.state.mtx_stop.acquire()
            self.state.dsp_stop = True
            self.state.mtx_stop.release()
            self.dsp_thread.join()
        event_q_close_event.accept()
