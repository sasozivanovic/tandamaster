# TandaMaster, a music player dedicated to playing tango music at milongas.
# Copyright (C) 2025 Sašo Živanović <saso.zivanovic@guest.arnes.si>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from PyQt5.Qt import *

from gi.repository import GObject, Gst, GLib
Gst.init(None)

import collections

from .model import PlayTreeModel, PlayTreeItem, PlayTreeFile
from .util import *
from .app import *

#from IPython import embed
#import traceback

import datetime

class TMPlayer(QObject):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.play_order = PlayOrderStandard()

        self._state = self.STOPPED
        self._volume = 1.0
        self._fadeout_position = 0.0
        self.duration = None

        self._current = PlaybackConfig()
        self.current_ancestors = []
        self._next = PlaybackConfig()

        self._make_playbin()
        
        self._timer = QTimer()
        self._timer.setTimerType(Qt.CoarseTimer)
        self._timer.timeout.connect(self.on_timer)
        self._timer.setInterval(config.timer_precision)

        self._pending_ops = collections.defaultdict(lambda:[])
        self._fadeout_start = None

        self._n = 0
        self._gap_timer = QTimer()
        self._gap_timer.setTimerType(Qt.CoarseTimer)
        self._gap_timer.setSingleShot(True)
        self._n_gap = None
        
        self._gap_timer.timeout.connect(self._gap_timeout, type = Qt.QueuedConnection)
        self._signal_uri_change.connect(self._uri_change, type = Qt.QueuedConnection)
        self._signal_on_gst_message.connect(self.on_gst_message, type = Qt.QueuedConnection)
        
    def _make_playbin(self):
        self.playbin = Gst.ElementFactory.make("playbin", None)
        fakesink = Gst.ElementFactory.make("fakesink", None)
        self.playbin.set_property("video-sink", fakesink)

        rglimiter = Gst.ElementFactory.make("rglimiter", None)
        rgvolume = Gst.ElementFactory.make("rgvolume", None)
        autoaudiosink = Gst.ElementFactory.make("autoaudiosink", None)
        bin = Gst.Bin.new("audio_sink_bin")
        ac = Gst.ElementFactory.make("audioconvert", None)
        ar = Gst.ElementFactory.make("audioresample", None)
        bin.add(rgvolume)
        bin.add(rglimiter)
        bin.add(ac)
        bin.add(ar)
        bin.add(autoaudiosink)
        rgvolume.link(rglimiter)
        rglimiter.link(ac)
        ac.link(ar)
        ar.link(autoaudiosink)
        ghost_pad = Gst.GhostPad.new('sink', rgvolume.get_static_pad('sink'))
        ghost_pad.set_active(True)
        bin.add_pad(ghost_pad)
        self.playbin.set_property("audio-sink", bin)

        self.update_playbin_volume()
        self.playbin.connect("notify::volume", self.on_playbin_volume_changed)

        self.bus = self.playbin.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.on_message)

    def set_play_order(self, play_order):
        self.play_order = play_order
        current = play_order.config_playback(self.current.model, self.current.item)
        if current.model == self.current.model and current.item == self.current.item:
            self.current = current
        self.next = PlaybackConfig()
        
    current_changed = pyqtSignal()
    @property
    def current(self):
        return self._current
    @current.setter
    def current(self, current):
        old_current = self._current
        if current and current.model:
            self.current_ancestors_indexes = current.model.ancestors(current.index)
            self.current_ancestors = [current.model.item(a) for a in self.current_ancestors_indexes]
        else:
            self.current_ancestors_indexes = []
            self.current_ancestors = []
        self.old_current = old_current
        self._current = current
        # todo: don't emit if the same
        # hmm ... two signals, current_model_changed and current_item_changed?
        self.current_changed.emit()
        
    next_changed = pyqtSignal()
    @property
    def next(self):
        return self._next
    @next.setter
    def next(self, next):
        self._next = next
        if self.state in (self.PLAYING_FADEOUT, self.PLAYING_GAP):
            self.next_changed.emit()
            
    def concrete(self, pbc):
        if pbc.auto() and self.current:
            return self.play_order.auto(self.current.model, self.current.item)
        elif pbc:
            return pbc
        else:
            return PlaybackConfig()
        
    volume_changed = pyqtSignal(float)
    @property
    def volume(self):
        return self._volume
    @volume.setter
    def volume(self, volume):
        self._volume = volume
        self.update_playbin_volume()
        self.volume_changed.emit(volume)
    @property
    def fadeout_position(self):
        return self._fadeout_position
    @fadeout_position.setter
    def fadeout_position(self, position):
        self._fadeout_position = position
        self.update_playbin_volume()
        self.fadeout_position_changed.emit(position)
    @property
    def fadeout_factor(self):
        ff = self.fadeout_position / self.current.fadeout_duration if self.state == self.PLAYING_FADEOUT and self.current and self.current.fadeout_duration else 1.0
        return max(0.0, min(1.0, ff))
    def update_playbin_volume(self):
        self.playbin.freeze_notify()
        self.playbin.set_property('volume', self.volume * self.fadeout_factor)
        self.playbin.thaw_notify()
    def on_playbin_volume_changed(self, playbin, gparam):
        if self.state == self.PLAYING_FADEOUT:
            return
        volume = playbin.get_property("volume")
        fadeout_factor = self.fadeout_factor
        if fadeout_factor:
            self._volume = volume / fadeout_factor
            self.volume_changed.emit(volume)
        
    _signal_uri_change = pyqtSignal(int)
    def play_previous(self):
        position = self.position
        if not position or position - self.current.song_begin < config.min_time_for_previous_restarts_song:
            self.next = self.play_order.previous(self.current.model, self.current.item)
            self.state = self.PLAYING_FADEOUT
        else:
            self.current = self.play_order.config_playback(self.current.model, self.current.item)
            self.seek(self.current.song_begin)
    def pause(self):
        self._next = PlaybackConfig(state = self.PAUSED)
        self.state = self.PLAYING_FADEOUT
    def play(self):
        self.next = PlaybackConfig()
        if self.state == self.PAUSED:
            self.state = self.PLAYING
        else:
            self.state = self.PLAYING_FADEOUT
    def stop(self):
        self.next = PlaybackConfig(state = self.STOPPED)
        self.state = self.PLAYING_FADEOUT
    def play_next(self):
        self.next = self.play_order.next(self.current.model, self.current.item)
        self.state = self.PLAYING_FADEOUT
    def play_index(self, index):
        self.next = self.play_order.jump(*model_item(index))
        self.state = self.PLAYING_FADEOUT

    def seek(self, position):
        position = int(position)
        self._gap_timer.stop()
        if self.current.song_end is not None and position >= self.current.song_end:
            self.current.song_end = None
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

    # todo: prepare uri while doing the real gap --- ie on eos, or about to finish
    # fix bug(?): moving works, but only at autoplay
    #   - maybe previous and next should find the prev/next song at the last moment too?
    #
    # ideja. playbackconfig naj bo še bolj živ. naj shrani model in item, ja, ampak tudi metodo iz playorderja, ki izračuna naslednjo skladbo (naj bo kar callable); metoda se seveda določi glede na uporabnikovi klike, na začetku pa je default (zdaj auto). pa še cacheja naj rezultat --- zato bi bilo treba imeti fiksen primerek klasa med celim predvajanjem skladbe v next-u (potem ga pa že dobi currrent). ostali parametri (vsi razen model in item) pa naj bodo shranjeni v dictu, da se jih lahko pobriše? --mah, saj se ob vsaki skladbi naredi nov playbackconfig
    STOPPED, PAUSED, PLAYING, PLAYING_FADEOUT, PLAYING_GAP, _URI_CHANGE = range(1,7)
    state_changed = pyqtSignal(int)
    @property
    def state(self):
        return self._state
    @state.setter
    def state(self, state):  # todo: thread safety
        if self._state == state:
            return
        self._state = state
        playing = state in (self.PLAYING, self.PLAYING_FADEOUT, self.PLAYING_GAP)
        if not playing and self._timer.isActive():
            self._timer.stop()
        if state == self.PLAYING:
            self.current.item.unavailable = False
            self.playbin.set_state(Gst.State.PLAYING)
        elif state == self.PAUSED:
            self.playbin.set_state(Gst.State.PAUSED)
            self.next = PlaybackConfig()
            position = self.playbin.query_position(Gst.Format.TIME)
            if position[0]:
                self.position_changed.emit(position[1])
            self.update_playbin_volume()
        elif state == self.STOPPED:
            self.playbin.set_state(Gst.State.READY)
            self.current = PlaybackConfig(self.current.model)
            self.next = PlaybackConfig()
            self.position_changed.emit(0)
            #self.duration_changed.emit(1) # todo
        elif state == self.PLAYING_FADEOUT:
            self._gap_timer.stop()
            if not self.current or self.gst_state != Gst.State.PLAYING:
                #self.state = self._URI_CHANGE
                self._signal_uri_change.emit(int(self._n))
                return
            elif not self.current.fadeout_duration:
                self.state = self.PLAYING_GAP
                return
            self._fadeout_start = self.position
        elif state == self.PLAYING_GAP:
            if not self.current.gap_duration or self.next.state in (self.PAUSED, self.STOPPED):
                self._signal_uri_change.emit(int(self._n))
                return
            if self.gst_state == Gst.State.PLAYING and (not self.current.song_end or self.position < self.current.song_end):
                self.playbin.set_state(Gst.State.PAUSED)
            if self.next.state:
                #self.state = self._URI_CHANGE
                self._signal_uri_change.emit(int(self._n))
                return
            else:
                self._n_gap = self._n
                self._gap_timer.start(int(self.current.gap_duration/Gst.MSECOND))
        elif state == self._URI_CHANGE:
            self._gap_timer.stop()
            self._pending_ops.clear()
            if self.next.state == self.PAUSED:
                self.state = self.PAUSED
                return
            self.bus.set_flushing(True)
            self.playbin.set_state(Gst.State.READY)
            self.bus.set_flushing(False)
            if self.next.state == self.STOPPED:
                self.state = self.STOPPED
                return
            if self.next:
                self.current = self.next
            elif self.current:
                self.current = self.play_order.auto(self.current.model, self.current.item)
            self.next = PlaybackConfig()
            if not self.current:
                self.state = self.STOPPED
                return
            self.update_playbin_volume()
            self._n += 1
            self.playbin.set_property('uri', QUrl.fromLocalFile(self.current.item.filename).toString())
            self.playbin.set_state(Gst.State.PAUSED)
            if self.current.song_begin:
                self._pending_ops[Gst.State.PAUSED].append(
                    lambda:
                    self.playbin.seek(
                        1.0, Gst.Format.TIME,
                        Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE,
                        Gst.SeekType.SET, self.current.song_begin,
                        Gst.SeekType.NONE, 0
                    ))
            self.on_message_duration_changed()
            self._pending_ops[Gst.State.PAUSED].append(
                lambda: self._set_state(self.PLAYING))
            return
        if playing and not self._timer.isActive():
            self._timer.start()
        self.state_changed.emit(state)
    def _uri_change(self, requesting_n):
        if self._n == requesting_n:
            self.state = self._URI_CHANGE
    def _gap_timeout(self):
        if self.state == self.PLAYING_GAP and self._n == self._n_gap:
            self._n_gap = None
            #self.state = self._URI_CHANGE
            self._signal_uri_change.emit(int(self._n))
    def _set_state(self, state):
        self.state = state

    _signal_on_gst_message = pyqtSignal(QVariant, QVariant, str) # for thread safety
    def on_message(self, bus, message):
        #print(gst_message_pprint(message))
        if message.type in self.message_handlers:
            try:
                requesting_file = message.src.get_property("source").get_property("location")
            except:
                requesting_file = ''
            self._signal_on_gst_message.emit(bus, message, requesting_file)
    def on_gst_message(self, bus, message, requesting_file):
        self.message_handlers[message.type](self, bus, message, requesting_file)
    def on_message_eos(self, bus, message, requesting_file):
        if self.state in (self.PLAYING, self.PLAYING_FADEOUT) and self.current.item.filename == requesting_file:
            self.state = self.PLAYING_GAP
    duration_changed = pyqtSignal('quint64')
    def on_message_duration_changed(self, bus = None, message = None, requesting_file = None):
        duration = self.playbin.query_duration(Gst.Format.TIME)
        if duration[0]:
            self.duration = duration[1]
        else:
            duration = self.current.item.get_tag('_length', only_first = True)
            if duration:
                self.duration = int(float(duration) * Gst.SECOND)
            else:
                self.duration = 0
        self.duration_changed.emit(self.duration)
            
    def on_message_error(self, bus, message, requesting_file):
        self._pending_ops.clear()
        error = message.parse_error()
        if GLib.quark_from_string(error[0].domain) == Gst.ResourceError.quark():
            self.current.item.unavailable = True
            self._signal_uri_change.emit(int(self._n))
        else:
            print(error)
    def on_message_state_changed(self, bus, message, requesting_file):
        previous, current, pending = message.parse_state_changed()
        while self._pending_ops[current]:
            self._pending_ops[current].pop(0)()
    message_handlers = {
        Gst.MessageType.EOS: on_message_eos,
        Gst.MessageType.DURATION_CHANGED: on_message_duration_changed,
        Gst.MessageType.ERROR: on_message_error,
        Gst.MessageType.STATE_CHANGED: on_message_state_changed,
    }

    position_changed = pyqtSignal('quint64')
    fadeout_position_changed = pyqtSignal('quint64')
    gap_position_changed = pyqtSignal('quint64')
    def on_timer(self):
        # shouldn't be in PAUSED or STOPPED state ...
        position = self.position
        if self.state == self.PLAYING:
            if position is None:
                return
            song_end = self.current.song_end if self.current.song_end is not None else self.duration
            if song_end is not None and position > song_end:
                self.state = self.PLAYING_GAP
                self.gap_position_changed.emit(position - song_end)
        elif self.state == self.PLAYING_FADEOUT:
            fadeout_elapsed = position - self._fadeout_start
            if fadeout_elapsed > self.current.fadeout_duration:
                self.playbin.set_state(Gst.State.PAUSED)
                self.fadeout_position = 0
                self.state = self.PLAYING_GAP
            else:
                self.fadeout_position = self.current.fadeout_duration - fadeout_elapsed
        elif self.state == self.PLAYING_GAP:
            gap_remaining = self._gap_timer.remainingTime()
            self.gap_position_changed.emit(max(0, self.current.gap_duration - gap_remaining * Gst.MSECOND))
        if position:
            self.position_changed.emit(position)
        
