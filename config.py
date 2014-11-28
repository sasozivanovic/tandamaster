import os.path
library_folders = {
        'tango': ['~/tango'],
        'glasba': ['~/glasba'],
    }
for folders in library_folders.values():
    for i, folder in enumerate(folders):
        folders[i] = os.path.expanduser(folder)

autosave_interval = 10

from gi.repository import Gst
gap = 3 * Gst.SECOND
fadeout_step = 0.05
fadeout_timeout = 100 # ms
fadeout_time = 5 * Gst.SECOND

