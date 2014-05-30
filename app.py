import sys
from PyQt5.Qt import QApplication, QUndoStack
class TandaMasterApplication(QApplication):
    pass
app = TandaMasterApplication(sys.argv)
undo_stack = QUndoStack(app)
