from IPython import embed

from PyQt5.Qt import *   # todo: import only what you need

from player import TandaMasterPlayer
from model import PlayTreeModel, PlayTreeList
from library import Library
from util import PartialFormatter

import collections

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
        #toolbar.setIconSize(2*toolbar.iconSize())
        toolbar.addAction(action_back)
        toolbar.addAction(self.action_play)
        toolbar.addAction(self.action_pause)
        toolbar.addAction(self.action_stop)
        toolbar.addAction(action_forward)
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

        self.player.currentMediaChanged.connect(self.update_song_info)
        self.player.stateChanged.connect(self.on_player_state_changed)
        self.on_player_state_changed(QMediaPlayer.StoppedState)

    def sizeHint(self):
        return QSize(1800, 800)

    song_info_formatter = PartialFormatter()
    def update_song_info(self, media):
        item = self.player.current_item
        if item:
            tags = item.get_tags()
            self.setWindowTitle(self.song_info_formatter.format(
                "{ARTIST} - {TITLE} | TandaMaster", **tags))
            self.song_info.setText(self.song_info_formatter.format(
                "{ARTIST} <b>{TITLE}</b>", **tags))
        else:
            self.setWindowTitle("TandaMaster")
            self.song_info.setText("")

    def on_player_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.action_play.setVisible(False)
            self.action_pause.setVisible(True)
            self.action_stop.setEnabled(True)
        else:
            self.action_play.setVisible(True)
            self.action_pause.setVisible(False)
            self.action_stop.setEnabled(state != QMediaPlayer.StoppedState)
                
    def update_library(self):
        Library('tango').refresh(['/home/saso/tango'])


class PlayTreeWidget(QWidget):

    def __init__(self, root_id, player, parent = None):
        super().__init__(parent)

        current_model_button = QToolButton()
        current_model_button.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        current_model_button.setCheckable(True)
        self.search = QLineEdit()
        self.ptv = PlayTreeView(root_id, player, self)

        controls = QToolBar()
        controls.addWidget(current_model_button)
        controls.addWidget(self.search)

        widget_layout = QVBoxLayout()
        self.setLayout(widget_layout)
        widget_layout.addWidget(controls)
        widget_layout.addWidget(self.ptv)

        self.search.textChanged.connect(lambda: QTimer.singleShot(50, self.refilter))
        current_model_button.toggled.connect(
            lambda checked: player.set_current(model = self.ptv.model()) if checked else None)
        player.current_changed.connect(
            lambda old_model, old_index, model, index: current_model_button.setChecked(
                self.ptv.model() == model))
        current_model_button.setChecked(self.ptv.model() == player.current_model)

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
        if not self.player.current_model:
            self.player.set_current(model = self.model())
        model.modelReset.connect(self.on_end_reset_model)

    def on_expanded(self, index):
        model = self.model()
        model.item(index).expanded[model] = True
        if model == self.player.current_model and \
           index in model.ancestors(self.player.current_index):
            self._autoexpand_on = True
        self.autosize_columns()

    def on_collapsed(self, index):
        model = self.model()
        model.item(index).expanded[model] = False
        if model == self.player.current_model and \
           index in model.ancestors(self.player.current_index):
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

    def on_end_reset_model(self):
        model = self.model()
        for item in model.rootItem.iter(model,
                lambda item: not item.isTerminal,
                lambda item: isinstance(item, PlayTreeList)):
            if model in item.expanded:
                self.setExpanded(item.modelindex(model), item.expanded[model])

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
