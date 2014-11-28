from PyQt5.Qt import *

from gi.repository import GObject, Gst
GObject.threads_init()
Gst.init(None)

from model import PlayTreeModel, PlayTreeItem
import config

from IPython import embed

class TMPlayer(QObject):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.play_order = PlayOrderStandard()

        self._state = self.STOPPED
        self._volume = 1.0
        self._next_uri = None
        self._fadeout_duration = None
        self._gap_duration = None        
        self._song_begin = 0
        self._song_end = None

        self._make_playbin()
        
        self._timer = QTimer()
        self._timer.setTimerType(Qt.CoarseTimer)
        self._timer.timeout.connect(self.on_timer)
        self._timer.setInterval(config._TMPlaybin_timer_precision)

        # playbin was playing continuously since this stream position
        self._playback_start = None
        self._playback_time_correction = 0
        # how much time has elapsed since the uninterrupted playback has started?
        self._playback_timer = QElapsedTimer()
        # when did the fadeout start, relative to self._playback_start?
        self._fadeout_start = None
        # when did the gap start, relative to self._playback_start?
        self._gap_start = None
        
        self.signal_play_next.connect(self._play_next, type = Qt.QueuedConnection)
        
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

        bus = self.playbin.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)
        
    def set_play_order(self, play_order):
        if self.play_order:
            play_order.current_model, play_order.current_item, play_order.stop_after = self.play_order.current_model, self.play_order.current_item, self.play_order.stop_after
        self.play_order = play_order
        
    def config_next(self, next_uri = None, song_begin = 0, song_end = None, fadeout_duration = 0, gap_duration = 0):
        self._next_uri = next_uri
        self._song_begin = song_begin
        self._song_end = song_end
        self._fadeout_duration = fadeout_duration
        self._gap_duration = gap_duration
        
    volume_changed = pyqtSignal(float)
    @property
    def volume(self):
        return self._volume
    @volume.setter
    def volume(self, volume):
        self._volume = volume
        self.playbin.set_property('volume', volume)
        self.volume_changed.emit(volume)
        
    signal_play_next = pyqtSignal()
    def previous(self):
        self.config_next(*self.play_order.previous())
        self._play_next()
    def pause(self):
        self.playbin.set_state(Gst.State.PAUSED)
        self.set_state(self.PAUSED)
    def play(self):
        if self.state == self.PAUSED:
            self.playbin.set_state(Gst.State.PLAYING)
            self.set_state(self.PLAYING)
        else:
            self.config_next(*self.play_order.auto())
            self._play_next()
    def stop(self):
        self.config_next()
        self._play_next()
    def next(self):
        self.config_next(*self.play_order.next())
        self._play_next()
    def jump(self, model, index):
        self.config_next(*self.play_order.jump(model, index))
        self._play_next()
    def _play_next(self):
        self.playbin.set_state(Gst.State.READY)
        self.playbin.set_property('uri', self._next_uri)
        self.playbin.set_property('volume', self.volume)
        if self._song_begin:
            self.playbin.seek(
                1.0, Gst.Format.TIME,
                Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE,
                Gst.SeekType.SET, self._song_begin,
                Gst.SeekType.NONE, 0
            )
        self._playback_start = self._song_begin
        self._playback_timer.start()
        self.on_message_duration_changed()
        self.state = self.PLAYING

    def seek(self, position):
        self.playbin.seek(
            1.0, Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE,
            Gst.SeekType.SET, position,
            Gst.SeekType.NONE, 0)
        self._playback_start = position
        self._playback_timer.start()

    STOPPED, PAUSED, PLAYING, PLAYING_FADEOUT, PLAYING_GAP = range(5)
    state_changed = pyqtSignal(int)
    @property
    def state(self):
        return self._state
    @state.setter
    def state(self, state):
        if self._state == state:
            return
        if state == self.PLAYING:
            self.playbin.set_state(Gst.State.PLAYING)
        elif state == self.PAUSED:
            self.playbin.set_state(Gst.State.PAUSED)
            position = self.playbin.query_position(Gst.Format.TIME)
            if position[0]:
                self.position_changed.emit(position[1])
        elif state == self.STOPPED:
            self.playbin.set_state(Gst.State.READY)
            self.play_order.set_current()
            self.position_changed.emit(0)
            self.duration_changed.emit(0)
        elif state == self.PLAYING_FADEOUT:
            if not self._fadeout_duration:
                self.state = self.PLAYING_GAP
                return
            self._fadeout_start = self._playback_timer.elapsed() * Gst.USECOND
        elif state == self.PLAYING_GAP:
            if not self._gap_duration:
                self.config_next(*self.play_order.auto())
                self.signal_play_next.emit()
                return
            self._gap_start = self._playback_timer.elapsed() * Gst.USECOND
        playing = state in (self.PLAYING, self.PLAYING_FADEOUT, self.PLAYING_GAP)
        if playing != self._timer.isActive():
            if playing:
                self._timer.start()
            else:
                self._timer.stop()
        self._state = state
        self.state_changed.emit(state)
                            
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
        #Gst.MessageType.STATE_CHANGED: on_message_state_changed,
    }

    def on_timer(self):
        # shouldn't be in PAUSED or STOPPED state ...
        # ... and self._playback_timer should be valid
        elapsed = self._playback_timer.elapsed() * Gst.USECOND
        if elapsed > config._TMPlaybin_gstreamer_sync_interval:
            position = self.playbin.query_position(Gst.Format.TIME)
            if position[0]:
                self._correction = (position[1] - self._playback_start) - elapsed
        self.timer_handlers[self.state](elapsed + self._correction)
    position_changed = pyqtSignal('ulong')
    def on_timer_playing(self, elapsed):
        position = self._playback_start + elapsed
        if position > self.song_end + self._gap_duration:
            self.playbin.set_state(Gst.State.PAUSED)
            self.signal_play_next.emit()
        elif position > self.song_end:
            self.set_state(self.PLAYING_GAP)
            self.gap_position_changed.emit(position - self.song_end)
        self.position_changed.emit(position)
    fadeout_position_changed = pyqtSignal('ulong')
    def on_timer_playing_fadeout(self, elapsed):
        fadeout_elapsed = elapsed - self._fadeout_start
        fadeout_volume = self.volume * (1 - fadeout_elapsed / self._fadeout_duration)
        if fadeout_volume > 0:
            self.playbin.set_property('volume', fadeout_volume)
            self.fadeout_position_changed.emit(self._fadeout_duration - fadeout_elapsed)
        else:
            self.state = self.PLAYING_GAP
            self.playbin.set_property('volume', self.volume)
    gap_position_changed = pyqtSignal('ulong')
    def on_timer_playing_gap(self, elapsed):
        gap_elapsed = elapsed - self._gap_start
        if gap_elapsed > self._gap_duration:
            self.play_next()
        else:
            self.gap_position_changed.emit(gap_elapsed)
    timer_handlers = {
        PLAYING: on_timer_playing,
        PLAYING_FADEOUT: on_timer_playing_fadeout,
        PLAYING_GAP: on_timer_playing_gap,
        #self.PAUSED: self.on_timer_paused,
        #self.STOPPED: self.on_timer_stopped,
    }
        

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
        self._current_model = None
        self._current_item = None
        self._stop_after = 0

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

    def previous(self):
        index = self.current_model.previous_song(self.current_index)
        return self.make_transition(index = index)
    def next(self):
        index = self.current_model.next_song(self.current_index)
        return self.make_transition(index = index)
    def jump(self, model = None, index = None, item = None):
        return self.make_transition(model, index, item)
    def set_stop_after(self, i):
        self._stop_after = i
        self._stop_after_initial = i
    def update_stop_after_spinbox(self):
        self.current_model.view.window().stopafter_spinbox.setValue(self._stop_after)
    def auto(self):
        if self._stop_after == 1:
            self._stop_after = self._stop_after_initial
            self.update_stop_after_spinbox()
            return None
        if self._stop_after:
            self._stop_after -= 1
            self.update_stop_after_spinbox()
        return self.next()
    def make_transition(self, model = None, index = None, item = None):
        self.set_current(model, index, item)
        next_uri = QUrl.fromLocalFile(self.current_item.filename).toString() if next_index.isValid() else None
        return next_uri, None, None, 0, 0

