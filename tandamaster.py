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
                "{ARTIST} - {TITLE} | TandaMaster".format(**self.current.tags)
                if self.current else TandaMaster
            ))

        self.playAction = QAction(self.style().standardIcon(QStyle.SP_MediaPlay), self.tr('&Play'), 
                                  self, triggered = self.player.play)
        self.pauseAction = QAction(self.style().standardIcon(QStyle.SP_MediaPause), 
                                   self.tr('&Pause'), self, triggered = self.player.pause)
        self.stopAction = QAction(self.style().standardIcon(QStyle.SP_MediaStop), 
                                  self.tr('&Stop'), self, triggered = self.player.stop)
        self._createPlayerControls()

        self.playtreemodel = PlayTreeModel('playtree.xml')

        self.playtreeview = QTreeView()
        self.playtreeview.setModel(self.playtreemodel)
        self.playtreeview.activated.connect(self.play)
        self.setCentralWidget(self.playtreeview)

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
        for action in (self.playAction, self.pauseAction, self.stopAction):
            button = QToolButton()
            button.setDefaultAction(action)
            button.setIconSize(2*button.iconSize())
            toolbar.addWidget(button)
        self.song_info = QLabel()
        self.player.currentMediaChanged.connect(self.update_song_info)
        toolbar.addWidget(self.song_info)
        self.addToolBar(toolbar)

    def update_song_info(self):
        self.song_info.setText("{ARTIST}<br><b>{TITLE}</b>".format(**self.current.tags))

    def sizeHint(self):
        return QSize(600, 800)

    def play(self, playtree_index = None):
        if playtree_index:
            self.current = playtree_index.internalPointer()
            tm.player.setMedia(QMediaContent(QUrl.fromLocalFile(self.current.filename)))
        self.player.play()

    def closeEvent(self, event):
        self.playtreemodel.save()
        event.accept()

from globals import app
import tandamaster_rc

from library import Librarian
from playtreemodel import PlayTreeModel

tm = TandaMasterWindow()
tm.show()

#embed()
sys.exit(app.exec())
#embed()
