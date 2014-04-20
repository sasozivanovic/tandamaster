#!/usr/bin/python3

import sys
import os, os.path

from IPython import embed
#from IPython.core import ultratb
#sys.excepthook = ultratb.FormattedTB(mode='Verbose',color_scheme='Linux', call_pdb=1)

from PyQt5.Qt import *   # todo: import only what you need

class TandaMasterWindow(QMainWindow):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.player = QMediaPlayer()
        self.librarian = Librarian()

        self.setWindowTitle('TandaMaster')        
        self.player.currentMediaChanged.connect(
            lambda: self.setWindowTitle(
                "{ARTIST} - {TITLE} | TandaMaster".format(**ptm.current.tags)
                if ptm.current else TandaMaster
            ))

        self.playcontrols_actions = [
            QAction(self.style().standardIcon(QStyle.SP_MediaSkipBackward), 
                    self.tr('P&revious'), self, triggered = self.play_previous),
            QAction(self.style().standardIcon(QStyle.SP_MediaPlay), 
                    self.tr('&Play'), self, triggered = self.play),
            QAction(self.style().standardIcon(QStyle.SP_MediaPause), 
                    self.tr('&Pause'), self, triggered = self.player.pause),
            QAction(self.style().standardIcon(QStyle.SP_MediaStop), 
                    self.tr('&Stop'), self, triggered = self.stop),
            QAction(self.style().standardIcon(QStyle.SP_MediaSkipForward), 
                    self.tr('&Next'), self, triggered = self.play_next),
        ]
        self._createPlayerControls()

        self.playtreeview = PlayTreeView()
        self.playtreeview.setModel(ptm)
        self.setCentralWidget(self.playtreeview)
        self.playtreeview.activated.connect(self.play_index)

        self._createMenuBar()


    def _createMenuBar(self):
        menubar = QMenuBar()

        self.filemenu = QMenu(self.tr('&File'))
        quitAction = QAction(self.tr("&Quit"), self, shortcut=QKeySequence.Quit,
                                   statusTip="Quit the program", triggered=self.close)
        self.filemenu.addAction(quitAction)
        menubar.addMenu(self.filemenu)

        self.setMenuBar(menubar)

    def _createPlayerControls(self):
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
        self.player.currentMediaChanged.connect(self.update_song_info)
        toolbar.addWidget(QWidget())
        toolbar.addWidget(self.song_info)
        self.addToolBar(toolbar)

    def update_song_info(self):
        self.song_info.setText("{ARTIST}<br><b>{TITLE}</b>".format(**ptm.current.tags))

    def sizeHint(self):
        return QSize(600, 800)

    def play_index(self, playtree_index):
        if playtree_index.isValid():
            if not ptm.isPlayable(playtree_index):
                playtree_index = ptm.next_song(playtree_index)
            ptm.current_index = playtree_index
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(ptm.current.filename)))
        self.player.play()

    def play_next(self):
        n = ptm.next_song()
        if n.isValid():
            self.play_index(n)

    def play_previous(self):
        n = ptm.previous_song()
        if n.isValid():
            self.play_index(n)

    def stop(self):
        self.player.stop()
        ptm.current_index = QModelIndex()

    def play(self):
        if not ptm.current_index.isValid():
            self.play_index(ptm.next_song())
        else:
            self.player.play()

class PlayTreeView(QTreeView):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setExpandsOnDoubleClick(False)
        self.expanded.connect(self._expanded)
        self._autoexpanded = None

    def isFirstColumnSpanned(row, parent):
        return True
        index = parent.index(row, 0, parent)
        return not parent.isPlayable(index)

    def _expanded(self, index):
        if not self.model().isPlayable(index):
            self.resizeColumnToContents(0)

    def setModel(self, model):
        super().setModel(model)
        model.current_changed.connect(self.autoexpand)

    def autoexpand(self, old_index, index):
        if self._autoexpanded:
            while old_index.isValid():
                self.collapse(old_index)
                if old_index == self._autoexpanded:
                    break
                old_index = self.model().parent(old_index)
        while index.isValid() and not self.isExpanded(index):
            self.expand(index)
            self._autoexpanded = index
            index = self.model().parent(index)

from globals import *
import tandamaster_rc

from library import Librarian
from playtreemodel import PlayTreeModel

tm = TandaMasterWindow()
tm.show()

#embed()
sys.exit(app.exec())
#embed()
