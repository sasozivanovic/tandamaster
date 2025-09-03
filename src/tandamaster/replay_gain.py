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

#from IPython import embed; from PyQt5.QtCore import pyqtRemoveInputHook
from PyQt5.Qt import *   # todo: import only what you need
from gi.repository import GObject, Gst
from .mutagen_guess import File as MutagenFile

from .app import *
from .util import *
from .library import *

class TMReplayGain(QObject):
    def __init__(self, model):
        super().__init__()
        model.root_item.populate(model, recursive = True)
        self.bg_thread = QThread()
        app.aboutToQuit.connect(self.bg_thread.exit)
        self.worker = TMReplayGainWorker([item for item in model.root_item.iter(model, lambda it: it.isPlayable, lambda it: not it.isTerminal)])
        self.worker.moveToThread(self.bg_thread)
        self.bg_thread.started.connect(self.worker.setup)
        self.keepalive = self
        self.bg_thread.finished.connect(self.finish)
        self.bg_thread.start()
        #self.bg_library = Library(connect = False)
        #self.bg_library.moveToThread(self.bg_thread)
        #self.bg_thread.started.connect(self.bg_library.connect)
        #self.bg_queries_start.connect(self.bg_library.bg_queries)

    def finish(self):
        self.keepalive = False

class TMReplayGainWorker(QObject):
    def __init__(self, items):
        super().__init__()        
        self.items = items

    def setup(self):
        self.playbin = Gst.ElementFactory.make("playbin", None)
        fakesink = Gst.ElementFactory.make("fakesink", None)
        self.playbin.set_property("video-sink", fakesink)

        rganalysis = Gst.ElementFactory.make("rganalysis", None)
        fakesink = Gst.ElementFactory.make("fakesink", None)
        bin = Gst.Bin.new("audio_sink_bin")
        bin.add(rganalysis)
        bin.add(fakesink)
        rganalysis.link(fakesink)
        ghost_pad = Gst.GhostPad.new('sink', rganalysis.get_static_pad('sink'))
        ghost_pad.set_active(True)
        bin.add_pad(ghost_pad)
        self.playbin.set_property("audio-sink", bin)

        bus = self.playbin.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)

        self.item = None
        self.taglist = None
        self.signal_next.connect(self.next, type = Qt.QueuedConnection)
        self.signal_next.emit()
    
    signal_next = pyqtSignal()
    def next(self, force = False):
        if self.item and self.taglist:
            self.store_rg_info(self.taglist)
        while self.items:
            self.item = self.items.pop(0)
            self.taglist = None
            song_info_formatter = SongInfoFormatter(self.item)
            try:
                if not force:
                    audiofile = MutagenFile(self.item.filename, easy = True)
                    ok = bool(audiofile)
                    if ok:
                        for tag in (Gst.TAG_TRACK_GAIN, Gst.TAG_TRACK_PEAK, Gst.TAG_REFERENCE_LEVEL):
                            ok = ok and normalize_tag_name(tag) in audiofile.tags.keys()
                        if ok:
                            print("ReplayGain tags already present in", self.item.filename)
                            continue
                app.info.emit(song_info_formatter.format("Calculating replay gain of {artist}: {title}."))
                self.playbin.set_state(Gst.State.READY)
                self.playbin.set_property('uri', QUrl.fromLocalFile(self.item.filename).toString())
                self.playbin.set_state(Gst.State.PLAYING)
                break
            except:
                app.info.emit(song_info_formatter.format('Failed to calculate ReplayGain for {artist}: {title}.'))
                continue
        else:
            app.info.emit('Finished calculating ReplayGain')
            self.thread().exit()
            
    def on_message(self, bus, message):
        if message.type == Gst.MessageType.TAG: # and message.src.name.startswith('rganalysis'):
            taglist = message.parse_tag()
            self.taglist = [(i[0], str(i[1][1]) + (' dB' if i[0]==Gst.TAG_TRACK_GAIN else '')) for i in [(t,taglist.get_double(t)) for t in (Gst.TAG_TRACK_GAIN, Gst.TAG_TRACK_PEAK, Gst.TAG_REFERENCE_LEVEL)] if i[1][0]]
        elif message.type == Gst.MessageType.EOS:
            self.signal_next.emit()

    def store_rg_info(self, taglist):
        try:
            audiofile = MutagenFile(self.item.filename, easy = True)
            for tag, value in taglist:
                audiofile[normalize_tag_name(tag)] = [str(value)]
            audiofile.save()
        except:
            print("Could not save ReplayGain tags to", self.item.filename)
            return
        library().connection.execute(
            "DELETE FROM tags WHERE song_id=? AND source=? AND tag IN (?,?,?)",
            (self.item.song_id,
            'file',
            normalize_tag_name(Gst.TAG_TRACK_GAIN),
            normalize_tag_name(Gst.TAG_TRACK_PEAK),
            normalize_tag_name(Gst.TAG_REFERENCE_LEVEL)))
        library().connection.executemany(
            "INSERT INTO tags (song_id, source, tag, value, ascii) VALUES (?,?,?,?,?)",
            ( (self.item.song_id, 'file', tag, value, value) for tag, value in taglist )
        )
        
