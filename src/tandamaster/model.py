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

#from PyQt5.QtCore import pyqtRemoveInputHook; from IPython import embed; pyqtRemoveInputHook()
import traceback

import threading

import sys, filecmp, os, datetime, copy, collections

#from lxml import etree
import xml.etree.ElementTree as etree
from PyQt5.Qt import *   # todo: import only what you need

from .util import *
from .library import *
from .app import *
from .commands import *

import bidict, shlex
import functools

from gi.repository import Gst

def register_xml_tag_handler(tag):
    def f(cls):
        PlayTreeItem.xml_tag_registry[tag] = cls
        cls.xml_tag = tag
        return cls
    return f

import weakref
class PlayTreeItem:
    weakrefs = weakref.WeakSet() # for debugging memory leaks

    max_id = 0
    xml_tag_registry = {}
    @classmethod
    def create_from_xml(cls, element, parent = None):
        return cls.xml_tag_registry[element.tag]._create_from_xml(element, parent)

    def to_xml(self):
        if self.Id:
            return etree.Element(self.xml_tag, id = str(self.Id))
        else:
            return etree.Element(self.xml_tag)

    @classmethod
    def create_from_url(cls, url, parent = None, url_is_local_filename = False):
        filename = url if url_is_local_filename else url.toLocalFile()
        fileinfo = QFileInfo(filename)
        if fileinfo.isDir():
            return PlayTreeFolder(filename, parent = parent)
        else:
            return PlayTreeFile(filename = filename, parent = parent)

    def save(self, filename):
        document = etree.ElementTree(self.to_xml())
        with open_autobackup(filename, 'w', encoding = 'utf-8') as outfile:
            document.write(outfile, encoding='unicode')

    def __init__(self, Id = None, parent = None):
        super().__init__()
        if Id is None:
            self._Id = None
        else:
            self._Id = int(Id)
            PlayTreeItem.max_id = max(PlayTreeItem.max_id, self._Id)
        self.parent = parent
        self.expanded = {}
        PlayTreeItem.weakrefs.add(self)

    @property
    def Id(self):
        if self._Id is None:
            PlayTreeItem.max_id += 1
            self._Id = PlayTreeItem.max_id
        return self._Id

    isTerminal = False
    are_children_manually_set = False

    def row(self, model):
        return self.parent.childs_row(model, self) if self.parent is not None else 0

    def index(self, model, column = 0):
        try:
            return QModelIndex() if self == model.root_item or self.parent is None else model.createIndex(self.row(model), column, self)
        except:
            return QModelIndex()

    def path(self, model):
        if self.parent:
            return self.parent.path(model) + (self.parent.childs_row(model, self),)
        else:
            return tuple()

    @property
    def isPlayable(self):
        return False

    def filter(self, model, filter_expr):
        raise RunTimeError

    def _copy_children(self, model_from, model_to):
        """Recursively copy children from model_from to model_to.
        
        Stop recursion when model_to is not a key in children.  This deals with PlayTreeBrowses, which fill model_from directly."""

        if self.unpopulated(model_from):
            self.unpopulate(model_to)
        else:
            self.children[model_to] = self.children[model_from]
            del self.children[model_from]
        if 'value' in self.__dict__ and isinstance(self.value, dict) and model_from in self.value: # za browse
            self.value[model_to] = self.value[model_from]
            del self.value[model_from]
        if 'song_count' in self.__dict__ and model_from in self.song_count: # za browse
            self.song_count[model_to] = self.song_count[model_from]
            del self.song_count[model_from]
        if self.have_children(model_to):
            for child in self.children[model_to]:
                child._copy_children(model_from, model_to)
    
    def iter(self, model, condition_yield, condition_propagate):
        if condition_yield(self):
            yield self
        if self.have_children(model) and condition_propagate(self):
            for i in range(self.rowCount(model)):
                for item in self.child(model, i).iter(model, condition_yield, condition_propagate):
                    yield item

    def populate(self, model, force = False, recursive = False, filter_expr = None):
        pass

    def delete(self, items):
        raise RuntimeError

    def __str__(self):
        return 'playtreeitem'

    def column_to_tag(self, model, column):
        return model.columns[column]
    
    def flags(self, model, column):
        tag = self.column_to_tag(model, column)
        return Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEnabled | (Qt.ItemIsEditable if tag and tag[0] != '_' else 0)

    duration_mode_all = 0
    duration_mode_cortinas = 1

    def function(self):
        return None

    def iter_depth(self, model, condition_yield, condition_propagate):
        if condition_yield(self):
            yield(self)
        if condition_propagate(self) and self.have_children(model):
            for child in self.children[model]:
                for item in child.iter_depth(model, condition_yield, condition_propagate):
                    yield item

    def setData(self, model, tag, value):
        if tag:
            EditTagsCommand(model, [self], tag, value, only_first = True)
            return True
        return False

    def duration(self, model, mode = duration_mode_all, populate = False):
        if populate:
            self.populate(model)
        d = 0
        if self.unpopulated(model):
            return None
        for child in self.children[model]:
            cd = child.duration(model, mode, populate = populate)
            if cd is None:
                return None
            d += cd
        return d

    def populated(self, model):
        try:
            return isinstance(self.children[model], list)
        except:
            return False
    def unpopulated(self, model):
        return not self.populated(model)
    def unpopulate(self, model):
        try:
            del self.children[model]
        except:
            pass
    def have_children(self, model):
        try:
            return self.populated(model) and bool(self.children[model])
        except:
            return False
    def all_children_wanted(self, model):
        try:
            return self.children[model] is None
        except:
            return False
    def want_all_children(self, model):
        self.children[model] = None



