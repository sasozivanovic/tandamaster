import sys
from PyQt5.Qt import QApplication, QUndoStack, pyqtSignal
class TandaMasterApplication(QApplication):
    info = pyqtSignal(str)
app = TandaMasterApplication(sys.argv)
