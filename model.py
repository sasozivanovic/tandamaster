from PyQt5.QtCore import pyqtRemoveInputHook; from IPython import embed; pyqtRemoveInputHook()

import sys, filecmp

#from lxml import etree
import xml.etree.ElementTree as etree
from PyQt5.Qt import *   # todo: import only what you need

import os, datetime, copy

from util import *
from library import *

def register_xml_tag_handler(tag):
    def f(cls):
        PlayTreeItem.xml_tag_registry[tag] = cls
        cls.xml_tag = tag
        return cls
    return f

def _timestamp(sep = ' '):
    ts = datetime.datetime.now().isoformat(sep)
    return ts[0:ts.index('.')]
        

class PlayTreeItem:

    xml_tag_registry = {}
    @classmethod
    def create_from_xml(cls, element, parent = None):
        return cls.xml_tag_registry[element.tag]._create_from_xml(element, parent)

    def to_xml(self):
        return etree.Element(self.xml_tag)

    def save(self, filename):
        document = etree.ElementTree(self.to_xml())
        with open(filename + '.tmp', 'w') as outfile:
            document.write(outfile, encoding='unicode')
            if filecmp.cmp(filename, filename + '.tmp'):
                os.remove(filename + '.tmp')
            else:
                try:
                    os.rename(filename, filename + '.' + _timestamp('_') + '.bak')
                except:
                    pass
                os.rename(filename + '.tmp', filename)

    def __init__(self, parent = None):
        super().__init__()
        self.parent = parent
        self.expanded = {}

    isTerminal = False
    are_children_editable = False

    def row(self, model):
        return self.parent.childs_row(model, self) if self.parent is not None else 0

    def modelindex(self, model):
        return QModelIndex() if self == model.rootItem or self.parent is None else model.createIndex(self.row(model), 0, self)

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

    def populate(self, model):
        pass

    def delete_children(self, model, top, bottom):
        pass

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
        if self.Id is not None:
            element.set('id', self.Id)
        for child in self.children[None]:
            element.append(child.to_xml())
        return element

    def __init__(self, name, Id = None, parent = None, *iterable):
        super().__init__(parent)
        self.name = name
        self.Id = None if Id is None else int(Id)
        self.children = {None: list(*iterable)}
        
    def copy(self):
        copy = PlayTreeList(self.name)
        copy.children = {None: [child.copy() for child in self.children[None]]}
        return copy

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

    def data(self, model, column_name, role):
        if column_name:
            return None
        if role == Qt.DisplayRole:
            return self.name

    def populate(self, model, force = False):
        if force or model not in self.children or self.children[model] is None:
            self.children[model] = [ child for child in self.children[None]
                                      if child.filter(model) ]

    def filter(self, model):
        for child in self.children[None]:
            if child.filter(model):
                return True
        return model.filter_string in self.name.lower()

    def iter_width(self, model, condition_yield, condition_propagate):
        items = [self]
        while items:
            item = items.pop(0)
            if condition_yield(item):
                yield item
            if condition_propagate(item):
                items.extend(item.children[model])

    def dropMimeData(self, mime_data, action, row, column, calling_model):
        source_items = None
        new_items = None
        if isinstance(mime_data, PlayTreeMimeData):
            source_items = mime_data.items
            new_items = [item.copy() for item in source_items]
        elif mime_data.hasFormat('audio/x-mpegurl'):
            new_items = [
                PlayTreeFile(filename, parent = self)
                for filename in mime_data.text().split("\n")
            ]
        elif mime_data.hasUrls():
            new_items = [
                PlayTreeFile(url.toLocalFile(), parent = self)
                for url in mime_data.urls()
                if url.isLocalFile()
            ]
        inserted_items = self.insert(new_items, row, calling_model) \
                         if new_items else None
        if isinstance(mime_data, PlayTreeMimeData) and mime_data.model == calling_model:
            calling_model.delete(source_items)
        return inserted_items

    def insert(self, new_items, row, calling_model):
        inserted_items = None
        children = self.children[None]
        if row is None: row = len(children)
        for model in self.children.keys():
            if model:
                parent_index = self.modelindex(model)
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
                if model == calling_model:
                    inserted_items = model_new_items
        children[row:row] = new_items
        for item in new_items:
            item.parent = self
        return inserted_items
        
        

    are_children_editable = True

    def delete_children(self, items):
        for model, children in self.children.items():
            rows = sorted([children.index(item) for item in items])
            row_ranges = integers_to_ranges(rows)
            for range in row_ranges:
                if model:
                    model.beginRemoveRows(self.modelindex(model), range[0], range[1]-1)
                del children[range[0]:range[1]]
                if model:
                    model.endRemoveRows()
            

