from IPython import embed; from PyQt5.QtCore import pyqtRemoveInputHook
from PyQt5.Qt import *   # todo: import only what you need

import taglib
import sqlite3
import os, os.path
from warnings import warn
import functools, itertools, collections, weakref

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
        assert not [query for query in iterable if not isinstance(query, ByQuery)]
        self.callback = callback
        self.relevant = relevant
    
class Library(QObject):
    _cache = {}

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
            '(id INTEGER PRIMARY KEY, filename BLOB, mtime INTEGER, filesize INTEGER)'
            .format(name=name)
        )
        self.connection.execute(
            'CREATE INDEX IF NOT EXISTS files_{name}_filename ON files_{name} (filename)'
            .format(name=name)
        )
        self.connection.execute(
            'CREATE TABLE IF NOT EXISTS tags_{name}'
            '(id INTEGER, tag TEXT, value TEXT)'
            .format(name=name)
        )
        self.connection.execute(
            'CREATE INDEX IF NOT EXISTS tags_{name}_id_tag ON tags_{name}'
            '(id, tag)'
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
        self.connection.commit()

    def refresh(self, name, folders):
        cursor = self.connection.cursor()
        for folder in folders:
            for dirpath, dirnames, filenames in os.walk(folder):
                for fn in filenames:
                    filename = os.path.join(dirpath, fn)
                    if not os.path.isfile(filename):
                        continue
                    try:
                        filestat = os.stat(filename)
                    except:
                        warn("Cannot stat {}".format(filename), RuntimeWarning)
                    try:
                        audiofile = taglib.File(filename)
                        assert(audiofile)
                    except:
                        warn("Cannot read {}. Probably not an audio file".format(filename), RuntimeWarning)
                        continue
                    print(filename)
                    cursor.execute(
                        'SELECT id FROM files_{name} WHERE filename=?'
                        .format(name=name),
                        (filename,)
                    )
                    song = cursor.fetchone()
                    if song:
                        song_id = song[0]
                        cursor.execute(
                            'DELETE FROM tags_{name} WHERE id=?'
                            .format(name = name),
                            (song_id,)
                        )
                    else:
                        cursor.execute(
                            'INSERT INTO files_{name} (filename) VALUES(?)'
                            .format(name = name),
                            (filename,)
                        )
                        song_id = cursor.lastrowid
                    
                    cursor.executemany(
                        'INSERT INTO tags_{name} (id, tag, value) VALUES (?,?,?)'
                        .format(name = name),
                        ( (song_id, tag, value) 
                          for tag, values in audiofile.tags.items() 
                          for value in values )
                    )
                    self.connection.commit()

    def _cache_file(self, filename):
        if filename not in self._cache:
            try:
                audiofile = taglib.File(filename)
                tags = audiofile.tags
                self._cache[filename] = _strip(tags)
            except OSError:
                self._cache[filename] = None

    def tags_by_id(self, name, Id):
        cursor = self.connection.execute(
            'SELECT tag, value FROM tags_{} WHERE id=?'
            .format(name),
            (Id,)
        )
        # todo: multiple values
        tags = dict( (row[0], row[1]) for row in cursor.fetchall() )
        return tags

    def tag_by_id(self, name, key, Id):
        cursor = self.connection.execute(
            'SELECT value FROM tags_{} WHERE id=? AND tag=?'
            .format(name),
            (Id, key)
        )
        values = list(row[0] for row in cursor.fetchall() )
        if len(values):
            return values[0] if len(values) == 1 else values

    def tags_by_filename(self, filename):
        self._cache_file(filename)
        return self._cache[filename]

    def tag_by_filename(self, key, filename):
        self._cache_file(filename)
        try:
            return self._cache[filename][key]
        except KeyError:
            return None
        
    def filename_by_id(self, name, Id):
        row = self.connection.execute(
            'SELECT filename FROM files_{} WHERE id=?'
            .format(name),
            (Id,)
        ).fetchone()
        return row[0] if row else None

    def _build_join(self, table_alias_list):
        return "{} AS {} {}".format(
            table_alias_list[0][0], table_alias_list[0][1],
            " ".join("INNER JOIN {} AS {} USING(id)".format(t,a) for t,a in table_alias_list[1:])
        )

    def _build_query_statement(self, name, fixed_tags, filter_string):
        def tables():
            if not (fixed_tags or filter_string):
                yield 'files_' + name, 'files'
            for i in range(len(fixed_tags)):
                yield 'tags_' + name, 'tags_' + str(i)
            if filter_string:
                yield 'tags_' + name, 'tags_filter'
        join = self._build_join(list(tables()))
        where = " AND ".join(filter(None,(
            " AND ".join(
                "tags_{n}.tag=? AND tags_{n}.value=?".format(n=n)
                if tv[1] is not None else
                'NOT EXISTS (SELECT id FROM tags_{} WHERE id=tags_{}.id AND tag=?)'.format(name, n)
                for n,tv in enumerate(fixed_tags)
            ),
            "tags_filter.value LIKE ?" if filter_string else ""
        )))
        statement = 'SELECT DISTINCT {} FROM {} {} {}' \
            .format(
                'tags_0.id' if fixed_tags else ('tags_filter.id' if filter_string else 'files.id'),
                join, 
                'WHERE' if where else '', 
                where)
        return statement

    def _query_tags(self, name, tag, fixed_tags, filter_string):
        """Get all values of "tag" of songs having the given fixed tags, and the number of songs for each value.

        "fixed_tags" should be a list of pairs."""
        statement = "SELECT tags.value, COUNT(*) FROM ({}) AS songs " \
                    "LEFT JOIN tags_{} AS tags ON songs.id=tags.id AND tags.tag=? " \
                    "GROUP BY tags.value" \
                        .format(
                            self._build_query_statement(name, fixed_tags, filter_string),
                            name
                        )
        def params():
            for t,v in fixed_tags:
                yield t
                if v is not None:
                    yield v
            if filter_string:
                yield '%' + filter_string + '%'
            yield tag
        return self.connection.execute(statement, list(params()))

    def query_tags_iter(self, name, tag, fixed_tags, filter_string):
        cursor = self._query_tags(name, tag, fixed_tags, filter_string)
        row = cursor.fetchone()
        while row:
            yield row
            row = cursor.fetchone()

    def query_tags_all(self, name, tag, fixed_tags, filter_string):
        cursor = self._query_tags(name, tag, fixed_tags, filter_string)
        return cursor.fetchall()

    def _query_songs(self, name, fixed_tags, filter_string):
        """Get ids of songs having the given fixed tags.

        "fixed_tags" should be a list of pairs."""

        def params():
            for t,v in fixed_tags:
                yield t
                if v is not None:
                    yield v
            if filter_string:
                yield '%' + filter_string + '%'
        statement = self._build_query_statement(name, fixed_tags, filter_string)
        return self.connection.execute(statement, list(params()))

    def query_songs_iter(self, name, fixed_tags, filter_string):
        cursor = self._query_songs(name, fixed_tags, filter_string)
        row = cursor.fetchone()
        while row:
            yield row[0]
            row = cursor.fetchone()

    def query_songs_all(self, name, fixed_tags, filter_string):
        cursor = self._query_songs(name, fixed_tags, filter_string)
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
        if queries.relevant():
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
            audiofile = taglib.File(fileinfo.filename)
            fileinfo.tags = audiofile.tags
        except:
            fileinfo.tags = None
        self.file_reading_done.emit(fileinfo)

class FileReader(QObject):
    def __init__(self):
        super().__init__()
        self.bg_thread = QThread()
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
        self.tags[fileinfo.filename] = _strip(fileinfo.tags) if fileinfo.tags else None
        for file_item in self.playtreefiles[fileinfo.filename]:
            for model, children in file_item.parent.children.items():
                if model and file_item in children:
                    file_index = file_item.index(model)
                    model.dataChanged.emit(
                        file_index,
                        model.sibling(
                            file_index.row(), 
                            model.columnCount(file_index), 
                            file_index),
                        [Qt.DisplayRole, Qt.DecorationRole, Qt.EditRole, 
                        Qt.ToolTipRole, Qt.StatusTipRole, 
                        Qt.WhatsThisRole, Qt.SizeHintRole]
                    )
        self.do()
                        
    def register_file(self, filename, file_item):
        self.playtreefiles[filename].add(file_item)

    def get_tags(self, filename):
        return self.tags[filename] if filename in self.tags else collections.defaultdict(lambda: '')

    def get_tag(self, filename, tag):
        return self.tags[filename][tag] if filename in self.tags else None

file_reader = FileReader()

