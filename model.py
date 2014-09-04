from PyQt5.QtCore import pyqtRemoveInputHook; from IPython import embed; pyqtRemoveInputHook()

import sys, filecmp, os, datetime, copy, collections

#from lxml import etree
import xml.etree.ElementTree as etree
from PyQt5.Qt import *   # todo: import only what you need

from util import *
from library import *
from app import *
from commands import *

import bidict, shlex

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
            library_name, song_id = library.library_name_and_song_id_from_filename(filename)
            return PlayTreeLibraryFile(library_name = library_name, song_id = song_id, parent = parent) if song_id else PlayTreeFile(filename = filename, parent = parent)

    def save(self, filename):
        document = etree.ElementTree(self.to_xml())
        with open(filename + '.tmp', 'w') as outfile:
            document.write(outfile, encoding='unicode')
            if filecmp.cmp(filename, filename + '.tmp'):
                os.remove(filename + '.tmp')
            else:
                try:
                    os.mkdir('bak')
                except OSError:
                    pass
                try:
                    os.rename(filename, os.path.join('bak', filename + '.' + tm_timestamp('_') + '.bak'))
                except:
                    pass
                os.rename(filename + '.tmp', filename)

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
        return QModelIndex() if self == model.root_item or self.parent is None else model.createIndex(self.row(model), column, self)

    def path(self, model):
        if self.parent:
            return self.parent.path(model) + (self.parent.childs_row(model, self),)
        else:
            return tuple()

    @property
    def isPlayable(self):
        return False

    def filter(self, model):
        return True

    def expand_small_children(self, model):
        return 

    def iter(self, model, condition_yield, condition_propagate):
        if condition_yield(self):
            yield self
        if self.hasChildren(model) and condition_propagate(self):
            for i in range(self.rowCount(model)):
                for item in self.child(model, i).iter(model, condition_yield, condition_propagate):
                    yield item

    def populate(self, model, force = False):
        pass

    def delete(self, items):
        raise RuntimeError

    def __str__(self):
        return 'playtreeitem'

    def flags(self, column = ''):
        return Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEnabled

    duration_mode_all = 0
    duration_mode_cortinas = 1

    def function(self):
        return None

    def iter_depth(self, model, condition_yield, condition_propagate):
        if condition_yield(self):
            yield(self)
        if condition_propagate(self):
            for child in self.children[model]:
                for item in child.iter_depth(model, condition_yield, condition_propagate):
                    yield item
            
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
        copy.children = {None: [child.copy(parent = self) for child in self.children[None]]}
        return copy

    are_children_manually_set = True

    def __repr__(self):
        return '{}(id={},name={})'.format(type(self).__name__, self.Id, self.name)

    def rowCount(self, model):
        self.populate(model)
        return len(self.children[model])

    def hasChildren(self, model):
        self.populate(model)
        return bool(self.children[model])

    def child(self, model, row):
        self.populate(model)
        return self.children[model][row]

    def childs_row(self, model, child):
        self.populate(model)
        return self.children[model].index(child)

    def __str__(self):
        return self.name if self.name is not None else ''

    def data(self, model, column_name, role):
        if role in (Qt.DisplayRole, Qt.EditRole):
            if column_name == '_length':
                return hmsms_to_text(*ms_to_hmsms(1000*self.duration(model)), include_ms=False)
            if column_name:
                first = True
                for child in self.children[None]:
                    if not child.isPlayable:
                        return
                    child_data = child.data(model, column_name, role)
                    if first:
                        data = child_data
                        first = False
                    elif child_data != data:
                        return
                return data if not first else None
            else:
                return str(self)
        elif not column_name and role == Qt.DecorationRole:
            return QIcon('icons/iconfinder/silk/list.png')

    def populate(self, model, force = False):
        if force or model not in self.children or self.children[model] is None:
            self.children[model] = [ child for child in self.children[None]
                                      if child.filter(model) ]

    def filter(self, model):
        for child in self.children[None]:
            if child.filter(model):
                return True
        return all(filter_word in self.name.lower() for filter_word in model.filter_expr)

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
            if model:
                parent_index = self.index(model)
                model_new_items = [item for item in new_items
                                   if item.filter(model)]
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
            rows = sorted([children.index(item) for item in items])
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
                    command_prefix = 'Drop')
        return new_items
        
    def flags(self, column = ''):
        return Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def setData(self, column, value):
        if column == 0:
            EditPlayTreeNameCommand(self, value)
            #self.name = value
            #for model in self.children.keys():
            #    if model:
            #        index = self.index(model, column)
            #        model.dataChanged.emit(index, index, [Qt.EditRole])
            return True
        return False

    def duration(self, model, mode = PlayTreeItem.duration_mode_all):
        return sum(child.duration(model, mode) for child in self.children[model]) \
            if model in self.children else 0