@register_xml_tag_handler('file')
class PlayTreeFile(PlayTreeItem):
    isTerminal = True

    def to_xml(self):
        element = super().to_xml()
        element.set('filename', self.filename)
        return element

    @classmethod
    def _create_from_xml(cls, element, parent):
        return PlayTreeLibraryFile(
            library_name = element.get('library'),
            Id = element.get('id'),
            parent = parent
        ) if element.get('id') else PlayTreeFile(
            filename = element.get('filename'),
            parent = parent
        )

    def __init__(self, filename, parent = None):
        super().__init__(parent)
        self.filename = filename

    def copy(self):
        return PlayTreeFile(self.filename)

    def get_tag(self, tag):
        return library.tag_by_filename(tag, self.filename)

    def get_tags(self):
        return library.tags_by_filename(self.filename)

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self.filename)

    def rowCount(self, model):
        return 0

    def hasChildren(self, model):
        return False

    def child(self, model, row):
        raise RuntimeError

    def data(self, model, column_name, role):
        if role == Qt.DisplayRole:
            return self.get_tag(column_name) if column_name else os.path.basename(self.filename)
        elif not column_name and role == Qt.DecorationRole:
            #return tmSongIcon
            #return QIcon('crazyeye_dance.png')
            return QIcon('song.png')

    def childs_row(self, model, child):
        raise RuntimeError

    @property
    def isPlayable(self):
        return True

    def filter(self, model):
        for value in self.get_tags().values():
            if model.filter_string in value.lower():
                return True

class PlayTreeLibraryFile(PlayTreeFile):
    
    def to_xml(self):
        element = super().to_xml()
        element.set('library', self.library)
        element.set('id', str(self.Id))
        return element

    def __init__(self, library_name, Id, parent = None):
        super(PlayTreeFile, self).__init__(parent)
        self.library = library_name
        self.Id = Id
        self.filename = library.filename_by_id(self.library, self.Id)

    def copy(self):
        return PlayTreeLibraryFile(self.library, self.Id)

    def get_tag(self, tag):
        return library.tag_by_id(self.library, tag, self.Id)

    def get_tags(self):
        return library.tags_by_id(self.library, self.Id)
        
    def __repr__(self):
        return '{}({},{},{})'.format(type(self).__name__, self.library, self.Id, self.filename)

    def data(self, model, column_name, role):
        if role == Qt.DisplayRole:
            if column_name:
                return self.get_tag(column_name)
            else:
                title = self.get_tag('TITLE')
                return title if title else os.path.basename(self.filename)
        elif not column_name and role == Qt.DecorationRole:
            #return tmSongIcon
            #return QIcon('crazyeye_dance.png')
            return QIcon('song.png')

