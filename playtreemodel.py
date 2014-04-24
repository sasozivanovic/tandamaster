from IPython import embed
import sys, filecmp

from lxml import etree
from PyQt5.Qt import *   # todo: import only what you need

import os, datetime

class PlayTreeItem(etree.ElementBase):

    _keepalive = set() # todo: removing items from _keepalive when necessary
    _keepalive_on = True

    def _init(self):
        if self._keepalive_on:
            self._keepalive.add(self)

    @property
    def parent(self):
        return self._parent if '_parent' in self.__dict__ else self.getparent()

    @property
    def row(self):
        return self.parent.childs_row(self) if self.parent is not None else 0

    def modelindex(self, model):
        return QModelIndex() if self == model.rootItem else model.createIndex(self.row, 0, self)

    @property
    def isPlayable(self):
        return False

class PlayTreeList(PlayTreeItem):

    @property
    def name(self):
        return self.get('name', '')

    def __str__(self):
        return self.name

    def rowCount(self): # todo: filtering
        return len(self)

    def hasChildren(self):
        return bool(len(self)) # todo: filtering

    def child(self, row): # todo: filtering
        try:
            return self[row]
        except IndexError:
            return None

    def childs_row(self, child): # todo: filtering
        return self.index(child)

    def data(self, column_name, role):
        if column_name:
            return None
        if role == Qt.DisplayRole:
            return self.name

class PlayTreeFile(PlayTreeItem):

    @property
    def filename(self):
        return self.get('filename')

    def __str__(self):
        return self.get('filename', '')

    def rowCount(self):
        return 0

    def hasChildren(self):
        return False

    def child(self, row):
        return None

    def data(self, column_name, role):
        if column_name and role == Qt.DisplayRole:
            return librarian.tag(column_name, self.filename)
        elif role == Qt.DisplayRole:
            return os.path.basename(self.filename)
        elif not column_name and role == Qt.DecorationRole:
            return tmSongIcon

    @property
    def tags(self):
        return librarian.tags(filename = self.filename)

    def childs_row(self, child):
        return None

    @property
    def isPlayable(self):
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

    def rowCount(self): # todo: filtering
        self._populate()
        return len(self._children)

    def hasChildren(self): # todo: filtering & hasChildren in the model
        if self._children is None:
            return True
        else:
            return bool(len(self._children))

    def child(self, row): # todo: filtering
        self._populate()
        return self._children[row]

    def childs_row(self, child): # todo: filtering
        try:
            return self._children.index(child)
        except IndexError:
            return None

    def data(self, column_name, role):
        if column_name:
            return None
        if role == Qt.DisplayRole:
            return os.path.basename(self.filename)
        elif role == Qt.DecorationRole:
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
            self._children.extend(
                make_playtree_element(self, 'file', filename=fullfn) for fn,fullfn in files
            )
        
class PlayTreeBrowse(PlayTreeItem):
    pass

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

    def __init__(self, root_xml_id = None, parent = None):
        super().__init__(parent)
        self.rootItem = playtree_xml_document.xpath('//*[@id="{}"]'.format(root_xml_id))[0] \
                        if root_xml_id is not None else playtree_xml_document.getroot()

    def item(self, index):
        return index.internalPointer() if index.isValid() else self.rootItem

    # column "" provides browsing info (folder name, file name, ...)
    _columns = ('', 'ARTIST', 'ALBUM', 'TITLE')

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        parentItem = self.item(parent)
        childItem = parentItem.child(row)
        return self.createIndex(row, column, childItem) if childItem is not None else QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return index
        parentItem = self.item(index).parent
        return QModelIndex() if parentItem in (None, self.rootItem) else \
            self.createIndex(parentItem.row, 0, parentItem)

    def rowCount(self, parent):
        # why oh why?
        if parent.column() > 0:
            return 0
        parentItem = self.item(parent)
        return parentItem.rowCount()

    def hasChildren(self, index):
        return self.item(index).hasChildren()

    def columnCount(self, parent):
        return len(self._columns)

    def data(self, index, role = Qt.DisplayRole):
        if role in (Qt.ForegroundRole, Qt.FontRole):
            if index == self.view.player.current_index:
                if role == Qt.ForegroundRole:
                    return QBrush(QColor(Qt.red))
                elif role == Qt.FontRole:
                    font = QFont()
                    font.setWeight(QFont.Bold)
                    return font
        else:
            return self.item(index).data(self._columns[index.column()], role)

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

from app import app
#app.aboutToQuit.connect(playtree_xml_save)

tmSongIcon = QIcon(':images/song.png')
import tandamaster_rc

from library import Librarian
librarian = Librarian()