@register_xml_tag_handler('list')
class PlayTreeList(PlayTreeItem):

    @classmethod
    def _create_from_xml(cls, element, parent):
        item = cls(name = element.get('name'), Id = element.get('id'), parent = parent)
        for subelement in element:
            item.children[None].append(PlayTreeItem.create_from_xml(subelement, item))
        return item

    def to_xml(self):
        element = super().to_xml()
        if self.name is not None:
            element.set('name', self.name)
        for child in self.children[None]:
            element.append(child.to_xml())
        return element

    def __init__(self, name, Id = None, parent = None, *iterable):
        super().__init__(Id, parent)
        self.name = name
        self.children = {None: list(*iterable)}
        
    def copy(self, parent = None):
        copy = PlayTreeList(self.name, parent = parent)
        copy.children = {None: [child.copy(parent = copy) for child in self.children[None]]}
        return copy

    are_children_manually_set = True

    def __repr__(self):
        return '{}({},id={},name={})'.format(type(self).__name__, id(self), self.Id, self.name)

    def rowCount(self, model):
        self.populate(model)
        return len(self.children[model])

    def hasChildren(self, model):
        if self.unpopulated(model):
            return True
        else:
            return bool(self.children[model])

    def child(self, model, row):
        self.populate(model)
        return self.children[model][row]

    def childs_row(self, model, child):
        self.populate(model)
        return self.children[model].index(child)

    def __str__(self):
        return self.name if self.name is not None else ''

    def column_to_tag(self, model, column):
        return '@name' if column == 0 else super().column_to_tag(model, column)
    
    def data(self, model, tag, role):
        if role in (Qt.DisplayRole, Qt.EditRole):
            if tag == '_length':
                duration = self.duration(model)
                return hmsms_to_text(*ms_to_hmsms(1000*duration), include_ms=False) if duration is not None else duration
            elif tag == '@name':
                return str(self)
            else:
                first = True
                for child in self.children[None]:
                    if not child.isPlayable:
                        return
                    child_data = child.data(model, tag, role)
                    if first:
                        data = child_data
                        first = False
                    elif child_data != data:
                        return
                return data if not first else None
        elif tag == '@name' and role == Qt.DecorationRole:
            return MyIcon('iconfinder/silk/list.png')

    def populate(self, model, force = False, recursive = False, filter_expr = None):
        filter_expr = filter_expr if filter_expr or not model else model.filter_expr
        if force or self.unpopulated(model):
            self.children[model] = [
                child for child in self.children[None]
                if not isinstance(child, PlayTreeFile) or child.filter(model, model.filter_expr)
            ]
        if recursive:
            for child in self.children[model]:
                child.populate(model, force = force, recursive = recursive)

    def filter(self, model, filter_expr):
        if not filter_expr:
            self.unpopulate(model)
            for child in self.children[None]:
                child.filter(model, None)
            return self
        self.children[(model, 'f')] = []
        filtered_children = self.children[(model, 'f')]
        for child in self.children[None]:
            filtered = child.filter(model, filter_expr)
            if filtered:
                filtered_children.append(filtered)
        if filtered_children:
            return self
        elif all(filter_word in self.name.lower() for filter_word in filter_expr):
            self.want_all_children( (model, 'f') )
            return self
        else:
            return None

    def iter_width(self, model, condition_yield, condition_propagate):
        items = [self]
        while items:
            item = items.pop(0)
            if condition_yield(item):
                yield item
            if condition_propagate(item):
                item.populate(model)
                items.extend(item.children[model])


    def insert(self, new_items, row):
        children = self.children[None]
        if row is None:
            row = len(children)
        for model in self.children.keys():
            if isinstance(model, PlayTreeModel): # ignore (..., 'f')
                parent_index = self.index(model)
                #model_new_items = [item for item in new_items
                #                   if item.filter(model)]
                model_new_items = new_items # show all new items
                model_children = self.children[model]
                target_i = len(model_children)
                for child in children[row:]:
                    if child in model_children:
                        target_i = model_children.index(child)
                        break
                model.beginInsertRows(parent_index, target_i, target_i + len(model_new_items) - 1)
                model_children[target_i:target_i] = model_new_items
                model.endInsertRows()
        children[row:row] = new_items
        for item in new_items:
            item.parent = self

    def delete(self, items):
        for model, children in self.children.items():
            rows = sorted([children.index(item) for item in items
                           if item in children  # because there were problems with (..., 'f')
            ])
            row_ranges = integers_to_ranges(rows)
            for range in row_ranges:
                if model:
                    model.beginRemoveRows(self.index(model), range[0], range[1]-1)
                del children[range[0]:range[1]]
                if model:
                    model.endRemoveRows()
        for item in items:
            item.parent = None
            
    def dropMimeData(self, mime_data, action, row, command_prefix = 'Drop'):
        new_items = None
        if isinstance(mime_data, PlayTreeMimeData):
            source_items = mime_data.items
            if action == Qt.MoveAction:
                new_items = source_items
            else:
                new_items = [item.copy() for item in source_items]
        elif mime_data.hasFormat('audio/x-mpegurl'):
            new_items = [
                PlayTreeItem.create_from_url(filename, parent = self, url_is_local_filename = True)
                for filename in mime_data.text().split("\n")
            ]
        elif mime_data.hasUrls():
            new_items = [
                PlayTreeItem.create_from_url(url, parent = self)
                for url in mime_data.urls()
                if url.isLocalFile()
            ]
        if new_items:
            if action == Qt.MoveAction:
                if row == -1:
                    before_item = None
                else:
                    before_item = self.child(None, row)
                    n = self.rowCount(None)
                    while before_item in new_items:
                        row += 1
                        if row < n:
                            before_item = self.child(None, row)
                        else:
                            before_item = None
                            break
                MovePlayTreeItemsCommand(
                    new_items, self, before_item)
            else:
                InsertPlayTreeItemsCommand(
                    new_items, self, None if row == -1 else self.child(None, row), 
                    command_prefix = command_prefix)
        return new_items
        
    def flags(self, model, column):
        return super().flags(model, column) | Qt.ItemIsDropEnabled

    def setData(self, model, tag, value):
        if tag == '@name':
            EditPlayTreeNameCommand(self, value)
            return True
        else:
            return super().setData(model, tag, value)


