from PyQt5.Qt import *

from gi.repository import GObject, Gst
GObject.threads_init()
Gst.init(None)

from model import PlayTreeModel, PlayTreeItem, model_index_item
import config
from util import *

from IPython import embed
import traceback

class TMPlayer(QObject):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.play_order = PlayOrderStandard()

        self._state = self.STOPPED
        self._volume = 1.0

        self._current_model = None
        self._current_item = None

        self.current_song = SongInfo(None)
        self._next_song = None

        self._make_playbin()
        
        self._timer = QTimer()
        self._timer.setTimerType(Qt.CoarseTimer)
        self._timer.timeout.connect(self.on_timer)
        self._timer.setInterval(config._TMPlaybin_timer_precision)

        self._fadeout_start = None
        
        self._gap_timer = QTimer()
        self._gap_timer.setTimerType(Qt.CoarseTimer)
        self._gap_timer.setSingleShot(True)
        
        self._gap_timer.timeout.connect(self._uri_change, type = Qt.QueuedConnection)
        self._signal_uri_change.connect(self._uri_change, type = Qt.QueuedConnection)
        
    def _make_playbin(self):
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

        self.bus = self.playbin.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.on_message)
        
    def set_play_order(self, play_order):
        self.play_order = play_order
        self.current_song = play_order.make_transition(model = self.current_song.model, item = self.current_song.item) if isinstance(self.current_song, SongInfo) else self.current_song
        self.next_song = play_order.make_transition(model = self.next_song.model, item = self.next_song.item) if isinstance(self.next_song, SongInfo) else self.next_song
        
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
        model, index, item = model_index_item(model, index, item, root_item = False)
        if not model:
            model = self._current_model
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

    next_changed = pyqtSignal(PlayTreeModel, QModelIndex)
    @property
    def next_song(self):
        return self._next_song
    @next_song.setter
    def next_song(self, next_song):
        self._next_song = next_song
        if next_song is None:
            next_song = self.play_order.auto(model = self.current_model, item = self.current_item)
        if next_song:
            self.next_changed.emit(next_song.model, next_song.item.index(next_song.model))
        else:
            self.next_changed.emit(None, QModelIndex())

    volume_changed = pyqtSignal(float)
    @property
    def volume(self):
        return self._volume
    @volume.setter
    def volume(self, volume):
        self._volume = volume
        self.playbin.set_property('volume', volume)
        self.volume_changed.emit(volume)
        
    _signal_uri_change = pyqtSignal()
    def previous(self):
        self.next_song = self.play_order.previous(model = self.current_model, item = self.current_item)
        self.state = self.PLAYING_FADEOUT
    def pause(self):
        self._next_song = self.PAUSED
        self.state = self.PLAYING_FADEOUT
    def play(self):
        if self.state == self.PAUSED:
            self.playbin.set_state(Gst.State.PLAYING)
            self.state = self.PLAYING
        else:
            self.next_song = None
            self.state = self.PLAYING_FADEOUT
    def stop(self):
        self.next_song = SongInfo(None)
        self.state = self.PLAYING_FADEOUT
    def next(self):
        self.next_song = self.play_order.next(model = self.current_model, item = self.current_item)
        self.state = self.PLAYING_FADEOUT
    def play_index(self, index):
        self.next_song = self.play_order.play_index(index = index)
        self.state = self.PLAYING_FADEOUT

    def seek(self, position):
        if self.current_song.song_end is not None and position >= self.current_song.song_end:
            self.current_song.song_end = None
        self.playbin.seek(
            1.0, Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE,
            Gst.SeekType.SET, position,
            Gst.SeekType.NONE, 0)
        if self.state != self.PAUSED:
            self.state = self.PLAYING
        else:
            self.position_changed.emit(position)

    @property
    def position(self):
        position = self.playbin.query_position(Gst.Format.TIME)
        if position[0]:
            return position[1]

    @property
    def gst_state(self):
        gst_state = self.playbin.get_state(0)
        if gst_state[0]:
            return gst_state[1]
        
    STOPPED, PAUSED, PLAYING, PLAYING_FADEOUT, PLAYING_GAP, _URI_CHANGE = range(6)
    state_changed = pyqtSignal(int)
    @property
    def state(self):
        return self._state
    @state.setter
    def state(self, state):
        if self._state == state:
            return
        self._state = state
        playing = state in (self.PLAYING, self.PLAYING_FADEOUT, self.PLAYING_GAP)
        if not playing and self._timer.isActive():
            self._timer.stop()
        if state == self.PLAYING:
            self.playbin.set_state(Gst.State.PLAYING)
        elif state == self.PAUSED:
            self.playbin.set_state(Gst.State.PAUSED)
            position = self.playbin.query_position(Gst.Format.TIME)
            if position[0]:
                self.position_changed.emit(position[1])
        elif state == self.STOPPED:
            self.playbin.set_state(Gst.State.READY)
            self.set_current(model = self.current_model)
            self.position_changed.emit(0)
            #self.duration_changed.emit(1) # todo
        elif state == self.PLAYING_FADEOUT:
            self._gap_timer.stop()
            if self.gst_state != Gst.State.PLAYING:
                self.state = self._URI_CHANGE
                return
            elif not self.current_song.fadeout_duration:
                self.state = self.PLAYING_GAP
                return
            self._fadeout_start = self.position
        elif state == self.PLAYING_GAP:
            if not self.current_song.gap_duration or self.next_song == self.PAUSED:
                self._signal_uri_change.emit()
                return
            if self.gst_state == Gst.State.PLAYING and (not self.current_song.song_end or self.position < self.current_song.song_end):
                self.playbin.set_state(Gst.State.PAUSED)
            if not self.next_song or self.next_song.item:
                self._gap_timer.start(int(self.current_song.gap_duration/Gst.MSECOND))
            else:
                self.state = self._URI_CHANGE
                return
        elif state == self._URI_CHANGE:
            self._gap_timer.stop()
            if self.next_song and self.next_song == self.PAUSED:
                self.next_song = None
                self.state = self.PAUSED
                return
            self.current_song = self.next_song if self.next_song else self.play_order.auto(model = self.current_model, item = self.current_item)
            self.set_current(model = self.current_song.model, item = self.current_song.item)
            self.next_song = None
            if self.current_song.item is None:
                self.state = self.STOPPED
                return
            self.bus.set_flushing(True)
            self.playbin.set_state(Gst.State.READY)
            self.bus.set_flushing(False)
            self.playbin.set_property('volume', self.volume)
            self.playbin.set_property('uri', QUrl.fromLocalFile(self.current_song.item.filename).toString())
            self.playbin.set_state(Gst.State.PAUSED)
            if self.current_song.song_begin:
                self.playbin.seek(
                    1.0, Gst.Format.TIME,
                    Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE,
                    Gst.SeekType.SET, self.current_song.song_begin,
                    Gst.SeekType.NONE, 0
                )
            self.on_message_duration_changed()
            self.state = self.PLAYING
            return
        if playing and not self._timer.isActive():
            self._timer.start()
        self.state_changed.emit(state)
    def _uri_change(self):
        self.state = self._URI_CHANGE
        
    def on_message(self, bus, message):
        try:
            self.message_handlers[message.type](self, bus, message)
        except KeyError:
            pass
    def on_message_eos(self, bus, message):
        if self.state in (self.PLAYING, self.PLAYING_FADEOUT):
            self.state = self.PLAYING_GAP
    duration_changed = pyqtSignal('ulong')
    def on_message_duration_changed(self, bus = None, message = None):
        duration = self.playbin.query_duration(Gst.Format.TIME)
        self.duration = duration[1] if duration[0] else None
        if duration[0]:
            self.duration_changed.emit(duration[1])
    def on_message_error(self, bus, message):
        print(message, message.parse_error())
    #def on_message_state_changed(self, bus, message):
    #    previous, current, pending = message.parse_state_changed()
    #    state = self.PLAYING if current == Gst.State.PLAYING else \
    #            (self.PAUSED if current == Gst.State.PAUSED else self.STOPPED)
    #    if not(self.state in (self.PLAYING_FADEOUT, self.PLAYING_GAP) and
    #           state != self.STOPPED):
    #        self.set_state(state)
    message_handlers = {
        Gst.MessageType.EOS: on_message_eos,
        Gst.MessageType.DURATION_CHANGED: on_message_duration_changed,
        Gst.MessageType.ERROR: on_message_error,
        #Gst.MessageType.STATE_CHANGED: on_message_state_changed,
    }

    position_changed = pyqtSignal('ulong')
    fadeout_position_changed = pyqtSignal('ulong')
    gap_position_changed = pyqtSignal('ulong')
    def on_timer(self):
        # shouldn't be in PAUSED or STOPPED state ...
        position = self.position
        if self.state == self.PLAYING:
            if position is None:
                return
            song_end = self.current_song.song_end if self.current_song.song_end is not None else self.duration
            if song_end is not None and position > song_end:
                self.state = self.PLAYING_GAP
                self.gap_position_changed.emit(position - song_end)
        elif self.state == self.PLAYING_FADEOUT:
            fadeout_elapsed = position - self._fadeout_start
            if fadeout_elapsed > self.current_song.fadeout_duration:
                self.playbin.set_state(Gst.State.PAUSED)
                self.playbin.set_property('volume', self.volume)
                self.state = self.PLAYING_GAP
            else:
                fadeout_volume = self.volume * (1 - fadeout_elapsed / self.current_song.fadeout_duration)
                self.playbin.set_property('volume', fadeout_volume)
                self.fadeout_position_changed.emit(self.current_song.fadeout_duration - fadeout_elapsed)
        elif self.state == self.PLAYING_GAP:
            gap_remaining = self._gap_timer.remainingTime()
            self.gap_position_changed.emit(self.current_song.gap_duration - gap_remaining * Gst.MSECOND)
        if position:
            self.position_changed.emit(position)
        
