__all__ = ['app', 'config'] 

import sys, os, platform


from PyQt5.Qt import QApplication, pyqtSignal, QStandardPaths, QTimer, Qt, QThread

class TandaMasterApplication(QApplication):
    info = pyqtSignal(str)
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



class Config:
    pass
config = Config()

from util import locate_file
exec(open(locate_file(QStandardPaths.AppConfigLocation, 'config.py')).read())

for folders in config.library_folders.values():
    for i, folder in enumerate(folders):
        folders[i] = os.path.expanduser(folder)
