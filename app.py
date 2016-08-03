import sys
from PyQt5.Qt import QApplication, pyqtSignal
class TandaMasterApplication(QApplication):
    info = pyqtSignal(str)
sys.argv[0] = 'tandamaster'
app = TandaMasterApplication(sys.argv)
