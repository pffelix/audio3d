"""
Library for GUI of Audio 3D Project, Group B
author: H. Zhu, M. Heiss
"""

from PyQt4 import QtCore, QtGui

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
# import matplotlib.pyplot as plt
# import numpy as np

# initialization of variables
gui_dict = {}
gui_stop = True
gui_pause = False
audience_pos = QtCore.QPoint(170, 170)
speaker_list = []
speaker_to_show = 0


# stop playback and convolution of dsp algorithm
def switch_stop_playback():
    global gui_stop
    if gui_stop is False:
        gui_stop = True
    else:
        gui_stop = False
    print (gui_stop)
    return gui_stop

def switch_pause_playback():
    global gui_pause
    # start pause
    if gui_pause is False:
        gui_pause = True
    # end pause
    else:
        gui_pause = False
    print (gui_pause)


# Headtracker - to be implemented
class Headtracker(object):

    def __init__(self):
        self.head_deg = 0

    def cal_head_deg(self):
        pass

    def get_head_deg(self):
        return self.head_deg


# Items inside the QGraphicsScene, including Speaker and Audience
class Item(QtGui.QGraphicsPixmapItem):

    def __init__(self):

        image = self.origin_image.scaled(
            50, 50, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

        super(Item, self).__init__(QtGui.QPixmap.fromImage(image))

        self.setCursor(QtCore.Qt.OpenHandCursor)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtGui.QGraphicsItem.ItemIsFocusable)

    def mousePressEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            event.ignore()
            return

        self.setCursor(QtCore.Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):

        if QtCore.QLineF(QtCore.QPointF(event.screenPos()),
                         QtCore.QPointF(event.buttonDownScreenPos(
                             QtCore.Qt.LeftButton))).length() < QtGui.QApplication.startDragDistance():
                                return

        drag = QtGui.QDrag(event.widget())
        mime = QtCore.QMimeData()
        drag.setMimeData(mime)
        drag.exec_()
        self.setCursor(QtCore.Qt.OpenHandCursor)

    def mouseReleaseEvent(self, event):
        self.setCursor(QtCore.Qt.OpenHandCursor)


# Room displays the relative Audience and Speaker items positions
class Room(QtGui.QGraphicsScene):

    current_item = 0

    def mousePressEvent(self, e):
        self.current_item = self.itemAt(e.scenePos())
        QtGui.QGraphicsScene.mousePressEvent(self, e)

    def dragEnterEvent(self, e):
        e.acceptProposedAction()

    def dragMoveEvent(self, e):

        e.acceptProposedAction()
        global audience_pos
        global speaker_list
        try:
            self.current_item.setPos(e.scenePos().x()-25, e.scenePos().y()-25)
            x = self.current_item.scenePos().x()
            y = self.current_item.scenePos().y()

            if x > 350:
                self.current_item.setPos(350, y)
                if y > 350:
                    self.current_item.setPos(350, 350)
                if y < 0:
                    self.current_item.setPos(350, 0)
            if x < 0:
                self.current_item.setPos(0, y)
                if y < 0:
                    self.current_item.setPos(0, 0)
                if y > 350:
                    self.current_item.setPos(0, 350)
            if y < 0:
                self.current_item.setPos(x, 0)
                if x < 0:
                    self.current_item.setPos(0, 0)
                if x > 350:
                    self.current_item.setPos(350, 0)
            if y > 350:
                self.current_item.setPos(x, 350)
                if x > 350:
                    self.current_item.setPos(350, 350)
                if x < 0:
                    self.current_item.setPos(0, 350)

            if self.current_item.type == 'audience':
                audience_pos = self.current_item.pos()

                for speaker in speaker_list:
                    speaker.cal_rel_pos()

            elif self.current_item.type == 'speaker':
                self.current_item.cal_rel_pos()
                global speaker_to_show
                speaker_to_show = self.index
        except AttributeError:
            pass


class View(QtGui.QGraphicsView):

    def dragEnterEvent(self, e):
        e.acceptProposedAction()
        QtGui.QGraphicsView.dragEnterEvent(self, e)

    def dropEvent(self, e):
        self.viewport().update()
        QtGui.QGraphicsView.dropEvent(self, e)

    def dragMoveEvent(self, e):
        e.acceptProposedAction()
        QtGui.QGraphicsView.dragMoveEvent(self, e)

    # this will disable scrolling of the view
    def wheelEvent(self, QWheelEvent):
        pass

    def keyPressEvent(self, QKeyEvent):
        pass


# Signal handler for QGraphicsItem
# which doesn't provide the signal/slot function
class SignalHandler(QtCore.QObject):

    show_property = QtCore.pyqtSignal()

    def __init__(self, index):
        super(SignalHandler, self).__init__()
        self.index = index


