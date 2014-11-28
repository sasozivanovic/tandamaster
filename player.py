from PyQt5.Qt import *

from gi.repository import GObject, Gst
GObject.threads_init()
Gst.init(None)

from model import PlayTreeModel, PlayTreeItem
import config

from IPython import embed

class TandaMasterPlayer(QObject):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_model = None
        self._current_item = None
        self.stop_after = 0
        self.fadeout_timer = None
        self.gap_timer = None
        self.state = self.STOPPED
        self.song_begin = None
        self.song_end = None
        self._volume = 1.0
        
        self.playbin = Gst.ElementFactory.make("playbin", None)
        fakesink = Gst.ElementFactory.make("fakesink", None)
        self.playbin.set_property("video-sink", fakesink)

        rglimiter = Gst.ElementFactory.make("rglimiter", None)
        rgvolume = Gst.ElementFactory.make("rgvolume", None)
        autoaudiosink = Gst.ElementFactory.make("autoaudiosink", None)
        bin = Gst.Bin.new("audio_sink_bin")
        bin.add(rglimiter)
        bin.add(rgvolume)
        bin.add(autoaudiosink)
        rglimiter.link(rgvolume)
        rgvolume.link(autoaudiosink)
        ghost_pad = Gst.GhostPad.new('sink', rglimiter.get_static_pad('sink'))
        ghost_pad.set_active(True)
        bin.add_pad(ghost_pad)
        self.playbin.set_property("audio-sink", bin)

        bus = self.playbin.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)

        self.position_timer = QTimer()
        self.position_timer.setTimerType(Qt.CoarseTimer)
        self.position_timer.timeout.connect(self.on_position_timer)
        self.position_timer.start(100)

        self.signal_play_next.connect(self.play_next, type = Qt.QueuedConnection)

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

    STOPPED, PAUSED, PLAYING, PLAYING_FADEOUT, PLAYING_GAP = range(5)
    state_changed = pyqtSignal(int)
    def set_state(self, state):
        if self.state != state:
            self.state = state
            self.state_changed.emit(state)
            if state == self.PAUSED:
                position = self.playbin.query_position(Gst.Format.TIME)
                if position[0]:
                    self.position_changed.emit(position[1])
            elif state == self.STOPPED:
                self.position_changed.emit(0)
            
    def play(self):
        if not self.current_item.isPlayable:
            self.play_index(self.current_model.next_song(self.current_index))
        else:
            self.playbin.set_state(Gst.State.PLAYING)

    def play_previous(self):
        n = self.current_model.previous_song(self.current_index)
        if n.isValid():
            self.play_index(n)

    signal_play_next = pyqtSignal()
    def play_next(self):
        if self.current_model and self.current_item and self.milonga_mode():
            if self.current_item.function() == 'cortina':
                self.fadeout(self._play_next)
            else:
                self.gap(self._play_next)
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
            self.playbin.set_state(Gst.State.PAUSED) # stop

    def set_stop_after(self, i):
        self.stop_after = i

    def stop(self):
        self.playbin.set_state(Gst.State.READY)
        self.set_state(self.STOPPED)
        self.set_current(item = None)

    def pause(self):
        self.playbin.set_state(Gst.State.PAUSED)
        self.set_state(self.PAUSED)

    def seek(self, position):
        self.playbin.seek(
            1.0, Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE,
            Gst.SeekType.SET, position,
            Gst.SeekType.NONE, 0)

    volume_changed = pyqtSignal(float)
    @property
    def volume(self):
        return self._volume
    @volume.setter
    def volume(self, volume):
        self._volume = volume
        self.playbin.set_property('volume', volume)
        self.volume_changed.emit(volume)

    def milonga_mode(self):
        return self.current_model.view.window().action_milonga_mode.isChecked()

    def play_index(self, playtree_index):
        if self.current_model and self.current_item and self.milonga_mode() and self.current_item.function() == 'cortina':
            self.fadeout(self._play_index, playtree_index)
        else:
            self._play_index(playtree_index)

    def _play_index(self, playtree_index):
        if not playtree_index.model() == self.current_model:
            self.set_current(model = playtree_index.model())
        if not self.current_model.item(playtree_index).isPlayable:
            playtree_index = self.current_model.next_song(playtree_index)
        self.set_current(index = playtree_index)
        self.playbin.set_state(Gst.State.READY)
        self.playbin.set_property('uri', QUrl.fromLocalFile(self.current_item.filename).toString())
        self.playbin.set_property('volume', self.volume)
        try:
            self.song_begin = int(float(self.current_item.get_tag('tm:song_start')[0])*Gst.SECOND)
        except:
            self.song_begin = None
        try:
            self.song_end = int(float(self.current_item.get_tag('tm:song_end')[0])*Gst.SECOND)
        except:
            self.song_end = None
        if self.milonga_mode() and self.song_begin:
            self.playbin.seek(
                1.0, Gst.Format.TIME,
                Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE,
                Gst.SeekType.SET, self.song_begin if self.song_begin else 0,
                Gst.SeekType.NONE, 0
            )
        self.playbin.set_state(Gst.State.PLAYING)
        self.set_state(self.PLAYING)
        self.current_media_changed.emit()
        
    current_media_changed = pyqtSignal()

    fadeout_volume_changed = pyqtSignal(float)
    def fadeout(self, method, *args, **kwargs):
        if not self.fadeout_timer:
            self.fadeout_timer = QTimer()
            self.fadeout_step = 0
            self.fadeout_timer.setTimerType(Qt.PreciseTimer)
            self.fadeout_timer.timeout.connect(lambda: self.fadeout(method, *args, **kwargs))
            self.fadeout_timer.start(config.fadeout_timeout)
            self.set_state(self.PLAYING_FADEOUT)
        else:
            self.fadeout_step += 1
            fadeout_volume = self._volume * (1 - self.fadeout_step * config.fadeout_timeout * Gst.MSECOND / config.fadeout_time)
            if fadeout_volume > 0:
                self.playbin.set_property('volume', fadeout_volume)
                self.fadeout_volume_changed.emit(fadeout_volume)
            else:
                self.fadeout_timer.stop()
                self.fadeout_timer = None
                self.playbin.set_state(Gst.State.PAUSED)
                self.playbin.set_property('volume', self.volume)
                self.gap(method, *args, **kwargs)

    gap_position_changed = pyqtSignal(float)
    def gap(self, method,  *args, **kwargs):
        position = self.playbin.query_position(Gst.Format.TIME)
        if position[0]:
            song_end = self.song_end if self.song_end is not None else position[1]
            gap = max(0, config.gap - (position[1] - song_end))
            if gap:
                self.set_state(self.PLAYING_GAP)
                self.gap_timer = QTimer()
                self.gap_timer.setSingleShot(True)
                self.gap_timer.setInterval(int(gap/Gst.MSECOND))
                self.gap_timer.setTimerType(Qt.PreciseTimer)
                self.gap_timer.timeout.connect(lambda: self._gap_do_method(method, *args, **kwargs))
                self.gap_timer.start()
            else:
                method(*args, **kwargs)
        else:
            method(*args, **kwargs)
    def _gap_do_method(self, method, *args, **kwargs):
        self.gap_timer = None
        method(*args, **kwargs)
            
    def on_message(self, bus, message):
        try:
            self.message_handlers[message.type](self, bus, message)
        except KeyError:
            pass
    def on_eos(self, bus, message):
        self.signal_play_next.emit()
    def on_duration_changed(self, bus, message):
        duration = self.playbin.query_duration(Gst.Format.TIME)
        self.duration = duration[1] if duration[0] else None
        if duration[0]:
            self.duration_changed.emit(duration[1])
    def on_state_changed(self, bus, message):
        previous, current, pending = message.parse_state_changed()
        state = self.PLAYING if current == Gst.State.PLAYING else \
                (self.PAUSED if current == Gst.State.PAUSED else self.STOPPED)
        if not(self.state in (self.PLAYING_FADEOUT, self.PLAYING_GAP) and
               state != self.STOPPED):
            self.set_state(state)
    message_handlers = {
        Gst.MessageType.EOS: on_eos,
        Gst.MessageType.DURATION_CHANGED: on_duration_changed,
        Gst.MessageType.STATE_CHANGED: on_state_changed,
    }

    duration_changed = pyqtSignal('ulong')
    position_changed = pyqtSignal('ulong')

    # todo: optimize!
    def on_position_timer(self):
        if self.state == self.PLAYING:
            position = self.playbin.query_position(Gst.Format.TIME)
            if position[0]:
                if self.song_end is not None and self.milonga_mode():
                    if position[1] > self.song_end + config.gap:
                        self.playbin.set_state(Gst.State.PAUSED)
                        self.signal_play_next.emit()
                    elif position[1] > self.song_end:
                        self.set_state(self.PLAYING_GAP)
                        self.gap_position_changed.emit(position[1] - self.song_end)
                self.position_changed.emit(position[1])
        elif self.state == self.PLAYING_GAP:
            position = self.playbin.query_position(Gst.Format.TIME)
            if self.gap_timer is not None:
                self.gap_position_changed.emit(
                    (position[1] - self.song_end if self.song_end is not None else 0) + 
                    (self.gap_timer.interval() -
                     self.gap_timer.remainingTime())*Gst.MSECOND)
            else:
                if position[0] and self.song_end is not None and self.milonga_mode() and position[1] > self.song_end:
                    self.gap_position_changed.emit(position[1] > self.song_end)
        
