#!/usr/env python

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