@register_xml_tag_handler('file')
class PlayTreeFile(PlayTreeItem):
    isTerminal = True

    def to_xml(self):
        element = super().to_xml()
        element.set('filename', self.filename)
        return element

    @classmethod
    def _create_from_xml(cls, element, parent):
        filename = element.get('filename')
        library_name, song_id = library.library_name_and_song_id_from_filename(filename)
        return PlayTreeLibraryFile(
            library_name = library_name,
            song_id = song_id,
            Id = element.get('id'),
            parent = parent
        ) if song_id else PlayTreeFile(
            filename = filename,
            Id = element.get('id'),
            parent = parent
        )

    def __init__(self, filename, Id = None, parent = None):
        super().__init__(Id, parent)
        self.filename = filename
        file_reader.register_file(filename, self)
        file_reader.bg_get_fileinfo(FileInfo(filename, FileInfo.reason_NewPlayTreeFile))
        #print("add file", filename, fs_watcher.addPath(filename))

    @property
    def Id(self):
        return None

    def copy(self, parent = None):
        return PlayTreeFile(self.filename, parent = parent)

    def get_tag(self, tag):
        return file_reader.get_tag(self.filename, tag)

    def get_tags(self):
        return file_reader.get_tags(self.filename)

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self.filename)

    def rowCount(self, model):
        return 0

    def hasChildren(self, model):
        return False

    def child(self, model, row):
        raise RuntimeError

    def __str__(self):
        return os.path.basename(self.filename)

    def data(self, model, column_name, role):
        if role in (Qt.DisplayRole, Qt.EditRole):
            if column_name == '_length':
                return hmsms_to_text(*ms_to_hmsms(1000*self.duration()), include_ms=False)
            elif column_name:
                return self.get_tag(column_name)
            else:
                return str(self)
        elif not column_name and role == Qt.DecorationRole:
            #return tmSongIcon
            #return QIcon('crazyeye_dance.png')
            if self.function() == 'cortina':
                return QIcon('icons/iconfinder/farm-fresh/curtain.png')
            else:
                return QIcon('icons/happy-dance.gif')

    def function(self):
        return 'tanda' if '/tango/' in self.filename else 'cortina'

    def childs_row(self, model, child):
        raise RuntimeError

    @property
    def isPlayable(self):
        return True

    def filter(self, model):
        if not file_reader.have_tags(self.filename):
            return True
        return True # temp!!!!
        for value in self.get_tags().values():
            if model.filter_string in str(value).lower():
                return True

    def refresh_models(self):
        if self.get_tags() is None: # not an audio file: delete
            for model, children in self.parent.children.items():
                if self in self.parent.children[model]:
                    i = self.parent.childs_row(model, self)
                    if model:
                        model.beginRemoveRows(self.parent.index(model), i, i)
                    del self.parent.children[model][i]
                    if model:
                        model.endRemoveRows()
        else:
            for model, children in self.parent.children.items():
                if model and self in children:
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
    def duration(self, model = None, mode = PlayTreeItem.duration_mode_all):
        if mode & self.duration_mode_cortinas and self.function() == 'cortina':
            return self.cortina_duration
        try:
            return int(self.get_tag('_length'))
        except:
            return 0