class PlaybackConfig:
    """state is None:
    - both model and item: this is / will be playing
    - only model: we're at the start of the playtree
    - none: automatically continue from the current position
state is not None: don't play anything, invoke a TMPlayer state
"""
    def __init__(self,
                 model = None, item = None, index = None,
                 song_begin = 0, song_end = None,
                 fadeout_duration = 0, gap_duration = 0,
                 state = None):
        self.model, item, index = model_item_index(model, item, index)
        self.item = self.model.root_item if self.model and item is None else item
        self.fadeout_duration = fadeout_duration
        self.gap_duration = gap_duration
        self.song_begin = song_begin
        self.song_end = song_end
        self.state = state
    @property
    def index(self):
        try:
            return self.item.index(self.model) if self.item else QModelIndex()
        except ValueError:
            return QModelIndex()
    def __str__(self):
        return 'PlaybackConfig(state={},model={},item={},fadeout={},gap={},begin={},end={})'.format(self.state,self.model.root_item if self.model else None,self.item,self.fadeout_duration,self.gap_duration,self.song_begin,self.song_end)
    def __bool__(self):
        "A PlaybackConfig is True when it actually contains a song that can be played."
        return self.state is None and bool(self.model) \
            and self.item != self.model.root_item and \
            isinstance(self.item, PlayTreeFile)
    def auto(self):
        return self.state is None and self.model is None and self.item is None

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

    def previous(self, model, item):
        try:
            index = model.previous_song(item.index(model))
        except ValueError:
            index = QModelIndex()
        if not index.isValid():
            return PlaybackConfig(state = TMPlayer.STOPPED)
        si = self.config_playback(*model_item(index))
        while not si:
            index = model.previous_song(index)
            if not index.isValid():
                return PlaybackConfig(state = TMPlayer.STOPPED)
            si = self.config_playback(*model_item(index))
        return si
    def next(self, model, item):
        try:
            index = model.next_song(item.index(model))
        except ValueError:
            index = QModelIndex()
        if not index.isValid():
            return PlaybackConfig(state = TMPlayer.STOPPED)
        si = self.config_playback(*model_item(index))
        while not si:
            index = model.next_song(index)
            if not index.isValid():
                return PlaybackConfig(state = TMPlayer.STOPPED)
            si = self.config_playback(*model_item(index))
        return si
    def jump(self, model, item):
        if item.isPlayable:
            si = self.config_playback(model, item)
            if si:
                return si
        return self.next(model, item)
    def set_stop_after(self, i):
        self._stop_after = i
        self._stop_after_initial = i
    def update_stop_after_spinbox(self, model):
        stopafter_spinbox = model.view.window().stopafter_spinbox # todo: this is ugly
        stopafter_spinbox.blockSignals(True)
        stopafter_spinbox.setValue(self._stop_after)
        stopafter_spinbox.blockSignals(False)
    def auto(self, model, item):
        if self._stop_after == 1:
            self._stop_after = self._stop_after_initial
            self.update_stop_after_spinbox(model)
            return PlaybackConfig(state = TMPlayer.STOPPED)
        if self._stop_after:
            self._stop_after -= 1
            self.update_stop_after_spinbox(model)
        return self.next(model, item)
    def config_playback(self, model, item):
        return PlaybackConfig(model, item)

