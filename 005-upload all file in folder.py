import glob
import os
import socket
import sys
from tkinter import END

import PySimpleGUI as sg
import time
import threading
import ftplib

from psgtray import SystemTray

nameUploadThread = 'upload_glx'
stopThread = 0

folderUpload = "e:/Iso"
folderOnServer = "/iso"

class FtpUploadTracker:
    global stopThread, folderUpload, folderOnServer

    sizeWritten = 0
    totalSize = 0
    lastShownPercent = 0
    handleFtp = 0

    def __init__(self, totalSize):
        self.totalSize = totalSize

    def handle(self, block):
        self.sizeWritten += 1024
        percentComplete = round((self.sizeWritten / self.totalSize) * 100)

        if stopThread > 0:
            # print(" stopThread 3 ")
            #self.handleFtp.abort()
            # Khi dừng thread, phải dừng FTP bằng cách này, nếu không file cuối sẽ upload xong, mới kết thúc Thread
            self.handleFtp.close()

        if (self.lastShownPercent != percentComplete):
            self.lastShownPercent = percentComplete
            sg.cprint(str(percentComplete) + " percent complete")

def upload_file_thread():

    global stopThread , textBox

    # session = ftplib.FTP()
    host = "glx.com.vn"
    port = 55555
    username = "backup01"
    password = "..."
    stopThread = 0
    tries = 0
    done = False

    while not done:
        if stopThread > 0:
            print(" stopThread 4 ")
            return

        try:
            tries += 1

            # time.sleep(5)

            # with ftplib.FTP(host) as ftp:
            if 1:
                print("connecting to " + host + " ... ")

                ftp = ftplib.FTP()

                ftp.connect(host, port)
                # print(session.getwelcome())

                print("Logging in...")

                ftp.login("backup01", "...")

                ftp.set_debuglevel(2)

                ftp.login(username, password)


                # ftp.set_pasv(False)



                ftp.cwd(folderOnServer)

                for fileUp in glob.iglob(folderUpload + '**/**', recursive=True):

                    if stopThread > 0:
                        print(" stopThread 5 ")
                        done = True
                        return

                    print(" ----- LEN = " + str(textBox.get_size()))

                    if os.path.isfile(fileUp):
                        print("=== Upload now === " + fileUp)
                        with open(fileUp, 'rb') as f:

                            if stopThread > 0:
                                print(" stopThread 1 ")
                                done = True
                                return

                            totalSize = os.path.getsize(fileUp)
                            print('Total file size : ' + str(round(totalSize / 1024 / 1024, 1)) + ' Mb', flush=True)
                            uploadTracker = FtpUploadTracker(int(totalSize))
                            uploadTracker.handleFtp = ftp

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

                                try:
                                    print(ftp.storbinary('STOR ' + os.path.basename(fileUp), f,
                                                     blocksize=1024, callback=uploadTracker.handle, rest=rest_pos), flush=True)

                                except Exception as e:
                                    print("*** Upload Exception glx: " + e.__doc__)

                                done = True
                            else:
                                print(ftp.storbinary('STOR ' + os.path.basename(fileUp), f, 1024, uploadTracker.handle),
                                      flush=True)
                                done = True

        except (BrokenPipeError, ftplib.error_temp, socket.gaierror) as e:
            print(str(type(e)) + ": " + str(e))
            print("connection died, trying again 60 second ...")

            for i in range(60):
                time.sleep(1)
                if stopThread > 0:
                    print(" stopThread 2 ")
                    return

    print("Done")

def upload_file():

    for thread in threading.enumerate():
        print(" threadname " + thread.name + " ID " + str(thread.native_id))
        if thread.name == nameUploadThread:
            sg.Popup("Uploading is running already!")
            return

    new_thread = threading.Thread(target=upload_file_thread, args=(), daemon=True)
    new_thread.name = nameUploadThread
    new_thread.start()

