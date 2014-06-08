from PyQt5.QtCore import pyqtRemoveInputHook; from IPython import embed; pyqtRemoveInputHook()

from PyQt5.Qt import *   # todo: import only what you need

from player import TandaMasterPlayer
from model import *
from library import Library
from util import *
from app import *
from commands import *

import collections, weakref

class TandaMasterWindow(QMainWindow):

    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle('TandaMaster')        

        self.player = TandaMasterPlayer()
        #self.player2 = TandaMasterPlayer() # pre-listening

        #splitter = QSplitter()
        #splitter.addWidget(PlayTreeWidget(None, self.player))
        #splitter.addWidget(PlayTreeWidget(None, self.player))
        #self.setCentralWidget(splitter)
        self.setCentralWidget(TMWidget.create_from_xml(etree.parse('central_widget.xml').getroot()))
        for ptv in self.centralWidget().findChildren(PlayTreeWidget):
            ptv.set_player(self.player)

        menubar = QMenuBar()

        self.musicmenu = QMenu(self.tr('&Music'))
        action_save_playtree = QAction(
            self.tr("&Save playtree"), self,
            shortcut=QKeySequence.Save,
            triggered = save_playtree)
        self.musicmenu.addAction(action_save_playtree)
        action_update_library = QAction(
            self.tr("&Update library"), self,
            triggered = self.update_library)
        self.musicmenu.addAction(action_update_library)
        action_quit = QAction(
            self.tr("&Quit"), self, shortcut=QKeySequence.Quit,
            statusTip="Quit the program", triggered=self.close)
        self.musicmenu.addAction(action_quit)
        menubar.addMenu(self.musicmenu)

        self.playbackmenu = QMenu(self.tr('&Playback'))
        self.action_back = QAction(
            #self.style().standardIcon(QStyle.SP_MediaSkipBackward), 
            #MyIcon('Tango', 'actions', 'media-skip-backward'),
            QIcon('button_rewind_green.png'),
            #QIcon('icons/iconfinder/32pxmania/previous.png'),
            self.tr('P&revious'), self, triggered = self.player.play_previous)
        self.playbackmenu.addAction(self.action_back)        
        self.action_play = QAction(
            #self.style().standardIcon(QStyle.SP_MediaPlay), 
            #MyIcon('Tango', 'actions', 'media-playback-start'),
            QIcon('button_play_green.png'),
            #QIcon('icons/iconfinder/32pxmania/play.png'),
            self.tr('&Play'), 
            self,
            shortcut = QKeySequence('space'),
            triggered = self.player.play)
        self.playbackmenu.addAction(self.action_play)
        self.action_pause =  QAction(
            #self.style().standardIcon(QStyle.SP_MediaPause), 
            #MyIcon('Tango', 'actions', 'media-playback-pause'),
            QIcon('button_pause_green.png'),
            #QIcon('icons/iconfinder/32pxmania/pause.png'),
            self.tr('&Pause'), self, 
            shortcut = QKeySequence('space'),
            triggered = self.player.pause)
        self.playbackmenu.addAction(self.action_pause)        
        self.action_stop = QAction(
            #self.style().standardIcon(QStyle.SP_MediaStop), 
            #MyIcon('Tango', 'actions', 'media-playback-stop'),
            QIcon('button_stop_green.png'),
            #QIcon('icons/iconfinder/32pxmania/stop.png'),
            self.tr('&Stop'), self, triggered = self.player.stop)
        self.playbackmenu.addAction(self.action_stop)        
        self.action_forward = QAction(
            #self.style().standardIcon(QStyle.SP_MediaSkipForward), 
            #MyIcon('Tango', 'actions', 'media-skip-forward'),
            QIcon('button_fastforward_green.png'),
            #QIcon('icons/iconfinder/32pxmania/next.png'),
            self.tr('&Next'), self, triggered = self.player.play_next)
        self.playbackmenu.addAction(self.action_forward)
        self.playbackmenu.addSeparator()
        self.action_lock = QAction(
            QIcon('icons/iconfinder/iconza/unlocked.png'),
            self.tr('Un&locked'), self, toggled = self.lock)
        self.action_lock.setCheckable(True)
        self.playbackmenu.addAction(self.action_lock)
        menubar.addMenu(self.playbackmenu)

        self.playtreemenu = QMenu(self.tr('Play&tree'))
        self.action_cut = QAction(
            MyIcon('Tango', 'actions', 'edit-cut'),
            self.tr('Cu&t'), self, triggered = self.playtree_cut,
            shortcut = QKeySequence(QKeySequence.Cut))
        self.action_copy = QAction(
            MyIcon('Tango', 'actions', 'edit-copy'),
            self.tr('&Copy'), self, triggered = self.playtree_copy,
            shortcut = QKeySequence(QKeySequence.Copy))
        self.action_paste = QAction(
            MyIcon('Tango', 'actions', 'edit-paste'),
            self.tr('&Paste'), self, triggered = self.playtree_paste,
            shortcut = QKeySequence(QKeySequence.Paste))
        self.action_insert = QAction(
            QIcon('icons/iconfinder/32pxmania/insert.png'),
            self.tr('&Insert'), self, triggered = self.playtree_insert,
            shortcut = QKeySequence('insert'))        
        self.action_delete = QAction(
            QIcon('icons/iconfinder/32pxmania/delete.png'),
            self.tr('&Delete'), self, triggered = self.playtree_delete,
            shortcut = QKeySequence(QKeySequence.Delete))
        self.action_move_up = QAction(
            QIcon('icons/iconfinder/32pxmania/up.png'),
            self.tr('Move &up'), self, triggered = self.playtree_move_up,
            shortcut = QKeySequence('alt+up'))
        self.action_move_down = QAction(
            QIcon('icons/iconfinder/32pxmania/down.png'),
            self.tr('Move &down'), self, triggered = self.playtree_move_down,
            shortcut = QKeySequence('alt+down'))
        self.action_move_left = QAction(
            QIcon('icons/iconfinder/momentum_glossy/arrow-up-left.png'),
            self.tr('Move &out of parent'), self, triggered = self.playtree_move_left,
            shortcut = QKeySequence('alt+left'))
        self.action_move_right = QAction(
            QIcon('icons/iconfinder/momentum_glossy/arrow-down-right.png'),
            self.tr('Move into &next sibling'), self, triggered = self.playtree_move_right,
            shortcut = QKeySequence('alt+right'))
        self.action_move_home = QAction(
            QIcon('icons/iconfinder/momentum_glossy/move_top.png'),
            self.tr('Move to &top'), self, triggered = self.playtree_move_home,
            shortcut = QKeySequence('alt+home'))
        self.action_move_end = QAction(
            QIcon('icons/iconfinder/momentum_glossy/move_bottom.png'),
            self.tr('Move to &bottom'), self, triggered = self.playtree_move_end,
            shortcut = QKeySequence('alt+end'))
        action_undo = undo_stack.createUndoAction(self)
        action_redo = undo_stack.createRedoAction(self)
        action_undo.setIcon(QIcon('icons/iconfinder/32pxmania/undo.png'))
        action_redo.setIcon(QIcon('icons/iconfinder/32pxmania/redo.png'))
        action_undo.setShortcut(QKeySequence(QKeySequence.Undo))
        action_redo.setShortcut(QKeySequence(QKeySequence.Redo))
        self.playtreemenu.addAction(action_undo)
        self.playtreemenu.addAction(action_redo)
        self.playtreemenu.addSeparator()
        self.playtreemenu.addAction(self.action_cut)
        self.playtreemenu.addAction(self.action_copy)
        self.playtreemenu.addAction(self.action_paste)
        self.playtreemenu.addSeparator()
        self.playtreemenu.addAction(self.action_insert)
        self.playtreemenu.addAction(self.action_delete)
        self.playtreemenu.addAction(self.action_move_home)
        self.playtreemenu.addAction(self.action_move_up)
        self.playtreemenu.addAction(self.action_move_down)
        self.playtreemenu.addAction(self.action_move_end)
        self.playtreemenu.addAction(self.action_move_left)
        self.playtreemenu.addAction(self.action_move_right)

        menubar.addMenu(self.playtreemenu)

        self.setMenuBar(menubar)

        toolbar = QToolBar('ProgressBar', self)
        pb = TMProgressBar(self.player)
        toolbar.addWidget(pb)
        self.addToolBar(Qt.BottomToolBarArea, toolbar)

        self.addToolBarBreak(Qt.BottomToolBarArea)

        toolbar = QToolBar('Play controls', self)
        toolbar.setAllowedAreas(Qt.TopToolBarArea | Qt.BottomToolBarArea)
        toolbar.setFloatable(False)
        #toolbar.setIconSize(2*toolbar.iconSize())
        toolbar.addAction(self.action_back)
        toolbar.addAction(self.action_play)
        toolbar.addAction(self.action_pause)
        toolbar.addAction(self.action_stop)
        toolbar.addAction(self.action_forward)
        toolbar.addSeparator()
        toolbar.addAction(self.action_lock)
        self.song_info = QLabel()
        self.song_info.setContentsMargins(8,0,0,0)
        toolbar.addWidget(QWidget())
        toolbar.addWidget(self.song_info)
        self.addToolBar(Qt.BottomToolBarArea, toolbar)
        
        toolbar = QToolBar('Edit', self)
        toolbar.addAction(action_undo)
        toolbar.addAction(action_redo)
        toolbar.addSeparator()
        toolbar.addAction(self.action_cut)
        toolbar.addAction(self.action_copy)
        toolbar.addAction(self.action_paste)
        toolbar.addSeparator()
        toolbar.addAction(self.action_insert)
        toolbar.addAction(self.action_delete)
        toolbar.addAction(self.action_move_home)
        toolbar.addAction(self.action_move_up)
        toolbar.addAction(self.action_move_down)
        toolbar.addAction(self.action_move_end)
        toolbar.addAction(self.action_move_left)
        toolbar.addAction(self.action_move_right)
        
        self.addToolBar(toolbar)        

        self.setStatusBar(QStatusBar())

        self.player.currentMediaChanged.connect(self.update_song_info)
        self.player.currentMediaChanged.connect(lambda: self.lock_action_forward())
        self.player.stateChanged.connect(self.on_player_state_changed)
        self.on_player_state_changed(QMediaPlayer.StoppedState)
        QApplication.clipboard().changed.connect(self.on_clipboard_data_changed)

    def sizeHint(self):
        return QSize(1800, 800)

    song_info_formatter = PartialFormatter()
    def update_song_info(self, media):
        item = self.player.current_item
        if item:
            tags = item.get_tags()
            self.setWindowTitle(self.song_info_formatter.format(
                "{ARTIST} - {TITLE} | TandaMaster", **tags))
            self.song_info.setText(self.song_info_formatter.format(
                "{ARTIST} <b>{TITLE}</b>", **tags))
        else:
            self.setWindowTitle("TandaMaster")
            self.song_info.setText("")

    def on_player_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.action_play.setVisible(False)
            self.action_pause.setVisible(True)
            self.action_stop.setEnabled(not self.action_lock.isChecked())
        else:
            self.action_play.setVisible(True)
            self.action_pause.setVisible(False)
            self.action_stop.setEnabled(state != QMediaPlayer.StoppedState and not self.action_lock.isChecked())
                
    def update_library(self):
        Library('tango').refresh(['/home/saso/tango'])

    def playtree_cut(self):
        ptv = app.focusWidget()
        if not isinstance(ptv, PlayTreeView): return
        ptv.cut()

    def playtree_copy(self):
        ptv = app.focusWidget()
        if not isinstance(ptv, PlayTreeView): return
        ptv.copy()

    def playtree_paste(self):
        ptv = app.focusWidget()
        if not isinstance(ptv, PlayTreeView): return
        ptv.paste()

    def on_clipboard_data_changed(self, mode):
        if mode == QClipboard.Clipboard:
            ptv = app.focusWidget()
            if not isinstance(ptv, PlayTreeView): return
            self.window().action_paste.setEnabled(ptv.can_paste())

    def playtree_delete(self):
        ptv = app.focusWidget()
        if not isinstance(ptv, PlayTreeView): return
        ptv.delete()

    def playtree_insert(self):
        ptv = app.focusWidget()
        if not isinstance(ptv, PlayTreeView): return
        ptv.insert()

    def playtree_move_up(self):
        ptv = app.focusWidget()
        if not isinstance(ptv, PlayTreeView): return
        ptv.move_up()

    def playtree_move_down(self):
        ptv = app.focusWidget()
        if not isinstance(ptv, PlayTreeView): return
        ptv.move_down()

    def playtree_move_left(self):
        ptv = app.focusWidget()
        if not isinstance(ptv, PlayTreeView): return
        ptv.move_left()

    def playtree_move_right(self):
        ptv = app.focusWidget()
        if not isinstance(ptv, PlayTreeView): return
        ptv.move_right()

    def playtree_move_home(self):
        ptv = app.focusWidget()
        if not isinstance(ptv, PlayTreeView): return
        ptv.move_home()

    def playtree_move_end(self):
        ptv = app.focusWidget()
        if not isinstance(ptv, PlayTreeView): return
        ptv.move_end()

    def lock(self, locked):
        if locked:
            self.action_lock.setIcon(QIcon('icons/iconfinder/iconza/locked.png'))
            self.action_lock.setText(app.tr('&Locked'))
            self.action_play.setEnabled(locked)
        else:
            self.action_lock.setIcon(QIcon('icons/iconfinder/iconza/unlocked.png'))
            self.action_lock.setText(app.tr('Un&locked'))
        self.action_back.setEnabled(not locked)
        self.action_play.setEnabled(not locked)
        self.action_pause.setEnabled(not locked)
        self.action_stop.setEnabled(not locked)
        self.lock_action_forward(locked)

    def lock_action_forward(self, locked = None):
        if locked is None:
            locked = self.action_lock.isChecked()
        self.action_forward.setEnabled(not locked or self.player.current_item.function() == 'cortina')