@register_xml_tag_handler('file')
class PlayTreeFile(PlayTreeItem):
    isTerminal = True

    def to_xml(self):
        element = super().to_xml()
        element.set('filename', self.filename)
        return element

    @classmethod
    def _create_from_xml(cls, element, parent):
        return PlayTreeFile(
            element.get('filename'),
            Id = element.get('id'),
            parent = parent
        )

    def __init__(self, filename = None, song_id = None, Id = None, parent = None):
        super().__init__(Id, parent)
        assert song_id is not None or filename is not None
        self._song_id = song_id
        self._filename = filename
        self._querying = False
        self.unavailable = False
        
    def got_song_id(self, queries):
        self._querying = False
        if queries[0].result:
            self._song_id = queries[0].result
        else:
            self.unavailable = True
        self.refresh_models()

    @property
    def song_id(self):
        if self._song_id is None and not self.unavailable:
            self._song_id = library().song_id_from_filename(self._filename)
            if not self._song_id:
                if not self._querying:
                    self._querying = True
                    librarian.bg_queries(BgQueries([BgQuery(Library.update_song_from_file, (None, self._filename))], self.got_song_id, relevant = lambda: True))
        return self._song_id

    @property
    def filename(self):
        if self._filename is None:
            self._filename = library().filename_by_song_id(self._song_id)
        return self._filename
        
    @property
    def Id(self):
        return None

    children = {}
    
    def copy(self, parent = None):
        return PlayTreeFile(self.filename, song_id = self.song_id, parent = parent)

    def get_tag(self, tag, only_first = False, default = None):
        values = library().tag_by_song_id(tag, self.song_id)
        if values:
            return values[0] if only_first else values
        else:
            return default

    def get_tags(self, only_first = False):
        tags = library().tags_by_song_id(self.song_id)
        if only_first:
            for tag, value in tags.items():
                tags[tag] = value[0]
        return tags
        
    def set_tag(self, tag, value):
        library().set_tag(self.song_id, tag, value)

    def __repr__(self):
        return '{}({},{},song_id {})'.format(type(self).__name__, id(self), self.filename, self.song_id)

    def rowCount(self, model):
        return 0

    def hasChildren(self, model):
        return False

    def child(self, model, row):
        raise RuntimeError

    def __str__(self):
        return os.path.basename(self.filename)

    def function(self):
        if '/tango/' in self.filename:
            return 'tanda'
        genre = self.get_tag('genre', only_first = True)
        return 'tanda' if genre and genre.lower() in ('tango', 'vals', 'milonga') else 'cortina' # todo: configurable

    def childs_row(self, model, child):
        raise RuntimeError

    @property
    def isPlayable(self):
        return True

    def flags(self, model, column):
        return super().flags(model, column) & (~Qt.ItemIsEditable if self.unavailable else ~0)

    def filter(self, model, filter_expr):
        if not filter_expr:
            return self
        if not self.song_id:
            return None
        for row in library().query_songs_iter(
                [], filter_expr, [], [self.song_id]):
            return self
        return None

    def maybe_refresh_models(self, queries):
        if queries[0].result:
            self.refresh_models()
    
    def refresh_models(self):
        for model, children in self.parent.children.items():
            if isinstance(children, list) and model and self in children:
                index = self.index(model)
                model.dataChanged.emit(
                    index,
                    model.sibling(
                        index.row(), 
                        model.columnCount(index), 
                        index),
                    [Qt.DisplayRole, Qt.DecorationRole, Qt.EditRole, 
                    Qt.ToolTipRole, Qt.StatusTipRole, 
                    Qt.WhatsThisRole, Qt.SizeHintRole]
                )

    cortina_duration = 30
    def duration(self, model = None, mode = PlayTreeItem.duration_mode_all, populate = False):
        if mode & self.duration_mode_cortinas and self.function() == 'cortina':
            return self.cortina_duration
        d = self.get_tag('_length', only_first = True)
        return float(d) if d is not None else None

    def data(self, model, tag, role):
        if role in (Qt.DisplayRole, Qt.EditRole):
            if tag == '_length':
                duration = self.duration(model)
                return hmsms_to_text(*ms_to_hmsms(1000*duration), include_ms=False) if duration is not None else duration
            elif tag == 'title':
                value = self.get_tag(tag, only_first = True)
                return value if value else os.path.basename(self.filename)
            elif tag:
                return self.get_tag(tag, only_first = True)
            else:
                return None
        elif role == Qt.DecorationRole and model.tag_to_column(tag) == 0:
            #return tmSongIcon
            #return MyIcon('crazyeye_dance.png')
            if self.function() == 'cortina':
                return MyIcon('iconfinder/farm-fresh/curtain.png')
            else:
                return MyIcon('happy-dance.gif')
        elif role == Qt. BackgroundRole and library().dirty(self.song_id, tag):
            return QBrush(QColor(Qt.yellow))
        elif role == Qt.ToolTipRole and library().dirty(self.song_id, tag):
            orig_values = library().tag_by_song_id(tag, self.song_id, sources = ('file',))
            if orig_values:
                return app.tr('Original value') + ': ' + orig_values[0]
        elif self.unavailable and role == Qt.ForegroundRole:
            return QBrush(QColor(Qt.gray))

    def get_song_begin(self):
        try:
            song_begin = int(float(self.get_tag('tm:song_start')[0])*Gst.SECOND)
        except:
            song_begin = 0
        return song_begin

    def get_song_end(self):
        try:
            song_end = int(float(self.get_tag('tm:song_end')[0])*Gst.SECOND)
        except:
            song_end = None
        return song_end
        
