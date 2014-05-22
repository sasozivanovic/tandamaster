from PyQt5.QtCore import pyqtRemoveInputHook; from IPython import embed
#pyqtRemoveInputHook(); embed()

import sys, filecmp

#from lxml import etree
import xml.etree.ElementTree as etree
from PyQt5.Qt import *   # todo: import only what you need

import os, datetime, copy

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
    def create_from_xml(cls, element):
        return cls.xml_tag_registry[element.tag]._create_from_xml(element)

    def to_xml(self):
        return etree.Element(self.xml_tag)

    def save(self, filename):
        document = etree.ElementTree(self.to_xml())
        with open(filename + '.tmp', 'wb') as outfile:
            document.write(outfile, pretty_print = True, encoding='UTF-8')
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
        self.was_expanded = False

    isTerminal = False

    @property
    def row(self):
        return self.parent.childs_row(self) if self.parent is not None else 0

    def modelindex(self, model):
        return QModelIndex() if self == model.rootItem or self.parent is None else model.createIndex(self.row, 0, self)

    @property
    def isPlayable(self):
        return False

    def filter(self):
        return True

    def expand_small_children(self, model):
        return 

    def iter(self, condition_yield, condition_propagate):
        if condition_yield(self):
            yield self
        if self.hasChildren() and condition_propagate(self):
            for i in range(self.rowCount()):
                for item in self.child(i).iter(condition_yield, condition_propagate):
                    yield item


@register_xml_tag_handler('list')
class PlayTreeList(PlayTreeItem):

    @classmethod
    def _create_from_xml(cls, element):
        item = cls(name = element.get('name'), Id = element.get('id'))
        for subelement in element:
            item._children.append(PlayTreeItem.create_from_xml(subelement))
        return item

    def to_xml(self):
        element = super().to_xml()
        element.set('name', self.name)
        element.set('id', self.Id)
        for child in self._children:
            element.append(child.to_xml())
        return element

    def __init__(self, name, Id = None, parent = None, *iterable):
        super().__init__(parent)
        self.name = name
        self.Id = Id
        self._children = list(*iterable)
        
    def __str__(self):
        return self.name if self.name else ''

    def __repr__(self):
        return '{}(id={},name={})'.format(type(self).__name__, self.Id, self.name)

    @property
    def children(self):
        return [ c for c in self._children if c.filter() ]

    def rowCount(self):
        return len(self.children)

    def hasChildren(self):
        return bool(self.children)

    def child(self, row):
        try:
            return self.children[row]
        except IndexError:
            return None

    def childs_row(self, child):
        return self.children.index(child)

    def data(self, column_name, role):
        if column_name:
            return None
        if role == Qt.DisplayRole:
            return self.name

    def iter_width(self, condition_yield, condition_propagate):
        items = [self]
        while items:
            item = items.pop(0)
            if condition_yield(item):
                yield item
            if condition_propagate(item):
                items.extend(item.children)

@register_xml_tag_handler('file')
class PlayTreeFile(PlayTreeItem):
    isTerminal = True

    def to_xml(self):
        element = super().to_xml()
        element.set('filename', self.filename)

    @classmethod
    def _create_from_xml(cls, element):
        return PlayTreeLibraryFile(
            library_name = element.get('library'),
            Id = element.get('id')
        ) if element.get('id') else PlayTreeFile(
            filename = element.get('filename')
        )

    def __init__(self, filename, parent = None):
        super().__init__(parent)
        self.filename = filename

    def get_tag(self, tag):
        return library.tag_by_filename(tag, self.filename)

    def get_tags(self):
        return library.tags_by_filename(self.filename)

    def __str__(self):
        title = self.get_tag('TITLE')
        return title if title else os.path.basename(self.filename)

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self.filename)

    def rowCount(self):
        return 0

    def hasChildren(self):
        return False

    def child(self, row):
        return None

    def data(self, column_name, role):
        if role == Qt.DisplayRole:
            return self.get_tag(column_name) if column_name else str(self)
        elif not column_name and role == Qt.DecorationRole:
            return tmSongIcon

    def childs_row(self, child):
        return None

    @property
    def isPlayable(self):
        return True

    def filter(self):
        for value in self.get_tags().values():
            if PlayTreeModel.current.filter_string in value.lower():
                return True

