
from PyQt4 import QtCore, QtGui


class ColorItem(QtGui.QGraphicsItem):
    n = 0

    def __init__(self):
        super(ColorItem, self).__init__()

        self.color = QtGui.QColor(QtCore.qrand() % 256, QtCore.qrand() % 256,
                QtCore.qrand() % 256)

        self.setToolTip(
            "QColor(%d, %d, %d)\nClick and drag this speaker!" %
              (self.color.red(), self.color.green(), self.color.blue())
        )
        self.setCursor(QtCore.Qt.OpenHandCursor)
    
    def boundingRect(self):
        return QtCore.QRectF(-15.5, -15.5, 34, 34)

    def paint(self, painter, option, widget):
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtCore.Qt.darkGray)
        painter.drawEllipse(-12, -12, 30, 30)
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 1))
        painter.setBrush(QtGui.QBrush(self.color))
        painter.drawEllipse(-15, -15, 30, 30)

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

        mime.setColorData(self.color)
        mime.setText("#%02x%02x%02x" % (self.color.red(), self.color.green(), self.color.blue()))

        pixmap = QtGui.QPixmap(34, 34)
        pixmap.fill(QtCore.Qt.white)

        painter = QtGui.QPainter(pixmap)
        painter.translate(15, 15)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        self.paint(painter, None, None)
        painter.end()

        pixmap.setMask(pixmap.createHeuristicMask())

        drag.setPixmap(pixmap)
        drag.setHotSpot(QtCore.QPoint(15, 20))

        drag.exec_()
        self.setCursor(QtCore.Qt.OpenHandCursor)

    def mouseReleaseEvent(self, event):
        self.setCursor(QtCore.Qt.OpenHandCursor)