class SongInfo:
    def __init__(self, model = None, index = None, item = None, song_begin = 0, song_end = None, fadeout_duration = 0, gap_duration = 0):
        self.model, _index, self.item = model_index_item(model, index, item)
        self.fadeout_duration = fadeout_duration
        self.gap_duration = gap_duration
        self.song_begin = song_begin
        self.song_end = song_end
            
class PlayOrder(QObject):
    play_orders = []
    @classmethod
    def register(cls, subcls):
        cls.play_orders.append((subcls.name, subcls))
        return subcls

@PlayOrder.register
class PlayOrderStandard(PlayOrder):
    name = 'Standard'
    def __init__(self, parent = None):
        super().__init__(parent)
        self._stop_after = 0

    def previous(self, model = None, index = None, item = None):
        model, index, item = model_index_item(model, index, item)
        index = model.previous_song(index)
        return self.make_transition(index = index)
    def next(self, model = None, index = None, item = None):
        model, index, item = model_index_item(model, index, item)
        index = model.next_song(index)
        return self.make_transition(index = index)
    def play_index(self, model = None, index = None, item = None):
        model, index, item = model_index_item(model, index, item)
        if not item.isPlayable:
            index = model.next_song(index)
        return self.make_transition(index = index)
    def set_stop_after(self, i):
        self._stop_after = i
        self._stop_after_initial = i
    def update_stop_after_spinbox(self, model):
        stopafter_spinbox = model.view.window().stopafter_spinbox # todo: this is ugly
        stopafter_spinbox.blockSignals(True)
        stopafter_spinbox.setValue(self._stop_after)
        stopafter_spinbox.blockSignals(False)
    def auto(self, model = None, index = None, item = None):
        model, index, item = model_index_item(model, index, item)
        if self._stop_after == 1:
            self._stop_after = self._stop_after_initial
            self.update_stop_after_spinbox(model)
            return self.make_transition()
        if self._stop_after:
            self._stop_after -= 1
            self.update_stop_after_spinbox(model)
        return self.next(model, index, item)
    def make_transition(self, model = None, index = None, item = None):
        return SongInfo(*model_index_item(model, index, item))