class TMWidget:
    xml_tag_registry = {}

    @classmethod
    def register_xml_tag_handler(cls, tag):
        def f(subcls):
            cls.xml_tag_registry[tag] = subcls
            cls.xml_tag = tag
            return subcls
        return f

    @classmethod
    def create_from_xml(cls, element, parent = None):
        return cls.xml_tag_registry[element.tag]._create_from_xml(element, parent)

    def to_xml(self):
        return etree.Element(self.xml_tag)

@TMWidget.register_xml_tag_handler('splitter')
class TMSplitter(QSplitter, TMWidget):
    @classmethod
    def _create_from_xml(cls, element, parent):
        splitter = cls(parent = parent)
        for subelement in element:
            splitter.addWidget(cls.create_from_xml(subelement, splitter))
        return splitter

    def to_xml(self):
        element = super().to_xml()
        for child in self.children():
            element.append(child.to_xml())

@TMWidget.register_xml_tag_handler('playtree')
class PlayTreeWidget(QWidget, TMWidget):

    @classmethod
    def _create_from_xml(cls, element, parent):
        ptv = cls(element.get('id'), parent)
        return ptv

    def to_xml(self):
        element = super().to_xml()
        element.set('id', self.ptv.model().root_item.Id)

    def __init__(self, root_id, parent = None):
        super().__init__(parent)

        self.current_model_button = QToolButton()
        #current_model_button.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        #current_model_button.setIcon(QIcon('circle_green.png'))
        self.current_model_button.setIcon(QIcon('icons/iconfinder/32pxmania/current_playtree.png')),
        self.current_model_button.setCheckable(True)
        self.search = QLineEdit()
        self.ptv = PlayTreeView(root_id, self)

        controls = QToolBar()
        controls.addWidget(self.current_model_button)
        controls.addWidget(self.search)

        widget_layout = QVBoxLayout()
        self.setLayout(widget_layout)
        widget_layout.addWidget(controls)
        widget_layout.addWidget(self.ptv)

        self.search.textChanged.connect(lambda: QTimer.singleShot(50, self.refilter))

        self.addAction(QAction(
            self, 
            shortcut = QKeySequence.Find, 
            shortcutContext = Qt.WidgetWithChildrenShortcut,
            triggered = lambda: self.search.setFocus(Qt.ShortcutFocusReason)))

        self.search.returnPressed.connect(lambda: self.ptv.setFocus(Qt.OtherFocusReason))
        
        self.addAction(QAction(
            self, 
            shortcut = QKeySequence('Escape'),
            shortcutContext = Qt.WidgetWithChildrenShortcut,
            triggered = self.search.clear))

    def set_player(self, player):
        if self.ptv.player:
            for connection in self.player_connections:
                self.disconnect(connection)
        self.player_connections = []
        self.ptv.set_player(player)
        self.player_connections.append(
            self.current_model_button.toggled.connect(
                lambda checked: player.set_current(
                    model = self.ptv.model()) if checked else None))
        self.player_connections.append(
            player.current_changed.connect(
            lambda old_model, old_index, model, index: 
                self.current_model_button.setChecked(
                self.ptv.model() == model)))
        self.player_connections.append(
            self.current_model_button.setChecked(self.ptv.model() == player.current_model))

    def refilter(self):
        self.ptv.model().refilter(self.search.text())
        