class PlayTreeLibraryFile(PlayTreeFile):
    
    def to_xml(self):
        element = super().to_xml()
        element.set('library', self.library)
        element.set('id', self.Id)

    def __init__(self, library_name, Id, parent = None, ):
        super(PlayTreeFile, self).__init__(parent)
        self.library = library_name
        self.Id = Id
        self.filename = library.filename_by_id(self.library, self.Id)

    def get_tag(self, tag):
        return library.tag_by_id(self.library, tag, self.Id)

    def get_tags(self):
        return library.tags_by_id(self.library, self.Id)
        
    def __repr__(self):
        return '{}({},{},{})'.format(type(self).__name__, self.library, self.Id, self.filename)


@register_xml_tag_handler('folder')
class PlayTreeFolder(PlayTreeItem):

    def to_xml(self):
        element = super().to_xml()
        element.set('filename', self.filename)

    @classmethod
    def _create_from_xml(cls, element):
        return cls(filename = element.get('filename'))

    def __init__(self, filename, parent = None):
        super().__init__(parent)
        self.filename = filename
        self._children = None

    def __str__(self):
        return self.filename

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self.filename)

    @property
    def children(self):
        return [ c for c in self._children if c.filter() ]

    def rowCount(self):
        self._populate()
        return len(self.children)

    def hasChildren(self):
        if self._children is None:
            return True
        else:
            return bool(len(self.children))

    def child(self, row):
        self._populate()
        return self.children[row]

    def childs_row(self, child):
        try:
            return self.children.index(child)
        except IndexError:
            return None

    def data(self, column_name, role):
        if column_name:
            return None
        elif role == Qt.DisplayRole:
            return os.path.basename(self.filename)
        elif column_name == '' and role == Qt.DecorationRole:
            return app.style().standardIcon(QStyle.SP_DirIcon)

    def _populate(self, force = False):
        if force:
            self._children = None
        if self._children is None:
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
            self._children = [
                PlayTreeFolder(filename=fullfn, parent = self) for fn,fullfn in folders
            ]
            fileelements = [
                PlayTreeFile(filename=fullfn, parent = self) for fn,fullfn in files
            ]
            self._children.extend(filter(lambda f: f.get_tags() is not None, fileelements))

    def expand_small_children(self, model):
        if model.view.isExpanded(self.modelindex(model)):
            for child in self.children:
                if isinstance(child, PlayTreeFolder) and child._children is not None and child.rowCount() == 1:
                    model.view.setExpanded(child.modelindex(model), True)
                    child.expand_small_children(model)
        

