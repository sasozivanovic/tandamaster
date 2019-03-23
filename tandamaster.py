#!/usr/bin/python3

#import pyximport; pyximport.install(pyimport = True)

import datetime
print('Tandamaster', datetime.datetime.now())

import sys
import os, os.path

if sys.stdout.encoding != 'UTF-8' and sys.stdout.errors != 'replace':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding = None, errors = 'replace', newline = sys.stdout.newlines, line_buffering = sys.stdout.line_buffering)

#from IPython import embed
#from IPython.core import ultratb
#sys.excepthook = ultratb.FormattedTB(mode='Verbose',color_scheme='Linux', call_pdb=1)

from PyQt5.Qt import *   # todo: import only what you need

from app import *
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


import logging
from systemd.journal import JournalHandler
logger = logging.getLogger(__name__)
journald_handler = JournalHandler()
journald_handler.setFormatter(logging.Formatter(
    '[%(levelname)s] %(message)s'
))
logger.addHandler(journald_handler)
logger.setLevel(logging.WARNING)

import traceback
def exception_hook(exctype, value, tb):
    #from IPython import embed
    sys.__excepthook__(exctype, value, tb)
    loginfo = ''.join(traceback.format_exception(exctype, value, tb))
    logger.error(loginfo)
    app.info.emit(f"{exctype.__name__}: {value}")
    #embed()
    
sys.excepthook = exception_hook



#import cProfile; cProfile.run('app.exec()', sort="tottime")
app.exec()
sys.exit()
