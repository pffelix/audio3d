"""
Library for GUI of Audio 3D Project, Group B
author: H. Zhu, M. Heiss
"""

from PySide import QtCore, QtGui
from audio3d.plot import GLPlotWidget
from audio3d.dt2 import DT2
from math import acos, degrees, cos, sin, radians
import audio3d.headtracker_data as headtracker
import threading
import pkg_resources


class State(QtCore.QObject):
    """
    H1 -- State
    ************************
    **This is an exchange class for variables which are read and written by
    the DSP algorithm and all GUI applications.**
    """
    
    """Constructor of the State class."""
    def __init__(self):
        super(State, self).__init__()
        # variables which are shared between gui and dsp algorithm
        self.gui_sp = []
        self.gui_settings = {}
        self.gui_error = []
        self.dsp_run = False
        self.dsp_stop = True
        self.dsp_pause = False
        self.dsp_sp_spectrum = []
        self.dsp_hrtf_spectrum = []

        # mutex for exchanging data between gui and dsp algorithm
        self.mtx_sp = threading.Lock()
        self.mtx_settings = threading.Lock()
        self.mtx_error = threading.Lock()
        self.mtx_run = threading.Lock()
        self.mtx_stop = threading.Lock()
        self.mtx_pause = threading.Lock()

        # gui state variables
        # enable head tracker
        self.enable_headtracker = False
        # head position in gui coordinates
        self.audience_pos = QtCore.QPoint(170, 170)
        self.speaker_list = []
        self.speaker_to_show = 0

    def switch_stop_playback(self):
        """
        H2 -- switch_stop_playback
        ===================
        **This function is called from the MainWindow Play/Stop button and
        remembers the state and transfers to a DSP command.**
        """
        self.mtx_stop.acquire()
        if self.dsp_stop is False:
            self.dsp_stop = True
        else:
            self.dsp_stop = False
        self.mtx_stop.release()

    def switch_pause_playback(self):
        """
        H2 -- switch_pause_playback
        ===================
        **This function is called from the MainWindow Pause button and
        remembers the state and transfers to respective DSP command.**
        """
        # start pause
        self.mtx_pause.acquire()
        if self.dsp_pause is False:
            self.dsp_pause = True
        # end pause
        else:
            self.dsp_pause = False
        self.mtx_pause.release()

    def send_error(self, message):
        """
        H2 -- send_error
        ===================
        **The function can be used by the DSP classes to create case-specific
        error messages.**
        """

        self.mtx_error.acquire()
        if message not in self.gui_error:
            self.gui_error.append(message)
        self.mtx_error.release()

    def check_error(self):
        """
        H2 -- check_error
        ===================
        **The function creates GUI message box with error message.**
        """

        self.mtx_error.acquire()
        if len(self.gui_error) > 0:
            msgbox = QtGui.QMessageBox()
            msgbox.setText(self.gui_error.pop(0))
            msgbox.exec_()
        self.mtx_error.release()


class Headtracker(object):
    """
    H1 -- Headtracker
    ************************
    **This class enables the integration of a headtracking system.**
    The networking interface from where the data can be extracced is
    initialized and thus the azimuthal angle can be read out.
    """
    
    """Constructor of the Headtracker class."""
    def __init__(self):
        self.head_deg = 0
        self.dt2 = DT2()

    def cal_head_deg(self):
        """
        H2 -- head_deg
        ===================
        **This function calls the azimuth_angle function of DT2 object.**
        This only extracts the azimuthal head movement
        recorded by the headtracking setup.
        """

        self.head_deg = headtracker.azimuth_angle(self.dt2.angle()[0])

    def get_head_deg(self):
        """
        H2 -- get_head_deg
        ===================
        **This function returns the azimuth angle, which is recorded
        with the headtracker setup**
        """
        return self.head_deg