@register_xml_tag_handler('browse')
class PlayTreeBrowse(PlayTreeItem):
    @classmethod
    def _create_from_xml(cls, element):
        fixed_tags = []
        browse_by_tags = []
        for by in element:
            if by.tag == 'by':
                if by.get('fixed'):
                    fixed_tags.append((by.get('tag'), by.get('value')))
                else:
                    browse_by_tags.append(by.get('tag'))
        return cls(library_name = element.get('library'), fixed_tags = fixed_tags, browse_by_tags = browse_by_tags)

    def to_xml(self):
        element = super().to_xml()
        element.set('library_name', self.library)
        for tag, value in self.fixed_tags:
            by = etree.SubElement(element, 'by', fixed = 'yes', tag = tag)
            if value is not None:
                by.set('value', value)
        for tag in self.browse_by_tags:
            by = etree.SubElement(element, 'by', tag = tag)
        return element

    def __init__(self, library_name, fixed_tags, browse_by_tags, parent = None):
        super().__init__(parent)
        self.children = None
        self.library = library_name
        self.fixed_tags = tuple(fixed_tags)
        self.browse_by_tags = tuple(browse_by_tags)
        self.value = None
        self.song_count = None
   
    def __str__(self):
        if self.song_count is not None:
            return (self.value if self.value is not None else '') + ' (' + str(self.song_count) + ')'
        else:
            return app.tr('Browse') + ' ' + self.library + ' ' + app.tr('by') + ' ' + \
                ", ".join(tag.lower() for tag in self.browse_by_tags)

    def __repr__(self):
        return '{}({},fixed={},by={})'.format(type(self).__name__, self.library, self.fixed_tags, self.browse_by_tags)

    def rowCount(self):
        self._populate()
        return len(self.children)

    def hasChildren(self):
        if self.children is None:
            return True
        else:
            return bool(len(self.children))

    def child(self, row):
        self._populate()
        return self.children[row]

    def childs_row(self, child):
        try:
            return self.children.index(child)
        except IndexError:
            return None

    def data(self, column_name, role):
        if column_name:
            return None
        elif role == Qt.DisplayRole:
            return str(self)
        elif column_name == '' and role == Qt.DecorationRole:
            return app.style().standardIcon(QStyle.SP_DriveCDIcon)

    def _populate_tags(self, rows):
        self.children = []
        tag = self.browse_by_tags[0]
        browse_by_tags = self.browse_by_tags[1:]        
        for value, count in rows:
            fixed_tags = self.fixed_tags + ((tag, value),)
            child = PlayTreeBrowse(self.library, fixed_tags, browse_by_tags, parent = self)
            child.value = value
            child.song_count = count
            self.children.append(child)
        
    def _populate_songs(self, rows):
        self.children = [
            PlayTreeLibraryFile(self.library, Id, parent = self)
            for Id in rows
        ]

    def _populate(self, force = False):
        if force:
            self.children = None
        if self.children is None:
            if self.browse_by_tags:
                self._populate_tags(library.query_tags_iter(
                    self.library, self.browse_by_tags[0], self.fixed_tags,
                    PlayTreeModel.current.filter_string))
            else:
                self._populate_songs(library.query_songs_iter(
                    self.library, self.fixed_tags,  
                    PlayTreeModel.current.filter_string))
                
    def expand_small_children(self, model):
        if self.rowCount() == 0 or isinstance(self.child(0), PlayTreeFile):
            return
        filter_string = model.filter_string
        queries = BgQueries([], self.expand_small_children_callback, 
                               lambda: model.filter_string == filter_string)
        for child in self.children:
            if child.rowCount() == 1:
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
            if query.browse in query.browse.parent.children:
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
    current = None

    def __init__(self, root_id = None, parent = None):
        super().__init__(parent)
        self.rootItem = playtree
        if root_id is not None:
            for item in playtree.iter_width(
                    lambda item: isinstance(item, PlayTreeList) and item.Id == root_id,
                    lambda item: isinstance(item, PlayTreeList)):
                self.rootItem = item
                break
        self.filter_string = ''

    def item(self, index):
        return index.internalPointer() if index.isValid() else self.rootItem

    # column "" provides browsing info (folder name, file name, ...)
    #_columns = ('', 'ARTIST', 'ALBUM', 'TITLE')
    _columns = ('',)

    def index(self, row, column, parent):
        self.__class__.current = self
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        parentItem = self.item(parent)
        childItem = parentItem.child(row)
        return self.createIndex(row, column, childItem) if childItem is not None else QModelIndex()

    def parent(self, index):
        self.__class__.current = self
        if not index.isValid():
            return index
        parentItem = self.item(index).parent
        return QModelIndex() if parentItem in (None, self.rootItem) else \
            self.createIndex(parentItem.row, 0, parentItem)

    def rowCount(self, parent):
        self.__class__.current = self
        # why oh why?
        if parent.column() > 0:
            return 0
        parentItem = self.item(parent)
        return parentItem.rowCount()

    def hasChildren(self, index):
        self.__class__.current = self
        return self.item(index).hasChildren()

    def columnCount(self, parent):
        self.__class__.current = self
        return len(self._columns)

    currentindexroles = (Qt.ForegroundRole, Qt.FontRole)
    def data(self, index, role = Qt.DisplayRole):
        self.__class__.current = self
        #if role in (Qt.ForegroundRole, Qt.FontRole):
        if role in self.currentindexroles:
            if index == self.view.player.current_index:
                if role == Qt.ForegroundRole:
                    return QBrush(QColor(Qt.red))
                elif role == Qt.FontRole:
                    font = QFont()
                    font.setWeight(QFont.Bold)
                    return font
        #elif role == Qt.DisplayRole:
        #    return 'data'
        else:
            return self.item(index).data(self._columns[index.column()], role)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._columns[section].title()

    def sibling(self, row, column, index):
        self.__class__.current = self
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
        for browse in self.rootItem.iter(
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
                query.browse._populate_tags(query.result)
            else: # query.method == Library.query_songs_all:
                query.browse._populate_songs(query.result)
        self.endResetModel()
        if self.filter_string:
            for item in self.rootItem.iter(
                    lambda item: isinstance(item, PlayTreeBrowse) or 
                    isinstance(item, PlayTreeFolder),
                    lambda item: isinstance(item, PlayTreeList)):
                item.expand_small_children(self)


from app import app
#app.aboutToQuit.connect(lambda: playtree.save(playtree_xml_filename))

tmSongIcon = QIcon(':images/song.png')
import tandamaster_rc

from library import *

