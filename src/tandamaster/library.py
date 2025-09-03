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

#from IPython import embed; from PyQt5.QtCore import pyqtRemoveInputHook
from PyQt5.Qt import *   # todo: import only what you need

import mutagen.easyid3, mutagen.easymp4
import mutagen
from .mutagen_guess import File as MutagenFile

import sqlite3
#import threading
import os, os.path, sys
from warnings import warn
import functools, itertools, collections
from fnmatch import fnmatch
from .app import *
from .util import *
from gi.repository import Gst

def id3_performer_get(id3, key):
    people = []
    wanted_role = key.split(":", 1)[1].lower()
    try:
        mcl = id3["TMCL"]
    except KeyError:
        raise KeyError(key)
    for role, person in mcl.people:
        if role.lower() == wanted_role:
            people.append(person)
    if people:
        return people
    else:
        raise KeyError(key)


def id3_performer_set(id3, key, value):
    wanted_role = key.split(":", 1)[1].lower()
    try:
        mcl = id3["TMCL"]
    except KeyError:
        mcl = mutagen.id3.TMCL(encoding=3, people=[])
        id3.add(mcl)
    mcl.encoding = 3
    people = [p for p in mcl.people if p[0].lower() != wanted_role]
    for v in value:
        people.append((wanted_role, v))
    mcl.people = people


def id3_performer_delete(id3, key):
    wanted_role = key.split(":", 1)[1].lower()
    try:
        mcl = id3["TMCL"]
    except KeyError:
        raise KeyError(key)
    people = [p for p in mcl.people if p[0].lower() != wanted_role]
    if people == mcl.people:
        raise KeyError(key)
    elif people:
        mcl.people = people
    else:
        del(id3["TMCL"])


def id3_performer_list(id3, key):
    try:
        mcl = id3["TMCL"]
    except KeyError:
        return []
    else:
        return list(set("performer:" + p[0].lower() for p in mcl.people))

mutagen.easyid3.EasyID3.RegisterKey('performer:*', getter = id3_performer_get, setter = id3_performer_set, deleter = id3_performer_delete, lister = id3_performer_list)


def mp4_freeform_key_atomid(name, mean="com.apple.iTunes"):
    return "----:" + mean + ":" + name
def mp4_strip_freeform_atomid(atomid, mean="com.apple.iTunes"):
    start = "----:" + mean + ":"
    if atomid.startswith(start):
        return atomid[len(start):]
    else:
        return atomid

def mp4_performer_get(tags, key):
    return [s.decode("utf-8", "replace") for s in tags[mp4_freeform_key_atomid(key)]]

def mp4_performer_set(tags, key, value):
    encoded = []
    for v in value:
        if not isinstance(v, str):
            v = v.decode("utf-8")
        encoded.append(v.encode("utf-8"))
    tags[mp4_freeform_key_atomid(key)] = encoded

def mp4_performer_delete(tags, key):
    del(tags[mp4_freeform_key_atomid(key)])

def mp4_performer_list(tags, key):
    return [mp4_strip_freeform_atomid(k)
            for k in tags.keys() 
            if fnmatch(k, mp4_freeform_key_atomid(key))
            ]
    
mutagen.easymp4.EasyMP4.RegisterKey('performer:*', getter = mp4_performer_get, setter = mp4_performer_set, deleter = mp4_performer_delete, lister = mp4_performer_list)

def RegisterID3TXXXKey(key, Desc):
    desc = Desc.lower()
    DESC = Desc.upper()

    def rightdesccase(id3):
        descs = set(txxx.desc for txxx in id3.getall('TXXX'))
        return Desc if Desc in descs else (
            DESC if DESC in descs else (
                decs if desc in descs else Desc))
    
    def getter(id3, key):
        return list(id3['TXXX:'+rightdesccase(id3)])

    def setter(id3, key, value):
        try:
            frame = id3['TXXX:'+rightdesccase(id3)]
        except KeyError:
            enc = 0
            # Store 8859-1 if we can, per MusicBrainz spec.
            for v in value:
                if v and max(v) > u'\x7f':
                    enc = 3
                    break

            id3.add(mutagen.id3.TXXX(encoding=enc, text=value, desc=Desc))
        else:
            frame.text = value

    def deleter(id3, key):
        del(id3['TXXX:'+rightdesccase(id3)])

    mutagen.easyid3.EasyID3.RegisterKey(key, getter, setter, deleter)
    