@register_xml_tag_handler('folder')
class PlayTreeFolder(PlayTreeItem):

    def to_xml(self):
        element = super().to_xml()
        element.set('filename', self.filename)
        return element

    @classmethod
    def _create_from_xml(cls, element, parent):
        return cls(filename = element.get('filename'), parent = parent)

    def __init__(self, filename, Id = None, parent = None):
        super().__init__(Id, parent)
        self.filename = os.path.expanduser(filename)
        self.children = {None: None}

    def copy(self, parent = None):
        return PlayTreeFolder(self.filename, parent = parent)

    def __repr__(self):
        return '{}({},{})'.format(type(self).__name__, id(self), self.filename)

    def rowCount(self, model):
        self.populate(model)
        return len(self.children[model])

    def hasChildren(self, model):
        if self.unpopulated(model):
            return True
        else:
            return bool(self.children[model])

    def child(self, model, row):
        self.populate(model)
        return self.children[model][row]

    def childs_row(self, model, child):
        self.populate(model)
        return self.children[model].index(child)

    def __str__(self):
        return os.path.basename(self.filename)

    def flags(self, model, column):
        return super().flags(model, column) & (~Qt.ItemIsEditable if column == 0 else ~0)

    def column_to_tag(self, model, column):
        return '_filename' if column == 0 else super().column_to_tag(model, column)
    
    def data(self, model, tag, role):
        if tag == '_filename':
            if role == Qt.DisplayRole:
                return str(self)
            elif role == Qt.DecorationRole:
                return MyIcon('iconfinder/ionicons/folder.png')

    def populate(self, model, force = False, recursive = False, filter_expr = None):
        filter_expr = filter_expr if filter_expr or not model else model.filter_expr
        if force or self.unpopulated(None):
            folders = []
            files = []
            for fn in os.listdir(self.filename):
                fullfn = os.path.join(self.filename, fn)
                if os.path.isdir(fullfn):
                    folders.append((fn, fullfn))
                else:
                    files.append((fn, fullfn))
            folders.sort()
            files.sort()
            self.children[None] = [
                PlayTreeFolder(filename=fullfn, parent = self) for fn,fullfn in folders
            ]
            for fn,fullfn in files:
                if os.path.splitext(fn)[1] in config.musicfile_extensions:
                    self.children[None].append(
                        PlayTreeFile(filename=fullfn, parent = self))
        if model and self.unpopulated(model):
            self.children[model] = [
                child
                for child in self.children[None]
                if not isinstance(child, PlayTreeFile) or child.filter(model, model.filter_expr)
            ]
            #self.children[model] = self.children[None]
        if recursive:
            for child in self.children[model]:
                child.populate(model, force = force, recursive = recursive)

    def filter(self, model, filter_expr):
        if self.unpopulated(None):
            if all(filter_word in self.filename.lower() for filter_word in filter_expr):
                self.want_all_children(model)
                return self
            else:
                return None
        if not filter_expr:
            self.children[model] = self.children[None]
            return self
        self.children[(model, 'f')] = []
        filtered_children = self.children[(model, 'f')]
        for child in self.children[None]:
            filtered = child.filter(model, filter_expr)
            if filtered:
                filtered_children.append(filtered)
        if filtered_children:
            return self
        elif all(filter_word in self.filename.lower() for filter_word in filter_expr):
            self.want_all_children( (model, 'f') )
            return self
        else:
            return None
        
