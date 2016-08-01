import os.path
config.library_folders = {
        'tango': ['~/tango'],
        'glasba': ['~/glasba'],
    }
for folders in config.library_folders.values():
    for i, folder in enumerate(folders):
        folders[i] = os.path.expanduser(folder)

config.autosave_interval = 10 # minutes

from gi.repository import Gst
import collections
config.fadeout_duration = collections.defaultdict(
    lambda: 1 * Gst.SECOND,
    {
        'cortina': 5 * Gst.SECOND,
    })
config.gap_duration = collections.defaultdict(
    lambda: 3 * Gst.SECOND,
    {
        'cortina': 2 * Gst.SECOND,
    })

config._TMPlayer_timer_precision = 100 # ms
config.previous_restarts_song__min_time = 3 * Gst.SECOND

config.ui_search_wait_for_enter = True
