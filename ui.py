from IPython import embed

from PyQt5.Qt import *   # todo: import only what you need

from player import TandaMasterPlayer
from playtreemodel import PlayTreeModel

class TandaMasterWindow(QMainWindow):

    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle('TandaMaster')        

        self.player = TandaMasterPlayer()
        #self.player2 = TandaMasterPlayer() # pre-listening

        ptv = PlayTreeView('root', self.player)
        self.setCentralWidget(ptv)
        self.player.set_current(model = ptv.model(), silent = True)

        self.playcontrols_actions = [
            QAction(self.style().standardIcon(QStyle.SP_MediaSkipBackward), 
                    self.tr('P&revious'), self, triggered = self.player.play_previous),
            QAction(self.style().standardIcon(QStyle.SP_MediaPlay), 
                    self.tr('&Play'), self, triggered = self.player.play),
            QAction(self.style().standardIcon(QStyle.SP_MediaPause), 
                    self.tr('&Pause'), self, triggered = self.player.pause),
            QAction(self.style().standardIcon(QStyle.SP_MediaStop), 
                    self.tr('&Stop'), self, triggered = self.player.stop),
            QAction(self.style().standardIcon(QStyle.SP_MediaSkipForward), 
                    self.tr('&Next'), self, triggered = self.player.play_next),
        ]

        toolbar = QToolBar('Play controls', self)
        toolbar.setAllowedAreas(Qt.TopToolBarArea | Qt.BottomToolBarArea)
        toolbar.setFloatable(False)
        toolbar.setIconSize(2*toolbar.iconSize())
        for action in self.playcontrols_actions:
            button = QToolButton()
            button.setDefaultAction(action)
            button.setIconSize(2*button.iconSize())
            toolbar.addWidget(button)
        self.song_info = QLabel()
        toolbar.addWidget(QWidget())
        toolbar.addWidget(self.song_info)
        self.addToolBar(toolbar)

        menubar = QMenuBar()
        self.filemenu = QMenu(self.tr('&File'))
        quitAction = QAction(self.tr("&Quit"), self, shortcut=QKeySequence.Quit,
                                   statusTip="Quit the program", triggered=self.close)
        self.filemenu.addAction(quitAction)
        menubar.addMenu(self.filemenu)
        self.setMenuBar(menubar)

        self.player.current_changed.connect(self.update_song_info)

    def update_song_info(self, old_model, old_index, model, index):
        if index.isValid():
            item = model.item(index)
            self.setWindowTitle("{ARTIST} - {TITLE} | TandaMaster".format(**item.tags))
            self.song_info.setText("{ARTIST}<br><b>{TITLE}</b>".format(**item.tags))
        else:
            self.setWindowTitle("TandaMaster")
            self.song_info.setText("")
            

    def sizeHint(self):
        return QSize(600, 800)

class PlayTreeView(QTreeView):

    def __init__(self, root_xml_id, player, parent = None):
        super().__init__(parent)

        model = PlayTreeModel(root_xml_id, self)
        self.setModel(model)
        model.view = self

        self.player = player
        self.activated.connect(player.play_index)

        self.setExpandsOnDoubleClick(False)
        self.expanded.connect(self.on_expanded)
        self.collapsed.connect(self.on_collapsed)
        self._autoexpanded = None
        self._autoexpand_on = True
        player.current_changed.connect(self.on_current_changed)

    def isFirstColumnSpanned(row, parent):
        return False
        index = parent.index(row, 0, parent)
        return not parent.isPlayable(index)

    def on_expanded(self, index):
        if self.model() == self.player.current_model and \
           index in self.model().ancestors(self.player.current_index):
            self._autoexpand_on = True
        self.resizeColumnToContents(0)

    def on_collapsed(self, index):
        if self.model() == self.player.current_model and \
           index in self.model().ancestors(self.player.current_index):
            self._autoexpand_on = False

    def on_current_changed(self, old_model, old_index, model, index):
        if self._autoexpand_on:
            if self._autoexpanded and old_model == self.model():
                while old_index.isValid():
                    if old_index.isValid():
                        self.collapse(old_index)
                    if old_index == self._autoexpanded:
                        break
                    old_index = old_model.parent(old_index)
            if model == self.model():
                while index.isValid() and not self.isExpanded(index):
                    self.expand(index)
                    self._autoexpanded = index
                    index = model.parent(index)
