from PyQt5.Qt import *

from gi.repository import GObject, Gst
GObject.threads_init()
Gst.init(None)

from model import PlayTreeModel, PlayTreeItem
from IPython import embed

class TandaMasterPlayer(QObject):

    STOPPED, PAUSED, PLAYING = range(3)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_model = None
        self._current_item = None
        self.stop_after = 0
        self._playback_start = None
        self.fadeout_timer = None
        self.state = self.STOPPED
        self.song_begin = None
        self.song_end = None
        
        self.playbin = Gst.ElementFactory.make("playbin", None)
        fakesink = Gst.ElementFactory.make("fakesink", None)
        self.playbin.set_property("video-sink", fakesink)

        if True:
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

        self._volume = 1.0

        self.position_timer = QTimer()
        self.position_timer.setTimerType(Qt.CoarseTimer)
        self.position_timer.timeout.connect(self.on_position_timer)
        self.position_timer.start(200)

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

    def milonga_mode(self):
        return self.current_model.view.window().action_milonga_mode.isChecked()
    def gap(self):
        #return max(0, self._gap_ns - self.duration + (self.song_end if self.song_end is not None else self.duration))
        return self._gap_ns
        
    def play(self):
        if not self.current_item.isPlayable:
            self.play_index(self.current_model.next_song(self.current_index))
        else:
            self.playbin.set_state(Gst.State.PLAYING)
            #self.setNotifyInterval(100)

    def play_index(self, playtree_index):
        if self.current_model and self.current_item and self.milonga_mode() and self.current_item.function() == 'cortina':
            self._fadeout(self._play_index, playtree_index)
        else:
            self._play_index(playtree_index)

    def _play_index(self, playtree_index):
        if not playtree_index.model() == self.current_model:
            self.set_current(model = playtree_index.model())
        if not self.current_model.item(playtree_index).isPlayable:
            playtree_index = self.current_model.next_song(playtree_index)
        self.set_current(index = playtree_index)
        self.playbin.set_state(Gst.State.READY)
        print('setting uri to', self.current_item.filename)
        self.playbin.set_property('uri', QUrl.fromLocalFile(self.current_item.filename).toString())
        self.playbin.set_state(Gst.State.PAUSED)
        try:
            self.song_begin = int(float(self.current_item.get_tag('tm:song_start')[0])*1000000000)
        except:
            self.song_begin = None
        try:
            self.song_end = int(float(self.current_item.get_tag('tm:song_end')[0])*1000000000)
        except:
            self.song_end = None
        state = self.playbin.get_state(100000000)
        if state[0] == Gst.StateChangeReturn.FAILURE:
            return
        if self.milonga_mode() and state[0] == Gst.StateChangeReturn.SUCCESS and state[1] == Gst.State.PAUSED and (self.song_begin or self.song_end):
            self.playbin.seek(
                1.0, Gst.Format.TIME,
                Gst.SeekFlags.FLUSH|Gst.SeekFlags.ACCURATE,
                Gst.SeekType.SET, self.song_begin if self.song_begin else 0,
                Gst.SeekType.SET if self.song_end else Gst.SeekType.NONE,
                1000000000000 # self.song_end if self.song_end else 0
            )
        self.playbin.set_state(Gst.State.PLAYING)
        self.current_media_changed.emit()
    current_media_changed = pyqtSignal()

    signal_play_next = pyqtSignal()
    def play_next(self):
        if self.current_model and self.current_item and self.milonga_mode():
            if self.current_item.function() == 'cortina':
                self._fadeout(self._play_next)
            else:
                self._gap(self._play_next)
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

    _gap_ns = 3  *1000000000

    fadeout_step = 0.05
    fadeout_timeout = 200

    def _fadeout(self, method, *args, **kwargs):
        if not self.fadeout_timer:
            self.fadeout_timer = QTimer()
            self.fadeout_timer.setTimerType(Qt.PreciseTimer)
            self.fadeout_timer.timeout.connect(lambda: self._fadeout(method, *args, **kwargs))
            self.fadeout_timer.start(self.fadeout_timeout)
        else:
            if self.playbin.get_property('volume') == 0:
                self.fadeout_timer.stop()
                self.fadeout_timer = None
                self.playbin.set_state(Gst.State.PAUSED)
                self.playbin.set_property('volume', self._volume)
                self._gap(method, *args, **kwargs)
            else:
                self.playbin.set_property('volume', max(0,self.playbin.get_property('volume')-self.fadeout_step))

    def _gap(self, method,  *args, **kwargs):
        if self.gap():
            print("Doing a gap of", self.gap())
            QTimer.singleShot(int(float(self.gap())/1000000), Qt.PreciseTimer, lambda: method(*args, **kwargs))
        else:
            method(*args, **kwargs)

    def play_previous(self):
        n = self.current_model.previous_song(self.current_index)
        if n.isValid():
            self.play_index(n)

    def stop(self):
        self.playbin.set_state(Gst.State.READY)
        self.set_current(item = None)

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            print('EOS at ', self.playbin.query_position(Gst.Format.TIME)[1])
            self.signal_play_next.emit()
        if t == Gst.MessageType.DURATION_CHANGED:
            duration = self.playbin.query_duration(Gst.Format.TIME)
            self.duration = duration[1] if duration[0] else None
            if duration[0]:
                   self.duration_changed.emit(int(duration[1]/1000000))
        if t == Gst.MessageType.STATE_CHANGED:
            gst_state = self.playbin.get_state(0)[1]
            state = self.PLAYING if gst_state == Gst.State.PLAYING else (self.PAUSED if gst_state == Gst.State.PAUSED else self.STOPPED)
            self.state_changed.emit(state)
            if gst_state == Gst.State.PAUSED:
                self.on_position_timer(force = True)
    duration_changed = pyqtSignal(int)
    position_changed = pyqtSignal(int)
    state_changed = pyqtSignal(int)


    def set_volume(self, volume):
        self._volume = float(volume) / 100
        self.playbin.set_property('volume', self._volume)

    def volume(self):
        return self._volume

    def pause(self):
        self.playbin.set_state(Gst.State.PAUSED)

    def on_position_timer(self, force = True):
        if force or self.playbin.get_state(0)[1] == Gst.State.PLAYING:
            position = self.playbin.query_position(Gst.Format.TIME)
            if position[0]:
                self.position_changed.emit(int(position[1]/1000000))
        
    def seek(self, position): # position in ms
        self.playbin.seek(
            1.0, Gst.Format.TIME,
            Gst.SeekFlags.FLUSH|Gst.SeekFlags.ACCURATE,
            Gst.SeekType.SET,
            position * 1000000,
            Gst.SeekType.SET if self.milonga_mode() and self.song_end else Gst.SeekType.NONE,
            self.song_end if self.song_end else 0)
