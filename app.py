__all__ = ['app', 'config'] 

import sys, os, platform

from PyQt5.Qt import QApplication, pyqtSignal, QStandardPaths, QTimer, Qt

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GLib

from util import *

_integrate_glib_event_loop = (platform.system() != 'Linux')

class TandaMasterApplication(QApplication):
    info = pyqtSignal(str)

    if _integrate_glib_event_loop:
        def _iterate_glib_event_loop(self):
            context = GLib.main_context_get_thread_default()
            if not context:
                context = GLib.main_context_default()
            if context.iteration(False):
                self._glib_timer.setInterval(config.glib_timer_timeout)
            else:
                self._glib_timer.setInterval(0)
            self._glib_timer.start()
        _signal_iterate_glib_event_loop = pyqtSignal()
        def iterate_glib_event_loop(self):
            context = GLib.main_context_get_thread_default()
            if not context:
                context = GLib.main_context_default()
            context.iteration(False)
    else:
        def iterate_glib_event_loop(self):
            pass

    def __init__(self, *args):
        super().__init__(*args)
        if _integrate_glib_event_loop:
            self._glib_timer = QTimer()
            self._glib_timer.setSingleShot(True)
            self._glib_timer.timeout.connect(
                self._iterate_glib_event_loop, type = Qt.QueuedConnection)
            self._signal_iterate_glib_event_loop.connect(
                self._iterate_glib_event_loop, type = Qt.DirectConnection)

    
app = TandaMasterApplication(sys.argv)
app.setApplicationName('TandaMaster')
app.setOrganizationName('MilongueroSi')
app.setOrganizationDomain('milonguero.si')

try:
    os.makedirs(os.path.normpath(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)))
except FileExistsError:
    pass
try:
    os.makedirs(os.path.normpath(QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)))
except FileExistsError:
    pass

class Config:
    pass
config = Config()

exec(open(locate_file(QStandardPaths.AppConfigLocation, 'config.py')).read())

import os.path
for folders in config.library_folders.values():
    for i, folder in enumerate(folders):
        folders[i] = os.path.expanduser(folder)

if _integrate_glib_event_loop:
    app._glib_timer.setInterval(config.glib_timer_timeout)
    app._glib_timer.start()
