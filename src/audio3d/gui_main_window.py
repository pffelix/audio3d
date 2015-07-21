# -*- coding: utf-8 -*-
#
# Author: Huaijiang Zhu, Manuela Heiss

from PySide import QtCore, QtGui
from math import acos, degrees
import audio3d.gui_utils
from audio3d.dsp import Dsp
import threading


class MainWindow(QtGui.QWidget):
    """
    H1 -- MainWindow
    ************************
    **This class sets up the main window which includes all necessaries to
    start/stop and control the DSP algorithm. It also includes all user 
    interactions, corresponding functions and executing and updating these.**
    """

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setAcceptDrops(True)

        # set items
        self.state = audio3d.gui_utils.State()
        self.audience = audio3d.gui_utils.Audience(self.state)
        self.default_speaker_position = [[50, 20], [290, 20], [170, 50],
                                         [50, 320], [290, 320], [170, 290],
                                         [50, 120], [290, 120], [50, 220],
                                         [290, 220]]
        # set scene and view
        self.room = audio3d.gui_utils.Room(self.state)
        self.room.setSceneRect(0, 0, 400, 400)
        self.room.addItem(self.audience)

        # set view
        self.view = audio3d.gui_utils.View(self.state, self.room)
        self.view.setFixedSize(400, 400)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # set property window
        self.speaker_property = audio3d.gui_utils.SpeakerProperty(self.state)

        # set plot window
        self.sequence_plot = audio3d.gui_utils.SequencePlot()
        self.sequence_plot.plot_on.connect(self.update_sequences)

        self.dsp_obj = None
        self.dspthread = None
        self.init_ui()

    def init_ui(self):
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
        self.record_box = QtGui.QCheckBox('Record Output')
        self.buffersize_label = QtGui.QLabel('Buffer Size:')
        self.headtracker_box = QtGui.QCheckBox('Headtracker')
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
        layout.addWidget(self.record_box, 8, 2, 1, 1)
        layout.addWidget(self.buffersize_label, 8, 0, 1, 1)
        layout.addWidget(self.buffersize_spin_box, 8, 1, 1, 1)
        layout.addWidget(self.headtracker_box, 8, 3, 1, 1)

        # initialize head tracker, connect signal and slots
        self.headtracker_box.stateChanged.connect(self.activate_headtracker)
        if self.state.enable_headtracker:
            self.head_tracker = audio3d.gui_utils.Headtracker()
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
#        self.combo_box.currentIndexChanged.connect(self.update_settings)
        self.inverse_box.stateChanged.connect(self.inverse_disable)
