__author__ = 'hzhu'
from PyQt4.QtCore import QTimer

error_present = False
error_message = []

def check_error():
    global error_present
    if error_present:
        return error_message.pop(0)

def send_error(message):
    global error_present
    error_present = True
    if message not in error_message:
        error_message.append(message)

def update_error_state():
    global error_present
    print(len(error_message))
    if len(error_message) == 0:
        error_present = False