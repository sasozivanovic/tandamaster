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

__all__ = ['app', 'config'] 

import sys, os, platform


from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import pyqtSignal
from PyQt5.Qt import QStandardPaths, QTimer, Qt, QThread

class TandaMasterApplication(QApplication):
    info = pyqtSignal(str)
    error = pyqtSignal(str)
    def quit_glib_event_loop(self):
        glib_event_loop.quit()
    
app = TandaMasterApplication(sys.argv)
app.setApplicationName('TandaMaster')
app.setOrganizationName('MilongueroSi')
app.setOrganizationDomain('milonguero.si')


integrate_glib_event_loop = (platform.system() != 'Linux')
if integrate_glib_event_loop:
    import threading
    glib_ready = threading.Event()
    glib_event_loop = None
    def run_glib_thread():
        import gi
        gi.require_version('Gst', '1.0')
        from gi.repository import GLib
        glib_ready.set()
        global glib_event_loop
        glib_event_loop = GLib.MainLoop()
        app.aboutToQuit.connect(app.quit_glib_event_loop)
        glib_event_loop.run()
    glib_thread = threading.Thread(target = run_glib_thread)
    glib_thread.start()
    glib_ready.wait()
else:
    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import GLib, Gst
    Gst.init(None)



try:
    os.makedirs(os.path.normpath(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)))
except FileExistsError:
    pass
try:
    os.makedirs(os.path.normpath(QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)))
except FileExistsError:
    pass


import tomllib, pydantic, collections
from gi.repository import Gst

class Config(pydantic.BaseModel):
    
    libraries: dict[str, list[str]]
    musicfile_extensions: list[str]
    autosave_interval: int
    gap_duration: dict[str, float]
    fadeout_duration: dict[str, float]
    timer_precision: int
    min_time_for_previous_restarts_song: float
    ui_search_wait_for_enter: bool
    song_pdf: str

    def __init__(self, **kwargs):
        
        super().__init__(**kwargs)

        # Expand user.
        for folders in self.libraries.values():
            for i, folder in enumerate(folders):
                folders[i] = os.path.expanduser(folder)
        self.song_pdf = os.path.expanduser(self.song_pdf)

        # 1. Convert to nanoseconds for Gstreamer
        # 2. Convert into a defaultdict
        for attr in ('gap_duration', 'fadeout_duration'):
            d = getattr(self, attr)
            default = d.pop('default')
            setattr(self, attr, collections.defaultdict(
                lambda: int(default * Gst.SECOND), {
                    k: int(v * Gst.SECOND)
                    for k,v in d.items()
                }))
                
        # Convert to nanoseconds for Gstreamer
        self.min_time_for_previous_restarts_song = int(
            self.min_time_for_previous_restarts_song * Gst.SECOND)

        
from .util import locate_file
with open(locate_file(QStandardPaths.AppConfigLocation, 'config.toml'), 'rb') as f:
    config = Config(**tomllib.load(f))
