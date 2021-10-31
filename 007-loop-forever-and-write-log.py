import glob
import inspect
import os
import pickle
import socket
import sys
from datetime import datetime
from pprint import pprint
from tkinter import END

import pystray._win32

import PySimpleGUI as sg
import time
import threading
import ftplib

from psgtray import SystemTray

# from tendo import singleton
# me = singleton.SingleInstance()
# will sys.exit(-1) if other instance is running

blockSizeUpload = 8096
nameUploadThread = 'upload_glx'
stopThread = 0

folderUpload = "e:/Iso"
folderOnServer = "/iso"

fileConfig = os.path.expanduser("~") + "/ftp_upload_glx.conf"
fileLog = os.path.expanduser("~") + "/ftp_upload_glx.log"

def ol1(str):
    global fileLog
    print(str + "   " +datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    with open(fileLog, 'a') as fd:
        fd.write(f'\n' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "#" + str)

class ftpUpload:
    setServer = ''
    setPort = ''
    setUsername = ''
    setPassword = ''
    setFolderLocal = ''
    setFolderServer = ''

    def checkValid(self):
        if len(self.setServer) < 1:
            print(" not valid Server? ")
            return 0
        if len(self.setUsername) < 1:
            print("***Error: not valid Username? ")
            return 0
        if len(self.setPassword) < 1:
            print("***Error:  not valid Password? ")
            return 0
        if len(self.setFolderLocal) < 1:
            print("***Error:  not valid FolderLocal? ")
            return 0
        if len(self.setFolderServer) < 1:
            print("***Error:  not valid FolderServer? ")
            return 0
        return 1

    def loadFromArray(self, mm):
        att = dir(self)
        for i in att:
            if callable(getattr(self, i)) == False:
                # print('not callable:', i)
                if mm and i[0] != "_":
                    # print(mm[i])
                    setattr(self, i, mm[i])


    # https://stackoverflow.com/questions/48280605/get-list-of-all-attributes-which-are-not-inherited
    def dumpAll(self):
        print("---- Dump Obj1 -----")
        # att = dir(self)
        # for i in att:
        #     if i[0] != "_":
        #         print(i + " = " + str(getattr(self, i)))

        mField = dict(inspect.getmembers(self))
        mBaseField = dict(inspect.getmembers(self.__class__.__base__))
        for k, v in mField.items():
            if k.startswith('__'):
                continue
            if callable(getattr(self, k)) == False:
                # if k not in mBaseField:
                # if True and k != 'setPassword':
                print(k + " = " + v)

        print("----------------------")

class FtpUploadTracker:
    global stopThread, folderUpload, folderOnServer, blockSizeUpload

    sizeWritten = 0
    totalSize = 0
    lastShownPercent = 0
    handleFtp = 0

    def __init__(self, totalSize):
        self.totalSize = totalSize

    def handle(self, block):
        self.sizeWritten += blockSizeUpload
        percentComplete = round((self.sizeWritten / self.totalSize) * 100)

        if stopThread > 0:
            # print(" stopThread 3 ")
            #self.handleFtp.abort()
            # Khi dừng thread, phải dừng FTP bằng cách này, nếu không file cuối sẽ upload xong, mới kết thúc Thread
            self.handleFtp.close()

        if (self.lastShownPercent != percentComplete):
            self.lastShownPercent = percentComplete
            print(str(percentComplete) + "% ", end = " ")

def upload_file_thread():

    global stopThread, textBox, ftpSetting, blockSizeUpload

    # session = ftplib.FTP()
    host = ftpSetting.setServer
    port = ftpSetting.setPort
    username = ftpSetting.setUsername
    password = ftpSetting.setPassword
    stopThread = 0
    tries = 0
    done = False

    ol1("Start upload thread")

    while True:
        if stopThread > 0:
            print(" stopThread 4 ")
            return
        try:
            if tries > 1:
                print(" sleep 10s ")
                time.sleep(10)

            tries += 1

            # time.sleep(5)

            # with ftplib.FTP(host) as ftp:
            if 1:
                print("connecting to " + host + " ... ")

                ftp = ftplib.FTP()

                ftp.connect(host, int(port))

                # print(session.getwelcome())

                print("Logging in...")

                ftp.login("backup01", "...")

                ftp.set_debuglevel(2)

                ftp.login(username, password)
                # ftp.set_pasv(False)

                ftp.cwd(ftpSetting.setFolderServer)

                countFile = 0
                # List all file, and upload all

                nFile = len([name for name in os.listdir(ftpSetting.setFolderLocal) if os.path.isfile(os.path.join(ftpSetting.setFolderLocal, name))])

                ol1("Total file sync:" + str(nFile))

                for fileUp in glob.iglob(ftpSetting.setFolderLocal + '**/**', recursive=True):

                    if stopThread > 0:
                        print(" stopThread 5 ")
                        done = True
                        return

                    print(" ----- LEN = " + str(textBox.get_size()))

                    if os.path.isfile(fileUp):
                        countFile += 1
                        print(" Check upload now: " + fileUp)

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

                                if rest_pos == os.path.getsize(fileUp):
                                    print("size remote = local file, file upload before done???" + fileUp)
                                    continue

                                ol1("Upload now (Resume): " + fileUp)

                                f.seek(rest_pos, 0)

                                print("seek to " + str(rest_pos))
                                uploadTracker.sizeWritten = rest_pos

                                try:
                                    print(ftp.storbinary('STOR ' + os.path.basename(fileUp), f,
                                                     blocksize=blockSizeUpload, callback=uploadTracker.handle, rest=rest_pos), flush=True)

                                except Exception as e:
                                    print("*** Upload Exception glx2: " + e.__doc__)

                                ol1("upload done " + fileUp)
                                done = True
                            else:
                                ol1("Upload now (new file) : " + fileUp)
                                print(ftp.storbinary('STOR ' + os.path.basename(fileUp), f, blockSizeUpload, uploadTracker.handle),
                                      flush=True)
                                ol1("Upload done " + fileUp)
                                done = True

                ol1(" count file = " + str(countFile))

        except (BrokenPipeError, ftplib.error_temp, socket.gaierror) as e:
            print(str(type(e)) + ": " + str(e))
            print("connection died, trying again 10 second ...")
            for i in range(10):
                time.sleep(1)
                print(i, end=" ")
                if stopThread > 0:
                    print(" stopThread 2 ")
                    return
            print("continue ...")
            continue

        except Exception as e:
            print("*** Upload Exception glx1: " + e.__doc__)
            print(str(type(e)) + ": " + str(e))
            print("connection died, trying again 10 second ...")
            for i in range(10):
                time.sleep(1)
                print(i, end=" ")
                if stopThread > 0:
                    print(" stopThread 23 ")
                    return
            print("continue ...")
            continue


        ol1("--- Done loop: " + str(tries))

        ol1("Sleep 1 hour to do next...")
        for i in range(3600):
            time.sleep(1)
            if stopThread > 0:
                print(" stopThread 21 ")
                return

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

ftpSetting = ftpUpload()

fileConfig = os.path.expanduser("~") + "/ftp_upload_glx.conf"

if os.path.exists(fileConfig):
    a_file = open(fileConfig, "rb")
    output = pickle.load(a_file)
    ftpSetting.loadFromArray(output)

if len(ftpSetting.setPort) == 0:
    ftpSetting.setPort = "21"

ftpUpload.dumpAll(ftpSetting)

textBox = sg.Multiline(size=(60,20), reroute_stdout=True, reroute_cprint=True, write_only=True, key='-OUT-')

layout = [
            [sg.T('Server'), sg.Input(ftpSetting.setServer, key='setServer', s=(20,1)), sg.T('Port'), sg.Input(ftpSetting.setPort, key='setPort', s=(20,1))],
            [sg.T('Username'), sg.Input(ftpSetting.setUsername, key='setUsername', s=(20,1)), sg.T('Password'), sg.Input(ftpSetting.setPassword, key='setPassword', s=(20,1), password_char='*')],
          [sg.T('Local Folder'), sg.Input(ftpSetting.setFolderLocal, key='setFolderLocal', s=(40,1)), sg.FolderBrowse()],
            [sg.T('Server Folder'), sg.Input(ftpSetting.setFolderServer, key='setFolderServer', s=(40,1))],
          [textBox],
          [sg.Button('StartSync'),  sg.B('StopSync'),  sg.B('Clear'), sg.Button('Exit')]]

window = sg.Window('FTP Sync V1.0 - 31.10.21', layout, finalize=True, enable_close_attempted_event=True)
# window = sg.Window('FTP Sync - GalaxyCloud', layout)

tray = SystemTray(menu, single_click_events=False, window=window, tooltip=tooltip, icon=sg.DEFAULT_BASE64_ICON)
# tray.show_message('System Tray', 'System Tray Icon Started!')
sg.cprint(sg.get_versions())

while True:  # Event Loop

    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    elif event == 'StartSync':

        print("Config file: " + fileConfig)

        a_file = open(fileConfig, "wb")
        pickle.dump(values, a_file)
        a_file.close()

        ftpSetting.loadFromArray(values)

        if ftpSetting.checkValid() == 1:
            print('Call StartSync function')
            upload_file()

        # print('Upload function has returned from starting')

    elif event == 'StopSync':
        for thread in threading.enumerate():
            if thread.name == nameUploadThread:
                print(" set stopThread = 1")
                stopThread = 1
    elif event == 'Clear':
        textBox.update("")
    elif event == '-THREAD DONE-':
        print('Your Upload operation completed')
    # else:
    #     print(event, values)

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