#        self.inverse_box.stateChanged.connect(self.update_settings)
#        self.buffersize_spin_box.valueChanged.connect(self.update_settings)

        # set window
        self.setLayout(layout)
        self.setWindowTitle('3D Audio')
        self.show()

    def activate_headtracker(self):
        if self.headtracker_box.isChecked():
            try:
                self.head_tracker = audio3d.gui_utils.Headtracker()
                self.update_headtracker_timer = QtCore.QTimer()
                self.update_headtracker_timer.timeout.connect(self.update_head)
                self.update_headtracker_timer.start(10)
            except:
                self.headtracker_box.setCheckState(QtCore.Qt.Unchecked)
                try:
                    msgbox = QtGui.QMessageBox()
                    msgbox.setText("Headtracking is not possible on this PC!")
                    msgbox.exec_()
                except BrokenPipeError:
                    self.head_tracker.dt2.__del__()
        else:
            return

    def update_head(self):
        """
        H2 -- update_head
        ===================
        **This function is nessecary if the program is run in connection with
        a headtracking system.**
        If the DSP algorithm is running the Headtracking angle output is
        requested and the speaker list is updated.
        A threading.Lock() avoids read-write overlaps of the dsp_run variable.
        """

        if self.state.dsp_run is True:
            self.head_tracker.cal_head_deg()
            self.update_gui_sp(self.head_tracker.get_head_deg())

    def update_gui_sp(self, deg):
        """
        H2 -- update_gui_sp
        ===================
        **This function is continuously updating the list with the settings
        for each speaker**
        It is called every 10 ms by a timer and updating the speaker 
        list for every present speaker.
        A threading.Lock() avoids read-write overlaps of the dsp_run variable.
        """
        if self.state.dsp_run is True:
            for speaker in self.state.speaker_list:
                speaker.cal_rel_pos(deg)

    def inverse_disable(self):
        """
        H2 -- inverse_disable
        ===================
        **This function is needed to disable the CheckBox for inverse filtering
        if the kemarr_compact database is selected.**
        The kemar_compact database already includes inverse filtering of the
        measurement speaker disturbtions which can therefore not be optional
        for this setting.
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
        **With this function the speaker property widget from gui_utils is
        opened and handeled.**
        If a new speaker is added or by double click on an existing one 
        gui_utils' SpeakerProperty widget, containing the default or 
        instantaneous settings respectively, is opened to define/change the
        individual speaker settings.
        The change_property function is called to save changes.
        A threading.Lock() avoids read-write overlaps of the gui_sp
        variable.
        """
        sp = self.state.speaker_to_show
        self.state.mtx_sp.acquire()
        path = str(self.state.gui_sp[sp]["path"])
        azimuth = "{:.0f}".format(self.state.gui_sp[sp]["angle"])
        dist = "{:.2f}".format(self.state.gui_sp[sp]["distance"])
        if self.state.gui_sp[sp]["normalize"] is True:
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
        **With this function transfers the speaker property changes and updates
        the speaker list and gui_sp variables.**
        A threading.Lock() avoids read-write overlaps of the gui_sp
        variable.
        """
        sp = self.state.speaker_to_show
        x_new = self.speaker_property.posx
        y_new = self.speaker_property.posy
        path_new = self.speaker_property.path
        self.state.speaker_list[sp].setPos(x_new, y_new)
        self.state.speaker_list[sp].path = path_new
        self.state.speaker_list[sp].cal_rel_pos()
        self.state.mtx_sp.acquire()
        if self.speaker_property.normalize_box.isChecked():
            self.state.gui_sp[sp]["normalize"] = True
        else:
            self.state.gui_sp[sp]["normalize"] = False
        self.state.mtx_sp.release()

    @QtCore.Slot()
    def add_speaker(self):
        if len(self.state.gui_sp) < 10:
            index = len(self.state.gui_sp)
        """
        H2 -- add_speaker
        ===================
        **This function is called when a new speaker is added to the scene.**
        Up to 10 speakers can be added successively to the GUIscene on the
        MainWindow. 
        The current default position is calculated depending on the number
        of speakers and relative to the position of the audience item.
        """
        if len(self.state.gui_sp) < 10:
            index = len(self.state.gui_sp)
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
                QtCore.Qt.Unchecked)
            self.speaker_property.azimuth_line_edit.setText(str_deg)
            self.speaker_property.distance_line_edit.setText(str_dis)
            self.speaker_property.show()
            self.speaker_property.is_on = True
        else:
            self.state.send_error("speaker number limited to 10")
            return

    @QtCore.Slot()
    def add2scene(self):
        """
        H2 -- add2scene
        ===================
        **This function creates a new speaker item.**
        The function is called by the confirm button of gui_utils'
        SpeakerProperty widget.
        A new speaker item is created with arguments defined in the speaker
        property widget. Furthermore the gui_utils' room.addItem function
        is called to add the new speaker to the GuiScene.
        Finally the GuiView is updated to display the change.
        """
        if len(self.state.gui_sp) < 10:
            # read in data
            index = len(self.state.gui_sp)
            path = self.speaker_property.path
            x = self.speaker_property.posx
            y = self.speaker_property.posy
            # create new speaker
            if self.speaker_property.normalize_box.isChecked():
                new_speaker = audio3d.gui_utils.Speaker(
                    self.state, index, path, x, y, True)
            else:
                new_speaker = audio3d.gui_utils.Speaker(self.state, index,
                                                        path, x, y)
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
        **This function is called by the MainWindow reset button and removes
        all existing speakers from the GuiScene and resets also the gui_sp
        variable.**
        """
        self.state.mtx_run.acquire()
        self.state.mtx_stop.acquire()
        # stop dsp thread when audio is currently convolved
        if self.state.dsp_run is True:
            self.state.dsp_stop = True
        self.state.mtx_run.release()
        self.state.mtx_stop.release()
        # wait until thread finished
        if self.dspthread is not None:
            self.dspthread.join()

        self.room.clear()

        self.state.mtx_sp.acquire()
        del self.state.gui_sp[:]
        self.state.mtx_sp.release()

        del self.state.speaker_list[:]
        new_audience = audio3d.gui_utils.Audience(self.state)
        self.room.addItem(new_audience)
        self.view.viewport().update()

    @QtCore.Slot()
    def play(self):
        """
        H2 -- play
        ===================
        **This function is called by the MainWindow play/stop button .**
        The algorithm specific stettings such as the HRTF database, the
        inverse filter and the bufferblock size are recorded and
        an DSP object is initialized and run in a seperate thread.
        """

        # check whether speaker has been selected
        if len(self.state.gui_sp) == 0:
            msgbox = QtGui.QMessageBox()
            msgbox.setText("Please add a speaker.")
            msgbox.exec_()
            return
        else:
            # if algorithm is alread running
            if self.state.dsp_run is True:
                # switch stop variable: mark stop as True
                self.state.switch_stop_playback()
                return
            else:
                # switch stop variable: mark stop as False
                self.state.switch_stop_playback()

            # update gui_settings
            self.state.gui_settings["hrtf_database"] = \
                self.combo_box.currentText()
            self.state.gui_settings["inverse_filter_active"] = \
                self.inverse_box.isChecked()
            self.state.gui_settings["bufferblocks"] = \
                self.buffersize_spin_box.value()
            self.state.gui_settings["record"] = \
                self.record_box.isChecked()
            self.plot_button.setEnabled(True)

            # create a dsp algorithm object
            self.dsp_obj = Dsp(self.state)
            # create a new thread dsp thread which executes the dsp object run
            #  function
            self.dspthread = threading.Thread(
                target=self.dsp_obj.run)
            # start dsp thread
            self.dspthread.start()

    @QtCore.Slot()
    def pause(self):
        """
        H2 -- pause
        ===================
        **The algorithm can be paused by the pause button of MainWindow.**
        The state variable switch_pause_playback remembers the status of the
        algorithm and enables pausing and restarting of the play-back of the
        dsp algorithm.
        """
        self.state.mtx_run.acquire()
        # if algorithm is alread running
        if self.state.dsp_run is True:
            # switch stop variable: mark pause as true or false
            self.state.switch_pause_playback()
        self.state.mtx_run.release()

    def positions(self):
        """
        H2 -- positions
        ===================
        **This function places all speakers on their respective default
        positions.**
        Depending on their order every speakers default position is defined
        in the default_speaker_position variable.
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
        **This function is called by MainWindow plot button and shows the 
        gui_utils' SequencePlot of the last selected speaker.**
        The sequences are continously updated by the update_sequences in
        connection with a QTimer.
        """

        sp = self.state.speaker_to_show

        self.sequence_plot.speaker_spec.initialize_data(
            self.state.dsp_sp_spectrum[sp][:, 0],
            self.state.dsp_sp_spectrum[sp][:, 1])
        self.sequence_plot.lhrtf_spec.initialize_data(
            self.state.dsp_hrtf_spectrum[sp][0][:, 0],
            self.state.dsp_hrtf_spectrum[sp][0][:, 1])
        self.sequence_plot.rhrtf_spec.initialize_data(
            self.state.dsp_hrtf_spectrum[sp][1][:, 0],
            self.state.dsp_hrtf_spectrum[sp][1][:, 1])
        self.sequence_plot.show()
        self.sequence_plot.is_on = True
        self.sequence_plot.timer.timeout.connect(self.update_sequences)
        self.sequence_plot.timer.start(50)

    def update_sequences(self):
        """
        H2 -- update_sequences
        ===================
        **This function is used to update speaker spectrum while it is
        displayed in the SequencePlot widget.**
        """

        sp = self.state.speaker_to_show
        self.sequence_plot.speaker_spec.update_data(
            self.state.dsp_sp_spectrum[sp][:, 0],
            self.state.dsp_sp_spectrum[sp][:, 1])
        self.sequence_plot.lhrtf_spec.update_data(
            self.state.dsp_hrtf_spectrum[sp][0][:, 0],
            self.state.dsp_hrtf_spectrum[sp][0][:, 1])
        self.sequence_plot.rhrtf_spec.update_data(
            self.state.dsp_hrtf_spectrum[sp][1][:, 0],
            self.state.dsp_hrtf_spectrum[sp][1][:, 1])

    def closeEvent(self, event_q_close_event):  # flake8: noqa
        """
        H2 -- closeEvent
        ===================
        **This function is responsible for a smooth closure of the MainWindow
        .**
        Whenever the MainWindow is closed by the user all widgets such as
        the SpeakerProperty and SequencePlot have to be closed. If the
        headtracking system is used its continuous updating is stopped.
        And the algorithm control variables are set repsectively.
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

        # stop dsp Thread
        if self.dspthread is not None:
            # stop dsp Thread
            self.state.mtx_pause.acquire()
            self.state.dsp_pause = False
            self.state.mtx_pause.release()
            self.state.mtx_stop.acquire()
            self.state.dsp_stop = True
            self.state.mtx_stop.release()
            self.dspthread.join()
        event_q_close_event.accept()