class PlayTreeLibraryFile(PlayTreeFile):
    
    def __init__(self, library_name, song_id, Id = None, parent = None):
        super(PlayTreeFile, self).__init__(Id, parent)
        self.library = library_name
        self.song_id = song_id
        self.filename = library.filename_by_id(self.library, song_id)

    def copy(self, parent = None):
        return PlayTreeLibraryFile(self.library, self.song_id, parent = parent)

    def get_tag(self, tag):
        return library.tag_by_id(self.library, tag, self.song_id)

    def get_tags(self):
        return library.tags_by_id(self.library, self.song_id)
        
    def __repr__(self):
        return '{}({},{},{})'.format(type(self).__name__, self.library, self.song_id, self.filename)

    def __str__(self):
        return os.path.basename(self.filename)

    def data(self, model, column_name, role):
        if role in (Qt.DisplayRole, Qt.EditRole):
            if column_name:
                return super().data(model, column_name, role)
            else:
                title = self.get_tag('TITLE')
                return title if title else str(self)
        else:
            return super().data(model, column_name, role)

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
        self.filename = filename
        self.children = {None: None}

    def copy(self, parent = None):
        return PlayTreeFolder(self.filename, parent = parent)

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self.filename)

    def rowCount(self, model):
        self.populate(model)
        return len(self.children[model])

    def hasChildren(self, model):
        if model not in self.children or self.children[model] is None:
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

    def data(self, model, column_name, role):
        if column_name:
            return None
        elif role == Qt.DisplayRole:
            return str(self)
        elif column_name == '' and role == Qt.DecorationRole:
            #return app.style().standardIcon(QStyle.SP_DirIcon)
            return MyIcon('Tango', 'places', 'folder')

    def populate(self, model, force = False):
        if force or model not in self.children or self.children[model] is None:
            self.children[model] = None
        if self.children[None] is None:
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
                if os.path.splitext(fn)[1] in Library.musicfile_extensions and \
                   not file_reader.not_an_audio_file(fullfn):
                    self.children[None].append(
                        PlayTreeFile(filename=fullfn, parent = self))
            #print("add dir", self.filename, fs_watcher.addPath(self.filename))
        if self.children[model] is None:
            self.children[model] = [child for child in self.children[None] if child.filter(model) ]
            self.children[model] = self.children[None]

    def filter(self, model):
        if self.children[None] is None or model not in self.children:
            return all(filter_word in self.filename.lower() for filter_word in model.filter_expr)
        for child in self.children[None]:
            if child.filter(model):
                return True
        return all(filter_word in self.filename.lower() for filter_word in model.filter_expr)

    def expand_small_children(self, model):
        if model.view.isExpanded(self.index(model)):
            for child in self.children[model]:
                if isinstance(child, PlayTreeFolder) and model in child.children and child.children[model] is not None and child.rowCount(model) == 1:
                    model.view.setExpanded(child.index(model), True)
                    child.expand_small_children(model)

    def duration(self, model, mode = PlayTreeItem.duration_mode_all):
        return sum(child.duration(model, mode) for child in self.children[model]) \
            if model in self.children else 0
        

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
        return '{}({},fixed={},by={})'.format(type(self).__name__, self.library, self.fixed_tags, self.browse_by_tags)

    def rowCount(self, model):
        self.populate(model)
        return len(self.children[model])

    def hasChildren(self, model):
        if model not in self.children:
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


    icons = { None: 'library.png', 'ARTIST': 'personal.png', 'ALBUM': 'image_album.png' }
    def data(self, model, column_name, role):
        if column_name:
            return None
        elif role == Qt.DisplayRole:
            if model in self.song_count:
                return (self.value[model] if model in self.value and self.value[model] else '') + \
                    ' (' + str(self.song_count[model]) + ')'
            else:
                return str(self)
        elif column_name == '' and role == Qt.DecorationRole:
            #return app.style().standardIcon(QStyle.SP_DriveCDIcon)
            try:
                return QIcon(self.icons[self.tag])
            except:
                return QIcon(self.icons[None])

    def populate_tags(self, model, rows):
        self.children[model] = []
        children = self.children[model]
        tag = self.browse_by_tags[0]
        browse_by_tags = self.browse_by_tags[1:]        
        for value, count in rows:
            fixed_tags = self.fixed_tags + ((tag, value),)
            child = PlayTreeBrowse(self.library, fixed_tags, browse_by_tags, tag = tag, parent = self)
            child.value[model] = value
            child.song_count[model] = count
            children.append(child)
        
    def populate_songs(self, model, rows):
        self.children[model] = []
        children = self.children[model]
        for Id in rows:
            children.append(PlayTreeLibraryFile(self.library, Id, parent = self))

    def populate(self, model, force = False):
        if force or model not in self.children or self.children[model] is None:
            self.children[model] = None
        if self.children[model] is None:
            if self.browse_by_tags:
                self.populate_tags(model, library.query_tags_iter(
                    self.library, self.browse_by_tags[0], self.fixed_tags,
                    model.filter_expr))
            else:
                self.populate_songs(model, library.query_songs_iter(
                    self.library, self.fixed_tags,  
                    model.filter_expr))
                
    def expand_small_children(self, model):
        if self.rowCount(model) == 0 or isinstance(self.child(model, 0), PlayTreeFile):
            return
        filter_expr = model.filter_expr
        queries = BgQueries([], self.expand_small_children_callback, 
                               lambda: model.filter_expr == filter_expr)
        for child in self.children[model]:
            if child.song_count[model] == 1:
                query = BgQuery(Library.query_tags_all,
                                (child.library, child.browse_by_tags[0], child.fixed_tags, filter_expr)
                            ) if child.browse_by_tags else \
                    BgQuery(Library.query_songs_all,
                            (child.library, child.fixed_tags, filter_expr)
                        )
                query.browse = child
                queries.append(query)
        queries.model = model
        librarian.bg_queries(queries)

    def expand_small_children_callback(self, queries):
        for query in queries:
            if query.browse in query.browse.parent.children[queries.model]:
                queries.model.view.setExpanded(query.browse.index(queries.model), True)
                query.browse.expand_small_children(queries.model)
        
    def duration(self, model, mode = PlayTreeItem.duration_mode_all):
        return sum(child.duration(model, mode) for child in self.children[model]) \
            if model in self.children else 0


