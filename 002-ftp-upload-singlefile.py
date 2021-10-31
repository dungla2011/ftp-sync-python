import os

import PySimpleGUI as sg
import time
import threading


import ftplib

# Upload ok, show status


fileUp = 'e:/HirentBoot2015.GHO'

class FtpUploadTracker:
    sizeWritten = 0
    totalSize = 0
    lastShownPercent = 0

    def __init__(self, totalSize):
        self.totalSize = totalSize

    def handle(self, block):
        self.sizeWritten += 1024
        percentComplete = round((self.sizeWritten / self.totalSize) * 100)

        if (self.lastShownPercent != percentComplete):
            self.lastShownPercent = percentComplete
            print(str(percentComplete) + " percent complete")
        # else:
        #     print(".", " ")

totalSize = os.path.getsize(fileUp)

uploadTracker = FtpUploadTracker(int(totalSize))


def upload_file_thread(window, tid):

    session = ftplib.FTP()
    host = "glx.com.vn"
    port = 55555
    session.connect(host, port)
    print(session.getwelcome())
    try:
        print("Logging in...")
        session.login("backup01", "...")
    except:
        "failed to login"

    file = open(fileUp, 'rb')  # file to send
    session.storbinary('STOR test1234', file, 1024, uploadTracker.handle)  # send the file
    file.close()  # close file and FTP
    session.quit()

def upload_file(tid):
    threading.Thread(target=upload_file_thread, args=(window, tid), daemon=True).start()

layout = [[sg.Output(size=(60, 10))],
          [sg.Button('Go'), sg.Button('Nothing'), sg.Button('Exit')]]

window = sg.Window('FTP Sync', layout)

tid = 0

while True:  # Event Loop
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    if event == 'Go':
        tid += 1
        print('Call Upload function')
        upload_file(tid)
        print('Upload function has returned from starting')
    elif event == '-THREAD DONE-':
        print('Your Upload operation completed')
    else:
        print(event, values)
window.close()
