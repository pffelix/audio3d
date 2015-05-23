
from PyQt4 import QtCore, QtGui


class Item(QtGui.QGraphicsPixmapItem):

    origin_image = QtGui.QImage('./image/speaker.png')
    image = origin_image.scaled(50, 50, QtCore.Qt.KeepAspectRatio)

    def __init__(self):

        super(Item, self).__init__(QtGui.QPixmap.fromImage(self.image))
        self.setToolTip("Click and drag this speaker!")
        self.setCursor(QtCore.Qt.OpenHandCursor)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtGui.QGraphicsItem.ItemIsFocusable)

    def boundingRect(self):
        return QtCore.QRectF(-15.5, -15.5, 34, 34)

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

        pixmap = QtGui.QPixmap.fromImage(self.image)

        pixmap.setMask(pixmap.createHeuristicMask())

        drag.setPixmap(pixmap)
        drag.setHotSpot(QtCore.QPoint(30, 30))

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

    def dropEvent(self, e):
        self.current_item.setPos(e.scenePos())

    def dragMoveEvent(self, e):
        e.acceptProposedAction()

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

class AddSpeakerButton(QtGui.QPushButton):

    def __init__(self):
        super(AddSpeakerButton,self).__init__('Add Speaker')