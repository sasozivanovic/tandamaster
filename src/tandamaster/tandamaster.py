#!/usr/bin/env python

# TandaMaster, a music player dedicated to playing tango music at milongas.
# Copyright (C) 2025 Sašo Živanović <saso.zivanovic@guest.arnes.si>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


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

from .app import *
from .util import *
#app.aboutToQuit.connect(ptm.save)

from .ui import TandaMasterWindow
tm = TandaMasterWindow()
tm.show()

app.system_tray_icon = QSystemTrayIcon(MyIcon('iconarchive/icons8/tandamaster-Sports-Dancing-icon.png'))
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
journald_handler = JournalHandler(SYSLOG_IDENTIFIER = 'tandamaster')
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
    app.error.emit(f"{exctype.__name__}: {value}")
    #embed()
    
sys.excepthook = exception_hook

def main():
    app.exec()

if __name__ == '__main__':
    #import cProfile; cProfile.run('app.exec()', sort="tottime")
    main()
