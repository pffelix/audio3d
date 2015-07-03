__author__ = 'hzhu'
from PyQt4.QtCore import QTimer

error_message = []

def check_error():
    if len(error_message) > 0:
        return error_message.pop(0)

def send_error(message):
    if message not in error_message:
        error_message.append(message)