RegisterID3TXXXKey('tm:song_start', "tm:song_start")
RegisterID3TXXXKey('tm:song_end', "tm:song_end")
mutagen.easymp4.EasyMP4Tags.RegisterFreeformKey('tm:song_start', "tm:song_start")
mutagen.easymp4.EasyMP4Tags.RegisterFreeformKey('tm:song_end', "tm:song_end")

RegisterID3TXXXKey(normalize_tag_name(Gst.TAG_TRACK_GAIN), normalize_tag_name(Gst.TAG_TRACK_GAIN))
RegisterID3TXXXKey(normalize_tag_name(Gst.TAG_TRACK_PEAK), normalize_tag_name(Gst.TAG_TRACK_PEAK))
RegisterID3TXXXKey(normalize_tag_name(Gst.TAG_REFERENCE_LEVEL), normalize_tag_name(Gst.TAG_REFERENCE_LEVEL))

mutagen.easymp4.EasyMP4Tags.RegisterFreeformKey(normalize_tag_name(Gst.TAG_TRACK_GAIN), normalize_tag_name(Gst.TAG_TRACK_GAIN))
mutagen.easymp4.EasyMP4Tags.RegisterFreeformKey(normalize_tag_name(Gst.TAG_TRACK_PEAK), normalize_tag_name(Gst.TAG_TRACK_PEAK))
mutagen.easymp4.EasyMP4Tags.RegisterFreeformKey(normalize_tag_name(Gst.TAG_REFERENCE_LEVEL), normalize_tag_name(Gst.TAG_REFERENCE_LEVEL))

# temporary solution:
mutagen.easyid3.EasyID3.RegisterTextKey("comment", "COMM::eng")

def _strip(tags):
    """Pulls single list items out of lists."""
    return collections.defaultdict(lambda: '', ((t,v[0] if isinstance(v,list) and len(v)==1 else v) for t,v in tags.items()))

class BgQuery:
    def __init__(self, method, args):
        self.method = method
        self.args = args

class BgQueries(list):
    def __init__(self, iterable, callback, relevant = lambda: True):
        super().__init__(iterable)
        assert not [query for query in iterable if not isinstance(query, BgQuery)]
        self.callback = callback
        self.relevant = relevant
    
