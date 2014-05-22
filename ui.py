from IPython import embed

from PyQt5.Qt import *   # todo: import only what you need

from player import TandaMasterPlayer
from playtreemodel import PlayTreeModel, PlayTreeList
from library import Library

class TandaMasterWindow(QMainWindow):

    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle('TandaMaster')        

        self.player = TandaMasterPlayer()
        #self.player2 = TandaMasterPlayer() # pre-listening

        splitter = QSplitter()
        splitter.addWidget(PlayTreeWidget(None, self.player))
        splitter.addWidget(PlayTreeWidget(None, self.player))
        self.setCentralWidget(splitter)

        menubar = QMenuBar()

        self.musicmenu = QMenu(self.tr('&Music'))
        action_update_library = QAction(
            self.tr("&Update library"), self,
            triggered = self.update_library)
        self.musicmenu.addAction(action_update_library)
        action_quit = QAction(
            self.tr("&Quit"), self, shortcut=QKeySequence.Quit,
            statusTip="Quit the program", triggered=self.close)
        self.musicmenu.addAction(action_quit)
        menubar.addMenu(self.musicmenu)

        self.playbackmenu = QMenu(self.tr('&Playback'))
        action_back = QAction(
            self.style().standardIcon(QStyle.SP_MediaSkipBackward), 
            self.tr('P&revious'), self, triggered = self.player.play_previous)
        self.playbackmenu.addAction(action_back)        
        self.action_play = QAction(
            self.style().standardIcon(QStyle.SP_MediaPlay), 
            self.tr('&Play'), self, triggered = self.player.play)
        self.playbackmenu.addAction(self.action_play)        
        self.action_pause =  QAction(
            self.style().standardIcon(QStyle.SP_MediaPause), 
            self.tr('&Pause'), self, triggered = self.player.pause)
        self.playbackmenu.addAction(self.action_pause)        
        self.action_stop = QAction(
            self.style().standardIcon(QStyle.SP_MediaStop), 
            self.tr('&Stop'), self, triggered = self.player.stop)
        self.playbackmenu.addAction(self.action_stop)        
        action_forward = QAction(
            self.style().standardIcon(QStyle.SP_MediaSkipForward), 
            self.tr('&Next'), self, triggered = self.player.play_next)
        self.playbackmenu.addAction(action_forward)        
        menubar.addMenu(self.playbackmenu)

        self.setMenuBar(menubar)

        toolbar = QToolBar('Play controls', self)
        toolbar.setAllowedAreas(Qt.TopToolBarArea | Qt.BottomToolBarArea)
        toolbar.setFloatable(False)
        toolbar.setIconSize(2*toolbar.iconSize())
        def create_playcontrol_button(action):
            button = QToolButton()
            button.setDefaultAction(action)
            button.setIconSize(2*button.iconSize())
            toolbar.addWidget(button)
            return button
        create_playcontrol_button(action_back)
        self.button_play = create_playcontrol_button(self.action_play)
        self.button_pause = create_playcontrol_button(self.action_pause)
        create_playcontrol_button(self.action_stop)
        create_playcontrol_button(action_forward)
        self.song_info = QLabel()
        self.song_info.setContentsMargins(8,0,0,0)
        toolbar.addWidget(QWidget())
        toolbar.addWidget(self.song_info)
        self.addToolBar(toolbar)
        
        self.addToolBarBreak()
        toolbar2 = QToolBar('Test', self)
        pb = TMProgressBar(self.player)
        toolbar2.addWidget(pb)
        self.addToolBar(toolbar2)

        self.player.current_changed.connect(self.update_song_info)
        self.player.stateChanged.connect(self.on_player_state_changed)
        self.on_player_state_changed(QMediaPlayer.StoppedState)

    def sizeHint(self):
        return QSize(1800, 800)

    def update_song_info(self, old_model, old_index, model, index):
        if index.isValid():
            item = model.item(index)
            self.setWindowTitle("{ARTIST} - {TITLE} | TandaMaster".format(**item.get_tags()))
            self.song_info.setText("{ARTIST}<br><b>{TITLE}</b>".format(**item.get_tags()))
        else:
            self.setWindowTitle("TandaMaster")
            self.song_info.setText("")

    def on_player_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.action_play.setEnabled(False)
            self.action_pause.setEnabled(True)
            self.action_stop.setEnabled(True)
            self.button_play.setVisible(False) # todo!
            self.button_pause.setVisible(True) # todo!
        else:
            self.action_play.setEnabled(True)
            self.action_pause.setEnabled(False)
            self.button_play.setVisible(True) # todo!
            self.button_pause.setVisible(False) # todo!
            if state == QMediaPlayer.StoppedState:
                self.action_stop.setEnabled(False)
            else:
                self.action_stop.setEnabled(True)
                
    def update_library(self):
        Library('tango').refresh(['/home/saso/tango'])