@register_xml_tag_handler('folder')
class PlayTreeFolder(PlayTreeItem):

    def to_xml(self):
        element = super().to_xml()
        element.set('filename', self.filename)
        return element

    @classmethod
    def _create_from_xml(cls, element, parent):
        return cls(filename = element.get('filename'), parent = parent)

    def __init__(self, filename, parent = None):
        super().__init__(parent)
        self.filename = filename
        self.children = {None: None}

    def copy(self):
        return PlayTreeFolder(self.filename)

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self.filename)

    def rowCount(self, model):
        self.populate(model)
        return len(self.children[model])

    def hasChildren(self, model):
        if self.children[model] is None:
            return True
        else:
            return bool(self.children[model])

    def child(self, model, row):
        self.populate(model)
        return self.children[model][row]

    def childs_row(self, model, child):
        self.populate(model)
        return self.children[model].index(child)

    def data(self, model, column_name, role):
        if column_name:
            return None
        elif role == Qt.DisplayRole:
            return os.path.basename(self.filename)
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
            fileelements = [
                PlayTreeFile(filename=fullfn, parent = self) for fn,fullfn in files
            ]
            self.children[None].extend(filter(lambda f: f.get_tags() is not None, fileelements))
        if self.children[model] is None:
            self.children[model] = [child for child in self.children[None]
                                     if child.filter(model) ]

    def filter(self, model):
        self.populate(model)
        for child in self.children[None]:
            if child.filter(model):
                return True
        return model.filter_string in self.name.lower()

    def expand_small_children(self, model):
        if model.view.isExpanded(self.modelindex(model)):
            for child in self.children[model]:
                if isinstance(child, PlayTreeFolder) and model in child.children and child.children[model] is not None and child.rowCount(model) == 1:
                    model.view.setExpanded(child.modelindex(model), True)
                    child.expand_small_children(model)
        

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
        return cls(library_name = element.get('library'), fixed_tags = fixed_tags, browse_by_tags = browse_by_tags, parent = parent)

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

    def __init__(self, library_name, fixed_tags, browse_by_tags, tag = None, parent = None):
        super().__init__(parent)
        self.library = library_name
        self.fixed_tags = tuple(fixed_tags)
        self.browse_by_tags = tuple(browse_by_tags)
        self.tag = tag
        self.children = {}
        self.value = {}
        self.song_count = {}
        self.value_to_child = {}

    def copy(self):
        return PlayTreeBrowse(self.library, self.fixed_tags, self.browse_by_tags, self.tag)

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

    icons = { None: 'library.png', 'ARTIST': 'personal.png', 'ALBUM': 'image_album.png' }
    def data(self, model, column_name, role):
        if column_name:
            return None
        elif role == Qt.DisplayRole:
            if model in self.song_count:
                return (self.value[model] if model in self.value and self.value[model] else '') + \
                    ' (' + str(self.song_count[model]) + ')'
            else:
                return app.tr('Browse') + ' ' + \
                    " -> ".join([self.library]+[str(v) for t,v in self.fixed_tags]) + ' ' + app.tr('by') + ' ' + \
                    ", ".join(tag.lower() for tag in self.browse_by_tags)
        elif column_name == '' and role == Qt.DecorationRole:
            #return app.style().standardIcon(QStyle.SP_DriveCDIcon)
            try:
                return QIcon(self.icons[self.tag])
            except:
                return None

    def populate_tags(self, model, rows):
        self.children[model] = []
        children = self.children[model]
        tag = self.browse_by_tags[0]
        browse_by_tags = self.browse_by_tags[1:]        
        for value, count in rows:
            fixed_tags = self.fixed_tags + ((tag, value),)
            if value in self.value_to_child:
                child = self.value_to_child[value]
            else:
                child = PlayTreeBrowse(self.library, fixed_tags, browse_by_tags, tag = tag, parent = self)
                self.value_to_child[value] = child
            child.value[model] = value
            child.song_count[model] = count
            children.append(child)
        
    def populate_songs(self, model, rows):
        self.children[model] = []
        children = self.children[model]
        for Id in rows:
            if Id not in self.value_to_child:
                self.value_to_child[Id] = PlayTreeLibraryFile(self.library, Id, parent = self)
            children.append(self.value_to_child[Id])

    def populate(self, model, force = False):
        if force or model not in self.children or self.children[model] is None:
            self.children[model] = None
        if self.children[model] is None:
            if self.browse_by_tags:
                self.populate_tags(model, library.query_tags_iter(
                    self.library, self.browse_by_tags[0], self.fixed_tags,
                    model.filter_string))
            else:
                self.populate_songs(model, library.query_songs_iter(
                    self.library, self.fixed_tags,  
                    model.filter_string))
                
    def expand_small_children(self, model):
        if self.rowCount(model) == 0 or isinstance(self.child(model, 0), PlayTreeFile):
            return
        filter_string = model.filter_string
        queries = BgQueries([], self.expand_small_children_callback, 
                               lambda: model.filter_string == filter_string)
        for child in self.children[model]:
            if child.song_count[model] == 1:
                query = BgQuery(Library.query_tags_all,
                                (child.library, child.browse_by_tags[0], child.fixed_tags, filter_string)
                            ) if child.browse_by_tags else \
                    BgQuery(Library.query_songs_all,
                            (child.library, child.fixed_tags, filter_string)
                        )
                query.browse = child
                queries.append(query)
        queries.model = model
        librarian.bg_queries(queries)

    def expand_small_children_callback(self, queries):
        for query in queries:
            if query.browse in query.browse.parent.children[queries.model]:
                queries.model.view.setExpanded(query.browse.modelindex(queries.model), True)
                query.browse.expand_small_children(queries.model)
        

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

    def __init__(self, root_id = None, parent = None):
        super().__init__(parent)
        self.rootItem = playtree
        if root_id is not None:
            for item in playtree.iter_width(self, 
                    lambda item: isinstance(item, PlayTreeList) and item.Id == root_id,
                    lambda item: isinstance(item, PlayTreeList)):
                self.rootItem = item
                break
        self.filter_string = ''
        self.rootItem.populate(self)

    def item(self, index):
        return index.internalPointer() if index.isValid() else self.rootItem

    # column "" provides browsing info (folder name, file name, ...)
    #_columns = ('', 'ARTIST', 'ALBUM', 'TITLE')
    _columns = ('',)

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
        return QModelIndex() if parentItem in (None, self.rootItem) else \
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
        return len(self._columns)

    currentindexroles = (Qt.ForegroundRole, Qt.FontRole)
    def data(self, index, role = Qt.DisplayRole):
        if role in self.currentindexroles:
            if index == self.view.player.current_index:
                if role == Qt.ForegroundRole:
                    #return QBrush(QColor(Qt.red))
                    return QBrush(QColor(Qt.darkGreen))
                elif role == Qt.FontRole:
                    font = QFont()
                    font.setWeight(QFont.Bold)
                    return font
        else:
            return self.item(index).data(self, self._columns[index.column()], role)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._columns[section].title()

    def sibling(self, row, column, index):
        return super().sibling(
            index.row() if row is None else row,
            index.column() if column is None else column,
            index
        )
        
    def next(self, index):
        descend  = True
        if not index.isValid():
            index = self.index(0,0,index)
        while index.isValid():
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
        return ancestors

    def refilter(self, string):
        filter_string = string.lower()
        self.filter_string = filter_string
        queries = BgQueries([],
            self.refilter_update_model, 
            lambda: self.filter_string == filter_string
        )
        for browse in self.rootItem.iter(self,
                lambda item: isinstance(item, PlayTreeBrowse),
                lambda item: isinstance(item, PlayTreeList)):
            query = BgQuery(Library.query_tags_all,
                            (browse.library, browse.browse_by_tags[0], browse.fixed_tags, filter_string)
                        ) if browse.browse_by_tags else \
                 BgQuery(Library.query_songs_all,
                         (browse.library, browse.fixed_tags, filter_string)
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
        if self.filter_string:
            for item in self.rootItem.iter(self,
                    lambda item: isinstance(item, PlayTreeBrowse) or 
                    isinstance(item, PlayTreeFolder),
                    lambda item: isinstance(item, PlayTreeList)):
                item.expand_small_children(self)

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEnabled | (Qt.ItemIsDropEnabled if self.item(index).are_children_editable else Qt.NoItemFlags)

    def mimeData(self, indexes, action = 'copy'):
        return PlayTreeMimeData(self, [self.item(index) for index in indexes], action)
        mime_data = super().mimeData(indexes)
        filenames = [
            item.filename
            for index in indexes
            for item in self.item(index).iter(
                    self, 
                    lambda i: isinstance(i, PlayTreeFile),
                    lambda i: True)
            ]
        urls = [QUrl.fromLocalFile(fn) for fn in filenames]
        mime_data.setUrls(urls)
        mime_data.setText("\n".join(filenames))
        mime_data.setData('x-special/gnome-copied-files', action + "\n" + 
                          "\n".join(url.url() for url in urls))
        return mime_data

    def supportedDropActions(self):
        return Qt.CopyAction | Qt.MoveAction

    def dropMimeData(self, mime_data, action, row, column, parent):
        parent_item = self.item(parent)
        inserted_items = parent_item.dropMimeData(mime_data, action, row, column, self)
        selection_model = self.view.selectionModel()
        selection_model.clear()
        for item in inserted_items:
            selection_model.select(item.modelindex(self),QItemSelectionModel.Select)
        selection_model.setCurrentIndex(inserted_items[0].modelindex(self), QItemSelectionModel.NoUpdate)
        return bool(inserted_items)

    def delete(self, item_selection):
        ranges = {}
        for selection_range in item_selection:
            parent = self.item(selection_range.parent())
            if parent not in ranges:
                ranges[parent] = []
            ranges[parent].extend(
                parent.child(self, i)
                for i in range(selection_range.top(), selection_range.bottom()+1))
        for parent, items in ranges.items():
            parent.delete_children(items)

from app import app
def save_playtree():
    playtree.save(playtree_xml_filename)
#app.aboutToQuit.connect(save_playtree)

#tmSongIcon = QIcon(':images/song.png')
#import tandamaster_rc

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
            
