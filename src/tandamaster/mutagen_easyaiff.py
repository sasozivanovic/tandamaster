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

from mutagen.aiff import *
from mutagen.aiff import _IFFID3, AIFFInfo

from mutagen.easyid3 import EasyID3
from mutagen.id3._util import ID3NoHeaderError, error as ID3Error

__all__ = ["EasyAIFF", "Open", "delete"]

class _EasyIFFID3(EasyID3):
    def __init__(self, filename=None):
        self._EasyID3__id3 = _IFFID3()
        if filename is not None:
            self.load(filename)
            
class EasyAIFF(AIFF):
    ID3 = _EasyIFFID3

    def add_tags(self):
        """Add an empty ID3 tag to the file."""
        if self.tags is None:
            self.tags = _EasyIFFID3()
        else:
            raise error("an ID3 tag already exists")

    def load(self, filename, **kwargs):
        """Load stream and tag information from a file."""
        self.filename = filename

        try:
            self.tags = _EasyIFFID3(filename, **kwargs)
        except ID3NoHeaderError:
            self.tags = None
        except ID3Error as e:
            raise error(e)

        with open(filename, "rb") as fileobj:
            self.info = AIFFInfo(fileobj)

Open = EasyAIFF

#bacan = EasyAIFF("/home/saso/tango/temp/01 Bacan fulero.aif")