class PlayTreeWidget(QWidget):

    def __init__(self, root_id, player, parent = None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.search = QLineEdit()
        self.ptv = PlayTreeView(root_id, player, self)
        layout.addWidget(self.search)
        layout.addWidget(self.ptv)
        self.search.textChanged.connect(lambda: QTimer.singleShot(50, self.refilter))

    def refilter(self):
        self.ptv.model().refilter(self.search.text())
        
class PlayTreeView(QTreeView):

    def __init__(self, root_id, player, parent = None):
        super().__init__(parent)
        self.setUniformRowHeights(True)

        model = PlayTreeModel(root_id, self)
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
        self.player.set_current(model = self.model(), silent = True) # temporary
        model.modelAboutToBeReset.connect(self.on_begin_reset_model)
        model.modelReset.connect(self.on_end_reset_model)

    def on_expanded(self, index):
        if self.model() == self.player.current_model and \
           index in self.model().ancestors(self.player.current_index):
            self._autoexpand_on = True
        self.autosize_columns()

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

    def autosize_columns(self):
        return
        columns = self.model().columnCount(QModelIndex())
        for i in range(columns):
            self.resizeColumnToContents(i)

    def on_begin_reset_model(self):
        model = self.model()
        for item in model.rootItem.iter(
                lambda item: item.isTerminal,
                lambda item: isinstance(item, PlayTreeList)):
            item.was_expanded = self.isExpanded(item.modelindex(model))

    def on_end_reset_model(self):
        model = self.model()
        for item in model.rootItem.iter(
                lambda item: item.isTerminal,
                lambda item: isinstance(item, PlayTreeList)):
            self.setExpanded(item.modelindex(model), item.was_expanded)


class TMProgressBar(QProgressBar):
    def __init__(self, player, parent = None):
        super().__init__(parent)
        self.setMinimum(0)
        self.setValue(-1)
        self.player = player
        player.durationChanged.connect(self.on_durationChanged)
        player.positionChanged.connect(self.on_positionChanged)
        player.stateChanged.connect(self.on_stateChanged)
        self.hours, self.minutes, self.seconds, self.milliseconds = 0,0,0,0
        self.on_stateChanged(QMediaPlayer.StoppedState)
        self.update()

    def on_durationChanged(self, duration):
        self.setMaximum(duration)
        self.update()
        
    def on_positionChanged(self, position):
        self.setValue(position)
        position, self.milliseconds = divmod(position, 1000)
        position, self.seconds = divmod(position, 60)
        self.hours, self.minutes = divmod(position, 60)
        self.update()

    def text(self):
        return str(self.hours) + ":" if self.hours else '' + \
            ('{:02d}:{:02d}' if self.hours else '{:2d}:{:02d}').format(self.minutes, self.seconds) + \
            (':' + self.milliseconds if self.player.state == QMediaPlayer.PausedState else '')
        
    def on_stateChanged(self, state):
        self.setTextVisible(state != QMediaPlayer.StoppedState)
        self.update()