class Library(QObject):
    _cache = {}

    def __init__(self, filename = 'tandamaster.db', connect = True):
        super().__init__()
        self.filename = os.path.join(
            os.path.normpath(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)),
            filename)
        if connect:
            self.connect()

    def connect(self):
        self.connection = sqlite3.connect(self.filename)

    def create_tables(self):
        self.connection.execute(
            'CREATE TABLE IF NOT EXISTS files'
            '(song_id INTEGER PRIMARY KEY, filename BLOB, mtime INTEGER, filesize INTEGER)'
        )
        self.connection.execute(
            'CREATE UNIQUE INDEX IF NOT EXISTS files_filename ON files (filename)'
        )
        # source = file, user, musicbranz, tango.info, ...
        # ascii = lowercase ascii approximation of the value, for searching
        self.connection.execute(
            'CREATE TABLE IF NOT EXISTS tags'
            '(song_id INTEGER, source TEXT, tag TEXT, value NUMERIC, ascii NUMERIC)'
        )
        self.connection.execute(
            'CREATE INDEX IF NOT EXISTS tags_gettag ON tags'
            '(song_id, source, tag)'
        )
        self.connection.execute(
            'CREATE INDEX IF NOT EXISTS tags_search ON tags'
            '(ascii, tag)'
        )
        self.connection.execute(
            'CREATE INDEX IF NOT EXISTS tags_browse_index ON tags'
            '(tag, value)'
        )
        self.connection.execute(
            'CREATE INDEX IF NOT EXISTS tags_tag ON tags'
            '(song_id, tag)'
        )
        self.connection.commit()

    def update_song_from_file(self, library_name, filename, force = False, commit = True, fix_file = True):
        fileinfo = QFileInfo(filename)
        if not (fileinfo.exists() and fileinfo.isReadable()):
            warn("Cannot read {}".format(filename), RuntimeWarning)
            audiofile = None
            return
        cursor = self.connection.cursor()
        cursor.execute(
            'SELECT song_id,mtime,filesize FROM files WHERE filename=?',
            (filename,)
        )
        song = cursor.fetchone()
        if song:
            song_id,mtime,filesize = song
            if mtime is not None and filesize is not None and fileinfo.lastModified().toTime_t() <= mtime and fileinfo.size() == filesize:
                if library_name is not None and library_name not in self.tag_by_song_id('_library', song_id):
                    cursor.execute('INSERT INTO tags '
                                   '(song_id, source, tag, value, ascii) '
                                   'VALUES (?,?,?,?,?)',
                                   (song_id, 'file', '_library', library_name, search_value(library_name)))
                    if commit:
                        self.connection.commit()
                if not force:
                    return
            else:
                cursor.execute(
                    'UPDATE files '
                    'SET mtime=?, filesize=? '
                    'WHERE song_id=?',
                    (fileinfo.lastModified().toTime_t(), fileinfo.size(), song_id)
                )
        else:
            cursor.execute(
                'INSERT INTO files (filename, mtime, filesize) VALUES(?,?,?)',
                (filename, fileinfo.lastModified().toTime_t(), fileinfo.size())
            )
            song_id = cursor.lastrowid
        try:
            audiofile = MutagenFile(filename, easy = True)
        except BaseException as err:
            print(err)
            warn("Cannot read {}. Probably not an audio file".format(filename), RuntimeWarning)
            audiofile = None
        filedir = fileinfo.absolutePath()
        if library_name is not None:
            for d in config.libraries[library_name]:
                if filedir.startswith(d):
                    filedir = filedir[len(d):].lstrip('/')
                    break
        print("Updating from", filename)
        cursor.execute('DELETE FROM tags WHERE song_id=? AND SOURCE="file"', (song_id,))
        tags = {
            '_filename': (fileinfo.fileName(),),
            '_dir': (filedir,)
        }
        if library_name is not None:
            tags['_library'] = (library_name,)
        for attr in ('length', 'bitrate', 'channels', 'sample_rate'):
            try:
                tags['_' + attr] = (getattr(audiofile.info, attr), )
            except AttributeError:
                pass
        if audiofile and audiofile.tags:
            # clean multiple empty tag values
            save = False
            try: # workaround for a strange bug with replaygain tags for some files from Gregor's collection
                for tag in audiofile.tags.keys():
                    if len(audiofile[tag]) > 1 and not all(audiofile[tag]):
                        values = list(filter(None, audiofile[tag]))
                        audiofile[tag] = values if values else ['']
                        save = True
                if fix_file and save:
                    print("Removed multiple empty tag values from", filename)
                    audiofile.save()
            except KeyError:
                pass
            for tag in audiofile.tags.keys():
                try:
                    tags[tag] = audiofile[tag]
                except:
                    print("Problem updating tag", tag, 'in file', filename)
                #tags.update(audiofile.tags)
        cursor.executemany(
            'INSERT INTO tags (song_id, source, tag, value, ascii) VALUES (?,"file",?,?,?)',
            ( (song_id, tag, value, search_value(value))
              for tag, values in tags.items()
              for value in values )
        )
        if commit:
            self.connection.commit()
        return song_id

    def _delete_nonexisting(self, existing):
        # todo: removable media
        existing = set( (i,) for i in existing)
        all_song_ids = self.connection.execute('SELECT DISTINCT filename FROM files NATURAL JOIN tags WHERE tags.tag="_library" AND value IS NOT NULL').fetchall()
        self.connection.executemany('DELETE FROM files WHERE filename=?',
                                    (set(all_song_ids) - existing))
    
    def tags_by_song_id(self, song_id, sources = ('user', 'file'), internal = True):
        last_source = collections.defaultdict(lambda: None)
        tags = {}
        for source in reversed(sources):
            cursor = self.connection.execute(
                'SELECT tag, value FROM tags WHERE song_id=? AND source=? '
                + ('AND substr(tag,1,1)!="_" ' if not internal else '') + 
                'ORDER BY tag, rowid',
                (song_id, source)
            )
            for tag, value in cursor.fetchall():
                if last_source[tag] != source:
                    tags[tag] = []
                    last_source[tag] = source
                tags[tag].append(value)
        return tags

    def tag_by_song_id(self, key, song_id, sources = ('user', 'file')):
        values = []
        for source in sources:
            cursor = self.connection.execute(
                'SELECT value FROM tags '
                'WHERE song_id=? AND tag=? AND source=? ORDER BY rowid',
                (song_id, key, source)
            )
            values = list(row[0] for row in cursor.fetchall() )
            if values:
                break
        return values

    def filename_by_song_id(self, song_id):
        row = self.connection.execute(
            'SELECT filename FROM files WHERE song_id=?',
            (song_id,)
        ).fetchone()
        return row[0] if row else None

    def song_id_from_filename(self, filename):
        try:
            row = self.connection.execute(
                'SELECT song_id FROM files WHERE filename=?',
                (filename,)
            ).fetchone()
            return row[0] if row else None
        except UnicodeEncodeError:
            return None

    def dirty(self, song_id, tag):
        return bool(self.tag_by_song_id(tag, song_id, sources = ('user',)))

    def set_tag(self, song_id, tag, values, source = 'user', ref_source = 'file', commit = True):
        self.connection.execute(
            'DELETE FROM tags '
            'WHERE song_id=? AND tag=? AND source=? ',
            (song_id, tag, source)
        )
        ref_values = self.tag_by_song_id(tag, song_id, sources = (ref_source,))
        if values != ref_values:
            self.connection.executemany(
                'INSERT INTO tags '
                '(song_id, source, tag, value, ascii) '
                'VALUES (?,?,?,?,?)',
                [(song_id, source, tag, value, search_value(value))
                 for value in values]
            )
        if commit:
            self.connection.commit()
        # todo: update views
        
    def save_changed_tags(self, update_source = 'file', from_source = 'user'):
        cursor = self.connection.cursor()
        for song_id, filename, mtime, filesize in self.connection.execute(
                'SELECT song_id, filename, mtime, filesize '
                'FROM files NATURAL JOIN tags '
                'WHERE source=?',
                (from_source,)):
            fileinfo = QFileInfo(filename)
            if fileinfo.lastModified().toTime_t() <= mtime and fileinfo.size() == filesize:
                try:
                    print("Saving tags to", filename)
                    audiofile = MutagenFile(filename, easy = True)
                    for t in list(audiofile.keys()):
                        del audiofile[t]
                    new_tags = self.tags_by_song_id(song_id, sources = (from_source, update_source), internal = False)
                    audiofile.update(new_tags)
                    audiofile.save()
                except:
                    print(" ... Failed.")
                    continue
                cursor.execute(
                    'DELETE FROM tags '
                    'WHERE song_id=? AND substr(tag,1,1)!="_" AND source IN (?,?)',
                    (song_id, from_source, update_source))
                bindings = [(song_id, update_source, tag, value, search_value(value))
                     for tag, values in new_tags.items()
                     for value in values
                     if value]
                cursor.executemany(
                    'INSERT INTO tags '
                    '(song_id, source, tag, value, ascii) '
                    'VALUES (?,?,?,?,?)',
                    bindings,
                )
                fileinfo = QFileInfo(filename)
                cursor.execute(
                    'UPDATE files '
                    'SET mtime=?, filesize=? '
                    'WHERE song_id=?',
                    (fileinfo.lastModified().toTime_t(), fileinfo.size(), song_id))
                
            else:
                pass
                # update library from file
                ####librarian.bg_queries(BgQueries([BgQuery(Library.update_song_from_file, (None, filename))], lambda qs: None, relevant = lambda: True))
                # todo: notify ui
        self.connection.commit() # must be here: if it's in the loop, all hell breaks loose

    def _query(self, fixed_tags, filter_words, browse_by_tags, tags_only, song_ids, source = 'file'):
        assert source in ('file', 'user')
        what = "".join("tags_browse_{}.value, ".format(i) for i in range(len(browse_by_tags)))
        def tables():
            for i in range(len(fixed_tags)):
                yield 'INNER', 'tags', 'tags_' + str(i)
            for i in range(len(filter_words)):
                yield 'INNER', 'tags', 'tags_filter_' + str(i)
            #for i in range(len(browse_by_tags)):
            #    yield 'LEFT', 'tags', 'tags_browse_' + str(i)
        join = " ".join(
            "{} JOIN {} AS {} USING(song_id)".format(j,t,a)
            for j,t,a in list(tables()))
        where = " AND ".join(filter(None,(
            "files.song_id IN ({})".format(",".join(str(sid) for sid in song_ids))
            if song_ids else None,
            " AND ".join(
                "tags_{n}.source = '{source}' AND tags_{n}.tag=? AND tags_{n}.value=?".format(n=n,source=source)
                if tv[1] is not None else
                'NOT EXISTS (SELECT song_id FROM tags WHERE song_id=tags_{n}.song_id AND tags_{n}.source = "{source}" and tag=?)'.format(n=n, source=source)
                for n,tv in enumerate(fixed_tags)
            ),
            " AND ".join(# todo: value OR ascii
                "tags_filter_{i}.source = '{source}' AND tags_filter_{i}.ascii LIKE ?".format(i=i,source=source) for i in range(len(filter_words))
            ),
            #" AND ".join(
            #    "tags_browse_{}.tag=?".format(i) for i in range(len(browse_by_tags))
            #)
        )))
        #group = ("GROUP BY " + ", ".join(
        #    "tags_browse_" + str(i) + '.value' for i in range(len(browse_by_tags)))
        #   ) if tags_only and browse_by_tags else ""
        group = ("GROUP BY " + ", ".join(
            "tags_browse_" + str(i) + '.value' for i in range(len(browse_by_tags)))
           ) if browse_by_tags else ""
        statement = 'SELECT {}{},{} FROM (SELECT DISTINCT files.song_id FROM files {} {}{}) AS songs {} {}'.format(
            what,
            'NULL' if tags_only else 'songs.song_id',
            'COUNT(*)' if tags_only else '1',
            join,
            'WHERE ' if where else '',
            where,
            " ".join(
                "LEFT JOIN tags AS tags_browse_{i} ON songs.song_id=tags_browse_{i}.song_id AND tags_browse_{i}.source = '{source}' AND tags_browse_{i}.tag=?".format(i=i,source=source)
                for i in range(len(browse_by_tags))
            ),
            group
        )
        def params():
            for t,v in fixed_tags:
                yield t
                if v is not None:
                    yield v
            for filter_word in filter_words:
                yield '%' + filter_word + '%'
            for t in browse_by_tags:
                yield t
        return self.connection.execute(statement, list(params()))

    def query_tags_iter(self, fixed_tags, filter_words, browse_by_tags, song_ids = None):
        cursor = self._query(fixed_tags, filter_words, browse_by_tags, True, song_ids)
        row = cursor.fetchone()
        while row:
            yield row
            row = cursor.fetchone()
    def query_tags_all(self, fixed_tags, filter_words, browse_by_tags, song_ids = None):
        return self._query(fixed_tags, filter_words, browse_by_tags, True, song_ids).fetchall()

    def query_songs_iter(self, fixed_tags, filter_words, browse_by_tags, song_ids = None):
        cursor = self._query(fixed_tags, filter_words, browse_by_tags, False, song_ids)
        row = cursor.fetchone()
        while row:
            yield row
            row = cursor.fetchone()
    def query_songs_all(self, fixed_tags, filter_words, browse_by_tags, song_ids = None):
        return self._query(fixed_tags, filter_words, browse_by_tags, False, song_ids).fetchall()
    def query_songs_create_playitems(self, browse, model, fixed_tags, filter_words, browse_by_tags, song_ids = None):
        rows = self.query_songs_iter(fixed_tags, filter_words, browse_by_tags, song_ids)
        browse._populate(model, rows)
    
    def filter_model(self, model, filter_expr):
        return model.root_item.filter(model, filter_expr)
        
    bg_queries_done = pyqtSignal(BgQueries)
    def bg_queries(self, queries):
        for query in queries:
            query.result = query.method.__get__(self)(*query.args)
        self.bg_queries_done.emit(queries)