class PlayTreeView(QTreeView):

    def __init__(self, root_id, parent = None):
        super().__init__(parent)
        self.setUniformRowHeights(True)

        model = PlayTreeModel(root_id, self)
        self.setModel(model)
        model.view = self
        self.player = None

        self.setExpandsOnDoubleClick(False)
        self.expanded.connect(self.on_expanded)
        self.collapsed.connect(self.on_collapsed)
        self._autoexpanded = None
        self._autoexpand_on = True

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.selectionModel().selectionChanged.connect(self.on_currentIndex_changed)

        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setEditTriggers(QAbstractItemView.EditKeyPressed)

    def set_player(self, player):
        if self.player:
            for connection in self.player_connections:
                self.disconnect(connection)
        self.player = player
        self.player_connections = []
        self.player_connections.append(           
            self.activated.connect(self.on_activated))
        self.player_connections.append(
            player.current_changed.connect(self.on_current_changed))
        if not self.player.current_model:
            self.player.set_current(model = self.model())
        self.player_connections.append(
            self.model().modelReset.connect(self.on_end_reset_model))

    def on_expanded(self, index):
        model = self.model()
        model.item(index).expanded[model] = True
        if model == self.player.current_model and \
           index in model.ancestors(self.player.current_index):
            self._autoexpand_on = True
        self.autosize_columns()

    def on_collapsed(self, index):
        model = self.model()
        model.item(index).expanded[model] = False
        if model == self.player.current_model and \
           index in model.ancestors(self.player.current_index):
            self._autoexpand_on = False

    def on_current_changed(self, old_model, old_index, model, index):
        if self._autoexpand_on:
            if self._autoexpanded and old_model == self.model():
                while old_index.isValid():
                    if old_index.isValid():
                        self.collapse(old_index)
                    if old_index == self._autoexpanded:
                        break
                    old_index = old_model.parent(old_index)
            if model == self.model():
                while index.isValid() and not self.isExpanded(index):
                    self.expand(index)
                    self._autoexpanded = index
                    index = model.parent(index)

    def on_activated(self, index):
        if self.player.current_model == self.model():
            if not self.window().action_lock.isChecked():
                self.player.play_index(index)
        else:
            destination = self.other().model().root_item
            if destination.are_children_manually_set:
                InsertPlayTreeItemsCommand(
                    [self.model().item(self.currentIndex()).copy()],
                    destination,
                    None)

    def autosize_columns(self):
        return
        columns = self.model().columnCount(QModelIndex())
        for i in range(columns):
            self.resizeColumnToContents(i)

    def on_end_reset_model(self):
        model = self.model()
        for item in model.root_item.iter(model,
                lambda item: not item.isTerminal,
                lambda item: isinstance(item, PlayTreeList)):
            if model in item.expanded:
                self.setExpanded(item.index(model), item.expanded[model])

    def cut(self):
        selected = self.selectedIndexes()
        QApplication.clipboard().setMimeData(self.model().mimeData(selected))
        self.delete()

    def delete(self):
        model = self.model()
        selection_model = self.selectionModel()
        item_selection = selection_model.selection() #QItemSelection
        current_index = self.currentIndex()
        current_path = model.index_to_path(current_index)
        DeletePlayTreeItemsCommand(
            [model.item(index) for index in item_selection.indexes()])
        current_index = model.path_to_index(current_path)
        if current_index.isValid():
            selection_model.setCurrentIndex(current_index, QItemSelectionModel.ClearAndSelect)

    def copy(self):
        QApplication.clipboard().setMimeData(
            self.model().mimeData(self.selectedIndexes()))

    def paste(self):
        model = self.model()
        current_index = self.currentIndex()
        current_path = model.index_to_path(current_index)
        parent_item, row, column = (model.item(current_index).parent, current_index.row(), current_index.column()) if current_index.isValid() else (QModelIndex(), -1, -1)
        new_items = parent_item.dropMimeData(QApplication.clipboard().mimeData(), Qt.CopyAction, row, column, command_prefix = 'Paste')
        inserted_items = [item for item in new_items
                          if item in item.parent.children[model]]
        selection_model = self.selectionModel()
        selection_model.clear()
        for item in inserted_items:
            selection_model.select(item.index(model),QItemSelectionModel.Select|QItemSelectionModel.Rows)
        selection_model.setCurrentIndex(
            model.path_to_index(current_path), QItemSelectionModel.NoUpdate)

    def insert(self, name = 'New playtree'):
        model = self.model()
        current_index = self.currentIndex()
        current_item = model.item(current_index)
        new_item = PlayTreeList(name)
        if current_index.isValid():
            InsertPlayTreeItemsCommand([new_item], current_item.parent, current_item, Id = 1)
        else:
            InsertPlayTreeItemsCommand([new_item], model.root_item, None, Id = 1)
        new_index = new_item.index(model)
        self.setCurrentIndex(new_index)
        self.edit(new_index)

    def can_cut(self):
        model = self.model()
        for index in self.selectedIndexes():
            if not model.item(index).parent.are_children_manually_set:
                return False
        return True

    def can_copy(self):
        return bool(self.selectedIndexes())

    def can_paste(self):
        if self.can_insert():
            mime_data = QApplication.clipboard().mimeData()
            return isinstance(mime_data, PlayTreeMimeData) or mime_data.hasFormat('audio/x-mpegurl') or mime_data.hasFormat('text/uri-list')
        else:
            return False

    def can_insert(self):
        if self.currentIndex().isValid():
            return self.model().item(self.currentIndex()).parent.are_children_manually_set
        else:
            return self.model().root_item.are_children_manually_set
        

    def can_move(self):
        model = self.model()
        selection_model = self.selectionModel()
        item_selection = selection_model.selection()
        if not item_selection: return (False,)*6
        parent_index = item_selection[0].parent()
        parent = model.item(parent_index)
        if not parent.are_children_manually_set: return (False,)*6
        for range in item_selection:
            if range.parent() != parent_index:
                return (False,)*6
        ranges = sorted([(range.top(), range.bottom()) for range in item_selection])
        if len(item_selection) > 1:
            for bottom, top in zip([range[1] for range in ranges[1:]],
                                   [range[0] for range in ranges[:-1]]):
                if bottom != top + 1: 
                    return (False,)*6
        top = ranges[0][0]
        bottom = ranges[-1][1]
        top_index = model.index(top, 0, parent_index)
        bottom_index = model.index(bottom, 0, parent_index)
        grandparent_index = model.parent(parent_index)
        grandparent_item = model.item(grandparent_index)
        can_move_up = top_index.row() != 0 or (parent_index.isValid() and parent_index.row() != 0 and model.item(model.index(parent_index.row()-1,0,grandparent_index)).are_children_manually_set)
        can_move_down = bottom_index.row() != model.rowCount(parent_index)-1 or (parent_index.isValid() and parent_index.row() != model.rowCount(grandparent_index)-1 and model.item(model.index(parent_index.row()+1,0,grandparent_index)).are_children_manually_set)
        can_move_left = parent_index.isValid()
        can_move_right = model.rowCount(parent_index) > ranges[-1][1]+1 and model.item(model.index(ranges[-1][1]+1, 0, parent_index)).are_children_manually_set
        can_move_home = top != 0 or (parent_index.isValid() and model.root_item.are_children_manually_set)
        can_move_end = bottom != model.rowCount(parent_index)-1 or (parent_index.isValid() and model.root_item.are_children_manually_set)
        return can_move_up, can_move_down, can_move_left, can_move_right, can_move_home, can_move_end

    def on_selection_changed(self):
        can_cut = self.can_cut()
        self.window().action_cut.setEnabled(can_cut)
        self.window().action_delete.setEnabled(can_cut)
        self.window().action_copy.setEnabled(self.can_copy())
        can_move_up, can_move_down, can_move_left, can_move_right, can_move_home, can_move_end = self.can_move()
        self.window().action_move_up.setEnabled(can_move_up)
        self.window().action_move_down.setEnabled(can_move_down)
        self.window().action_move_left.setEnabled(can_move_left)
        self.window().action_move_right.setEnabled(can_move_right)
        self.window().action_move_home.setEnabled(can_move_home)
        self.window().action_move_end.setEnabled(can_move_end)
        duration = {}
        for mode in (PlayTreeItem.duration_mode_all, PlayTreeItem.duration_mode_cortinas):
            duration[mode] = sum(
                    self.model().item(index).duration(self.model(), mode)
                    for index in self.selectionModel().selectedRows()
                ) if self.selectionModel().hasSelection() \
                else 1000*self.model().root_item.duration(self.model(), mode)
        self.window().statusBar().showMessage(
            'Duration: {} ({} for {}s cortinas)'.format(
                hmsms_to_text(*ms_to_hmsms(1000*duration[PlayTreeItem.duration_mode_all]),include_ms=False),
                hmsms_to_text(*ms_to_hmsms(1000*duration[PlayTreeItem.duration_mode_cortinas]),include_ms=False),
                PlayTreeFile.cortina_duration))

    def on_currentIndex_changed(self):
        self.window().action_paste.setEnabled(self.can_paste())
        self.window().action_insert.setEnabled(self.can_insert())

    def other(self):
        for w in self.window().findChildren(PlayTreeView):
            if w != self:
                return w

    def focusNextPrevChild(self, next):
        self.other().setFocus(Qt.TabFocusReason if next else Qt.BacktabFocusReason)
        return True

    def focusInEvent(self, event):
        r = super().focusInEvent(event)
        QWidget.setTabOrder(self, self.other())
        return r

    def move_up(self):
        model = self.model()
        selection_model = self.selectionModel()
        selected_indexes = selection_model.selectedRows()
        selected_items = [model.item(index) for index in selected_indexes]
        parent_index = selected_indexes[0].parent()
        parent = model.item(parent_index)
        top = min(index.row() for index in selected_indexes)
        current_item = model.item(self.currentIndex())
        if top == 0:
            new_parent = parent.parent.child(model, parent.parent.childs_row(model, parent)-1)
            MovePlayTreeItemsCommand(selected_items, new_parent, None, command_prefix = 'Move', command_suffix = 'up')
            for item in selected_items:
                selection_model.select(item.index(model),QItemSelectionModel.Select|QItemSelectionModel.Rows)
            selection_model.setCurrentIndex(current_item.index(model), QItemSelectionModel.NoUpdate)
        else:
            item = parent.child(model, top -1)
            before_index = model.index(
                max(index.row() for index in selected_indexes) + 1, 0, parent_index)
            before_item = model.item(before_index) if before_index.isValid() else None
            MovePlayTreeItemsCommand(
                [item], parent, before_item,
                command_text = 'Move {} up'.format(
                    TMPlayTreeItemsCommand.describe_items(selected_items)))
            selection_model.selectionChanged.emit(QItemSelection(), QItemSelection())
            selection_model.setCurrentIndex(
                current_item.index(model), QItemSelectionModel.NoUpdate)

    def move_down(self):
        model = self.model()
        selection_model = self.selectionModel()
        selected_indexes = selection_model.selectedRows()
        selected_items = [model.item(index) for index in selected_indexes]
        parent_index = selected_indexes[0].parent()
        parent = model.item(parent_index)
        bottom = max(index.row() for index in selected_indexes)
        current_item = model.item(self.currentIndex())
        if bottom == model.rowCount(parent_index)-1:
            new_parent = parent.parent.child(model, parent.parent.childs_row(model, parent)+1)
            MovePlayTreeItemsCommand(
                selected_items, 
                new_parent, 
                new_parent.child(model, 0) if new_parent.rowCount(model) else None, 
                command_prefix = 'Move', command_suffix = 'down')
            for item in selected_items:
                selection_model.select(item.index(model),QItemSelectionModel.Select|QItemSelectionModel.Rows)
            selection_model.setCurrentIndex(current_item.index(model), QItemSelectionModel.NoUpdate)
        else:
            item = parent.child(model, bottom+1)
            before_index = model.index(
                min(index.row() for index in selected_indexes), 0, parent_index)
            before_item = model.item(before_index)
            MovePlayTreeItemsCommand(
                [item], parent, before_item,
                command_text = 'Move {} down'.format(
                    TMPlayTreeItemsCommand.describe_items(selected_items)))
            selection_model.selectionChanged.emit(QItemSelection(), QItemSelection())
            selection_model.setCurrentIndex(
                current_item.index(model), QItemSelectionModel.NoUpdate)


    def move_left(self):
        model = self.model()
        selection_model = self.selectionModel()
        selected_indexes = selection_model.selectedRows()
        selected_items = [model.item(index) for index in selected_indexes]
        current_item = model.item(self.currentIndex())
        parent_index = selected_indexes[0].parent()
        parent_item = model.item(parent_index)
        grandparent_index = model.parent(parent_index)
        grandparent_item = model.item(grandparent_index)
        MovePlayTreeItemsCommand(
            selected_items, grandparent_item, parent_item,
            command_prefix = "Move", command_suffix = "before parent")
        for item in selected_items:
            selection_model.select(item.index(model),QItemSelectionModel.Select|QItemSelectionModel.Rows)
        selection_model.setCurrentIndex(current_item.index(model), QItemSelectionModel.NoUpdate)

    def move_right(self):
        model = self.model()
        selection_model = self.selectionModel()
        selected_indexes = selection_model.selectedRows()
        selected_items = [model.item(index) for index in selected_indexes]
        current_item = model.item(self.currentIndex())
        parent_index = selected_indexes[0].parent()
        parent_item = model.item(parent_index)
        bottom = max(index.row() for index in selected_indexes)
        new_parent_index = model.index(bottom+1, 0, parent_index)
        new_parent_item = model.item(new_parent_index)
        MovePlayTreeItemsCommand(
            selected_items, new_parent_item, 
            new_parent_item.child(None, 0) if model.rowCount(new_parent_index) != 0 else None,
            command_prefix = "Move", command_suffix = "info next sibling")
        for item in selected_items:
            selection_model.select(item.index(model),QItemSelectionModel.Select|QItemSelectionModel.Rows)
        selection_model.setCurrentIndex(current_item.index(model), QItemSelectionModel.NoUpdate)

    def move_home(self):
        model = self.model()
        selection_model = self.selectionModel()
        selected_indexes = selection_model.selectedRows()
        selected_items = [model.item(index) for index in selected_indexes]
        top = min(index.row() for index in selected_indexes)
        new_parent_index = selected_indexes[0].parent() if top != 0 else QModelIndex()
        new_parent = model.item(new_parent_index)
        current_item = model.item(self.currentIndex())
        MovePlayTreeItemsCommand(
            selected_items, new_parent, model.item(model.index(0, 0, new_parent_index)), 
            command_prefix = 'Move', command_suffix = 'before all siblings')
        for item in selected_items:
            selection_model.select(item.index(model),QItemSelectionModel.Select|QItemSelectionModel.Rows)
        selection_model.setCurrentIndex(current_item.index(model), QItemSelectionModel.NoUpdate)

    def move_end(self):
        model = self.model()
        selection_model = self.selectionModel()
        selected_indexes = selection_model.selectedRows()
        selected_items = [model.item(index) for index in selected_indexes]
        parent_index = selected_indexes[0].parent()
        bottom = max(index.row() for index in selected_indexes)
        new_parent_index = selected_indexes[0].parent() if bottom != model.rowCount(parent_index)-1 else QModelIndex()
        new_parent = model.item(new_parent_index)
        current_item = model.item(self.currentIndex())
        MovePlayTreeItemsCommand(selected_items, new_parent, None, 
                                 command_prefix = 'Move', command_suffix = 'after all siblings')
        for item in selected_items:
            selection_model.select(item.index(model),QItemSelectionModel.Select|QItemSelectionModel.Rows)
        selection_model.setCurrentIndex(current_item.index(model), QItemSelectionModel.NoUpdate)

    def dragEnterEvent(self, event):
        if event.source() == self:
            event.setDropAction(Qt.MoveAction)
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.source() == self:
            event.setDropAction(Qt.MoveAction)
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.source() == self:
            event.setDropAction(Qt.MoveAction)
        super().dropEvent(event)

    def keyPressEvent(self, event):
        modifiers = event.modifiers()
        key = event.key()
        if modifiers & Qt.AltModifier and key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right, Qt.Key_Home, Qt.Key_End):
            return
        if modifiers == Qt.NoModifier and key in (Qt.Key_Home, Qt.Key_End):
            ci = self.currentIndex()
            if ci.isValid():
                if key == Qt.Key_Home and ci.row() != 0:
                    self.setCurrentIndex(self.model().index(0,0,ci.parent()))
                    return
                if key == Qt.Key_End and ci.row() != self.model().rowCount(ci.parent())-1:
                    self.setCurrentIndex(self.model().index(self.model().rowCount(ci.parent())-1,0,ci.parent()))
                    return
        super().keyPressEvent(event)
            


