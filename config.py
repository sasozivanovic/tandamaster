import os.path
library_folders = {
        'tango': ['~/tango'],
#        'glasba': ['~/glasba'],
    }
for folders in library_folders.values():
    for i, folder in enumerate(folders):
        folders[i] = os.path.expanduser(folder)

autosave_interval = 10
