import ctypes
import sys, os.path
from PyQt5.Qt import QObject, QThread, QVariant, pyqtSignal
from library import library

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

    def trim_soledad(self):
        import model
        sol = model.PlayTreeFile('/home/saso/tango/Soledad.mp3')
        self.trim.emit([sol])
    
import subprocess
class Mp3SpltWorker(QObject):
    def __init__(self):
        super().__init__()        
        self.items = []
        self._processing = False

    def run(self):
        import mp3splt_h
        self.mp3splt_h = mp3splt_h
        self.mp3splt = mp3splt_h._libs["mp3splt"]
        self.mp3splt.mp3splt_new_state.restype = ctypes.POINTER(self.mp3splt_h.splt_state)
        self.mp3splt.mp3splt_get_splitpoints.restype = ctypes.POINTER(self.mp3splt_h.splt_points)
        self.mp3splt.mp3splt_points_next.restype = ctypes.POINTER(self.mp3splt_h.splt_point)
        self.mp3splt.mp3splt_point_get_value.restype = ctypes.c_long
    
    def queue(self, items):
        self.items.extend(items)
        if not self._processing:
            self.process()
    
    def process(self):
        self._processing = True
        while self.items:
            item = self.items.pop(0)
            old =  dict((tag, item.get_tag(tag, only_first = True))
                        for tag in ('tm:song_start', 'tm:song_end'))
            if all (old.values()):
                print("Skipping calculation of start and end of {}; the values are already known: {}, {}".format(item.filename, old['tm:song_start'], old['tm:song_end']))
                continue
            if not item.filename.endswith('.mp3'):
                subprocess.call(['gst-launch-1.0', 'uridecodebin', "uri=file://" + item.filename, '!', 'audioconvert', '!', 'lamemp3enc', '!', 'filesink', 'location=' + os.path.expanduser("~/temp.mp3")])
                fn = os.path.expanduser("~/temp.mp3")
            else:
                fn = item.filename
            try:
                start, end = self.trim(fn)
            except Mp3spltRuntimeError as er:
                print(er, item.filename)
                continue
            new = {'tm:song_start': "{:03}".format(start/100),
                   'tm:song_end': "{:03}".format(end/100) }
            print("Calculated start and end of {}, id {}: {}, {}".format(
                item.filename, item.song_id, new['tm:song_start'], new['tm:song_end']))
            for tag in ('tm:song_start', 'tm:song_end'):
                if not old[tag]:
                    library().connection.execute(
                        "DELETE FROM tags WHERE song_id=? AND source = ? AND tag = ?",
                        (item.song_id, 'user', # to be changed,
                        tag))
                    library().connection.execute(
                        "INSERT INTO tags (song_id, source, tag, value, ascii) VALUES (?,?,?,?,?)",
                        (item.song_id, 'user', # to be changed,
                         tag, new[tag], new[tag]))
            library().connection.commit()
        self._processing = False
        
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
        for i in range(state.contents.plug.contents.number_of_dirs_to_scan):
            print(c_char_p_to_string(state.contents.plug.contents.plugins_scan_dirs[i]))
        
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
            raise RuntimeError('Cannot find end of song')

        self.mp3splt.mp3splt_free_state(state)
        
        return (start, end)

class Mp3spltRuntimeError(RuntimeError):
    def __init__(self, libmp3splt_error_code, error_text):
        super().__init__('{}: {}'.format(libmp3splt_error_code, error_text))

from app import app        
mp3splt = Mp3Splt()

if __name__ == '__main__':
    w = Mp3SpltWorker()
    w.run()
    print(w.trim('/home/saso/tango/Soledad.mp3'))
