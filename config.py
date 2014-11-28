import os.path
library_folders = {
        'tango': ['~/tango'],
        'glasba': ['~/glasba'],
    }
for folders in library_folders.values():
    for i, folder in enumerate(folders):
        folders[i] = os.path.expanduser(folder)

autosave_interval = 10 # minutes

from gi.repository import Gst
fadeout_duration = {
    'cortina': 5 * Gst.SECOND,
    None: 0,
}
fadeout_duration = 5 * Gst.SECOND
gap_duration = {
    'cortina': int(2 * Gst.SECOND),
    None: 3 * Gst.SECOND,
}

_TMPlaybin_timer_precision = 100 # ms
_TMPlaybin_gstreamer_sync_interval = 1000 #ms

