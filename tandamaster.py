#!/usr/bin/python3

import sys
import os, os.path

#from IPython import embed
#from IPython.core import ultratb
#sys.excepthook = ultratb.FormattedTB(mode='Verbose',color_scheme='Linux', call_pdb=1)

from PyQt5.Qt import *   # todo: import only what you need

from app import app
#app.aboutToQuit.connect(ptm.save)

from ui import TandaMasterWindow
tm = TandaMasterWindow()
tm.show()

app.exec()
