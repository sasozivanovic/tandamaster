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

from mutagen import *

def File(filename, options=None, easy=False):
    """Guess the type of the file and try to open it.

    The file type is decided by several things, such as the first 128
    bytes (which usually contains a file type identifier), the
    filename extension, and the presence of existing tags.

    If no appropriate type could be found, None is returned.

    :param options: Sequence of :class:`FileType` implementations, defaults to
                    all included ones.

    :param easy: If the easy wrappers should be returnd if available.
                 For example :class:`EasyMP3 <mp3.EasyMP3>` instead
                 of :class:`MP3 <mp3.MP3>`.
    """

    if options is None:
        from mutagen.asf import ASF
        from mutagen.apev2 import APEv2File
        from mutagen.flac import FLAC
        if easy:
            from mutagen.easyid3 import EasyID3FileType as ID3FileType
        else:
            from mutagen.id3 import ID3FileType
        if easy:
            from mutagen.mp3 import EasyMP3 as MP3
        else:
            from mutagen.mp3 import MP3
        from mutagen.oggflac import OggFLAC
        from mutagen.oggspeex import OggSpeex
        from mutagen.oggtheora import OggTheora
        from mutagen.oggvorbis import OggVorbis
        from mutagen.oggopus import OggOpus
        if easy:
            from mutagen.trueaudio import EasyTrueAudio as TrueAudio
        else:
            from mutagen.trueaudio import TrueAudio
        from mutagen.wavpack import WavPack
        if easy:
            from mutagen.easymp4 import EasyMP4 as MP4
        else:
            from mutagen.mp4 import MP4
        from mutagen.musepack import Musepack
        from mutagen.monkeysaudio import MonkeysAudio
        from mutagen.optimfrog import OptimFROG
        if easy:
            from .mutagen_easyaiff import EasyAIFF as MyAIFF
        else:
            from mutagen.aiff import AIFF as MyAIFF
        from mutagen.aac import AAC
        options = [MP3, TrueAudio, OggTheora, OggSpeex, OggVorbis, OggFLAC,
                   FLAC, MyAIFF, APEv2File, MP4, ID3FileType, WavPack,
                   Musepack, MonkeysAudio, OptimFROG, ASF, OggOpus, AAC]

    if not options:
        return None

    with open(filename, "rb") as fileobj:
        header = fileobj.read(128)
        # Sort by name after score. Otherwise import order affects
        # Kind sort order, which affects treatment of things with
        # equals scores.
        results = [(Kind.score(filename, fileobj, header), Kind.__name__)
                   for Kind in options]

    results = list(zip(results, options))
    results.sort()
    (score, name), Kind = results[-1]
    if score > 0:
        return Kind(filename)
    else:
        return None


#bacan = File("/home/saso/tango/temp/01 Bacan fulero.aif", easy = True)
