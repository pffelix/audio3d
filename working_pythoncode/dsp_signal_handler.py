__author__ = 'hzhu'
from PyQt4 import QtCore, QtGui

# Initialize this object in the Dsp class (already done)
# Usage:
# When error occurs, call the function self.signal_handler.send_error()
# The only parameter (A String!) is the message you want to send

class DspSignalHandler(QtCore.QObject):

    error_occur = QtCore.pyqtSignal()

    def __init__(self):
        super(DspSignalHandler, self).__init__()
        self.error_message = "message"

    def send_error(self, message):
        self.error_message = message;
        self.error_occur.emit()
