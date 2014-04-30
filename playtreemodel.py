from PyQt5.QtCore import pyqtRemoveInputHook; from IPython import embed
#pyqtRemoveInputHook(); embed()

import sys, filecmp

from lxml import etree
from PyQt5.Qt import *   # todo: import only what you need

import os, datetime, copy

class PlayTreeItem(etree.ElementBase):

    _keepalive = set() # todo: removing items from _keepalive when necessary
    _keepalive_on = True

    def _init(self):
        if self._keepalive_on:
            self._keepalive.add(self)

    @property
    def parent(self):
        return self._parent if '_parent' in self.__dict__ else self.getparent()
    @parent.setter
    def parent(self, parent):
        self._parent = parent

    @property
    def row(self):
        return self.parent.childs_row(self) if self.parent is not None else 0

    def modelindex(self, model):
        return QModelIndex() if self == model.rootItem else model.createIndex(self.row, 0, self)

    @property
    def isPlayable(self):
        return False

    def filter(self):
        return True

class PlayTreeList(PlayTreeItem):

    @property
    def name(self):
        return self.get('name', '')

    def __str__(self):
        return self.name

    @property
    def children(self):
        return [ c for c in self if c.filter() ]

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

class PlayTreeFile(PlayTreeItem):

    def _init(self):
        filename = self.get('filename')
        if filename:
            library = Library()
            def get_tag(self, tag):
                return library.tag_by_filename(tag, filename)
            def get_tags(self):
                return library.tags_by_filename(filename)
        else:
            library_name = self.get('library')
            Id = self.get('id')
            assert library_name and Id
            library = Library(library_name)
            def get_tag(self, tag):
                return library.tag_by_id(tag, Id)
            def get_tags(self):
                return library.tags_by_Id(Id)
        self.library = library
        self.get_tag = get_tag.__get__(self, self)
        self.get_tags = get_tags.__get__(self, self)

    @property
    def filename(self):
        filename = self.get('filename')
        if filename:
            return filename
        else:
            return self.library.filename_by_id(self.get('id'))

    def __str__(self):
        #pyqtRemoveInputHook(); embed()
        title = self.get_tag('TITLE')
        return title if title else os.path.basename(self.filename)

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
            if PlayTreeModel.current.filter_string in value:
                return True

class PlayTreeFolder(PlayTreeItem):

    @property
    def filename(self):
        return self.get('filename')

    def _init(self):
        super()._init()
        self._children = None

    def __str__(self):
        return self.get('filename', '')

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
                make_playtree_element(self, 'folder', filename=fullfn) for fn,fullfn in folders
            ]
            fileelements = [
                make_playtree_element(self, 'file', filename=fullfn) for fn,fullfn in files
            ]
            self._children.extend(filter(lambda f: f.get_tags() is not None, fileelements))
        
class PlayTreeBrowse(PlayTreeItem):
    @property
    def library_name(self):
        return self.get('library', '')

    def _init(self):
        super()._init()
        self._children = None
        library_name = self.get('library')
        assert library_name
        self.library = Library(library_name)
        self.value = None
   
    def __str__(self):
        return self.value if self.value is not None else \
            app.tr('Browse') + ' ' + self.library.name + ' ' + app.tr('by') + ' ' + ", ".join(
                by.get('tag').lower() for by in self.iterchildren('by'))

    @property
    def children(self):
        return self._children
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
            return str(self)
        elif column_name == '' and role == Qt.DecorationRole:
            return app.style().standardIcon(QStyle.SP_DriveCDIcon)

    def _populate(self, force = False):
        if force:
            self._children = None
        if self._children is None:
            fixed_tags = []
            tag = None
            for by in self.iterchildren('by'):
                value = by.get('value')
                if value is None:
                    tag = by.get('tag')
                    break
                else:
                    fixed_tags.append((by.get('tag'),value))
            if tag is not None:
                self._children = []
                N = len(fixed_tags)
                for value in self.library.query_distinct_tags_iter(tag, fixed_tags):
                    child = copy.deepcopy(self)
                    child[N].set('value', value)
                    child.parent = self
                    child.value = value
                    self._children.append(child)
            else:
                self._children = [
                    make_playtree_element(self, 'file', library=self.library.name, id = str(Id))
                    for Id in self.library.query_songs_iter(fixed_tags)
                ]

class PlayTreeLink(PlayTreeItem):
    pass

_namespace = "http://milonguero.si/tandamaster"
_namespace = None
_lookup = etree.ElementNamespaceClassLookup()
_playtree_namespace = _lookup.get_namespace(_namespace)
_playtree_namespace.update({
    'list': PlayTreeList,
    'file': PlayTreeFile,
    'folder': PlayTreeFolder,
    'browse': PlayTreeBrowse,
    'link': PlayTreeLink
})
playtree_parser = etree.XMLParser(remove_blank_text=True)
playtree_parser.set_element_class_lookup(_lookup)
playtree_xml_filename = 'playtree.xml'
try:
    playtree_xml_document = etree.parse(playtree_xml_filename, playtree_parser)
except:
    playtree_xml_document = etree.ElementTree(
        #etree.XML('<list xmlns="{}" id="root"/>'.format(_namespace), playtree_parser)
        etree.XML('<list id="root"/>', playtree_parser)
    )

def make_playtree_element(parent, tag, **kwargs):
    PlayTreeItem._keepalive_on = False
    element = playtree_parser.makeelement(tag, **kwargs)
    PlayTreeItem._keepalive_on = True
    element._parent = parent
    return element
    

def _timestamp(sep = ' '):
    ts = datetime.datetime.now().isoformat(sep)
    return ts[0:ts.index('.')]
        
def playtree_xml_save():
    with open(playtree_xml_filename + '.tmp', 'wb') as outfile:
        playtree_xml_document.write(outfile, pretty_print = True, encoding='UTF-8')
        if filecmp.cmp(playtree_xml_filename, playtree_xml_filename + '.tmp'):
            os.remove(playtree_xml_filename + '.tmp')
        else:
            try:
                os.rename(playtree_xml_filename, playtree_xml_filename + '.' + _timestamp('_') + '.bak')
            except:
                pass
            os.rename(playtree_xml_filename + '.tmp', playtree_xml_filename)


class PlayTreeModel(QAbstractItemModel):
    current = None

    def __init__(self, root_xml_id = None, parent = None):
        super().__init__(parent)
        self.rootItem = playtree_xml_document.xpath('//*[@id="{}"]'.format(root_xml_id))[0] \
                        if root_xml_id is not None else playtree_xml_document.getroot()
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
        self.filter_string = string
        self.beginResetModel()
        self.endResetModel()

from app import app
#app.aboutToQuit.connect(playtree_xml_save)

tmSongIcon = QIcon(':images/song.png')
import tandamaster_rc

from library import Library
library = Library()