@PlayOrder.register
class PlayOrderMilongaMode(PlayOrderStandard):
    name = 'Milonga mode'
    def make_transition(self, model = None, index = None, item = None):
        self.set_current(model, index, item)
        next_uri = QUrl.fromLocalFile(self.current_item.filename).toString() if next_index.isValid() else None
        try:
            song_begin = int(float(self.current_item.get_tag('tm:song_start')[0])*Gst.SECOND)
        except:
            song_begin = 0
        try:
            song_end = int(float(self.current_item.get_tag('tm:song_end')[0])*Gst.SECOND)
        except:
            song_end = None
        return next_uri, song_begin, song_end, config.fadeout_duration, config.gap_duration
    

class PlayOrderCheckSongBegins(PlayOrderStandard):
    def make_transition(self, model = None, index = None, item = None):
        self.set_current(model, index, item)
        next_uri = QUrl.fromLocalFile(self.current_item.filename).toString() if next_index.isValid() else None
        try:
            song_begin = int(float(self.current_item.get_tag('tm:song_start')[0])*Gst.SECOND)
        except:
            song_begin = 0
        return next_uri, song_begin, song_begin + 3*Gst.SECOND, 0, 0

class PlayOrderCheckSongBeginsSilently(PlayOrderStandard):
    def make_transition(self, model = None, index = None, item = None):
        self.set_current(model, index, item)
        next_uri = QUrl.fromLocalFile(self.current_item.filename).toString() if next_index.isValid() else None
        try:
            song_begin = int(float(self.current_item.get_tag('tm:song_start')[0])*Gst.SECOND)
        except:
            song_begin = 0
        return next_uri, 0, song_begin, 0, 0
    
class PlayOrderCheckSongEnds(PlayOrderStandard):
    def make_transition(self, model = None, index = None, item = None):
        self.set_current(model, index, item)
        next_uri = QUrl.fromLocalFile(self.current_item.filename).toString() if next_index.isValid() else None
        try:
            song_end = int(float(self.current_item.get_tag('tm:song_end')[0])*Gst.SECOND)
        except:
            song_end = None
        return next_uri, song_end - 5*Gst.SECOND, song_end, 0, 0

class PlayOrderCheckSongEndsSilently(PlayOrderStandard):
    def make_transition(self, model = None, index = None, item = None):
        self.set_current(model, index, item)
        next_uri = QUrl.fromLocalFile(self.current_item.filename).toString() if next_index.isValid() else None
        try:
            song_end = int(float(self.current_item.get_tag('tm:song_end')[0])*Gst.SECOND)
        except:
            song_end = None
        return next_uri, song_end, None, 0, 0
