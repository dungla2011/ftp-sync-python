import os

import PySimpleGUI as sg
import time
import threading


import ftplib

def long_function_thread(window, tid):
    for i in range(10):
        time.sleep(1)
        window.write_event_value('-THREAD PROGRESS-', str(tid) + " - " + str(i))
    window.write_event_value('-THREAD DONE-', '')
    session = ftplib.FTP('glx.com.vn', 'backup01', '....')


def long_function(tid):
    threading.Thread(target=long_function_thread, args=(window, tid), daemon=True).start()

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
        print('About to go to call my long function')
        long_function(tid)
        print('Long function has returned from starting')
    elif event == '-THREAD DONE-':
        print('Your long operation completed')
    else:
        print(event, values)
window.close()
