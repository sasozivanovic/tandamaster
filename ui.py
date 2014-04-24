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
        
        menubar = QMenuBar()
        self.musicmenu = QMenu(self.tr('&Music'))
        action_back = QAction(
            self.style().standardIcon(QStyle.SP_MediaSkipBackward), 
            self.tr('P&revious'), self, triggered = self.player.play_previous)
        self.musicmenu.addAction(action_back)        
        self.action_play = QAction(
            self.style().standardIcon(QStyle.SP_MediaPlay), 
            self.tr('&Play'), self, triggered = self.player.play)
        self.musicmenu.addAction(self.action_play)        
        self.action_pause =  QAction(
            self.style().standardIcon(QStyle.SP_MediaPause), 
            self.tr('&Pause'), self, triggered = self.player.pause)
        self.musicmenu.addAction(self.action_pause)        
        self.action_stop = QAction(
            self.style().standardIcon(QStyle.SP_MediaStop), 
            self.tr('&Stop'), self, triggered = self.player.stop)
        self.musicmenu.addAction(self.action_stop)        
        action_forward = QAction(
            self.style().standardIcon(QStyle.SP_MediaSkipForward), 
            self.tr('&Next'), self, triggered = self.player.play_next)
        self.musicmenu.addAction(action_forward)        
        self.musicmenu.addSeparator()
        action_quit = QAction(
            self.tr("&Quit"), self, shortcut=QKeySequence.Quit,
            statusTip="Quit the program", triggered=self.close)
        self.musicmenu.addAction(action_quit)
        menubar.addMenu(self.musicmenu)
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
        toolbar.addWidget(QWidget())
        toolbar.addWidget(self.song_info)
        self.addToolBar(toolbar)

        self.player.current_changed.connect(self.update_song_info)
        self.player.stateChanged.connect(self.on_player_state_changed)
        self.on_player_state_changed(QMediaPlayer.StoppedState)

    def sizeHint(self):
        return QSize(600, 800)

    def update_song_info(self, old_model, old_index, model, index):
        if index.isValid():
            item = model.item(index)
            self.setWindowTitle("{ARTIST} - {TITLE} | TandaMaster".format(**item.tags))
            self.song_info.setText("{ARTIST}<br><b>{TITLE}</b>".format(**item.tags))
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
        columns = self.model().columnCount(QModelIndex())
        for i in range(columns):
            self.resizeColumnToContents(i)
