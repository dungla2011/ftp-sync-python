import os
import socket
import sys

import PySimpleGUI as sg
import time
import threading

import ftplib
from psgtray import SystemTray

# Upload ok, show status
# tray icon ok

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
            sg.cprint(str(percentComplete) + " percent complete")


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
                print("connecting to " + host + " ... ")

                ftp = ftplib.FTP()
                ftp.connect(host, port)
                print(session.getwelcome())

                print("Logging in...")

                ftp.login("backup01", "...")

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


# https://github.com/PySimpleGUI/psgtray
menu = ['', ['Show Window', 'Hide Window', '---', '!Disabled Item', 'Change Icon', ['Happy', 'Sad', 'Plain'], 'Exit']]
tooltip = 'Ftp Sync GalaxyCloud'

layout = [[sg.Text('My PySimpleGUI Celebration Window - X will minimize to tray')],
          [sg.T('Double clip icon to restore or right click and choose Show Window')],
          [sg.T('Icon Tooltip:'), sg.Input(tooltip, key='-IN-', s=(20,1)), sg.B('Change Tooltip')],
          [sg.Multiline(size=(60,20), reroute_stdout=True, reroute_cprint=True, write_only=True, key='-OUT-')],
          [sg.Button('Go'), sg.B('Hide Icon'), sg.B('Show Icon'), sg.B('Hide Window'), sg.Button('Exit')]]

window = sg.Window('Window Title', layout, finalize=True, enable_close_attempted_event=True)
# window = sg.Window('FTP Sync', layout)

tray = SystemTray(menu, single_click_events=False, window=window, tooltip=tooltip, icon=sg.DEFAULT_BASE64_ICON)
# tray.show_message('System Tray', 'System Tray Icon Started!')
sg.cprint(sg.get_versions())

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