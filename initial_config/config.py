# Where do you keep your music? TandaMaster supports any number of "libraries"
# (below, "tango" and (other) "music"), and each library consists of any number
# of folders.
# Notes:
# - Separate directory names by "/", not "\"!
config.library_folders = {
    'tango': [
        '~/tango',
        #r'C:\Users\Dawn\Music\iTunes\iTunes Media\Music',
        #'~/maybe/more/folders',
    ],
    'music': [
        '~/music',
        #'C:/maybe/more/folders',
    ],
}

# Library folders will be searched for files with the following suffixes:
config.musicfile_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.mp3', '.flac', '.aif', '.aiff']

# Don't lose your tandas! Save the entire playlist automatically every couple
# of minutes.
config.autosave_interval = 10 # minutes

import collections

SECOND = 1000000000 # Gst.SECOND

# In the "Milonga" mode, a pause (gap) is inserted between the songs. The
# lengths of the gaps after a song in a tanda and after a cortina are
# controlled independently. The default gap duration means after a song in a
# tanda.
# Note that the gaps work best if you process the songs using "Tools ->
# Calculate start and end of songs in playtree".
config.gap_duration = collections.defaultdict(
    lambda: 3 * SECOND, # default gap duration
    {
        'cortina': 2 * SECOND,
    })

# Controls the duration of the fadeout. (Same logic for cortinas/non-cortinas
# as for the gap duration above.)
config.fadeout_duration = collections.defaultdict(
    lambda: 1 * SECOND, # default fadeout duration
    {
        'cortina': 5 * SECOND,
    })

# How often the song position is updated while playing (in the (blue?) bar at
# the bottom).
config._TMPlayer_timer_precision = 100 # ms

# When you click the 'Previous' button:
# - go to the previous song if less than the given duration was played;
# - else, restart the song.
config.previous_restarts_song__min_time = 3 * SECOND

# Do I need to press enter to get the search results?
# Note that instant search might be a bit slow.
config.ui_search_wait_for_enter = True

# Don't change this.
config.glib_timer_timeout = 100
