from IPython import embed

from lxml import etree
from PyQt5.Qt import *   # todo: import only what you need

import os, datetime

tandamaster_namespace = "http://milonguero.si/tandamaster"

class PlayTreeItem:
    def my_row(self):
        return self.parent.childs_row(self) if self.parent is not None else None

class PlayTreeItem_XML(etree.ElementBase, PlayTreeItem):
    @property
    def parent(self):
        return self.getparent()
    def _clean(self):
        pass

class PlayTreeList_XML(PlayTreeItem_XML):
    @property
    def name(self):
        return self.get('name')
    def __str__(self):
        return self.name
    def childCount(self):
        return len(self)
    def child(self, row):
        try:
            return self[row]
        except IndexError:
            return None
    def childs_row(self, child):
        return self.index(child)
    def data(self, column_name, role):
        if column_name:
            return None
        if role == Qt.DisplayRole:
            return self.name
    def _clean(self):
        for child in element:
            self._clean()

class PlayTreeFile(PlayTreeItem):
    def __init__(self, parent, filename):
        self.parent = parent
        self.filename = filename
    def __str__(self):
        return self.filename    
    def childCount(self):
        return 0
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

class PlayTreeFile_XML(PlayTreeItem_XML, PlayTreeFile):
    @property
    def filename(self):
        return self.get('filename')

class PlayTreeFolder(PlayTreeItem):
    def __init__(self, parent, filename):
        self.parent = parent
        self.filename = filename
        self._children = None

    def __str__(self):
        return self.filename

    def childCount(self):
        if self._children is None:
            self._populate()
        return len(self._children)

    def hasChildren(self):
        return True

    def child(self, row):
        if self._children is None:
            self._populate()
        return self._children[row]

    def childs_row(self, child):
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

    def _populate(self):
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
        self._children = [ PlayTreeFolder(self, fullfn) for fn,fullfn in folders ]
        self._children.extend(PlayTreeFile(self, fullfn) for fn,fullfn in files)
        
class PlayTreeFolder_XML(PlayTreeItem_XML, PlayTreeFolder):
    @property
    def filename(self):
        return self.get('filename')
    def _init(self):
        self._children = None
        self.keepalive = self
    def _clean(self):
        self.keepalive = None

class PlayTreeBrowse(PlayTreeItem):
    pass

class PlayTreeBrowse_XML(PlayTreeItem_XML, PlayTreeBrowse):
    pass

class PlayTreeBrowsedFile(PlayTreeFile):
    pass


_lookup = etree.ElementNamespaceClassLookup()
_playtree_namespace = _lookup.get_namespace(tandamaster_namespace)
_playtree_namespace.update({
    'list': PlayTreeList_XML,
    'file': PlayTreeFile_XML,
    'folder': PlayTreeFolder_XML,
    'browse': PlayTreeBrowse_XML
})
playtree_parser = etree.XMLParser(remove_blank_text=True)
playtree_parser.set_element_class_lookup(_lookup)

class PlayTreeModel(QAbstractItemModel):
    def __init__(self, playtree_xml_filename, parent = None):
        super().__init__(parent)
        
        self.playtree_xml_filename = playtree_xml_filename
        try:
            self.playtree_xml_document = etree.parse(playtree_xml_filename, playtree_parser)
        except:
            self.playtree_xml_document = etree.ElementTree(
                etree.XML('<list xmlns="{}" id="root"/>'.format(tandamaster_namespace), playtree_parser)
            )
        self.rootItem = self.playtree_xml_document.getroot()
        self._current_index = QModelIndex()

    @property
    def current(self):
        return self.current_index.internalPointer() if self.isPlayable(self.current_index) else None

    @property
    def current_index(self):
        return self._current_index
    @current_index.setter
    def current_index(self, index):
        if self._current_index != index:
            old_index = self._current_index
            self._current_index = index
            self.dataChanged.emit(self.sibling_column_index(old_index, 0),
                                  self.sibling_column_index(old_index, -1),
                                  [Qt.ForegroundRole, Qt.FontRole])
            self.dataChanged.emit(self.sibling_column_index(index, 0),
                                  self.sibling_column_index(index, -1),
                                  [Qt.ForegroundRole, Qt.FontRole])
            self.current_changed.emit(old_index, index)
    current_changed = pyqtSignal(QModelIndex, QModelIndex)

    def sibling_column_index(self, index, column):
        if column == -1:
            column = self.columnCount(index)
        return self.index(index.row(), column, index.parent())

    # column "" provides browsing info (folder name, file name, ...)
    _columns = ('', 'ARTIST', 'ALBUM', 'TITLE')

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem is not None:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return index

        parentItem = index.internalPointer().parent

        if parentItem == self.rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.my_row(), 0, parentItem)

    def rowCount(self, parent):
        # why oh why?
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def columnCount(self, parent):
        return len(self._columns)
    
    def data(self, index, role = Qt.DisplayRole):
        if role in (Qt.ForegroundRole, Qt.FontRole):
            if index == self.current_index:
                if role == Qt.ForegroundRole:
                    return QBrush(QColor(Qt.red))
                elif role == Qt.FontRole:
                    font = QFont()
                    font.setWeight(QFont.Bold)
                    return font
        else:
            return index.internalPointer().data(self._columns[index.column()], role)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._columns[section].title()
        return None

    def save(self):
        with open(self.playtree_xml_filename + '.tmp', 'wb') as outfile:
            self.playtree_xml_document.write(outfile, pretty_print = True, encoding='UTF-8')
            try:
                os.rename(self.playtree_xml_filename, self.playtree_xml_filename + '.' + _timestamp('_') + '.bak')
            except:
                pass
            os.rename(self.playtree_xml_filename + '.tmp', self.playtree_xml_filename)

    def _clean(self):
        """Removes the references to _XML objects with children.

There references were created to keep the objects alive.  See lxml's
"Using custom Element class in lxml, Element initialization".
"""
        self.rootItem._clean()

    def row(self, index):
        return index.internalPointer().my_row()

    def next(self, index = None):
        if index is None:
            index = self.current_index
        descend  = True
        if not index.isValid():
            index = self.index(0,0,index)
        while index.isValid():
            if descend:
                next_index = self.index(0, 0, index)
            else:
                parent = self.parent(index)
                next_index = self.index(self.row(index)+1, 0, parent)
            if next_index.isValid():
                return next_index
            else:
                if not descend:
                    index = parent
                descend = False
        return index

    def next_song(self, index = None):
        if index is None:
            index = self.current_index
        index = self.next(index)
        while index.isValid() and not self.isPlayable(index):
            index = self.next(index)
        return index

    def previous(self, index = None):
        if index is None:
            index = self.current_index
        if index.isValid():
            row = self.row(index)
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

    def previous_song(self, index = None):
        if index is None:
            index = self.current_index
        index = self.previous(index)
        while index.isValid() and not self.isPlayable(index):
            index = self.previous(index)
        return index

    def isPlayable(self, index):
        return isinstance(index.internalPointer(), PlayTreeFile) if index.isValid() else False

    def ancestors(self, index):
        ancestors = []
        while index.isValid():
            ancestors.append(index)
            index = self.parent(index)
        return ancestors

def _timestamp(sep = ' '):
    ts = datetime.datetime.now().isoformat(sep)
    return ts[0:ts.index('.')]

from globals import *

from library import Librarian
librarian = Librarian()
