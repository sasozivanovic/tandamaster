import ctypes
import sys, os.path
from PyQt5.Qt import QObject, QThread, QVariant, pyqtSignal, QUrl, QTimer
from library import library
from app import app
from util import *
import tempfile
from gi.repository import GObject, Gst, GLib

import platform
integrate_Glib_event_loop = (platform.system() != 'Linux')
if integrate_Glib_event_loop:
    main_context = GLib.main_context_default()
    

class Mp3Splt(QObject):
    def __init__(self):
        super().__init__()
        self.bg_thread = QThread()
        app.aboutToQuit.connect(self.bg_thread.exit)
        self.worker = Mp3SpltWorker()
        self.worker.moveToThread(self.bg_thread)
        self.bg_thread.started.connect(self.worker.run)
        self.keepalive = self
        #self.bg_thread.finished.connect(self.finish)
        self.trim.connect(self.worker.queue)
        self.bg_thread.start()

    def finish(self):
        self.keepalive = False

    trim = pyqtSignal(QVariant) # arg = list of playtree items

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
        
        import mp3splt_h
        self.mp3splt_h = mp3splt_h
        self.mp3splt = mp3splt_h._libs["mp3splt"]
        self.mp3splt.mp3splt_new_state.restype = ctypes.POINTER(self.mp3splt_h.splt_state)
        self.mp3splt.mp3splt_get_splitpoints.restype = ctypes.POINTER(self.mp3splt_h.splt_points)
        self.mp3splt.mp3splt_points_next.restype = ctypes.POINTER(self.mp3splt_h.splt_point)
        self.mp3splt.mp3splt_point_get_value.restype = ctypes.c_long

        self.converter = Gst.Pipeline("converter")
        self.decoder = Gst.ElementFactory.make("uridecodebin", None)
        self.audioconvert = Gst.ElementFactory.make("audioconvert", None)
        ar = Gst.ElementFactory.make("audioresample", None)
        lame = Gst.ElementFactory.make("lamemp3enc", None)
        self.filesink = Gst.ElementFactory.make("filesink", None)
        self.converter.add(self.decoder)
        self.converter.add(self.audioconvert)
        self.converter.add(ar)
        self.converter.add(lame)
        self.converter.add(self.filesink)
        self.decoder.connect("pad-added", self.decoder_callback)
        self.audioconvert.link(ar)
        ar.link(lame)
        lame.link(self.filesink)
        self.bus = self.converter.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.on_message)
        
        self.process_next.connect(self.process)

        if integrate_Glib_event_loop:
            #self.main_context = GLib.main_context_default()
            self.glib_timer = QTimer()
            self.glib_timer.setInterval(100)
            self.glib_timer.setSingleShot(True)
            self.glib_timer.timeout.connect(self.run_glib_event_loop)

    def run_glib_event_loop(self):
        if main_context.iteration(False):
            self.glib_timer.setInterval(100)
        else:
            self.glib_timer.setInterval(0)
        self.glib_timer.start()    
        
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
                    
                    print("Error during calculation of start and end of song. I will try again via conversion to mp3.", er, self.item.filename)
                    try:
                        self.convert_to_mp3(self.item.filename) # .trim is called from here
                    except RuntimeError as er:
                        print(er, self.item.filename)
                        self.process_next.emit()
                else:
                    self.save_start_end()
        else:
            app.info.emit("Finished calculating start and end of songs.")
        self._processing = False

    def save_start_end(self):
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
        self.process_next.emit()
        
    def convert_to_mp3(self, filename):
        #subprocess.call(['gst-launch-1.0', 'uridecodebin', "uri=file://" + item.filename, '!', 'audioconvert', '!', 'lamemp3enc', '!', 'filesink', 'location=' + os.path.expanduser("~/temp.mp3")])
        self.decoder.set_property('uri', QUrl.fromLocalFile(filename).toString())
        self.temp_filename = tempfile.mktemp(suffix = '.mp3', prefix = 'tmp_' + os.path.basename(filename))
        self.filesink.set_property('location', self.temp_filename)
        self.converter.set_state(Gst.State.PLAYING)
        if integrate_Glib_event_loop:
            self.glib_timer.setInterval(0)
            self.glib_timer.start()
        return

    def decoder_callback(self, decoder, pad):
        pad.link(self.audioconvert.get_static_pad("sink"))
        
    def on_message(self, bus, message):
        print(gst_message_pprint(message))
        if message.type == Gst.MessageType.ERROR:
            self.converter.set_state(Gst.State.NULL)
            self.process_next.emit()
        elif message.type == Gst.MessageType.EOS:
            self.converter.set_state(Gst.State.NULL)
            self.process_again()
        return
            
    def process_again(self):
        try:
            self.start, self.end = self.trim(self.temp_filename)
        except RuntimeError as er:
            print(er, self.item.filename)
            self.process_next.emit()
        else:
            self.save_start_end()

    def trim(self, filename):
        assert isinstance(filename, str)
        start = ctypes.c_long()
        end = ctypes.c_long()

        state = self.mp3splt.mp3splt_new_state(None)
        if state is None:
            raise RuntimeError('Cannot initialize libmp3splt')

        if getattr(sys, 'frozen', False): # only in bundled version
            error = self.mp3splt.mp3splt_append_plugins_scan_dir(
                state,
                os.path.join(sys._MEIPASS, 'libmp3splt').encode())
            if error:
                self.mp3splt.mp3splt_free_state(state)
                raise Mp3spltRuntimeError(error, 'Cannot add libmp3splt plugin directory')
        elif platform.system() == 'Windows': # debug
            error = self.mp3splt.mp3splt_append_plugins_scan_dir(
                state,
                os.path.abspath(r'dist\tandamaster\libmp3splt').encode())
            if error:
                self.mp3splt.mp3splt_free_state(state)
                raise Mp3spltRuntimeError(error, 'Cannot add libmp3splt plugin directory')
            
        error = self.mp3splt.mp3splt_find_plugins(state)
        if error:
            self.mp3splt.mp3splt_free_state(state)
            raise Mp3spltRuntimeError(error, 'Cannot find plugins')

        # we need to pass filename as bytes
        self.mp3splt.mp3splt_set_filename_to_split(state, filename.encode())

        def c_char_p_to_string(p):
            s = ''
            i = 0
            while ord(p[i]):
                s += chr(ord(p[i]))
                i += 1
            return s
        
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

class Mp3spltRuntimeError(RuntimeError):
    def __init__(self, libmp3splt_error_code, error_text):
        self.error_code = libmp3splt_error_code
        super().__init__('{}: {}'.format(libmp3splt_error_code, error_text))

from app import app        
mp3splt = Mp3Splt()

if __name__ == '__main__':
    w = Mp3SpltWorker()
    w.run()
    print(w.trim('/home/saso/tango/Soledad.mp3'))