@PlayOrder.register
class PlayOrderMilongaMode(PlayOrderStandard):
    name = 'Milonga'
    def config_playback(self, model, item):
        return PlaybackConfig(
            model, item,
            song_begin = item.get_song_begin(),
            song_end = item.get_song_end(),
            fadeout_duration = config.fadeout_duration[item.function()],
            gap_duration = config.gap_duration[item.function()]) \
            if isinstance(item, PlayTreeFile) else PlaybackConfig()

@PlayOrder.register
class PlayOrderCheckSongBeginsSilently(PlayOrderStandard):
    name = 'To start'
    def config_playback(self, model, item):
        if not isinstance(item, PlayTreeFile):
            return PlaybackConfig()
        song_begin = item.get_song_begin()
        return PlaybackConfig(
            model, item, 
            song_begin = 0, song_end = song_begin) \
            if song_begin else PlaybackConfig()
    
@PlayOrder.register
class PlayOrderCheckSongBegins(PlayOrderStandard):
    name = 'From start'
    def config_playback(self, model, item):
        if not isinstance(item, PlayTreeFile):
            return PlaybackConfig()
        song_begin = item.get_song_begin()
        return PlaybackConfig(
            model, item, 
            song_begin = song_begin,
            song_end = song_begin + 3*Gst.SECOND) \
            if song_begin else PlaybackConfig() # todo: remove this line
    