class Item(QtGui.QGraphicsPixmapItem):
    """
    H1 -- Item
    ************************
    **This class defines items inside the QGraphicsScene,
    including Speaker and Audience.**
    """
    
    """Constructor of the Item class."""
    def __init__(self, state):

        image = self.origin_image.scaled(
            50, 50, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

        super(Item, self).__init__(QtGui.QPixmap.fromImage(image))

        self.setCursor(QtCore.Qt.OpenHandCursor)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtGui.QGraphicsItem.ItemIsFocusable)
        self.state = state

    def mousePressEvent(self, event):
        """
        H2 -- mousePressEvent
        ===================
        **This function defines the effect of mouse press on items.**
        Only left mouse click is noticed.
        """
        if event.button() != QtCore.Qt.LeftButton:
            event.ignore()
            return

        self.setCursor(QtCore.Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        """
        H2 -- mouseMoveEvent
        ===================
        **This function defines the effect of mouse move events in connection
        with items.**
        """

        if QtCore.QLineF(QtCore.QPointF(event.screenPos()),
                         QtCore.QPointF(event.buttonDownScreenPos(
                             QtCore.Qt.LeftButton))).length() < \
           QtGui.QApplication.startDragDistance():
                                return

        drag = QtGui.QDrag(event.widget())
        mime = QtCore.QMimeData()
        drag.setMimeData(mime)
        drag.exec_()
        self.setCursor(QtCore.Qt.OpenHandCursor)

    def mouseReleaseEvent(self, event):
        """
        H2 -- mouseReleaseEvent
        ===================
        **This function defines the effect of mouse release events in
        connection with items.** The Cursor symbol is changed.
        """
        self.setCursor(QtCore.Qt.OpenHandCursor)


# @class <Room> This class defines the Gui Scene
# A Room object displays the relative Audience and Speaker items positions
#
#
class Room(QtGui.QGraphicsScene):
    """
    H1 -- Room
    ************************
    **This class defines the QGraphicsScene on which the items are displayed
    and handeled.**
    * current_item: Indexes the item which is selected.
    """
    current_item = 0

    """Constructor of the Room class."""
    def __init__(self, state):
        super(Room, self).__init__()
        self.state = state

    # Definition of mouse move events related to the QGraphicsScene:

    def mousePressEvent(self, e):
        """
        H2 -- mousePressEvent
        ===================
        **This function defines the effect of mouse press on the room.**
        The item at the respective mouse event position is noticed.
        """
        self.current_item = self.itemAt(e.scenePos())
        QtGui.QGraphicsScene.mousePressEvent(self, e)

    def dragEnterEvent(self, e):
        e.acceptProposedAction()

    def dragMoveEvent(self, e):
        """
        H2 -- dragMoveEvent
        ===================
        **This function defines the effect of mouse move event on the room
        in connection with an item.**
        The mouse movement is recorded and the new item positions are extracted
        and used to calculate the respective positions of speaker(s) and
        audience.
        """
        e.acceptProposedAction()
        speaker_list = self.state.speaker_list
        try:
            self.current_item.setPos(e.scenePos().x() - 25, e.scenePos().y(
            ) - 25)
            bounded_x, bounded_y = self.get_bound_pos(e.scenePos().x() - 25,
                                                      e.scenePos().y() - 25)
            self.current_item.setPos(bounded_x, bounded_y)

            if self.current_item.type == 'audience':
                self.state.audience_pos = self.current_item.pos()

                for speaker in speaker_list:
                    deg, dis = speaker.cal_rel_pos()
                    if dis < 50:
                        x, y = self.get_abs_pos(deg, 50)
                        x, y = self.get_bound_pos(x, y)
                        speaker.setPos(x, y)
                    speaker.cal_rel_pos()

            elif self.current_item.type == 'speaker':
                deg, dis = self.current_item.cal_rel_pos()
                if dis < 50:
                    x, y = self.get_abs_pos(deg, 50)
                    self.current_item.setPos(x, y)
                self.current_item.cal_rel_pos()
                self.state.speaker_to_show = self.current_item.index

        except AttributeError:
            pass

    def get_bound_pos(self, x, y):
        """
        H2 -- get_bound_pos
        ===================
        **This function is used to avoid dragging outside the visible room
        area in the MainWindow.** By dragging items inside the QGraphicsScene
        the cursor can not leave this scene and items can not be hidden.
        """

        if x >= 350 and y >= 350:
            x = 350
            y = 350
        if x >= 350 and y <= 0:
            x = 350
            y = 0
        if x <= 0 and y <= 0:
            x = 0
            y = 0
        if x <= 0 and y >= 350:
            x = 0
            y = 350

        return x, y

    def get_abs_pos(self, azimuth, dist):
        """
        H2 -- get_abs_pos
        ===================
        **The function calculates and returns the new speaker position
        relative to the audience.**
        Return values:
        * x: is the horizontal coordinate of the speaker item.
        * y: is the vertical coordinate of the speaker item.
        """
        x0 = self.state.audience_pos.x()
        y0 = self.state.audience_pos.y()

        x = x0 + dist * sin(radians(azimuth))
        y = y0 - dist * cos(radians(azimuth))

        return x, y


class View(QtGui.QGraphicsView):
    """
    H1 -- View
    ************************
    **This class is responsible for displaying the contents of on the
    Room.**
    """
    
    """Constructor of the View class."""
    def __init__(self, state, scene):
        super(View, self).__init__(scene)
        self.state = state

    def dragEnterEvent(self, e):
        """
        H2 -- dragEnterEvent
        ===================
        **This function defines the effect of drag enter event on the view.**
        """
        e.acceptProposedAction()
        QtGui.QGraphicsView.dragEnterEvent(self, e)

    def dropEvent(self, e):
        """
        H2 -- dragMoveEvent
        ===================
        **This function defines the effect of mouse drop event on the view.**
        """
        self.viewport().update()
        QtGui.QGraphicsView.dropEvent(self, e)

    def dragMoveEvent(self, e):
        """
        H2 -- dragMoveEvent
        ===================
        **This function defines the effect of mouse move event on the view.**
        """
        e.acceptProposedAction()
        QtGui.QGraphicsView.dragMoveEvent(self, e)

    def wheelEvent(self, q_wheel_event):
        """
        H2 -- WheelEvent
        ===================
        **This function will disable scrolling of the view.**
        """
        pass

    def keyPressEvent(self, q_key_event):
        """
        H2 -- keyPressEvent
        ===================
        **This function will disable key usage effects on the view.**
        """
        pass


class SignalHandler(QtCore.QObject):
    """
    H1 -- SignalHandler
    ************************
    **Signal handler class for QGraphicsItem**
    This doesn't provide the signal/slot function.
    """

    show_property = QtCore.Signal()

    def __init__(self, index):
        super(SignalHandler, self).__init__()
        self.index = index


# @class <Speaker> Speaker item represent the source positions in
# the QGraphicsScene relative to the Audience item
#
#
class Speaker(Item):
    """
    H1 -- Speaker
    ************************
    **This subclass is defining speaker items.**
    * type: defines the type of the initialized item
    * path: defines the selected path of the .wav file
    """

    type = 'speaker'
    path = 'unknown'

    """Constructor of the Speaker class."""
    def __init__(self, state, index, path, posx=0, posy=0, norm=False):

        self.state = state
        speaker_list = self.state.speaker_list
        self.index = index
        image_path = 'image/speaker' + str(index + 1) + '.png'
        self.origin_image = QtGui.QImage(pkg_resources.resource_filename(
            "audio3d", image_path))
        super(Speaker, self).__init__(state)
        self.setPos(posx, posy)
        self.path = path
        self.norm = norm
        self.signal_handler = SignalHandler(self.index)
        speaker_list.append(self)
        self.state.mtx_sp.acquire()
        self.state.gui_sp.append({"angle": None, "distance": None, "path":
                                  self.path, "normalize": self.norm})
        self.state.mtx_sp.release()
        self.cal_rel_pos()

    # @brief this function returns the relative position of the speaker
    # to the 'audience', defined by a radial variable deg (defined counter
    # clockwise) and the distance
    # @details head_deg can take the azimuthal angle set by the headtracker
    # into account
    # @author
    def cal_rel_pos(self, head_deg=0):
        """
        H2 -- cal_rel_pos
        ===================
        **This function returns the relative position of the speaker
        to the 'audience', defined by a radial variable deg (defined counter
        clockwise) and the distance.**
        *head_deg: takes the azimuthal angle set by the headtracker
        into account
        """

        dx = self.x() - self.state.audience_pos.x()
        dy = self.state.audience_pos.y() - self.y()
        dis = (dx ** 2 + dy ** 2) ** 0.5
        if dis == 0:
            dis += 0.1

        # required geometric transformation due to the difference in definition
        # used by the headtracker setup
        deg = degrees(acos(dy / dis))
        if dx < 0:
            deg = 360 - deg

        deg -= head_deg

        if deg <= 0:
            deg += 360
        self.state.mtx_sp.acquire()
        # write new relative position in exchange variable gui - dsp
        self.state.gui_sp[self.index]["angle"] = deg
        self.state.gui_sp[self.index]["distance"] = dis / 100
        self.state.gui_sp[self.index]["path"] = self.path
        self.state.mtx_sp.release()
        return deg, dis

    def mouseDoubleClickEvent(self, event):
        """
        H2 -- mouseDoubleClickEvent
        ===================
        **This function defines the effect of double clicking on a speaker
        item.**
        Double click on speaker item offers the opportunity to change
        the speaker settings in the SpeakerProperty widget.
        """
    
        self.state.speaker_to_show = self.index
        self.signal_handler.show_property.emit()


# @class <Audience> Audience item represents the relative user position,
# without headtracker in the QGraphicsScene
#
class Audience(Item):
    """
    H1 -- Audience
    ************************
    **This sub-class defines the audience item.**
    An audience item represents the relative user position,
    without headtracker in the QGraphicsScene.
    *type: selects the type of item.
    *origin_image: selects the image representing the audience in the room.
    """

    type = 'audience'
    origin_image = QtGui.QImage(
        pkg_resources.resource_filename("audio3d", 'image/audience.png'))

    """Constructor of the Audience class."""
    def __init__(self, state):
        self.state = state
        super(Audience, self).__init__(state)
        self.setPos(170, 170)


class SpeakerProperty(QtGui.QWidget):
    """
    H1 -- SpeakerProperty
    ************************
    **This class defines a widget window to select speaker properties before
    adding a new speaker or to change the settings again later on.**
    Additional widget window to define speaker .wav path
    speaker position and to activate inverse filtering for speaker before
    adding it to the scene and afterwards by double click on the speaker item.
    *added: Signal emitted by the confirm button to connect to MainWindow's
    functions.
    *posx = horizontal position of the respective speaker item
    *posy = vertical position of the respective speaker item
    """

    added = QtCore.Signal()
    posx = 0
    posy = 0

    """Constructor of the SpeakerProperty class."""
    def __init__(self, state):
        super(SpeakerProperty, self).__init__()
        self.state = state
        self.is_on = False
        # set labels
        self.path_label = QtGui.QLabel('Audio Source:')
        self.position_label = QtGui.QLabel(
            'Relative Position to the Audience:')
        self.azimuth_label = QtGui.QLabel('Azimuth:')
        self.distance_label = QtGui.QLabel('Distance:')        # set line edit
        self.path_line_edit = QtGui.QLineEdit()
        self.azimuth_line_edit = QtGui.QLineEdit()
        self.distance_line_edit = QtGui.QLineEdit()

        # set buttons
        self.file_select_button = QtGui.QPushButton('Browse')
        self.confirm_button = QtGui.QPushButton('Confirm')
        self.cancel_button = QtGui.QPushButton('Cancel')
        self.normalize_box = QtGui.QCheckBox('Normalize Audio')
        self.normalize_box.setCheckState(QtCore.Qt.Checked)
        self.combo_box = QtGui.QComboBox()
        self.combo_box.addItem('Standard')
        self.combo_box.addItem('Big')
        self.path = 'unknown'
        self.init_ui()

    def init_ui(self):

        # set layout
        layout = QtGui.QGridLayout()
        layout.addWidget(self.path_label, 0, 0, 1, 4)
        layout.addWidget(self.path_line_edit, 1, 0, 1, 3)
        layout.addWidget(self.file_select_button, 1, 3, 1, 1)
        layout.addWidget(self.position_label, 4, 0, 1, 4)
        layout.addWidget(self.azimuth_label, 5, 0, 1, 1)
        layout.addWidget(self.azimuth_line_edit, 5, 1, 1, 1)
        layout.addWidget(self.distance_label, 5, 2, 1, 1)
        layout.addWidget(self.distance_line_edit, 5, 3, 1, 1)
        layout.addWidget(self.confirm_button, 6, 0, 1, 2)
        layout.addWidget(self.cancel_button, 6, 2, 1, 2)
        layout.addWidget(self.normalize_box, 4, 3, 1, 1)

        # connect signal and slots
        self.file_select_button.clicked.connect(self.browse)
        self.confirm_button.clicked.connect(self.confirm)
        self.cancel_button.clicked.connect(self.cancel)

        # set window
        self.setLayout(layout)
        self.setWindowTitle('Speaker Properties')

    @QtCore.Slot()
    def browse(self):
        """
        H2 -- browse
        ===================
        **Function corresponding to the browse button on the settings
        widget, to open a file dialog in order to choose a .wav file.**
        """

        file_browser = QtGui.QFileDialog()
        self.path = file_browser.getOpenFileName()[0]
        self.path_line_edit.setText(self.path)

    @QtCore.Slot()
    def confirm(self):
        """
        H2 -- confirm
        ===================
        **Function corresponding to the confirm button on the settings
        widget, to add a speaker to the QGraphicsScene with the choosen
        properties.**
        """
        x0 = self.state.audience_pos.x()
        y0 = self.state.audience_pos.y()
        azimuth = float(self.azimuth_line_edit.text())
        dist = 100 * float(self.distance_line_edit.text())
        self.posx = x0 + dist * sin(radians(azimuth))
        self.posy = y0 - dist * cos(radians(azimuth))

        x = self.posx
        y = self.posy

        self.posx, self.posy = self.get_bound_pos(x, y)
        self.added.emit()
        self.close()

    @QtCore.Slot()
    def cancel(self):
        """
        H2 -- cancel
        ===================
        **Function connected to the cancel button of SpeakerProperty.**
        Closes the SpeakerProperty window without making any changes to the
        speaker settings.
        """
        self.close()

    def clear(self):
        """
        H2 -- clear
        ===================
        **Function resets the default settings of the SpeakerProperty window.**
        """
        self.normalize_box.setCheckState(QtCore.Qt.Unchecked)
        self.path_line_edit.clear()
        self.azimuth_line_edit.clear()
        self.distance_line_edit.clear()
        self.posx = 0
        self.posy = 0

    def closeEvent(self, q_close_event):   # flake8: noqa
        """
        H2 -- closeEvent
        ===================
        **Function used with manual closing of the SpeakerProperty window.**
        """
        self.is_on = False
        self.added.disconnect()
        self.clear()

    def get_bound_pos(self, x, y):
        """
        H2 -- get_bound_pos
        ===================
        **Function avoids setting of coordinates which are outside the room.**
        """

        if x >= 350 and y >= 350:
            x = 350
            y = 350
        if x >= 350 and y <= 0:
            x = 350
            y = 0
        if x <= 0 and y <= 0:
            x = 0
            y = 0
        if x <= 0 and y >= 350:
            x = 0
            y = 350

        return x, y


# @class <SequencePlot> Additional window is created to display plot of speaker
# and HRTF spectrum while .wav is played
class SequencePlot(QtGui.QWidget):
    """
    H1 -- SequencePlot
    ************************
    **This class builts up a widget window to display real-time plots of the
    speaker sequence and HRTF sequence extracted from the DSP algorithm.**
    GLPlotWidget was preferred over Matplotlib due to performance. The plot
    is imported from plot.py.
    *plot_on: Signal to communicate wheter the plot widget is open.
    """

    plot_on = QtCore.Signal()

    """Constructor of the SequencePlot class."""
    def __init__(self, parent=None):
        super(SequencePlot, self).__init__(parent)
        self.is_on = False

        # initialize the GL widget
        self.speaker_spec = GLPlotWidget()
        self.lhrtf_spec = GLPlotWidget()
        self.rhrtf_spec = GLPlotWidget()

        self.layoutVertical = QtGui.QVBoxLayout(self)
        self.layoutVertical.addWidget(self.speaker_spec)
        self.layoutVertical.addWidget(self.lhrtf_spec)
        self.layoutVertical.addWidget(self.rhrtf_spec)
        self.setGeometry(100, 100, self.speaker_spec.width,
                         2 * self.speaker_spec.height)

        self.setWindowTitle('Sequence Plot')
        self.timer = QtCore.QTimer(self)

    def closeEvent(self, event):   # flake8: noqa
        """
        H2 -- closeEvent
        ===================
        **Function used with manual closing of the SequencePlot window.**
        """
        self.timer.timeout.disconnect()
        self.timer.stop()
        self.is_on = False
