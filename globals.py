import sys
from PyQt5.Qt import QApplication, QIcon
app = QApplication(sys.argv)
tmSongIcon = QIcon(':images/song.png')
import tandamaster_rc

from playtreemodel import PlayTreeModel
ptm = PlayTreeModel('playtree.xml')
app.aboutToQuit.connect(ptm.save)
