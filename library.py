from IPython import embed; from PyQt5.QtCore import pyqtRemoveInputHook
from PyQt5.Qt import *   # todo: import only what you need

import mutagen, mutagen.easyid3, mutagen.easymp4
import sqlite3
import os, os.path, sys
from warnings import warn
import functools, itertools, collections, weakref
from fnmatch import fnmatch
from app import app
import config
from util import *

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

mutagen.easyid3.EasyID3.RegisterTXXXKey('tm:song_start', "tm:song_start")
mutagen.easyid3.EasyID3.RegisterTXXXKey('tm:song_end', "tm:song_end")
mutagen.easymp4.EasyMP4Tags.RegisterFreeformKey('tm:song_start', "tm:song_start")
mutagen.easymp4.EasyMP4Tags.RegisterFreeformKey('tm:song_end', "tm:song_end")

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
    musicfile_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.mp3']

    def __init__(self, filename = 'tandamaster.db', connect = True):
        super().__init__()
        self.filename = filename
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
            '(song_id INTEGER, source TEXT, tag TEXT, value TEXT, ascii TEXT)'
        )
        self.connection.execute(
            'CREATE INDEX IF NOT EXISTS tags_gettag ON tags'
            '(song_id, source, tag)'
        )
        self.connection.execute(
            'CREATE INDEX IF NOT EXISTS tags_search ON tags'
            '(ascii, tag)'
        )
        self.connection.commit()

    refresh_next = pyqtSignal()
    refresh_finished = pyqtSignal()
    refreshing = pyqtSignal(str)
    def refresh_all_libraries(self):
        self.queue = []
        for library_name, folders in config.library_folders.items():
            for folder in folders:
                self.queue.append((library_name, folder))
        self.dir_iterator = None
        self.n_in_transaction = 0
        self.refresh_next.connect(self.refresh_one_song, type = Qt.QueuedConnection)
        self.refresh_next.emit()
        # todo: commit if app exists
    def refresh_one_song(self):
        if not self.dir_iterator or not self.dir_iterator.hasNext():
            if not self.queue:
                self.connection.commit()
                self.refresh_finished.emit()
            else:
                self.name, folder = self.queue.pop(0)
                self.dir_iterator = QDirIterator(
                    folder, 
                    ['*'+ext for ext in self.musicfile_extensions],
                    QDir.Files | QDir.Readable, 
                    QDirIterator.Subdirectories)
                self.refresh_next.emit()
        else:
            filename = self.dir_iterator.next()
            self.update_song_from_file(self.name, filename.encode().decode(), commit = False)
            if self.n_in_transaction >= 1000000:
                self.connection.commit()
                self.n_in_transaction = 0
            self.refresh_next.emit()

    def update_song_from_file(self, library_name, filename, commit = True):
        fileinfo = QFileInfo(filename)
        if not (fileinfo.exists() and fileinfo.isReadable()):
            warn("Cannot read {}".format(filename), RuntimeWarning)
            audiofile = None
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
                return
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
            audiofile = mutagen.File(filename, easy = True)
        except:
            warn("Cannot read {}. Probably not an audio file".format(filename), RuntimeWarning)
            audiofile = None
        filedir = fileinfo.absolutePath()
        if library_name is not None:
            for d in config.library_folders[library_name]:
                if filedir.startswith(d):
                    filedir = filedir[len(d):].lstrip('/')
                    break
        cursor.execute('DELETE FROM tags WHERE song_id=? AND SOURCE="file"', (song_id,))
        tags = {
            '_filename': (fileinfo.fileName(),),
            '_dir': (filedir,)
        }
        if library_name is not None:
            tags['_library'] = (library_name,)
        try:
            tags['_length'] = (audiofile.info.length,)
        except:
            pass
        if audiofile and audiofile.tags:
            tags.update(audiofile.tags)
        cursor.executemany(
            'INSERT INTO tags (song_id, source, tag, value, ascii) VALUES (?,"file",?,?,?)',
            ( (song_id, tag, value, search_value(value))
              for tag, values in tags.items()
              for value in values )
        )
        if commit:
            self.connection.commit()
        return song_id

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
        row = self.connection.execute(
            'SELECT song_id FROM files WHERE filename=?',
            (filename,)
        ).fetchone()
        return row[0] if row else None

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
                audiofile = mutagen.File(filename, easy = True)
                for t in list(audiofile.keys()):
                    del audiofile[t]
                new_tags = self.tags_by_song_id(song_id, sources = (from_source, update_source), internal = False)
                audiofile.update(new_tags)
                audiofile.save()
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
                # update library from file
                librarian.bg_queries(BgQueries([BgQuery(Library.update_song_from_file, (None, filename))], lambda qs: None, relevant = lambda: True))
                # todo: notify ui
        self.connection.commit() # must be here: if it's in the loop, all hell breaks loose


    def _build_join(self, table_alias_list):
        return "{} AS {} {}".format(
            table_alias_list[0][0], table_alias_list[0][1],
            " ".join("INNER JOIN {} AS {} USING(song_id)".format(t,a) for t,a in table_alias_list[1:])
        )

    def _build_query_statement(self, fixed_tags, filter_words):
        def tables():
            if not (fixed_tags or filter_words):
                yield 'files', 'files'
            for i in range(len(fixed_tags)):
                yield 'tags', 'tags_' + str(i)
            for i in range(len(filter_words)):
                yield 'tags', 'tags_filter_' + str(i)
        join = self._build_join(list(tables()))
        where = " AND ".join(filter(None,(
            " AND ".join(
                "tags_{n}.tag=? AND tags_{n}.value=?".format(n=n)
                if tv[1] is not None else
                'NOT EXISTS (SELECT song_id FROM tags WHERE song_id=tags_{}.song_id AND tag=?)'.format(n)
                for n,tv in enumerate(fixed_tags)
            ),
            " AND ".join(# todo: value OR ascii
                "tags_filter_{}.ascii LIKE ?".format(i) for i in range(len(filter_words))
            )
        )))
        statement = 'SELECT DISTINCT {} FROM {} {} {}' \
            .format(
                'tags_0.song_id' if fixed_tags else ('tags_filter_0.song_id' if filter_words else 'files.song_id'),
                join, 
                'WHERE' if where else '', 
                where)
        return statement

    def _query_tags(self, tag, fixed_tags, filter_words):
        """Get all values of "tag" of songs having the given fixed tags, and the number of songs for each value.

        "fixed_tags" should be a list of pairs."""
        statement = "SELECT tags.value, COUNT(*) FROM ({}) AS songs " \
                    "LEFT JOIN tags ON songs.song_id=tags.song_id AND tags.tag=? " \
                    "GROUP BY tags.value" \
                        .format(self._build_query_statement(fixed_tags, filter_words))
        def params():
            for t,v in fixed_tags:
                yield t
                if v is not None:
                    yield v
            for filter_word in filter_words:
                yield '%' + filter_word + '%'
            yield tag
        return self.connection.execute(statement, list(params()))

    def query_tags_iter(self, tag, fixed_tags, filter_words):
        cursor = self._query_tags(tag, fixed_tags, filter_words)
        row = cursor.fetchone()
        while row:
            yield row
            row = cursor.fetchone()

    def query_tags_all(self, tag, fixed_tags, filter_words):
        cursor = self._query_tags(tag, fixed_tags, filter_words)
        return cursor.fetchall()

    def _query_songs(self, fixed_tags, filter_words):
        """Get song_ids of songs having the given fixed tags.

        "fixed_tags" should be a list of pairs."""

        def params():
            for t,v in fixed_tags:
                yield t
                if v is not None:
                    yield v
            for filter_word in filter_words:
                yield '%' + filter_word + '%'
        statement = self._build_query_statement(fixed_tags, filter_words)
        return self.connection.execute(statement, list(params()))

    def query_songs_iter(self, fixed_tags, filter_words):
        cursor = self._query_songs(fixed_tags, filter_words)
        row = cursor.fetchone()
        while row:
            yield row[0]
            row = cursor.fetchone()

    def query_songs_all(self, fixed_tags, filter_words):
        cursor = self._query_songs(fixed_tags, filter_words)
        return [row[0] for row in cursor.fetchall()]

    bg_queries_done = pyqtSignal(BgQueries)
    def bg_queries(self, queries):
        for query in queries:
            query.result = query.method.__get__(self)(*query.args)
        self.bg_queries_done.emit(queries)

library = Library()
library.create_tables()

class Librarian(QObject):
    def __init__(self):
        super().__init__()        
        self.bg_thread = QThread()
        app.aboutToQuit.connect(self.bg_thread.exit)
        self.bg_library = Library(connect = False)
        self.bg_library.moveToThread(self.bg_thread)
        self.bg_thread.started.connect(self.bg_library.connect)
        self.bg_queries_start.connect(self.bg_library.bg_queries)
        self.bg_library.bg_queries_done.connect(self.bg_process_result)
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
