from PySide import QtGui, QtCore, QtOpenGL
from PySide.QtOpenGL import QGLWidget
import OpenGL.GL
import OpenGL.arrays.vbo as glvbo
import numpy as np

class GLPlotWidget(QGLWidget):
    """
    H1 -- GLPlotWidget
    ************************
    **This class sets up a GLPlot used for real-time plotting of the
    speaker and HRTF seuqences during the DSP algorithm is running as an
    additional feature in the MainWindow.**
    """

    """Constructor of the GLPlotWidget class."""
    def __init__(self, parent=None):
        super(GLPlotWidget, self).__init__(
            QtOpenGL.QGLFormat(QtOpenGL.QGL.SampleBuffers), parent)
        self.width = 400
        self.height = 150
        self.setFixedSize(self.width, self.height)
        self.setAutoFillBackground(False)

    def initialize_data(self, xdata_raw, ydata_raw):
        """
        H2 -- initialize_data
        ===================
        **This function sets the frequence intervall, defines the
        interpolation and adapts the plot to the sequence.**
        """
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
        self.ymax = np.max(ydata)
        if self.ymax != 0:
            self.ydata = ydata/self.ymax
        else:
            self.ydata = ydata
        # this line might be not needed in a futre version: the named axis
        # with Hz scale should reach from self.begin_hz to self.end_hz not
        # -1 Hz to 1 Hz -> the self.xdata = linspace(begin, end) command above
        # should be enough, but at the moment everything is scaled in between
        # -1 to 1 so i cannot delete it
        # (self.xdata contains the true Hz values)
        xdata = np.array(np.linspace(0, 1, ydata.shape[0]),
                         dtype=np.float32)
        self.size = self.xdata.size+ydata.size
        self.data = np.array(np.zeros(self.size), dtype=np.float32)

        self.data[0::2] = xdata
        self.data[1::2] = self.ydata
        self.count = ydata.size

    def set_data(self, xdata_raw, ydata_raw):
        """
        H2 -- set_data
        ===================
        **This function sets the plot variables respective to the sequence
        data.**
        """
        # interpolate y Values
        ydata = np.interp(self.xdata, xdata_raw, ydata_raw)
        self.ymax = np.max(ydata)
        if self.ymax != 0:
            self.ydata = ydata/self.ymax
        else:
            self.ydata = ydata
        self.data[1::2] = self.ydata

    def update_data(self, xdata_raw, ydata_raw):
        """
        H2 -- update_data
        ===================
        **This function updates the plot.**
        """
        self.set_data(xdata_raw, ydata_raw)
        self.repaint()

    def initializeGL(self):
        """
        H2 -- initializeGL
        ===================
        **This function initializes OpenGL, VBOs, upload data on the GPU, etc..
        .**
        """
        # background color
        OpenGL.GL.glClearColor(0, 0, 0, 0)
        self.vbo = glvbo.VBO(self.data)
        # create a Vertex Buffer Object with the specified data

    def paintEvent(self, event):
        """
        H2 -- mouseReleaseEvent
        ===================
        **This function is nessecary as GLPlotWidget does not offer pre-built
        plot settings. With this the axis are painted, scaled and named.**
        """
        self.makeCurrent()
        painter = QtGui.QPainter()
        painter.begin(self)

        OpenGL.GL.glClear(OpenGL.GL.GL_COLOR_BUFFER_BIT)
        OpenGL.GL.glColor(1, 1, 0)

        OpenGL.GL.glPushAttrib(OpenGL.GL.GL_ALL_ATTRIB_BITS)
        OpenGL.GL.glMatrixMode(OpenGL.GL.GL_PROJECTION)
        OpenGL.GL.glPushMatrix()
        OpenGL.GL.glMatrixMode(OpenGL.GL.GL_MODELVIEW)
        OpenGL.GL.glPushMatrix()

        self.vbo = glvbo.VBO(self.data)
        self.vbo.bind()
        OpenGL.GL.glEnableClientState(OpenGL.GL.GL_VERTEX_ARRAY)
        OpenGL.GL.glVertexPointer(2, OpenGL.GL.GL_FLOAT, 0, self.vbo)
        OpenGL.GL.glDrawArrays(OpenGL.GL.GL_POINTS, 0, self.count)
        self.vbo.unbind()
        OpenGL.GL.glDisableClientState(OpenGL.GL.GL_VERTEX_ARRAY)

        OpenGL.GL.glMatrixMode(OpenGL.GL.GL_MODELVIEW)
        OpenGL.GL.glPopMatrix()
        OpenGL.GL.glMatrixMode(OpenGL.GL.GL_PROJECTION)
        OpenGL.GL.glPopMatrix()
        OpenGL.GL.glPopAttrib()

        # paint the axis
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtGui.QColor(255, 255, 255))
        xaxis = QtCore.QLine(20, 130, 395, 130)
        yaxis = QtCore.QLine(20, 5, 20, 130)
        xarrow1 = QtCore.QLine(395, 130, 390, 127)
        xarrow2 = QtCore.QLine(395, 130, 390, 133)
        yarrow1 = QtCore.QLine(20, 5, 17, 10)
        yarrow2 = QtCore.QLine(20, 5, 23, 10)
        painter.drawLines([xaxis, yaxis, yarrow1, yarrow2, xarrow1, xarrow2])

        # paint the scale line
        scales_x = []
        scales_y = []
        for i in range(1, 6):
            scales_x.append(QtCore.QLine(76*i, 130, 76*i, 125))
            scales_y.append(QtCore.QLine(20, 130 - 22*i, 25, 130-22*i))
        painter.drawLines(scales_x)
        painter.drawLines(scales_y)

        # paint the axis description
        painter.drawText(QtCore.QPoint(10, 145), '0')

        for i in range(1, 6):
            xstring = "{:2.1f}".format(i*0.2)
            xpoint = QtCore.QPoint(0, 135 - 22*i)
            painter.drawText(xpoint, xstring)

        for i in range(1, 6):
            ystring = str(i*3)+'kHz'
            ypoint = QtCore.QPoint(76*i - 20, 145)
            painter.drawText(ypoint, ystring)

        painter.end()

    def resizeGL(self, width, height):
        """
        H2 -- resizeGL
        ===================
        **This function is called upon window resizing to reinitialize
        the viewport.**
        """
        self.width, self.height = width, height
        OpenGL.GL.glViewport(0, 0, width, height)
        OpenGL.GL.glMatrixMode(OpenGL.GL.GL_PROJECTION)
        OpenGL.GL.glLoadIdentity()
        OpenGL.GL.glOrtho(-0.06, 1.05, -0.18, 1.18, -1, 1)
