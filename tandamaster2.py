#!/usr/bin/python3

import sys
import os, os.path

from PyQt5.Qt import *   # todo: import only what you need
import taglib
import tandamaster_rc



from IPython import embed

class PlayTreeItem:
    def row(self):
        return self.parent.children.index(self) if self.parent else None
    def next(self):
        row = self.row()
        if row + 1 == len(self.parent.children):
            return self.parent.next()
        else:
            return self.parent.children[row+1]

class PlayTreeFolder(PlayTreeItem):
    def __init__(self, parent, folder):
        self.parent = parent
        self.folder = folder
        self.children = None
    def _populate(self):
        self.children = map(
            lambda isdir, fn, fullfn: (PlayTreeFolder(self, fullfn) if isdir else PlayTreeFile(self, fullfn)),
            sorted(
                map(
                    lambda fn, fullfn: ((ospath.isdir(fullfn), fn, fullfn)),
                    map(
                        lambda fn: (fn, os.path.join(self.folder, fn)), 
                        os.listdir(self.folder)
                    )
                )
            )
        )

    def data(self, column_name, role):
        if column_name:
            return None
        if role == Qt.DisplayRole:
            return os.path.basename(self.folder)
        elif role == Qt.DecorationRole:
            return tm.style().standardIcon(QStyle.SP_DirIcon)
    def child(self, row):
        if self.children is None:
            self._populate()
        return self.children[row]
    def childCount(self):
        if self.children is None:
            self._populate()
        return len(self.children)
        

class PlayTreeFile(PlayTreeItem):
    def __init__(self, parent, filename):
        self.parent = parent
        self.filename = filename
        try:
            audiofile = taglib.File(filename)
            self._tags = dict(audiofile.tags)
        except:
            self._tags = {}
    def tag(self, tag_name):
        try:
            value = self._tags[tag_name]
            if isinstance(value, list) and len(value) == 1:
                return value[0]
        except KeyError:
            return None
    @property
    def tags(self):
        return dict((t,v[0] if isinstance(v,list) and len(v)==1 else v) for t,v in self._tags.items())
    def data(self, column_name, role):
        if column_name and role == Qt.DisplayRole:
            return self.tag(column_name)
        elif role == Qt.DisplayRole:
            return os.path.basename(self.filename)
        elif not column_name and role == Qt.DecorationRole:
            return tmSongIcon
    def child(self, row):
        return None
    def childCount(self):
        return 0

class PlayTreeModel(QAbstractItemModel):
    def __init__(self, parent = None):
        super().__init__(parent)
        
        # temp
        self.rootItem = PlayTreeFolder(None, '/home/saso/tango/razno/')
        
    # column "" provides browsing info (folder name, file name, ...)
    _columns = ('', 'ARTIST', 'ALBUM', 'TITLE')

    def index(self, row, column, parent):
        # why oh why?
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        # why oh why?
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def columnCount(self, parent):
        return len(self._columns)
    
    def data(self, index, role = Qt.DisplayRole):
        return index.internalPointer().data(self._columns[index.column()], role)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._columns[section].title()

        return None


class PlayTreeView(QTreeView):
    def __init__(self, parent = None):
        super().__init__(parent)
        model = PlayTreeModel()
        self.setModel(model)
        self.activated.connect(lambda index: self.window().play(index))
        

class TandaMasterWindow(QMainWindow):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.player = QMediaPlayer()

        self.setWindowTitle('TandaMaster')        
        self.player.currentMediaChanged.connect(
            lambda: self.setWindowTitle(
                "{ARTIST}: {TITLE} | TandaMaster".format(**self.current.tags)
                if self.current else TandaMaster
            ))

        self.playAction = QAction(self.style().standardIcon(QStyle.SP_MediaPlay), self.tr('&Play'), 
                                  self, triggered = self.player.play)
        self.pauseAction = QAction(self.style().standardIcon(QStyle.SP_MediaPause), 
                                   self.tr('&Pause'), self, triggered = self.player.pause)
        self.stopAction = QAction(self.style().standardIcon(QStyle.SP_MediaStop), 
                                  self.tr('&Stop'), self, triggered = self.player.stop)
        self._createPlayerControls()
        self._createCentralWidget()
        self._createMenuBar()


    def _createCentralWidget(self):
        centralwidget = QWidget()
        layout = QVBoxLayout()
        centralwidget.setLayout(layout)
        layout.addWidget(PlayTreeView())
        self.setCentralWidget(centralwidget)

    def _createMenuBar(self):
        menubar = QMenuBar()

        self.filemenu = QMenu(self.tr('&File'))
        quitAction = QAction(self.tr("&Quit"), self, shortcut=QKeySequence.Quit,
                                   statusTip="Quit the program", triggered=self.close)
        self.filemenu.addAction(quitAction)
        menubar.addMenu(self.filemenu)

        self.setMenuBar(menubar)

    def _oldcreatePlayerControls(self):
        dockwidget = QDockWidget('', self)
        dockwidget.setFeatures(QDockWidget.DockWidgetMovable)
        dockwidget.setAllowedAreas(Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea)
        widget = QWidget()
        layout = QHBoxLayout()
        widget.setLayout(layout)        
        for action in (self.playAction, self.pauseAction, self.stopAction):
            button = QToolButton()
            button.setDefaultAction(action)
            button.setIconSize(*button.iconSize())
            layout.addWidget(button)
        self.song_info = QLabel()
        self.player.currentMediaChanged.connect(self.update_song_info)
        layout.addWidget(self.song_info)
        dockwidget.setWidget(widget)
        self.addDockWidget(Qt.TopDockWidgetArea, dockwidget)


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

    def play(self, playtree_index):
        if playtree_index:
            self.current = playtree_index.internalPointer()
            tm.player.setMedia(QMediaContent(QUrl.fromLocalFile(self.current.filename)))
        self.player.play()

    
app = QApplication(sys.argv)

tmSongIcon = QIcon(':images/song.png')

tm = TandaMasterWindow()
tm.show()

#embed()
sys.exit(app.exec())