@register_xml_tag_handler('browse')
class PlayTreeBrowse(PlayTreeItem):
    @classmethod
    def _create_from_xml(cls, element, parent):
        fixed_tags = []
        browse_by_tags = []
        for by in element:
            if by.tag == 'by':
                if by.get('fixed'):
                    fixed_tags.append((by.get('tag'), by.get('value')))
                else:
                    browse_by_tags.append(by.get('tag'))
        # transitory:
        #if not browse_by_tags or browse_by_tags[-1] != 'title':
        #    browse_by_tags.append('title')
        return cls(library_name = element.get('library'), fixed_tags = fixed_tags, browse_by_tags = browse_by_tags, Id = element.get('id'), parent = parent)

    def to_xml(self):
        element = super().to_xml()
        element.set('library', self.library)
        for tag, value in self.fixed_tags:
            by = etree.SubElement(element, 'by', fixed = 'yes', tag = tag)
            if value is not None:
                by.set('value', value)
        for tag in self.browse_by_tags:
            by = etree.SubElement(element, 'by', tag = tag)
        return element

    def __init__(self, library_name, fixed_tags, browse_by_tags, tag = None, Id = None, parent = None):
        super().__init__(Id, parent)
        self.library = library_name
        self.fixed_tags = tuple(fixed_tags)
        self.browse_by_tags = tuple(browse_by_tags)
        self.tag = tag
        self.children = {}
        self.value = {}
        self.song_count = {}

    def copy(self, parent = None):
        return PlayTreeBrowse(self.library, self.fixed_tags, self.browse_by_tags, self.tag, parent = parent)

    def __repr__(self):
        return '{}({},{},fixed={},by={})'.format(type(self).__name__, id(self), self.library, self.fixed_tags, self.browse_by_tags)

    def rowCount(self, model):
        self.populate(model)
        return len(self.children[model])

    def hasChildren(self, model):
        if self.unpopulated(model):
            return True
        else:
            return bool(self.children[model])

    def child(self, model, row):
        self.populate(model)
        return self.children[model][row]

    def childs_row(self, model, child):
        self.populate(model)
        return self.children[model].index(child)

    def __str__(self):
        return " -> ".join([self.library]+[str(v) for t,v in self.fixed_tags])
        # app.tr('Browse') + ' ' + \
        ###
        # + \
            # ' ' + app.tr('by') + ' ' + \
            # ", ".join(tag.lower() for tag in self.browse_by_tags)


    def column_to_tag(self, model, column):
        if column == 0:
            return self.tag if self.tag else '@name'
        else:
            return super().column_to_tag(model, column)
            
    icons = {
        '__browse': 'library.png',
        '__search': 'iconfinder/octicons/search.png',
        'artist': 'personal.png', 
        'album': 'image_album.png'
    }
    def data(self, model, tag, role):
        if tag in (self.tag, '@name'):
            if role in (Qt.DisplayRole, Qt.EditRole):
                #if model in self.song_count:
                #    return (self.value[model] if model in self.value and self.value[model] else '') + \
                #        ' (' + str(self.song_count[model]) + ')'
                if isinstance(self.parent, PlayTreeBrowse):
                    return self.value[model] if model in self.value and self.value[model] else ''
                else:
                    return str(self)
            elif role == Qt.DecorationRole:
                #return app.style().standardIcon(QStyle.SP_DriveCDIcon)
                try:
                    return MyIcon(self.icons[self.tag])
                except:
                    return MyIcon(self.icons['__browse']) if len(self.browse_by_tags) != 1 else MyIcon(self.icons['__search'])

    def setData(self, model, tag, value):
        if tag == self.tag:
            self.populate(model, recursive = True)
            for song in self.iter(model, lambda it: isinstance(it, PlayTreeFile), lambda it: not isinstance(it, PlayTreeFile)):
                song.setData(model, tag, value)
            return True
        return False
                
    def populate(self, model, force = False, recursive = False, filter_expr = None):
        filter_expr = filter_expr if filter_expr or not model else model.filter_expr
        if force:
            self.unpopulate(model)
        if self.unpopulated(model):
            if recursive or len(self.browse_by_tags) == 1:
                self._populate(
                    model,
                    library().query_songs_iter(
                        (('_library', self.library),) + self.fixed_tags,  
                        model.filter_expr,
                        self.browse_by_tags))
            else:
                self._populate(
                    model,
                    library().query_tags_iter(
                        (('_library', self.library),) + self.fixed_tags,
                        model.filter_expr,
                        self.browse_by_tags[0:1]))

    def _populate(self, model, rows):
        self.children[model] = []
        for row in rows:
            cols = list(row[0:(-3 if row[-2] else -2)])
            if cols:
                last_browse = self._populate_create_structure(model, cols)
            else:
                last_browse = self
            if row[-2]:
                song = PlayTreeFile(song_id = row[-2], parent = last_browse)
                song.value = row[-3]
                if model not in last_browse.children or last_browse.children[model] is None:
                    last_browse.children[model] = []
                last_browse.children[model].append(song)

    def _populate_create_structure(self, model, values):
        if not values:
            return self
        value = values.pop(0)
        if self.unpopulated(model):
            self.children[model] = []
        children = self.children[model]
        if len(children) == 0 or not isinstance(children[-1], PlayTreeBrowse) or value != children[-1].value[model]:
            new_browse = PlayTreeBrowse(
                self.library,
                self.fixed_tags + ( (self.browse_by_tags[0], value), ),
                self.browse_by_tags[1:],
                tag = self.browse_by_tags[0],
                parent = self)
            new_browse.value[model] = value
            children.append(new_browse)
        return children[-1]._populate_create_structure(model, values)

    def filter(self, model, filter_expr):
        if not filter_expr:
            self.unpopulate(model)
            return self
        library().query_songs_create_playitems(
            self,
            (model,'f'),
            (('_library', self.library),) + self.fixed_tags,
            filter_expr,
            self.browse_by_tags
        )
        return self if self.have_children( (model,'f') ) else None
    
