import sys
from PyQt5.Qt import QApplication, pyqtSignal
class TandaMasterApplication(QApplication):
    info = pyqtSignal(str)
app = TandaMasterApplication(sys.argv)
app.setApplicationName('TandaMaster')
app.setOrganizationName('MilongueroSi')
app.setOrganizationDomain('milonguero.si')
