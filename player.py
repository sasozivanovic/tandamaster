from PyQt5.Qt import *
from model import PlayTreeModel, PlayTreeItem
from IPython import embed

class TandaMasterPlayer(QMediaPlayer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_model = None
        self._current_item = None
        self.stop_after = 0
        self._playback_start = None
        self.fadeout_timer = None
        self.mediaStatusChanged.connect(self.on_media_status_changed)
        #self.setNotifyInterval(200)
        self.set_volume(100)

    @property
    def current_model(self):
        return self._current_model

    @property
    def current_item(self):
        return self._current_item

    @property
    def current_index(self):
        try:
            return self._current_item.index(self._current_model)
        except:
            return QModelIndex()

    current_changed = pyqtSignal(PlayTreeModel, QModelIndex, PlayTreeModel, QModelIndex)

    def set_current(self, model = None, index = None, item = None, silent = False):
        if model is None:
            model = self._current_model
        if index is not None:
            assert index.model() == self.current_model
            item = index.internalPointer() if index.isValid() else None
        if item is None:
            item = model.root_item
        old_model = self._current_model
        old_item = self._current_item
        self._current_model = model
        self._current_item = item
        if old_model != model or old_item != item:
            if old_model is not None and old_item is not None:
                old_index = old_item.index(old_model)
                if not silent:
                    old_model.dataChanged.emit(old_model.sibling(None, 0, old_index),
                                               old_model.sibling(None, -1, old_index),
                                               [Qt.ForegroundRole, Qt.FontRole])
            else:
                old_index = QModelIndex()
            if model is not None and item is not None:
                index = item.index(model)
                if not silent:
                    model.dataChanged.emit(model.sibling(None, 0, index),
                                           model.sibling(None, -1, index),
                                           [Qt.ForegroundRole, Qt.FontRole])
            else:
                index = QModelIndex()
            if not silent:
                self.current_changed.emit(old_model, old_index, model, index)

    def play(self):
        if not self.current_item.isPlayable:
            self.play_index(self.current_model.next_song(self.current_index))
        else:
            super().play()
            self.setNotifyInterval(100)

    def play_index(self, playtree_index):
        if self.current_model and self.current_item and self.current_model.view.window().action_milonga_mode.isChecked() and self.current_item.function() == 'cortina':
            self._fadeout(self._play_index, playtree_index)
        else:
            self._play_index(playtree_index)

    def _play_index(self, playtree_index):
        if not playtree_index.model() == self.current_model:
            self.set_current(model = playtree_index.model())
        if not self.current_model.item(playtree_index).isPlayable:
            playtree_index = self.current_model.next_song(playtree_index)
        self.set_current(index = playtree_index)
        self.setMedia(QMediaContent(QUrl.fromLocalFile(self.current_item.filename)))
        super().play()

    def play_next(self):
        if self.current_model and self.current_item and self.current_model.view.window().action_milonga_mode.isChecked() and self.current_item.function() == 'cortina':
            self._fadeout(self._play_next)
        else:
            self._play_next()    

    def _play_next(self):
        if self.stop_after == 1:
            return
        if self.stop_after:
            self.stop_after -= 1
            self.current_model.view.window().stopafter_spinbox.setValue(self.stop_after)
        n = self.current_model.next_song(self.current_index)
        if n.isValid():
            self._play_index(n)
        else:
            self.stop()

    def set_stop_after(self, i):
        self.stop_after = i

    #gap = 3000
    gap = 0

    fadeout_step = 5
    fadeout_timeout = 200

    def _fadeout(self, method, *args, **kwargs):
        if not self.fadeout_timer:
            self.fadeout_timer = QTimer()
            self.fadeout_timer.setTimerType(Qt.PreciseTimer)
            self.fadeout_timer.timeout.connect(lambda: self._fadeout(method, *args, **kwargs))
            self.fadeout_timer.start(self.fadeout_timeout)
        else:
            if self.volume() == 0:
                self.fadeout_timer.stop()
                self.fadeout_timer = None
                self.pause()
                self.setVolume(self._volume)
                self._gap(method, *args, **kwargs)
            else:
                self.setVolume(max(0,self.volume()-self.fadeout_step))

    def _gap(self, method,  *args, **kwargs):
        if self.gap:
            QTimer.singleShot(self.gap, lambda: method(*args, **kwargs))
        else:
            method(*args, **kwargs)

    def play_previous(self):
        n = self.current_model.previous_song(self.current_index)
        if n.isValid():
            self.play_index(n)

    def stop(self):
        super().stop()
        self.set_current(item = None)

    def on_media_status_changed(self, state):
        if state == QMediaPlayer.EndOfMedia:
            self.play_next()

    def set_volume(self, volume):
        self._volume = volume
        self.setVolume(volume)
