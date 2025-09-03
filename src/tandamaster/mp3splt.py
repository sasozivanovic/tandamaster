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

import ctypes
import sys, os.path
from PyQt5.Qt import QObject, QThread, QVariant, pyqtSignal, QUrl, QTimer, Qt
from .library import library
from .app import *
from .util import *
import tempfile

import gi
from gi.repository import GObject, Gst, GLib
import platform

class Mp3Splt(QObject):
    def __init__(self):
        super().__init__()
        self.bg_thread = QThread()
        app.aboutToQuit.connect(self.bg_thread.exit)
        self.worker = Mp3SpltWorker()
        self.worker.moveToThread(self.bg_thread)
        self.bg_thread.started.connect(self.worker.run)
        self.keepalive = self
        self.bg_thread.finished.connect(self.finish)
        self.trim.connect(self.worker.queue)
        self.worker.refresh_models.connect(self.do_refresh_models, Qt.QueuedConnection)
        self.bg_thread.start()

    def finish(self):
        self.keepalive = False

    trim = pyqtSignal(QVariant) # arg = list of playtree items
    
    def do_refresh_models(self, item):
        item.refresh_models()

import subprocess
class Mp3SpltWorker(QObject):
    def __init__(self):
        super().__init__()        
        self.items = []
        self._processing = False

    def run(self):
        gi.require_version('Gst', '1.0')
        GObject.threads_init()
        Gst.init(None)

        from .mp3splt_h import _libs, splt_state, splt_points, splt_point
        self.mp3splt = _libs["mp3splt"]
        self.mp3splt.mp3splt_new_state.restype = ctypes.POINTER(splt_state)
        self.mp3splt.mp3splt_get_splitpoints.restype = ctypes.POINTER(splt_points)
        self.mp3splt.mp3splt_points_next.restype = ctypes.POINTER(splt_point)
        self.mp3splt.mp3splt_point_get_value.restype = ctypes.c_long

        self.converter = Gst.Pipeline()
        self.uridecodebin = Gst.ElementFactory.make("uridecodebin", None)
        self.audioconvert = Gst.ElementFactory.make("audioconvert", None)
        self.vorbisenc = Gst.ElementFactory.make("vorbisenc", None)
        self.oggmux = Gst.ElementFactory.make("oggmux", None)
        self.filesink = Gst.ElementFactory.make("filesink", None)
        #self.temp_filename = tempfile.mktemp(suffix = '.ogg', prefix = 'tandamaster_mp3splt_convert_to_ogg_')
        self.converter.add(self.uridecodebin)
        self.converter.add(self.audioconvert)
        self.converter.add(self.vorbisenc)
        self.converter.add(self.oggmux)
        self.converter.add(self.filesink)
        self.uridecodebin.connect("pad-added", self.uridecodebin_pad_added)
        self.audioconvert.link(self.vorbisenc) 
        self.vorbisenc.link(self.oggmux)
        self.oggmux.link(self.filesink)
        self.bus = self.converter.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.on_message)
        
        self.process_next.connect(self.process)

    def queue(self, items):
        self.items.extend(items)
        if not self._processing:
            self.process_next.emit()

    process_next = pyqtSignal()
    def process(self):
        self._processing = True
        if self.items:
            self.item = self.items.pop(0)
            song_info_formatter = SongInfoFormatter(self.item)
            app.info.emit(song_info_formatter.format("Calculating start and end of {artist}: {title}."))
            self.old = dict((tag, self.item.get_tag(tag, only_first = True))
                       for tag in ('tm:song_start', 'tm:song_end'))
            if all (self.old.values()):
                print("Skipping calculation of start and end of {}; the values are already known: {}, {}".format(self.item.filename, self.old['tm:song_start'], self.old['tm:song_end']))
                self.process_next.emit()
            else:
                self.start, self.end = None, None
                try:
                    self.start, self.end = self.trim(self.item.filename)
                except RuntimeError as er:
                    print("Error during calculation of start and end of song. I will try again via conversion to ogg", er, self.item.filename)
                    try:
                        self.convert_to_ogg(self.item.filename) # .trim is called from here
                    except RuntimeError as er:
                        print(er, self.item.filename)
                        self.process_next.emit()
                else:
                    self.save_start_end()
        else:
            app.info.emit("Finished calculating start and end of songs.")
        self._processing = False

    def save_start_end(self):
        if self.start < self.end:
            new = {'tm:song_start': "{:03}".format(self.start/100),
                   'tm:song_end': "{:03}".format(self.end/100) }
            print("Calculated start and end of {}, id {}: {}, {}".format(
                self.item.filename, self.item.song_id, new['tm:song_start'], new['tm:song_end']))
            for tag in ('tm:song_start', 'tm:song_end'):
                if not self.old[tag]:
                    library().connection.execute(
                        "DELETE FROM tags WHERE song_id=? AND source = ? AND tag = ?",
                        (self.item.song_id, 'user', # to be changed,
                        tag))
                    library().connection.execute(
                        "INSERT INTO tags (song_id, source, tag, value, ascii) VALUES (?,?,?,?,?)",
                        (self.item.song_id, 'user', # to be changed,
                         tag, new[tag], new[tag]))
            library().connection.commit()
            self.refresh_models.emit(self.item)
        else:
            print("Start not less than end: {} - {}".format(self.start/100, self.end/100))
        self.process_next.emit()

    refresh_models = pyqtSignal(QVariant) # arg = item        

    def uridecodebin_pad_added(self, uridecodebin, pad):
        pad.link(self.audioconvert.get_static_pad("sink"))
    
    def convert_to_ogg(self, filename):
        #subprocess.call(['gst-launch-1.0', 'uridecodebin', "uri=file://" + item.filename, '!', 'audioconvert', '!', 'vorbisenc', '!', 'oggmux', '!', 'filesink', 'location=' + os.path.expanduser("~/temp.ogg")])
        self.uridecodebin.set_property('uri', QUrl.fromLocalFile(filename).toString())
        self.temp_filename = tempfile.mktemp(suffix = '.ogg', prefix = 'tmp_' + os.path.basename(filename))
        self.filesink.set_property('location', self.temp_filename)
        self.converter.set_state(Gst.State.PLAYING)

    def on_message(self, bus, message):
        #print(gst_message_pprint(message))
        if message.type == Gst.MessageType.ERROR:
            self.converter.set_state(Gst.State.NULL)
            try:
                os.remove(self.temp_filename)
            except FileNotFoundError:
                pass
            self.process_next.emit()
        elif message.type == Gst.MessageType.EOS:
            self.converter.set_state(Gst.State.NULL)
            self.process_again()
            
    def process_again(self):
        temp_filename = self.temp_filename # because self.process_next.emit() executes self.process before reaching the finally clause
        try:
            self.start, self.end = self.trim(self.temp_filename)
        except RuntimeError as er:
            print(er, self.item.filename)
            self.process_next.emit()
        else:
            self.save_start_end()
        finally:
            try:
                os.remove(temp_filename)
            except FileNotFoundError:
                pass

    def trim(self, filename):
        assert isinstance(filename, str)
        start = ctypes.c_long()
        end = ctypes.c_long()

        state = self.mp3splt.mp3splt_new_state(None)
        if state is None:
            raise RuntimeError('Cannot initialize libmp3splt')

        error = self.mp3splt.mp3splt_find_plugins(state)
        if error:
            self.mp3splt.mp3splt_free_state(state)
            raise Mp3spltRuntimeError(error, 'Cannot find plugins')

        # we need to pass filename as bytes
        self.mp3splt.mp3splt_set_filename_to_split(state, filename.encode())

        error = self.mp3splt.mp3splt_set_trim_silence_points(state)
        if error:
            self.mp3splt.mp3splt_free_state(state)
            raise Mp3spltRuntimeError(error, 'Cannot set trim silence points')

        error = ctypes.c_int()
        points = self.mp3splt.mp3splt_get_splitpoints(state, ctypes.byref(error))
        if error:
            self.mp3splt.mp3splt_free_state(state)
            raise Mp3spltRuntimeError(error, 'Cannot get splitpoints')

        self.mp3splt.mp3splt_points_init_iterator(points)

        point = self.mp3splt.mp3splt_points_next(points)
        if point:
            start = self.mp3splt.mp3splt_point_get_value(point)
        else:
            self.mp3splt.mp3splt_free_state(state)
            raise RuntimeError('Cannot find start of song')

        end = None
        point = self.mp3splt.mp3splt_points_next(points)
        while point:
            end = self.mp3splt.mp3splt_point_get_value(point)
            point = self.mp3splt.mp3splt_points_next(points)

        if end is None:
            self.mp3splt.mp3splt_free_state(state)
            raise RuntimeError('Cannot find end of song (start={})'.format(start))

        self.mp3splt.mp3splt_free_state(state)
        
        return (start, end)

    #def print_plugins_scan_dirs(self, state):
    #    n = state.contents.plug.contents.number_of_dirs_to_scan
    #    print("plugins_scan_dirs ({})".format(n))
    #    for i in range(n):
    #        d = ''
    #        j = 0
    #        c = state.contents.plug.contents.plugins_scan_dirs[i][j]
    #        while ord(c):
    #            d += c.decode()
    #            j += 1
    #            c = state.contents.plug.contents.plugins_scan_dirs[i][j]
    #        print(d)
    
class Mp3spltRuntimeError(RuntimeError):
    def __init__(self, libmp3splt_error_code, error_text):
        self.error_code = libmp3splt_error_code
        super().__init__('{}: {}'.format(libmp3splt_error_code, error_text))

# pretty print GStreamer message (duplicate def in player.py)
def gst_message_pprint(message):
    if message.type == Gst.MessageType.STATE_CHANGED:
        info = message.parse_state_changed()
    elif message.type == Gst.MessageType.ERROR:
        info = message.parse_error()
    else:
        info = None
    return (message.type, info)
        
if __name__ == '__main__':
    from IPython import embed
    w = Mp3SpltWorker()
    w.run()
    print(w.trim('/home/saso/tango/Soledad.mp3'))
