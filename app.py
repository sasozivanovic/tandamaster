import sys
from PyQt5.Qt import QApplication, QUndoStack, pyqtSignal, QSystemTrayIcon, QIcon
class TandaMasterApplication(QApplication):
    info = pyqtSignal(str)
app = TandaMasterApplication(sys.argv)

app.system_tray_icon = QSystemTrayIcon(QIcon('icons/iconarchive/icons8/tandamaster-Sports-Dancing-icon.png'))
app.system_tray_icon.show()