@register_xml_tag_handler('link')
class PlayTreeLink(PlayTreeItem):
    pass

playtree_xml_filename = 'playtree.xml'
try:
    playtree_xml_document = etree.parse(playtree_xml_filename)
    playtree_xml = playtree_xml_document.getroot()
except:
    playtree_xml = etree.Element('list')
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

    def item(self, index):
        return index.internalPointer() if index.isValid() else self.root_item

    # column "" provides browsing info (folder name, file name, ...)
    columns = ('', 'ARTIST', 'PERFORMER:VOCALS', 'QUODLIBET::RECORDINGDATE', 'GENRE', '_length')
    #columns = ('',)

    column_display_names = bidict.bidict({
        '': 'Title',
        #'ARTIST': 'Artist',
        #'ALBUM': 'Album',
        #'TITLE': 'Title',
        'PERFORMER:VOCALS': 'Singer',
        'QUODLIBET::RECORDINGDATE': 'Year',
        #'GENRE': 'Genre',
        #'_Length': 'Length',
    })

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        parentItem = self.item(parent)
        childItem = parentItem.child(self, row)
        assert childItem
        return self.createIndex(row, column, childItem)

    def parent(self, index):
        if not index.isValid():
            return index
        parentItem = self.item(index).parent
        return QModelIndex() if parentItem in (None, self.root_item) else \
            self.createIndex(parentItem.row(self), 0, parentItem)

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

    currentindexroles = (Qt.ForegroundRole, Qt.FontRole)
    def data(self, index, role = Qt.DisplayRole):
        if role in self.currentindexroles:
            if self.view.player.current_model == self and self.item(index) == self.view.player.current_item:
                if role == Qt.ForegroundRole:
                    #return QBrush(QColor(Qt.red))
                    return QBrush(QColor(Qt.darkGreen))
                elif role == Qt.FontRole:
                    font = QFont()
                    font.setWeight(QFont.Bold)
                    return font
        else:
            return self.item(index).data(self, self.columns[index.column()], role)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
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
        while index.isValid() and not self.item(index).isPlayable:
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

    def ancestors(self, index):
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
                    unidecode.unidecode(string).lower(),
                    comments = False, posix = False)
                ]
        except:
            return
        self.filter_expr = filter_expr
        self.root_item.filter(self)
        queries = BgQueries([],
            self.refilter_update_model, 
            lambda: self.filter_expr == filter_expr
        )
        for browse in self.root_item.iter(self,
                lambda item: isinstance(item, PlayTreeBrowse),
                lambda item: isinstance(item, PlayTreeList)):
            query = BgQuery(Library.query_tags_all,
                            (browse.library, browse.browse_by_tags[0], browse.fixed_tags, filter_expr)
                        ) if browse.browse_by_tags else \
                 BgQuery(Library.query_songs_all,
                         (browse.library, browse.fixed_tags, filter_expr)
                     )
            query.browse = browse
            queries.append(query)
        librarian.bg_queries(queries)

    def refilter_update_model(self, queries):
        self.beginResetModel()
        for query in queries:
            if query.method == Library.query_tags_all:
                query.browse.populate_tags(self, query.result)
            else: # query.method == Library.query_songs_all:
                query.browse.populate_songs(self, query.result)
        self.endResetModel()
        if self.filter_expr:
            for item in self.root_item.iter(self,
                    lambda item: isinstance(item, PlayTreeBrowse) or 
                    isinstance(item, PlayTreeFolder),
                    lambda item: isinstance(item, PlayTreeList)):
                item.expand_small_children(self)

    def flags(self, index):
        return self.item(index).flags(self.columns[index.column()])

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
        return bool(inserted_items)

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            return self.item(index).setData(index.column(), value)
        return False
        
from app import app
def save_playtree():
    playtree.save(playtree_xml_filename)
app.aboutToQuit.connect(save_playtree)

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
            return super().retrieveData(self, mimeType, preferredType)

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
            


#tmSongIcon = QIcon(':images/song.png')
#import tandamaster_rc
