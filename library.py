#from IPython import embed

import taglib
import sqlite3
import os, os.path
from warnings import warn
import functools

def _strip(tags):
    """Pulls single list items out of lists."""
    return dict((t,v[0] if isinstance(v,list) and len(v)==1 else v) for t,v in tags.items())

@functools.lru_cache(maxsize = None)
class Library:
    filename = 'tandamaster.db'
    _cache = {}

    def __init__(self, name = None):
        super().__init__()
        self.name = name
        self.connection = sqlite3.connect(self.filename)
        self.connection.execute(
            'CREATE TABLE IF NOT EXISTS files_{name}'
            '(id INTEGER PRIMARY KEY, filename BLOB, mtime INTEGER, filesize INTEGER)'
            .format(name=self.name)
        )
        self.connection.execute(
            'CREATE INDEX IF NOT EXISTS files_{name}_filename ON files_{name} (filename)'
            .format(name=self.name)
        )
        self.connection.execute(
            'CREATE TABLE IF NOT EXISTS tags_{name}'
            '(id INTEGER, tag TEXT, value TEXT)'
            .format(name=self.name)
        )
        self.connection.execute(
            'CREATE INDEX IF NOT EXISTS tags_{name}_id_tag ON tags_{name}'
            '(id, tag)'
            .format(name=self.name)
        )
        self.connection.execute(
            'CREATE INDEX IF NOT EXISTS tags_{name}_tag_value ON tags_{name}'
            '(tag, value)'
            .format(name=self.name)
        )
        self.connection.execute(
            'CREATE INDEX IF NOT EXISTS tags_{name}_value ON tags_{name}'
            '(value)'
            .format(name=self.name)
        )
        self.connection.commit()

    def refresh(self, folders):
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
                    print(filename)
                    cursor.execute(
                        'SELECT id FROM files_{name} WHERE filename=?'
                        .format(name=self.name),
                        (filename,)
                    )
                    song = cursor.fetchone()
                    if song:
                        song_id = song[0]
                        cursor.execute(
                            'DELETE FROM tags_{name} WHERE id=?'
                            .format(name = self.name),
                            (song_id,)
                        )
                    else:
                        cursor.execute(
                            'INSERT INTO files_{name} (filename) VALUES(?)'
                            .format(name = self.name),
                            (filename,)
                        )
                        song_id = cursor.lastrowid
                    
                    cursor.executemany(
                        'INSERT INTO tags_{name} (id, tag, value) VALUES (?,?,?)'
                        .format(name = self.name),
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

    def tags_by_id(self, Id):
        assert self.name
        cursor = self.connection.execute(
            'SELECT tag, value FROM tags_{} WHERE id=?'
            .format(self.name),
            (Id,)
        )
        # todo: multiple values
        tags = dict( (row[0], row[1]) for row in cursor.fetchall() )
        return tags

    def tag_by_id(self, key, Id):
        assert self.name
        cursor = self.connection.execute(
            'SELECT value FROM tags_{} WHERE id=? AND tag=?'
            .format(self.name),
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
        
    def filename_by_id(self, Id):
        row = self.connection.execute(
            'SELECT filename FROM files_{} WHERE id=?'
            .format(self.name),
            (Id,)
        ).fetchone()
        return row[0] if row else None
        
