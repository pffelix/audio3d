from PyQt4 import QtCore, QtGui

gui_dict = {}
audience_pos = QtCore.QPoint(170, 170)
speaker_list = []
speaker_to_show = 0

class Item(QtGui.QGraphicsPixmapItem):


    def __init__(self):

        image = self.origin_image.scaled(50, 50, QtCore.Qt.KeepAspectRatio)
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

        if QtCore.QLineF(QtCore.QPointF(event.screenPos()), QtCore.QPointF(event.buttonDownScreenPos(QtCore.Qt.LeftButton))).length() < QtGui.QApplication.startDragDistance():
            return

        drag = QtGui.QDrag(event.widget())
        mime = QtCore.QMimeData()
        drag.setMimeData(mime)
        drag.exec_()
        self.setCursor(QtCore.Qt.OpenHandCursor)

    def mouseReleaseEvent(self, event):
        self.setCursor(QtCore.Qt.OpenHandCursor)


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
            self.current_item.setPos(e.scenePos())
            if self.current_item.type == 'audience':
                audience_pos = e.scenePos()

                for speaker in speaker_list:
                    speaker.cal_rel_pos()

            elif self.current_item.type == 'speaker':
                self.current_item.cal_rel_pos()
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

# Signal handler for QGraphicsItem which doesn't provide the signal/slot function
class SignalHandler(QtCore.QObject):

    show_property = QtCore.pyqtSignal()

    def __init__(self, index):
        super(SignalHandler, self).__init__()
        self.index = index


class Speaker(Item):
    global speaker_to_show
    global gui_dict
    global speaker_list
    global audience_pos
    index = 0
    type = 'speaker'
    path = 'unknown'

    def __init__(self, index, path, posx=0,posy=0):

        self.index = index
        image_path = './image/speaker'+str(index+1)+'.png'
        self.origin_image = QtGui.QImage(image_path)
        super(Speaker, self).__init__()
        self.setPos(posx,posy)
        self.path = path
        self.signal_handler = SignalHandler(self.index)
        speaker_list.append(self)
        self.cal_rel_pos()

    def cal_rel_pos(self):

        dx = self.x() - audience_pos.x()
        dy = audience_pos.y() - self.y()
        dis = (dx**2+dy**2)**0.5

        from math import acos, degrees
        deg = degrees(acos(dy/dis))
        if dx < 0:
            deg = 360 - deg

        gui_dict[self.index] = [deg, dis/100, self.path]
        print(gui_dict)

    def mouseDoubleClickEvent(self, event):

        speaker_to_show = self.index
        self.signal_handler.show_property.emit()


class Audience(Item):

    type = 'audience'
    origin_image = QtGui.QImage('./image/audience.jpeg')

    def __init__(self):
        global audience_pos

        super(Audience, self).__init__()
        self.setPos(170, 170)
        audience_pos = self.pos()

class SpeakerProperty(QtGui.QWidget):

    added = QtCore.pyqtSignal()
    posx = 0
    posy = 0

    def __init__(self):
        super(SpeakerProperty,self).__init__()

        # set labels
        self.path_label = QtGui.QLabel('Audio Source:')
        self.position_label = QtGui.QLabel('Relative Position to the Audience:')
        self.azimuth_label = QtGui.QLabel('Azimuth:')
        self.distance_label = QtGui.QLabel('Distance:')
        # set line edit
        self.path_line_edit = QtGui.QLineEdit()
        self.azimuth_line_edit = QtGui.QLineEdit()
        self.distance_line_edit = QtGui.QLineEdit()

        # set buttons
        self.file_select_button = QtGui.QPushButton('Browse')
        self.confirm_button = QtGui.QPushButton('Confirm')
        self.cancel_button = QtGui.QPushButton('Cancel')
        self.path = 'unknown'
        self.setModal(True)
        self.init_ui()

    def init_ui(self):

        # set layout
        layout = QtGui.QGridLayout()
        layout.addWidget(self.path_label, 0, 0, 1, 4)
        layout.addWidget(self.path_line_edit, 1, 0, 1, 3)
        layout.addWidget(self.file_select_button, 1, 3, 1, 1)
        layout.addWidget(self.position_label, 3, 0, 1, 4)
        layout.addWidget(self.azimuth_label, 4, 0, 1, 1)
        layout.addWidget(self.azimuth_line_edit, 4, 1, 1, 1)
        layout.addWidget(self.distance_label, 4, 2, 1, 1)
        layout.addWidget(self.distance_line_edit, 4, 3, 1, 1)
        layout.addWidget(self.confirm_button, 5, 0, 1, 2)
        layout.addWidget(self.cancel_button, 5, 2, 1, 2)

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
        from math import cos, sin, radians
        x0 = audience_pos.x()
        y0 = audience_pos.y()
        azimuth = float(self.azimuth_line_edit.text())
        dist = 100*float(self.distance_line_edit.text())
        self.posx = x0 + dist*sin(radians(azimuth))
        self.posy = y0 - dist*cos(radians(azimuth))
        self.added.emit()
        self.close()

    @QtCore.pyqtSlot()
    def cancel(self):
        self.close()

    def clear(self):
        self.path_line_edit.clear()
        self.azimuth_line_edit.clear()
        self.distance_line_edit.clear()
        self.path = 'unknown'
        self.posx = 0
        self.posy = 0