# https://github.com/PySimpleGUI/psgtray
menu = ['', ['Show Window', 'Hide Window', '---', '!Disabled Item', 'Change Icon', ['Happy', 'Sad', 'Plain'], 'Exit']]
tooltip = 'Ftp Sync GalaxyCloud'

textBox = sg.Multiline(size=(60,20), reroute_stdout=True, reroute_cprint=True, write_only=True, key='-OUT-')


setServer = ''
setPort = ''
setUsername = ''
setPassword = ''
setFolderLocal = ''
setFolderServer = ''

layout = [
    # [sg.Text('My PySimpleGUI Celebration Window - X will minimize to tray')],
    #       [sg.T('Double clip icon to restore or right click and choose Show Window')],
    #       [sg.T('Icon Tooltip:'), sg.Input(tooltip, key='-IN-', s=(20,1)), sg.B('Change Tooltip')],
            [sg.T('Server'), sg.Input(setServer, key='-IN-', s=(20,1)), sg.T('Port'), sg.Input(setPort, key='-IN-', s=(20,1))],
            [sg.T('Username'), sg.Input(setUsername, key='-IN-', s=(20,1)), sg.T('Password'), sg.Input(setPassword, key='-IN-', s=(20,1))],
          [sg.T('Local Folder'), sg.Input(setFolderLocal, key='-IN-', s=(40,1))],
            [sg.T('Server Folder'), sg.Input(setFolderServer, key='-IN-', s=(40,1))],
          [textBox],
          [sg.Button('StartSync'),  sg.B('StopSync'),  sg.B('Clear'), sg.B('Hide Icon'), sg.B('Show Icon'), sg.B('Hide Window'), sg.Button('Exit')]]

window = sg.Window('FTP Sync', layout, finalize=True, enable_close_attempted_event=True)
# window = sg.Window('FTP Sync - GalaxyCloud', layout)

tray = SystemTray(menu, single_click_events=False, window=window, tooltip=tooltip, icon=sg.DEFAULT_BASE64_ICON)
# tray.show_message('System Tray', 'System Tray Icon Started!')
sg.cprint(sg.get_versions())

while True:  # Event Loop
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    if event == 'StartSync':
        print('Call StartSync function')
        upload_file()
        print('Upload function has returned from starting')
    if event == 'StopSync':
        for thread in threading.enumerate():
            if thread.name == nameUploadThread:
                print(" set stopThread = 1")
                stopThread = 1
    if event == 'Clear':
        textBox.update("")
    elif event == '-THREAD DONE-':
        print('Your Upload operation completed')
    else:
        print(event, values)

    if event == tray.key:
            sg.cprint(f'System Tray Event = ', values[event], c='white on red')
            event = values[event]       # use the System Tray's event as if was from the window

    #https://github.com/PySimpleGUI/psgtray
    # sg.cprint(event, values)

    # tray.show_message(title=event, message=values)

    if event in ('Show Window', sg.EVENT_SYSTEM_TRAY_ICON_DOUBLE_CLICKED):
        window.un_hide()
        window.bring_to_front()
    elif event in ('Hide Window', sg.WIN_CLOSE_ATTEMPTED_EVENT):
        window.hide()
        tray.show_icon()        # if hiding window, better make sure the icon is visible
        # tray.notify('System Tray Item Chosen', 'You chose {event}')
        tray.show_message('System Tray', 'System Tray Icon Started!')
    elif event == 'Happy':
        tray.change_icon(sg.EMOJI_BASE64_HAPPY_JOY)
    elif event == 'Sad':
        tray.change_icon(sg.EMOJI_BASE64_FRUSTRATED)
    elif event == 'Plain':
        tray.change_icon(sg.DEFAULT_BASE64_ICON)
    elif event == 'Hide Icon':
        tray.hide_icon()
    elif event == 'Show Icon':
        tray.show_icon()
    elif event == 'Change Tooltip':
        tray.set_tooltip(values['-IN-'])
    elif event == 'Exit':
        break
    else:
        print(event, values)

tray.close()            # optional but without a close, the icon may "linger" until moused over
window.close()
sys.exit()