@register_xml_tag_handler('link')
class PlayTreeLink(PlayTreeItem):
    pass

playtree_xml_filename = locate_file(QStandardPaths.AppDataLocation, 'playtree.xml')
playtree_xml_document = etree.parse(playtree_xml_filename)
playtree_xml = playtree_xml_document.getroot()
playtree = PlayTreeItem.create_from_xml(playtree_xml)

class PlayTreeModel(QAbstractItemModel):

    def __init__(self, root_id = None, parent = None, root_item = None):
        super().__init__(parent)
        self.filter_expr = []
        self.set_root_item(root_id = root_id, root_item = root_item)

    def set_root_item(self, root_item = None, root_id = None):
        if not root_item:
            root_item = playtree
            if root_id:
                root_id = int(root_id)
                for item in playtree.iter_width(None, 
                        lambda item: item.Id == root_id,
                        lambda item: isinstance(item, PlayTreeList)):
                    root_item = item
                    break
        if not root_item.Id:
            PlayTreeItem.max_id += 1
            root_item.Id = PlayTreeItem.max_id
        self.root_item = root_item
        root_item.populate(self)

    def item(self, index, invalid = 'root'):
        return index.internalPointer() if index.isValid() else (self.root_item if invalid == 'root' else invalid)

    # column "" provides browsing info (folder name, file name, ...)
    columns = ('title', 'artist', 'performer:vocals',
               #'quodlibet::recordingdate',
               'date', 'genre', '_length',
               'album', 'albumartist', 'tracknumber', 'comment',
               '_bitrate', '_channels', '_sample_rate',
               'tm:song_start', 'tm:song_end')
    #columns = ('',)

    def tag_to_column(self, tag):
        try:
            return self.columns.index(tag)
        except ValueError:
            return

    column_display_names = bidict.bidict({
        #'': 'Title',
        #'artist': 'Artist',
        #'album': 'Album',
        #'title': 'Title',
        'performer:vocals': 'Singer',
        'quodlibet::recordingdate': 'Year (old)',
        'date': 'Year',
        #'GENRE': 'Genre',
        #'_Length': 'Length',
        'tm:song_start': 'Start of song',
        'tm:song_end': 'End of song',
        'tracknumber': '#',
        '@name': '',
        'albumartist': 'Album artist',
    })

    def index(self, row, column, parent):
        try:
            parentItem = self.item(parent)
            childItem = parentItem.child(self, row)
            assert childItem
            return self.createIndex(row, column, childItem)
        except:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return index
        try:
            item = self.item(index)
            parentItem = item.parent
            return QModelIndex() \
                if parentItem in (None, self.root_item) else \
                self.createIndex(parentItem.row(self), 0, parentItem)
        except:
            return QModelIndex()

    def rowCount(self, parent):
        # why oh why?
        if parent.column() > 0:
            return 0
        parentItem = self.item(parent)
        return parentItem.rowCount(self)

    def hasChildren(self, index):
        return self.item(index).hasChildren(self)

    def columnCount(self, parent):
        return len(self.columns)

    def data(self, index, role = Qt.DisplayRole):
        item = self.item(index)
        return item.data(self, item.column_to_tag(self, index.column()), role)
    
    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            #tag = self.root_item.column_to_tag(self, section)
            tag = self.columns[section]
            return self.column_display_names[tag] if tag in self.column_display_names else tag.strip('_').title()

    def sibling(self, row, column, index):
        return super().sibling(
            index.row() if row is None else row,
            index.column() if column is None else column,
            index
        )
        
    def next(self, index, descend  = True):
        while descend or index.isValid():
            if descend:
                self.item(index).populate(self)
                next_index = self.index(0, 0, index)
            else:
                parent = self.parent(index)
                next_index = self.index(index.row()+1, 0, parent)
            if next_index.isValid():
                return next_index
            else:
                if not descend:
                    index = parent
                descend = False
        return index

    def next_song(self, index):
        index = self.next(index)
        while index.isValid():
            if self.item(index).isPlayable:
                return index
            index = self.next(index)
        return index

    def previous(self, index):
        if index.isValid():
            row = index.row()
            if row == 0:
                return self.parent(index)
            previous_index = self.index(row-1, 0, self.parent(index))
        else:
            previous_index = index
        rows = self.rowCount(previous_index)
        while rows:
            self.item(previous_index).populate(self)
            previous_index = self.index(rows-1, 0, previous_index)
            if not previous_index.isValid():
                break
            rows = self.rowCount(previous_index)
        return previous_index

    def previous_song(self, index):
        index = self.previous(index)
        while index.isValid() and not self.item(index).isPlayable:
            index = self.previous(index)
        return index

    def ancestors(self, index): # including oneself
        ancestors = []
        while index.isValid():
            ancestors.append(index)
            index = self.parent(index)
        ancestors.append(QModelIndex())
        return ancestors

    def index_to_path(self, index):
        path = []
        while index.isValid():
            path.insert(0, index.row())
            index = index.parent()
        return path

    def path_to_index(self, path):
        index = QModelIndex()
        for i in path:
            index = self.index(i, 0, index)
        return index

    def refilter(self, string):
        try:
            filter_expr = [
                word[1:-1] 
                if (word[0]=='"' and word[-1]=='"')
                else word
                for word in
                shlex.split(
                    search_value(string),
                    comments = False, posix = False)
                ]
        except:
            return
        self.filter_expr = filter_expr
        if not filter_expr:
            self.beginResetModel()
            self.root_item.filter(self, None)
            self.root_item.populate(self, force = True)
            self.endResetModel()
            return
        queries = BgQueries(
            [BgQuery(Library.filter_model, (self, filter_expr))],
            self.refilter_update_model, 
            lambda: self.filter_expr == filter_expr
        )
        librarian.bg_queries(queries)

    def refilter_update_model(self, queries):
        self.beginResetModel()
        for query in queries:
            self.root_item._copy_children((self, 'f'), self)
        self.endResetModel()
        for playitem in self.root_item.iter(
                self,
                lambda i: i.populated(self),
                lambda i: i.populated(self)):
            self.view.expand(playitem.index(self))

    def flags(self, index):
        return self.item(index).flags(self, index.column())

    def supportedDropActions(self):
        return Qt.CopyAction | Qt.MoveAction

    def mimeData(self, indexes, action = 'copy'):
        return PlayTreeMimeData(
            self, 
            [self.item(index) for index in sorted(set(
                index.sibling(index.row(), 0) for index in indexes
            ),key=lambda index: self.index_to_path(index))], 
            action)

    def mimeTypes(self):
        return [
            'application/x-qabstractitemmodeldatalist',
            'audio/x-mpegurl',
            'text/uri-list',
        ]

    def dropMimeData(self, mime_data, action, row, column, parent):
        if action == Qt.MoveAction and not isinstance(mime_data, PlayTreeMimeData):
            if mime_data.model != self:
                action = Qt.CopyAction
        parent_item = self.item(parent)
        parent_item.populate(self)
        new_items = parent_item.dropMimeData(
            mime_data, action, 
            -1 if (row == -1 or row >= parent_item.rowCount(self)) else
            parent_item.childs_row(None, parent_item.child(self, row)),
            command_prefix = 'Drop')
        inserted_items = [item for item in new_items
                          if item in item.parent.children[self]]
        selection_model = self.view.selectionModel()
        selection_model.select(QItemSelection(new_items[0].index(self),new_items[-1].index(self)), QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)
        selection_model.setCurrentIndex(inserted_items[0].index(self), QItemSelectionModel.NoUpdate)
        self.view.setFocus(Qt.OtherFocusReason)
        return bool(inserted_items)

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            item = self.item(index)
            return item.setData(self, item.column_to_tag(self, index.column()), value)
        return False

    def mark_as_playing(self, index):
        index = self.sibling(index.row(), 0, index)
        ca = self.view.player.current_ancestors
        item = self.item(index)
        if self.view.player.current and self.view.player.current.model == self:
            if item in ca:
                if item == ca[0] or not self.view.isExpanded(index):
                    return True
                
            
