import os
import socket
import sys

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


def upload_file_thread():
    session = ftplib.FTP()
    host = "glx.com.vn"
    port = 55555
    username = "backup01"
    password = "..."

    tries = 0
    done = False
    print("Uploading " + str(fileUp) + " to /", flush=True)

    while not done:
        try:
            tries += 1

            # time.sleep(5)

            # with ftplib.FTP(host) as ftp:
            if 1:
                ftp = ftplib.FTP()
                ftp.connect(host, port)
                print(session.getwelcome())

                print("Logging in...")
                ftp.login("backup01", "....")

                ftp.set_debuglevel(2)
                print("login", flush=True)
                ftp.login(username, password)
                # ftp.set_pasv(False)
                ftp.cwd('/')
                with open(fileUp, 'rb') as f:
                    totalSize = os.path.getsize(fileUp)
                    print('Total file size : ' + str(round(totalSize / 1024 / 1024, 1)) + ' Mb', flush=True)
                    uploadTracker = FtpUploadTracker(int(totalSize))

                    # Get file size if exists
                    files_list = ftp.nlst()
                    # print(files_list, flush=True)
                    if os.path.basename(fileUp) in files_list:
                        print(" .... Resuming .... ", flush=True)
                        ftp.voidcmd('TYPE I')
                        rest_pos = ftp.size(os.path.basename(fileUp))
                        f.seek(rest_pos, 0)
                        print("seek to " + str(rest_pos))
                        uploadTracker.sizeWritten = rest_pos
                        print(ftp.storbinary('STOR ' + os.path.basename(fileUp), f,
                                             blocksize=1024, callback=uploadTracker.handle, rest=rest_pos), flush=True)
                        done = True
                    else:
                        print(ftp.storbinary('STOR ' + os.path.basename(fileUp), f, 1024, uploadTracker.handle),
                              flush=True)
                        done = True

        except (BrokenPipeError, ftplib.error_temp, socket.gaierror) as e:
            print(str(type(e)) + ": " + str(e))
            print("connection died, trying again 60 second ...")
            time.sleep(60)

    print("Done")

def upload_file():
    threading.Thread(target=upload_file_thread, args=(), daemon=True).start()

layout = [[sg.Output(size=(60, 10))],
          [sg.Button('Go'), sg.Button('Nothing'), sg.Button('Exit')]]

window = sg.Window('FTP Sync', layout)

while True:  # Event Loop
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    if event == 'Go':
        print('Call Upload function')
        upload_file()
        print('Upload function has returned from starting')
    elif event == '-THREAD DONE-':
        print('Your Upload operation completed')
    else:
        print(event, values)

window.close()
sys.exit()