# Speaker item represent the source positions in the QGraphicsScene
# relative to the Audience item
class Speaker(Item):

    index = 0
    type = 'speaker'
    path = 'unknown'

    def __init__(self, index, path, posx=0, posy=0, norm=False):

        global speaker_list
        self.index = index
        image_path = './image/speaker'+str(index+1)+'.png'
        self.origin_image = QtGui.QImage(image_path)
        super(Speaker, self).__init__()
        self.setPos(posx, posy)
        self.path = path
        self.norm = norm
        self.signal_handler = SignalHandler(self.index)
        speaker_list.append(self)
        self.cal_rel_pos()

    def cal_rel_pos(self):
        global gui_dict
        global audience_pos
        dx = self.x() - audience_pos.x()
        dy = audience_pos.y() - self.y()
        dis = (dx**2+dy**2)**0.5

        from math import acos, degrees
        deg = degrees(acos(dy/dis))
        if dx < 0:
            deg = 360 - deg

        head_tracker = Headtracker()
        head_tracker.cal_head_deg()
        deg += head_tracker.get_head_deg()

        if deg >= 360:
            deg %= 360
        gui_dict[self.index] = [deg, dis/100, self.path, self.norm]
        # print(gui_dict)

    def mouseDoubleClickEvent(self, event):
        global speaker_to_show
        speaker_to_show = self.index
        self.signal_handler.show_property.emit()


# Audience item represents the relative user position in the QGraphicsScene
class Audience(Item):

    type = 'audience'
    origin_image = QtGui.QImage('./image/audience.png')

    def __init__(self):
        global audience_pos

        super(Audience, self).__init__()
        self.setPos(170, 170)
        audience_pos = self.scenePos()


# Widget window where speaker properties can be adjusted individually
class SpeakerProperty(QtGui.QWidget):

    added = QtCore.pyqtSignal()
    closed = QtCore.pyqtSignal()
    posx = 0
    posy = 0

    def __init__(self):
        super(SpeakerProperty, self).__init__()

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

    @QtCore.pyqtSlot()
    def browse(self):

        file_browser = QtGui.QFileDialog()
        self.path = file_browser.getOpenFileName()
        self.path_line_edit.setText(self.path)

    @QtCore.pyqtSlot()
    def confirm(self):
        global ear
        ear = self.combo_box.currentText()

        from math import cos, sin, radians
        x0 = audience_pos.x()
        y0 = audience_pos.y()
        azimuth = float(self.azimuth_line_edit.text())
        dist = 100*float(self.distance_line_edit.text())
        # if azimuth < 360 and dist < 300.0:
        self.posx = x0 + dist*sin(radians(azimuth))
        self.posy = y0 - dist*cos(radians(azimuth))

        x = self.posx
        y = self.posy

        if x > 350:
            self.posx = 350
            if y > 350:
                self.posy = 350
            if y < 0:
                self.posy = 0
        elif x < 0:
            self.posx = 0
            if y < 0:
                self.posy = 0
            if y > 350:
                self.posy = 350
        elif y < 0:
            self.posy = 0
            if x < 0:
                self.posx = 0
            if x > 350:
                self.posx = 350
        elif y > 350:
            self.posy = 350
            if x > 350:
                self.posx = 350
            if x < 0:
                self.posx = 0
        # if self.posx > 0 and self.posx < 350 and
        #                      self.posy > 0 and self.posy < 350:
        #     self.added.emit()
        #     self.close()
        # else:
        #     QtGui.QMessageBox.question(self, 'Message',
        #              'A value is out of range! Try again.',
        #                  QtGui.QMessageBox.Ok)

        print(self.posx)
        print(self.posy)
        self.added.emit()
        self.close()

    @QtCore.pyqtSlot()
    def cancel(self):
        self.close()

    def clear(self):
        self.normalize_box.setCheckState(QtCore.Qt.Unchecked)
        self.path_line_edit.clear()
        self.azimuth_line_edit.clear()
        self.distance_line_edit.clear()
        self.path = 'unknown'
        self.posx = 0
        self.posy = 0

    def closeEvent(self, QCloseEvent):
        self.closed.emit()


# Additional window for plot of speaker and HRTF spectrum while .wav is played
class SequencePlot(QtGui.QWidget):
    plot_closed = QtCore.pyqtSignal()
    plot_on = QtCore.pyqtSignal()

    def __init__(self):
        super(SequencePlot, self).__init__()

        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.axis0 = self.figure.add_subplot(311)
        self.axis1 = self.figure.add_subplot(312, ylabel='right HRTF')
        self.axis2 = self.figure.add_subplot(313, ylabel='left HRTF')

        self.layoutVertical = QtGui.QVBoxLayout(self)
        self.layoutVertical.addWidget(self.canvas)

        self.setWindowTitle('Sequence Plot')
        self.timer = QtCore.QTimer(self)

    def closeEvent(self, QCloseEvent):
        self.plot_closed.emit()
