import app

class Config:
    pass
config = Config()

from PyQt5.Qt import QStandardPaths
from util import *

exec(open(locate_file(QStandardPaths.AppConfigLocation, 'config.py')).read())

import os.path
for folders in config.library_folders.values():
    for i, folder in enumerate(folders):
        folders[i] = os.path.expanduser(folder)