class TMProgressBar(QProgressBar):
    def __init__(self, player, parent = None):
        super().__init__(parent)
        self.setMinimum(0)
        self.setValue(-1)
        self.player = player
        player.durationChanged.connect(self.on_durationChanged)
        player.positionChanged.connect(self.on_positionChanged)
        player.stateChanged.connect(self.on_stateChanged)
        self.hours, self.minutes, self.seconds, self.milliseconds = 0,0,0,0
        self.on_stateChanged(QMediaPlayer.StoppedState)
        self.update()

        self.in_seek = False
        self.setMouseTracking(True)
        self.installEventFilter(TMProgressBar_Interaction(self))

    def on_durationChanged(self, duration):
        self.setMaximum(duration)
        self.update()
        
    def on_positionChanged(self, position):
        self.setValue(position)
        self.hours, self.minutes, self.seconds, self.milliseconds = ms_to_hmsms(position)
        self.update()

    def text(self):
        return hmsms_to_text(self.hours, self.minutes, self.seconds, self.milliseconds,
                             include_ms = self.player.state == QMediaPlayer.PausedState)
        
    def on_stateChanged(self, state):
        self.player_state = state
        self.setTextVisible(state != QMediaPlayer.StoppedState)
        self.update()

class TMProgressBar_Interaction(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseMove:   
            if obj.in_seek:
                obj.player.setPosition(obj.maximum() * event.x() / obj.width())
            if obj.player_state != QMediaPlayer.StoppedState:
                QToolTip.showText(event.globalPos(),
                                  hmsms_to_text(*ms_to_hmsms(int(
                                      obj.maximum() * event.x() / obj.width())),
                                                include_ms = False),
                                  obj, QRect())
        elif event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            if obj.window().action_lock.isChecked():
                return False
            obj.in_seek = True
            obj.player.setPosition(obj.maximum() * event.x() / obj.width())
        elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            if obj.window().action_lock.isChecked():
                return False
            obj.in_seek = False
        return False
