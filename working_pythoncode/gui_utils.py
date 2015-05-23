
from PyQt4 import QtCore, QtGui


class Item(QtGui.QGraphicsPixmapItem):

    origin_image = QtGui.QImage('./image/speaker.png')
    image = origin_image.scaled(50, 50, QtCore.Qt.KeepAspectRatio)

    def __init__(self):

        super(Item, self).__init__(QtGui.QPixmap.fromImage(self.image))
        self.setToolTip("Click and drag this speaker!")
        self.setCursor(QtCore.Qt.OpenHandCursor)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)

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
        drag.setHotSpot(QtCore.QPoint(20, 20))

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