from .app import app
def save_playtree():
    playtree.save(playtree_xml_filename)
#app.aboutToQuit.connect(save_playtree)

class PlayTreeMimeData(QMimeData):
    def __init__(self, model, items, action):
        super().__init__()
        self.model = model
        self.items = items
        self.action = action
        self._urls = None
        self._filenames = None
        
    def formats(self):
        return ('application/x-qabstractitemmodeldatalist',
                'audio/x-mpegurl',
                'x-special/gnome-copied-files',
                'text/uri-list',
            )

    def hasFormat(self, fmt):
        return fmt in self.formats()

    def retrieveData(self, mimeType, preferredType):
        if mimeType == 'application/x-qabstractitemmodeldatalist':
            return self.items
        elif mimeType == 'audio/x-mpegurl':
            return "\n".join(self.filenames())
        elif mimeType == 'x-special/gnome-copied-files':
            return self.action + "\n" + self.urls()
        elif mimeType == 'text/uri-list':
            return self.urls()
        else:
            return super().retrieveData(mimeType, preferredType)

    def filenames(self):
        if self._filenames is None:
            self._filenames = [
                item.filename
                for root_item in self.items
                for item in root_item.iter(
                        self.model, 
                        lambda i: isinstance(i, PlayTreeFile),
                        lambda i: True)
            ]
        return self._filenames

    def urls(self):
        if self._urls is None:
            self._urls = "\n".join(QUrl.fromLocalFile(filename).url()
                                  for filename in self.filenames())
        return self._urls


def integers_to_ranges(ns):
    ranges = []
    n1 = None
    for n in ns:
        if n1 is None:
            n1 = n
            n2 = n + 1
            continue
        if n2 < n:
            ranges.append((n1, n2))
        else:
            n2 = n + 1
    if n1 is not None:
        ranges.append((n1, n2))
    return ranges
