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
import collections
fadeout_duration = collections.defaultdict(
    lambda: 1 * Gst.SECOND,
    {
        'cortina': 5 * Gst.SECOND,
    })
gap_duration = collections.defaultdict(
    lambda: 3 * Gst.SECOND,
    {
        'cortina': 2 * Gst.SECOND,
    })

_TMPlayer_timer_precision = 100 # ms
previous_restarts_song__min_time = 3 * Gst.SECOND

ui_search_wait_for_enter = True