@PlayOrder.register
class PlayOrderMilongaMode(PlayOrderStandard):
    name = 'Milonga'
    def make_transition(self, model = None, index = None, item = None):
        model, index, item = model_index_item(model, index, item)
        return SongInfo(
            model, index, item,
            song_begin = item.get_song_begin(),
            song_end = item.get_song_end(),
            fadeout_duration = config.fadeout_duration[item.function()],
            gap_duration = config.gap_duration[item.function()]) \
            if item else SongInfo()

class PlayOrderCheckSongBegins(PlayOrderStandard):
    def make_transition(self, model = None, index = None, item = None):
        model, index, item = model_index_item(model, index, item)
        song_begin = item.get_song_begin()
        return SongInfo(
            model, index, item,
            song_begin = song_begin,
            song_end = song_begin + 3*Gst.SECOND)

class PlayOrderCheckSongBeginsSilently(PlayOrderStandard):
    def make_transition(self, model = None, index = None, item = None):
        model, index, item = model_index_item(model, index, item)
        return SongInfo(model, index, item,
                        song_begin = 0,
                        song_end = item.get_song_begin())
    
class PlayOrderCheckSongEnds(PlayOrderStandard):
    def make_transition(self, model = None, index = None, item = None):
        model, index, item = model_index_item(model, index, item)
        song_end = item.get_song_end()
        return SongInfo(model, index, item,
                        song_begin = song_end - 5*Gst.SECOND,
                        song_end = song_end)

class PlayOrderCheckSongEndsSilently(PlayOrderStandard):
    def make_transition(self, model = None, index = None, item = None):
        model, index, item = model_index_item(model, index, item)
        return SongInfo(model, index, item, song_begin = item.get_song_end())