_libraries = {} #threading.local()
#_libraries.library = Library()
def library():
    ct = QThread.currentThread()
    try:
        return _libraries[ct]
    except KeyError:
        l = Library()
        ct.finished.connect(l.connection.close)
        _libraries[ct] = l
        return _libraries[ct]

#_library = Library()
#def library():
#    return _library
    
library().create_tables()

class TMThread(QThread):
    def __init__(self, parent = None):
        super().__init__(parent)
        #self.library = Library(connect = False)
        #self.library.moveToThread(self)
        #self.started.connect(self.connect_library)
        #self.finished.connect(self.disconnect_library)

    #def connect_library(self):
    #    self.library.connect()
    #    _libraries.library = self.library
        
    def disconnect_library(self):
        _libraries.library.connection.close()
        _libraries.library = None

class UpdateLibraryThread(TMThread):
    def __init__(self, parent = None, force = False):
        super().__init__(parent)
        self.force = force
        self.started.connect(self.refresh_all_libraries)
    progress = pyqtSignal()
    finished = pyqtSignal()
    def refresh_all_libraries(self):
        self.queue = []
        for library_name, folders in config.libraries.items():
            for folder in folders:
                self.queue.append((library_name, folder))
        self.dir_iterator = None
        self.n_in_transaction = 0
        self._existing = set()
        self.progress.connect(self.refresh_one_song, type = Qt.QueuedConnection)
        self.progress.emit()
        # todo: commit if app exists
    def refresh_one_song(self):
        if not self.dir_iterator or not self.dir_iterator.hasNext():
            if not self.queue:
                library()._delete_nonexisting(self._existing)
                library().connection.commit()
                print('Finished updating library')
                self.finished.emit()
            else:
                self.name, folder = self.queue.pop(0)
                self.dir_iterator = QDirIterator(
                    folder, 
                    ['*'+ext for ext in config.musicfile_extensions],
                    QDir.Files | QDir.Readable, 
                    QDirIterator.Subdirectories)
                self.progress.emit()
        else:
            filename = self.dir_iterator.next()
            library().update_song_from_file(self.name, filename.encode().decode(), force = self.force, commit = False)
            self._existing.add(filename)
            if self.n_in_transaction >= 1000000:
                library().connection.commit()
                self.n_in_transaction = 0
            self.progress.emit()
        
        
class Librarian(QObject):
    def __init__(self):
        super().__init__()        
        #self.bg_thread = QThread()
        self.bg_thread = TMThread()
        app.aboutToQuit.connect(self.bg_thread.exit)
        #self.bg_library = Library(connect = False)
        #self.bg_library.moveToThread(self.bg_thread)
        #self.bg_thread.started.connect(self.bg_library.connect)
        self.bg_queries_start.connect(library().bg_queries)
        library().bg_queries_done.connect(self.bg_process_result)
        #self.bg_thread.library.bg_queries_done.connect(self.bg_process_result)
        self.queue = []
        self.processing = False
        self.bg_thread.start()

    def bg_queries(self, queries):
        if queries:
            self.queue.append(queries)
            self.do()

    bg_queries_start = pyqtSignal(BgQueries)
    def do(self):
        if not self.processing:
            while self.queue:
                queries = self.queue.pop(0)
                if queries.relevant():
                    self.processing = True
                    self.bg_queries_start.emit(queries)
                    break
        
    def bg_process_result(self, queries):
        self.processing = False
        if queries.relevant() and queries.callback:
            queries.callback(queries)
        self.do()

librarian = Librarian()
