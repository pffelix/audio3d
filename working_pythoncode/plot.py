from PySide import QtGui, QtCore, QtOpenGL
from PySide.QtOpenGL import QGLWidget
from PySide.QtGui import QPaintEvent
import OpenGL.GL as gl
import OpenGL.arrays.vbo as glvbo
import numpy as np


class GLPlotWidget(QGLWidget):

    def __init__(self, parent=None):
        super(GLPlotWidget, self).__init__(QtOpenGL.QGLFormat(QtOpenGL.QGL.SampleBuffers), parent)
        self.width = 400
        self.height = 150
        self.setFixedSize(self.width,self.height)
        self.setAutoFillBackground(False)

    def initialize_data(self, xdata_raw, ydata_raw):
        # Felix
        # interpolate x and y Values
        # first frequency
        self.begin_hz = 0
        # last frequency
        self.end_hz = 15000
        # number of frequency points
        self.number_of_points = 15000
        # interpolate x frequency values
        self.xdata = np.linspace(self.begin_hz, self.end_hz,
                                 self.number_of_points)
        # interpolate y magnitude values
        ydata = np.interp(self.xdata, xdata_raw, ydata_raw)

        # Huaijiang
        self.ydata = ydata/np.max(ydata)
        # this line might be not needed in a futre version: the named axis
        # with Hz scale should reach from self.begin_hz to self.end_hz not -1 Hz
        #  to 1 Hz -> the self.xdata = linspace(begin, end) command above should
        #  be enough, but at the moment everything is scaled in between -1 to 1
        #  so i cannot delete it (self.xdata contains the true Hz values)
        xdata = np.array(np.linspace(0, 1, ydata.shape[0]),
                         dtype=np.float32)
        self.size = self.xdata.size+ydata.size
        self.data = np.array(np.zeros(self.size), dtype=np.float32)

        self.data[0::2] = xdata
        self.data[1::2] = self.ydata
        self.count = ydata.size

    def set_data(self, xdata_raw, ydata_raw):
        # interpolate y Values
        ydata = np.interp(self.xdata, xdata_raw, ydata_raw)
        self.ydata = ydata/np.max(ydata)
        self.data[1::2] = self.ydata

    def update_data(self, xdata_raw, ydata_raw):
        self.set_data(xdata_raw, ydata_raw)
        self.repaint()

    def initializeGL(self):
        """Initialize OpenGL, VBOs, upload data on the GPU, etc.
        """
        # background color
        gl.glClearColor(0, 0, 0, 0)
        self.vbo = glvbo.VBO(self.data)
        # create a Vertex Buffer Object with the specified data

    def paintEvent(self, event):
        """Paint the scene.
        """
        self.makeCurrent()
        painter = QtGui.QPainter()
        painter.begin(self)

        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glColor(1,1,0)

        gl.glPushAttrib(gl.GL_ALL_ATTRIB_BITS)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()

        self.vbo = glvbo.VBO(self.data)
        self.vbo.bind()
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        gl.glVertexPointer(2, gl.GL_FLOAT, 0, self.vbo)
        gl.glDrawArrays(gl.GL_POINTS, 0, self.count)
        self.vbo.unbind()
        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()
        gl.glPopAttrib()

        # # paint the axis
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtGui.QColor(255,255,255))
        xaxis = QtCore.QLine(20, 130, 380, 130)
        yaxis = QtCore.QLine(20, 20, 20, 130)
        painter.drawLines([xaxis,yaxis])
        painter.end()

    def resizeGL(self, width, height):
        """Called upon window resizing: reinitialize the viewport.
        """
        self.width, self.height = width, height
        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(-0.05, 1.05, -0.18, 1.18, -1, 1)
