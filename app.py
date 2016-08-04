import sys, os
from PyQt5.Qt import QApplication, pyqtSignal, QStandardPaths
class TandaMasterApplication(QApplication):
    info = pyqtSignal(str)
app = TandaMasterApplication(sys.argv)
app.setApplicationName('TandaMaster')
app.setOrganizationName('MilongueroSi')
app.setOrganizationDomain('milonguero.si')
try:
    os.makedirs(os.path.normpath(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)))
except FileExistsError:
    pass
try:
    os.makedirs(os.path.normpath(QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)))
except FileExistsError:
    pass
