from PySide import QtGui, QtCore, QtOpenGL
from PySide.QtOpenGL import QGLWidget
from PySide.QtGui import QPaintEvent
import OpenGL.GL as gl
import OpenGL.arrays.vbo as glvbo
import numpy as np


class GLPlotWidget(QGLWidget):
    width, height = 400, 200

    def set_data(self, xdata_raw, ydata_raw):
        # interpolate Values
        # first frequency
        begin_hz = 0
        # last frequency
        end_hz = 15000
        number_of_points = 15000
        self.xdata = np.linspace(begin_hz, end_hz, number_of_points)
        ydata = np.interp(self.xdata, xdata_raw, ydata_raw)

        self.xdata = np.array(np.linspace(-1, 1, ydata.shape[0]),
                              dtype=np.float32)
        self.ydata = ydata/np.max(ydata)
        self.size = self.xdata.size+ydata.size
        self.data = np.array(np.zeros(self.size), dtype=np.float32)

        self.data[0::2] = self.xdata
        self.data[1::2] = ydata
        self.count = ydata.size

    def update_data(self, xdata_raw, ydata_raw):
        self.set_data(xdata_raw, ydata_raw)
        self.repaint()
        self.updateGL()

    def initializeGL(self):
        """Initialize OpenGL, VBOs, upload data on the GPU, etc.
        """
        # background color
        gl.glClearColor(0, 0, 0, 0)
        # gl.setAutoBufferSwap(False)
        # gl.setAutoFillBackground(False)
        self.vbo = glvbo.VBO(self.data)
        # create a Vertex Buffer Object with the specified data

    def paintEvent(self, event):
        """Paint the scene.
        """
        event.accept()
        self.makeCurrent()
        # clear the buffer
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glColor(1,1,0)
        self.vbo = glvbo.VBO(self.data)
        self.vbo.bind()
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        gl.glVertexPointer(2, gl.GL_FLOAT, 0, self.vbo)
        gl.glDrawArrays(gl.GL_POINTS, 0, self.count)
        # self.swapBuffers()

    def resizeGL(self, width, height):
        """Called upon window resizing: reinitialize the viewport.
        """
        self.width, self.height = width, height
        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(-1, 1, -0.2, 1, -1, 1)



