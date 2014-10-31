from IPython import embed; from PyQt5.QtCore import pyqtRemoveInputHook
from PyQt5.Qt import *   # todo: import only what you need

import mutagen, mutagen.easyid3, mutagen.easymp4
import sqlite3
import os, os.path
from warnings import warn
import functools, itertools, collections, weakref
from app import app
import config
import unidecode

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

def mp4_performer_get(tags, key):
    return [s.decode("utf-8", "replace") for s in tags[mp4_freeform_key_atomid(key)]]

def mp4_performer_set(tags, key, value):
    encoded = []
    for v in value:
        if not isinstance(v, text_type):
            if PY3:
                raise TypeError("%r not str" % v)
            v = v.decode("utf-8")
        encoded.append(v.encode("utf-8"))
    tags[mp4_freeform_key_atomid(key)] = encoded

def mp4_performer_delete(tags, key):
    del(tags[mp4_freeform_key_atomid(key)])

mutagen.easymp4.EasyMP4.RegisterKey('performer:*', getter = mp4_performer_get, setter = mp4_performer_set, deleter = mp4_performer_delete)



### transition from recordingdate to date ###




### end of transition from recordingdate to date ###

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

    def create_library_table(self, name):
        self.connection.execute(
            'CREATE TABLE IF NOT EXISTS files_{name}'
            '(song_id INTEGER PRIMARY KEY, filename BLOB, mtime INTEGER, filesize INTEGER)'
            .format(name=name)
        )
        self.connection.execute(
            'CREATE INDEX IF NOT EXISTS files_{name}_filename ON files_{name} (filename)'
            .format(name=name)
        )
        self.connection.execute(
            'CREATE TABLE IF NOT EXISTS tags_{name}'
            '(song_id INTEGER, tag TEXT, value TEXT, ascii TEXT, dirty BOOLEAN, old_value TEXT)'
            .format(name=name)
        )
        self.connection.execute(
            'CREATE INDEX IF NOT EXISTS tags_{name}_song_id_tag ON tags_{name}'
            '(song_id, tag)'
            .format(name=name)
        )
        self.connection.execute(
            'CREATE INDEX IF NOT EXISTS tags_{name}_tag_value ON tags_{name}'
            '(tag, value)'
            .format(name=name)
        )
        self.connection.execute(
            'CREATE INDEX IF NOT EXISTS tags_{name}_value ON tags_{name}'
            '(value)'
            .format(name=name)
        )
        self.connection.execute(
            'CREATE INDEX IF NOT EXISTS tags_{name}_ascii ON tags_{name}'
            '(ascii)'
            .format(name=name)
        )
        self.connection.execute(
            'CREATE INDEX IF NOT EXISTS tags_{name}_dirty ON tags_{name}'
            '(dirty, song_id)'
            .format(name=name)
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
    def refresh_one_song(self):
        if not self.dir_iterator or not self.dir_iterator.hasNext():
            if not self.queue:
                self.connection.commit()
                self.refresh_finished.emit()
            else:
                self.name, folder = self.queue.pop(0)
                self.create_library_table(self.name)
                self.dir_iterator = QDirIterator(
                    folder, 
                    ['*'+ext for ext in self.musicfile_extensions],
                    QDir.Files | QDir.Readable, 
                    QDirIterator.Subdirectories)
                self.refresh_next.emit()
        else:
            filename = self.dir_iterator.next()
            self.update_song(self.name, filename, commit = False)
            if self.n_in_transaction >= 1000000:
                self.connection.commit()
                self.n_in_transaction = 0
            self.refresh_next.emit()

    def update_song(self, library_name, filename, commit = True):
        if library_name is None:
            return self._cache_file(filename, force = True)
        fileinfo = QFileInfo(filename)
        if not (fileinfo.exists() and fileinfo.isReadable()):
            warn("Cannot read {}".format(filename), RuntimeWarning)
            return
        try:
            audiofile = mutagen.File(filename, easy = True)
            assert(audiofile is not None)
        except:
            warn("Cannot read {}. Probably not an audio file".format(filename), RuntimeWarning)
            return
        cursor = self.connection.cursor()
        cursor.execute(
            'SELECT song_id,mtime,filesize FROM files_{} WHERE filename=?'
            .format(library_name),
            (filename,)
        )
        song = cursor.fetchone()
        if song:
            song_id,mtime,filesize = song
            if mtime is not None and filesize is not None and fileinfo.lastModified().toTime_t() <= mtime and fileinfo.size() == filesize:
                return
            cursor.execute(
                'UPDATE files_{name} '
                'SET mtime=?, filesize=? '
                'WHERE song_id=?'
                .format(name=library_name),
                (fileinfo.lastModified().toTime_t(), fileinfo.size(), song_id)
            )
        else:
            cursor.execute(
                'INSERT INTO files_{name} (filename, mtime, filesize) VALUES(?,?,?)'
                .format(name = library_name),
                (filename, fileinfo.lastModified().toTime_t(), fileinfo.size())
            )
            song_id = cursor.lastrowid
        filedir = fileinfo.absolutePath()
        for d in config.library_folders[library_name]:
            if filedir.startswith(d):
                filedir = filedir[len(d):].lstrip('/')
                break
        # todo: 3-point diff: old_values, new_values, file
        cursor.execute('DELETE FROM tags_{} WHERE song_id=?'.format(library_name), (song_id,))
        cursor.executemany(
            'INSERT INTO tags_{name} (song_id, tag, value, ascii) VALUES (?,?,?,?)'
            .format(name = library_name),
            ( (song_id, tag, value, unidecode.unidecode(value).lower() if isinstance(value, str) else value) 
              for tag, values in itertools.chain(
                      audiofile.tags.items() if audiofile.tags is not None else {}.items(), iter((
                          ('_filename', (fileinfo.fileName(),)),
                          ('_dir', (filedir,)),
                          ('_length', (audiofile.info.length,)),
                          ('_bitrate', (audiofile.info.bitrate,)),
                          ('_sample_rate', (audiofile.info.sample_rate,)),
                          #('_channels', (audiofile.channels,)),
                      )))
              for value in values )
        )
        if commit:
            self.connection.commit()

    def _cache_file(self, filename, force = False):
        if force or filename not in self._cache:
            try:
                audiofile = mutagen.File(filename, easy = True)
                tags = audiofile.tags
                tags['_filename'] = [os.path.basename(filename)]
                tags['_length'] = [audiofile.info.length]
                tags['_bitrate'] = [audiofile.info.bitrate]
                tags['_sample_rate'] = [audiofile.info.sample_rate]
                tags['_sample_rate'] = [audiofile.info.sample_rate]
                #tags['_channels'] = [audiofile.channels]
                #self._cache[filename] = _strip(tags)
            except OSError:
                self._cache[filename] = None

    def tags_by_song_id(self, name, song_id, internal = True):
        cursor = self.connection.execute(
            'SELECT tag, value FROM tags_{} WHERE song_id=? AND substr(tag,1,1)!="_" ORDER BY rowid'
            .format(name),
            (song_id,)
        )
        tags = {}
        for row in cursor.fetchall():
            if row[0] not in tags:
                tags[row[0]] = [row[1]]
            else:
                tags[row[0]].append(row[1])
        return tags

    def tag_by_song_id(self, name, key, song_id):
        cursor = self.connection.execute(
            'SELECT value FROM tags_{} WHERE song_id=? AND tag=? ORDER BY rowid'
            .format(name),
            (song_id, key)
        )
        return list(row[0] for row in cursor.fetchall() )

    def tag_old_value_by_song_id(self, name, key, song_id):
        cursor = self.connection.execute(
            'SELECT old_value FROM tags_{} WHERE song_id=? AND tag=? ORDER BY rowid'
            .format(name),
            (song_id, key)
        )
        return list(row[0] for row in cursor.fetchall() )

    def tags_by_filename(self, filename):
        self._cache_file(filename)
        return self._cache[filename]

    def tag_by_filename(self, key, filename):
        self._cache_file(filename)
        try:
            return self._cache[filename][key]
        except:
            return None
        
    def filename_by_song_id(self, name, song_id):
        row = self.connection.execute(
            'SELECT filename FROM files_{} WHERE song_id=?'
            .format(name),
            (song_id,)
        ).fetchone()
        return row[0] if row else None

    def library_name_and_song_id_from_filename(self, filename, library_name = None):
        for ln in ((library_name,) if library_name else config.library_folders):
            row = self.connection.execute(
                'SELECT song_id FROM files_{} WHERE filename=?'
                .format(ln),
                (filename,)
            ).fetchone()
            if row:
                return ln, row[0]
        return None, None

    def dirty(self, library_name, song_id, tag, get_old_value = False):
        row = self.connection.execute('SELECT dirty, old_value FROM tags_{} WHERE song_id=? and tag=?'.format(library_name), (song_id, tag)).fetchone()
        if get_old_value:
            return (bool(row[0]), row[1]) if row else (False, None)
        else:
            return bool(row[0]) if row else False

    def set_tag(self, library_name, song_id, tag, value, n = 0, commit = True):
        # n = nth occurrenct of song_id, tag in tags_{library_name}, first = 0
        rows = self.connection.execute('SELECT rowid, dirty, value, old_value FROM tags_{} WHERE song_id=? and tag=?'.format(library_name), (song_id, tag)).fetchall()
        if rows:
            rowid, dirty, old_value, original_value = rows[n]
            if not dirty and old_value == value:
                pass
            elif not dirty:
                self.connection.execute('UPDATE tags_{} SET value=?, ascii=?, dirty=1, old_value=? WHERE rowid=?'.format(library_name), (value, unidecode.unidecode(value).lower() if isinstance(value, str) else value, old_value, rowid))
            elif original_value == value:
                self.connection.execute('UPDATE tags_{} SET value=?, ascii=?, dirty=0, old_value=NULL WHERE rowid=?'.format(library_name), (value, unidecode.unidecode(value).lower() if isinstance(value, str) else value, rowid))
            else:
                self.connection.execute('UPDATE tags_{} SET value=?, ascii=? WHERE rowid=?'.format(library_name), (value, unidecode.unidecode(value).lower() if isinstance(value, str) else value, rowid))
        else:
            self.connection.execute('INSERT INTO tags_{} (song_id, tag, value, ascii, dirty) VALUES (?,?,?,?,1)'.format(library_name), (song_id, tag, value, unidecode.unidecode(value).lower() if isinstance(value, str) else value))
        if commit:
            self.connection.commit()
        # todo: update views
        
    def save_changed_tags(self):
        for library_name in config.library_folders.keys():
            for song_id, filename, mtime, filesize in self.connection.execute('SELECT DISTINCT song_id, filename, mtime, filesize FROM tags_{} NATURAL JOIN files_{} WHERE dirty=1'.format(library_name, library_name)):
                fileinfo = QFileInfo(filename)
                if fileinfo.lastModified().toTime_t() <= mtime and fileinfo.size() == filesize:
                    audiofile = mutagen.File(filename, easy = True)
                    for t in list(audiofile.keys()):
                        del audiofile[t]
                    audiofile.update(self.tags_by_song_id(library_name, song_id, internal = False))
                    audiofile.save()
                    self.connection.execute('DELETE FROM tags_{} WHERE song_id=? AND dirty=1 AND value=NULL'.format(library_name), (song_id,))
                    self.connection.execute('UPDATE tags_{} SET dirty=0, old_value=NULL WHERE song_id=? AND dirty=1'.format(library_name), (song_id,))
                    fileinfo = QFileInfo(filename)
                    self.connection.execute('UPDATE files_{} SET mtime=?, filesize=? WHERE song_id=?'.format(library_name), (fileinfo.lastModified().toTime_t(), fileinfo.size(), song_id))
                    self.connection.commit()

    def _build_join(self, table_alias_list):
        return "{} AS {} {}".format(
            table_alias_list[0][0], table_alias_list[0][1],
            " ".join("INNER JOIN {} AS {} USING(song_id)".format(t,a) for t,a in table_alias_list[1:])
        )

    def _build_query_statement(self, name, fixed_tags, filter_words):
        def tables():
            if not (fixed_tags or filter_words):
                yield 'files_' + name, 'files'
            for i in range(len(fixed_tags)):
                yield 'tags_' + name, 'tags_' + str(i)
            for i in range(len(filter_words)):
                yield 'tags_' + name, 'tags_filter_' + str(i)
        join = self._build_join(list(tables()))
        where = " AND ".join(filter(None,(
            " AND ".join(
                "tags_{n}.tag=? AND tags_{n}.value=?".format(n=n)
                if tv[1] is not None else
                'NOT EXISTS (SELECT song_id FROM tags_{} WHERE song_id=tags_{}.song_id AND tag=?)'.format(name, n)
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

    def _query_tags(self, name, tag, fixed_tags, filter_words):
        """Get all values of "tag" of songs having the given fixed tags, and the number of songs for each value.

        "fixed_tags" should be a list of pairs."""
        statement = "SELECT tags.value, COUNT(*) FROM ({}) AS songs " \
                    "LEFT JOIN tags_{} AS tags ON songs.song_id=tags.song_id AND tags.tag=? " \
                    "GROUP BY tags.value" \
                        .format(
                            self._build_query_statement(name, fixed_tags, filter_words),
                            name
                        )
        def params():
            for t,v in fixed_tags:
                yield t
                if v is not None:
                    yield v
            for filter_word in filter_words:
                yield '%' + filter_word + '%'
            yield tag
        return self.connection.execute(statement, list(params()))

    def query_tags_iter(self, name, tag, fixed_tags, filter_words):
        cursor = self._query_tags(name, tag, fixed_tags, filter_words)
        row = cursor.fetchone()
        while row:
            yield row
            row = cursor.fetchone()

    def query_tags_all(self, name, tag, fixed_tags, filter_words):
        cursor = self._query_tags(name, tag, fixed_tags, filter_words)
        return cursor.fetchall()

    def _query_songs(self, name, fixed_tags, filter_words):
        """Get song_ids of songs having the given fixed tags.

        "fixed_tags" should be a list of pairs."""

        def params():
            for t,v in fixed_tags:
                yield t
                if v is not None:
                    yield v
            for filter_word in filter_words:
                yield '%' + filter_word + '%'
        statement = self._build_query_statement(name, fixed_tags, filter_words)
        return self.connection.execute(statement, list(params()))

    def query_songs_iter(self, name, fixed_tags, filter_words):
        cursor = self._query_songs(name, fixed_tags, filter_words)
        row = cursor.fetchone()
        while row:
            yield row[0]
            row = cursor.fetchone()

    def query_songs_all(self, name, fixed_tags, filter_words):
        cursor = self._query_songs(name, fixed_tags, filter_words)
        return [row[0] for row in cursor.fetchall()]

    bg_queries_done = pyqtSignal(BgQueries)
    def bg_queries(self, queries):
        for query in queries:
            query.result = query.method.__get__(self)(*query.args)
        self.bg_queries_done.emit(queries)

library = Library()

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

class FileInfo:
    reason_NewPlayTreeFile = 1
    def __init__(self, filename, reason):
        self.filename = filename
        self.reason = reason

class FileReaderWorker(QObject):
    file_reading_done = pyqtSignal(FileInfo)
    def get_fileinfo(self, fileinfo):
        fileinfo.tags = {}
        try:
            audiofile = mutagen.File(fileinfo.filename, easy = True)
            fileinfo.tags = audiofile.tags
            fileinfo.tags['_filename'] = [os.path.basename(fileinfo.filename)]
            fileinfo.tags['_length'] = [audiofile.info.length]
            fileinfo.tags['_bitrate'] = [audiofile.info.bitrate]
            fileinfo.tags['_sample_rate'] = [audiofile.info.sample_rate]
            #fileinfo.tags['_channels'] = [audiofile.channels]
        except:
            fileinfo.tags = None
        self.file_reading_done.emit(fileinfo)

class FileReader(QObject):
    def __init__(self):
        super().__init__()
        self.bg_thread = QThread()
        app.aboutToQuit.connect(self.bg_thread.exit)
        self.worker = FileReaderWorker()
        self.worker.moveToThread(self.bg_thread)
        self.start_reading_file.connect(self.worker.get_fileinfo)
        self.worker.file_reading_done.connect(self.process_fileinfo)
        self.queue = []
        self.processing = False
        self.tags = {}
        self.playtreefiles = collections.defaultdict(lambda: weakref.WeakSet())
        self.bg_thread.start()

    def bg_get_fileinfo(self, empty_fileinfo):
        self.queue.append(empty_fileinfo)
        self.do()

    start_reading_file = pyqtSignal(FileInfo)
    def do(self):
        if not self.processing:
            while self.queue:
                empty_fileinfo = self.queue.pop(0)
                if empty_fileinfo.reason == FileInfo.reason_NewPlayTreeFile \
                   and empty_fileinfo.filename in self.tags:
                    continue
                self.processing = True
                self.start_reading_file.emit(empty_fileinfo)
                break

    def process_fileinfo(self, fileinfo):
        self.processing = False
        #self.tags[fileinfo.filename] = _strip(fileinfo.tags) if fileinfo.tags else None
        self.tags[fileinfo.filename] = fileinfo.tags
        for file_item in self.playtreefiles[fileinfo.filename]:
            file_item.refresh_models()
        self.do()
                        
    def register_file(self, filename, file_item):
        self.playtreefiles[filename].add(file_item)

    def have_tags(self, filename):
        return filename in self.tags

    def get_tags(self, filename):
        return self.tags[filename] if filename in self.tags else collections.defaultdict(lambda: [])

    def get_tag(self, filename, tag):
        try:
            return self.tags[filename][tag]
        except:
            return []

    def not_an_audio_file(self, filename):
        return filename in self.tags and self.tags[filename] is None

file_reader = FileReader()


for library_name in config.library_folders.keys():
    library.create_library_table(library_name)

#fs_watcher = QFileSystemWatcher(app)
#fs_watcher.directoryChanged.connect(lambda path: print('dir changed', path))
#fs_watcher.fileChanged.connect(lambda path: print('file changed', path))
#for folders in config.library_folders.values():
#    for folder in folders:
#        fs_watcher.addPath(folder)
#        continue
#        for dirpath, dirnames, filenames in os.walk(folder):
#            dirs = [os.path.join(dirpath,dirname) for dirname in dirnames]
#            if dirs:
#                fs_watcher.addPaths(dirs)
#            files = [os.path.join(dirpath,filename) for filename in filenames]
#            if files:
#                fs_watcher.addPaths(files)
#print(len(fs_watcher.directories()), len(fs_watcher.files()))