@PlayOrder.register
class PlayOrderCheckSongEnds(PlayOrderStandard):
    name = 'To end'
    def config_playback(self, model, item):
        if not isinstance(item, PlayTreeFile):
            return PlaybackConfig()
        song_end = item.get_song_end()
        return PlaybackConfig(
            model, item, 
            song_begin = song_end - 5*Gst.SECOND,
            song_end = song_end) \
            if song_end else PlaybackConfig() # todo: remove this line

@PlayOrder.register
class PlayOrderCheckSongEndsSilently(PlayOrderStandard):
    name = 'From end'
    def config_playback(self, model, item):
        if not isinstance(item, PlayTreeFile):
            return PlaybackConfig()
        song_end = item.get_song_end()
        return PlaybackConfig(model, item, song_begin = song_end) \
            if song_end else PlaybackConfig()

@PlayOrder.register
class PlayOrderStart(PlayOrderStandard):
    name = 'First 35s'
    def config_playback(self, model, item):
        if not isinstance(item, PlayTreeFile):
            return PlaybackConfig()
        song_begin = item.get_song_begin()
        return PlaybackConfig(
            model, item,
            song_begin = 0, song_end = 35*Gst.SECOND,
            fadeout_duration = 0.5*Gst.SECOND,
            gap_duration = 0.5*Gst.SECOND
        )

    
def model_item_index(model, item = None, index = None, root_item = True):
    if model and item:
        index = item.index(model)
    elif index and index.isValid():
        model = index.model()
        item = model.item(index)
    elif model:
        item = model.root_item if root_item else None
        index = QModelIndex()
    else:
        return None, None, None
    return model, item, index

def model_item(index):
    model = index.model()
    return (model, model.item(index)) if model else (None, None)

# pretty print GStreamer message
def gst_message_pprint(message):
    if message.type == Gst.MessageType.STATE_CHANGED:
        info = message.parse_state_changed()
    elif message.type == Gst.MessageType.ERROR:
        info = message.parse_error()
    else:
        info = None
    return (message.type, info)
