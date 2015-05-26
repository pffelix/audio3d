
from PyQt4 import QtCore, QtGui
import gui_main_window as mw

gui_dict = {}
audience_pos = QtCore.QPoint(170, 170)
speaker_list = []
speaker_added = 0

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

        # image = self.origin_image.scaled(50, 50, QtCore.Qt.KeepAspectRatio)
        # pixmap = QtGui.QPixmap.fromImage(image)
        #
        # pixmap.setMask(pixmap.createHeuristicMask())

        # drag.setPixmap(pixmap)
        # drag.setHotSpot(QtCore.QPoint(50, 50))

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

    # def dropEvent(self, e):
    #     global audience_pos
    #     global speaker_list
    #     self.current_item.setPos(e.scenePos())
    #
    #     if self.current_item.type == 'audience':
    #         audience_pos = e.scenePos()
    #
    #         for speaker in speaker_list:
    #             speaker.cal_rel_pos()
    #
    #     elif self.current_item.type == 'speaker':
    #         self.current_item.cal_rel_pos()

    def dragMoveEvent(self, e):

        e.acceptProposedAction()
        global audience_pos
        global speaker_list
        self.current_item.setPos(e.scenePos())
        if self.current_item.type == 'audience':
            audience_pos = e.scenePos()

            for speaker in speaker_list:
                speaker.cal_rel_pos()

        elif self.current_item.type == 'speaker':
            self.current_item.cal_rel_pos()

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

class Speaker(Item):

    index = 0
    type = 'speaker'
    origin_image = QtGui.QImage('./image/speaker.png')
    path = 'unknown'

    def __init__(self, index, path):
        global gui_dict
        global speaker_list

        super(Speaker, self).__init__()
        self.setPos(0,0)
        self.index = index
        self.path = path
        speaker_list.append(self)
        self.cal_rel_pos()

    def cal_rel_pos(self):
        global audience_pos
        global gui_dict
        dx = self.x() - audience_pos.x()
        dy = audience_pos.y() - self.y()
        dis = (dx**2+dy**2)**0.5

        from math import acos, degrees
        deg = degrees(acos(dy/dis))
        if dx < 0:
            deg = 360 - deg

        gui_dict[self.index] = [deg, dis/100, self.path]
        print(gui_dict)

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

    def __init__(self):
        super(SpeakerProperty,self).__init__()

        # set labels
        self.path_label = QtGui.QLabel('Audio Source:')
        self.position_label = QtGui.QLabel('Relative Position to the Audience:')
        # set line edit
        self.path_line_edit = QtGui.QLineEdit()
        # set buttons
        self.file_select_button = QtGui.QPushButton('Browse')
        self.path = 'unknown'
        self.init_ui()

    def init_ui(self):

        # set layout
        layout = QtGui.QGridLayout()
        layout.addWidget(self.path_label, 0, 0, 1, 1)
        layout.addWidget(self.path_line_edit, 1, 0, 1, 2)
        layout.addWidget(self.file_select_button, 1, 2, 1, 1)
        layout.addWidget(self.position_label, 3, 0, 1, 1)

        # connect signal and slots
        self.file_select_button.clicked.connect(self.browse)

        # set window
        self.setLayout(layout)
        # self.setFixedSize(500, 600)
        self.setWindowTitle('Speaker Properties')

    @QtCore.pyqtSlot()
    def browse(self):

        file_browser = QtGui.QFileDialog()
        self.path = file_browser.getOpenFileName()
        self.path_line_edit.setText(self.path)
        self.added.emit()