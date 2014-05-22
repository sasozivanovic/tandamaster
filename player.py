from PyQt5.Qt import *
from model import PlayTreeModel, PlayTreeItem
from IPython import embed

class TandaMasterPlayer(QMediaPlayer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_model = None
        self._current_item = None
        self._playback_start = None
        #self.setNotifyInterval(200)

    @property
    def current_model(self):
        return self._current_model

    @property
    def current_item(self):
        return self._current_item

    @property
    def current_index(self):
        return self._current_item.modelindex(self._current_model) \
            if self._current_model and self._current_item is not None \
               else QModelIndex()

    current_changed = pyqtSignal(PlayTreeModel, QModelIndex, PlayTreeModel, QModelIndex)

    def set_current(self, model = None, index = None, item = None, silent = False):
        if model is None:
            model = self._current_model
        if index is not None:
            assert index.model() == self.current_model
            item = index.internalPointer() if index.isValid() else None
        if item is None:
            item = model.rootItem
        old_model = self._current_model
        old_item = self._current_item
        self._current_model = model
        self._current_item = item
        if old_model != model or old_item != item:
            if old_model is not None and old_item is not None:
                old_index = old_item.modelindex(old_model)
                if not silent:
                    old_model.dataChanged.emit(old_model.sibling(None, 0, old_index),
                                               old_model.sibling(None, -1, old_index),
                                               [Qt.ForegroundRole, Qt.FontRole])
            else:
                old_index = QModelIndex()
            if model is not None and item is not None:
                index = item.modelindex(model)
                if not silent:
                    model.dataChanged.emit(model.sibling(None, 0, index),
                                           model.sibling(None, -1, index),
                                           [Qt.ForegroundRole, Qt.FontRole])
            else:
                index = QModelIndex()
            if not silent:
                self.current_changed.emit(old_model, old_index, model, index)
        if old_model != model:
            if old_model:
                old_model.modelReset.disconnect(self.on_model_reset)
            if model:
                model.modelReset.connect(self.on_model_reset)

    def play(self):
        if not self.current_item.isPlayable:
            self.play_index(self.current_model.next_song(self.current_index))
        else:
            super().play()
            self.setNotifyInterval(100)

    def play_index(self, playtree_index):
        assert playtree_index.isValid() and playtree_index.model() == self.current_model
        if not self.current_model.item(playtree_index).isPlayable:
            playtree_index = self.current_model.next_song(playtree_index)
        self.set_current(index = playtree_index)
        self.setMedia(QMediaContent(QUrl.fromLocalFile(self.current_item.filename)))
        super().play()

    def play_next(self):
        n = self.current_model.next_song(self.current_index)
        if n.isValid():
            self.play_index(n)

    def play_previous(self):
        n = self.current_model.previous_song(self.current_index)
        if n.isValid():
            self.play_index(n)

    def stop(self):
        super().stop()
        self.set_current(item = None)

    def on_model_reset(self):
        if self.current_item is not None:
            self.current_item.parent = None
