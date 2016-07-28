#!/usr/bin/python3

#import pyximport; pyximport.install(pyimport = True)

import datetime
print('Tandamaster', datetime.datetime.now())

import sys
import os, os.path

#from IPython import embed
#from IPython.core import ultratb
#sys.excepthook = ultratb.FormattedTB(mode='Verbose',color_scheme='Linux', call_pdb=1)

from PyQt5.Qt import *   # todo: import only what you need

from app import app
from util import *
#app.aboutToQuit.connect(ptm.save)

from ui import TandaMasterWindow
tm = TandaMasterWindow()
tm.show()

app.system_tray_icon = QSystemTrayIcon(MyIcon('icons/iconarchive/icons8/tandamaster-Sports-Dancing-icon.png'))
app.system_tray_icon.show()

def show_hide_tmwindow():
    if tm.isVisible():
        tm.hide()
    else:
        tm.show()

app.system_tray_icon.activated.connect(show_hide_tmwindow)


#import cProfile; cProfile.run('app.exec()', sort="tottime")
app.exec()
