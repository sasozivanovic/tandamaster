from PyQt5.QtCore import pyqtRemoveInputHook; from IPython import embed; pyqtRemoveInputHook()

from PyQt5.Qt import *   # todo: import only what you need

from player import TandaMasterPlayer
from model import PlayTreeModel, PlayTreeList, PlayTreeMimeData, save_playtree
from library import Library
from util import *
from app import *

import collections, weakref

class TandaMasterWindow(QMainWindow):

    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle('TandaMaster')        

        self.player = TandaMasterPlayer()
        #self.player2 = TandaMasterPlayer() # pre-listening

        splitter = QSplitter()
        splitter.addWidget(PlayTreeWidget(None, self.player))
        splitter.addWidget(PlayTreeWidget(None, self.player))
        self.setCentralWidget(splitter)

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
        action_back = QAction(
            #self.style().standardIcon(QStyle.SP_MediaSkipBackward), 
            #MyIcon('Tango', 'actions', 'media-skip-backward'),
            QIcon('button_rewind_green.png'),
            #QIcon('icons/iconfinder/32pxmania/previous.png'),
            self.tr('P&revious'), self, triggered = self.player.play_previous)
        self.playbackmenu.addAction(action_back)        
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
        action_forward = QAction(
            #self.style().standardIcon(QStyle.SP_MediaSkipForward), 
            #MyIcon('Tango', 'actions', 'media-skip-forward'),
            QIcon('button_fastforward_green.png'),
            #QIcon('icons/iconfinder/32pxmania/next.png'),
            self.tr('&Next'), self, triggered = self.player.play_next)
        self.playbackmenu.addAction(action_forward)        
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
            QIcon('icons/iconfinder/32pxmania/left.png'),
            self.tr('Move &left'), self, triggered = self.playtree_move_left,
            shortcut = QKeySequence('alt+left'))
        self.action_move_right = QAction(
            QIcon('icons/iconfinder/32pxmania/right.png'),
            self.tr('Move &right'), self, triggered = self.playtree_move_right,
            shortcut = QKeySequence('alt+right'))
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
        self.playtreemenu.addAction(self.action_move_up)
        self.playtreemenu.addAction(self.action_move_down)
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
        toolbar.addAction(action_back)
        toolbar.addAction(self.action_play)
        toolbar.addAction(self.action_pause)
        toolbar.addAction(self.action_stop)
        toolbar.addAction(action_forward)
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
        toolbar.addAction(self.action_move_up)
        toolbar.addAction(self.action_move_down)
        toolbar.addAction(self.action_move_left)
        toolbar.addAction(self.action_move_right)
        
        self.addToolBar(toolbar)        

        self.player.currentMediaChanged.connect(self.update_song_info)
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
            self.action_stop.setEnabled(True)
        else:
            self.action_play.setVisible(True)
            self.action_pause.setVisible(False)
            self.action_stop.setEnabled(state != QMediaPlayer.StoppedState)
                
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
        ptv.move_right()

    def playtree_move_left(self):
        ptv = app.focusWidget()
        if not isinstance(ptv, PlayTreeView): return
        ptv.move_left()

    def playtree_move_right(self):
        ptv = app.focusWidget()
        if not isinstance(ptv, PlayTreeView): return
        ptv.move_right()

class PlayTreeWidget(QWidget):

    def __init__(self, root_id, player, parent = None):
        super().__init__(parent)

        current_model_button = QToolButton()
        #current_model_button.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        #current_model_button.setIcon(QIcon('circle_green.png'))
        current_model_button.setIcon(QIcon('icons/iconfinder/32pxmania/current_playtree.png')),
        current_model_button.setCheckable(True)
        self.search = QLineEdit()
        self.ptv = PlayTreeView(root_id, player, self)

        controls = QToolBar()
        controls.addWidget(current_model_button)
        controls.addWidget(self.search)

        widget_layout = QVBoxLayout()
        self.setLayout(widget_layout)
        widget_layout.addWidget(controls)
        widget_layout.addWidget(self.ptv)

        self.search.textChanged.connect(lambda: QTimer.singleShot(50, self.refilter))
        current_model_button.toggled.connect(
            lambda checked: player.set_current(model = self.ptv.model()) if checked else None)
        player.current_changed.connect(
            lambda old_model, old_index, model, index: current_model_button.setChecked(
                self.ptv.model() == model))
        current_model_button.setChecked(self.ptv.model() == player.current_model)

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

    def refilter(self):
        self.ptv.model().refilter(self.search.text())
        
class PlayTreeView(QTreeView):

    def __init__(self, root_id, player, parent = None):
        super().__init__(parent)
        self.setUniformRowHeights(True)

        model = PlayTreeModel(root_id, self)
        self.setModel(model)
        model.view = self

        self.player = player
        self.activated.connect(player.play_index)

        self.setExpandsOnDoubleClick(False)
        self.expanded.connect(self.on_expanded)
        self.collapsed.connect(self.on_collapsed)
        self._autoexpanded = None
        self._autoexpand_on = True
        player.current_changed.connect(self.on_current_changed)
        if not self.player.current_model:
            self.player.set_current(model = self.model())
        model.modelReset.connect(self.on_end_reset_model)

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.selectionModel().selectionChanged.connect(self.on_currentIndex_changed)

        self.setDragDropMode(QAbstractItemView.DragDrop)

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

    def autosize_columns(self):
        return
        columns = self.model().columnCount(QModelIndex())
        for i in range(columns):
            self.resizeColumnToContents(i)

    def on_end_reset_model(self):
        model = self.model()
        for item in model.rootItem.iter(model,
                lambda item: not item.isTerminal,
                lambda item: isinstance(item, PlayTreeList)):
            if model in item.expanded:
                self.setExpanded(item.modelindex(model), item.expanded[model])

    def cut(self):
        selected = self.selectedIndexes()
        QApplication.clipboard().setMimeData(self.model().mimeData(selected))
        #self.delete()

    def delete(self):
        selection_model = self.selectionModel() #QItemSelectionModel
        item_selection = selection_model.selection() #QItemSelection
        self.model().delete(item_selection)

    def copy(self):
        QApplication.clipboard().setMimeData(
            self.model().mimeData(self.selectedIndexes()))

    def paste(self):
        index = self.currentIndex()
        # ugly hack ... when there is acutally no current index, the first row is returned
        if self.selectionModel().isSelected(index):
            row, column, parent = index.row(), index.column(), index.parent()
        else:
            row, column, parent = None, None, QModelIndex()
        self.model().dropMimeData(
            QApplication.clipboard().mimeData(),
            Qt.CopyAction,
            row, column, parent
        )

    def insert(self, name = 'New playtree'):
        item = PlayTreeList(name)
        index = self.currentIndex()
        # ugly hack ... when there is acutally no current index, the first row is returned
        if self.selectionModel().isSelected(index):
            row, column, parent = index.row(), index.column(), index.parent()
        else:
            row, column, parent = None, None, QModelIndex()
        #self.model().item(parent).insert([item], row, self.model())
        InsertPlayTreeItemCommand(item, self.model().item(parent), row, self.model())

    def can_cut(self):
        model = self.model()
        for index in self.selectedIndexes():
            if not model.item(index).parent.are_children_editable:
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
            return self.model().item(self.currentIndex()).parent.are_children_editable
        else:
            return self.model().rootItem.are_children_editable
        

    def can_move(self):
        selection_model = self.selectionModel() #QItemSelectionModel
        item_selection = selection_model.selection() #QItemSelection
        if not item_selection: return False
        parent = self.model().item(item_selection[0].parent())
        if not isinstance(parent, PlayTreeList): return False
        if len(item_selection) == 1: return True
        for range in item_selection:
            if range.parent() != parent:
                return False
        ranges = sorted([(range.top(), range.bottom()) for range in item_selection])
        for bottom, top in zip([range[1] for range in ranges[1:]],
                               [range[0] for range in ranges[:-1]]):
            if bottom != top + 1: return False
        return True

    def on_selection_changed(self):
        can_cut = self.can_cut()
        self.window().action_cut.setEnabled(can_cut)
        self.window().action_delete.setEnabled(can_cut)
        self.window().action_copy.setEnabled(self.can_copy())
        can_move = self.can_move()
        self.window().action_move_up.setEnabled(can_move)
        self.window().action_move_down.setEnabled(can_move)
        self.window().action_move_left.setEnabled(can_move)
        self.window().action_move_right.setEnabled(can_move)

    def on_currentIndex_changed(self):
        self.window().action_paste.setEnabled(self.can_paste())
        self.window().action_insert.setEnabled(self.can_insert())

    def other(self):
        for w in self.window().findChildren(PlayTreeView):
            if w != self:
                return w

    def focusInEvent(self, event):
        r = super().focusInEvent(event)
        QWidget.setTabOrder(self, self.other())
        return r

    def move_up(self):
        model = self.model()
        selection_model = self.selectionModel()
        parent = model.item(selection_model.selection()[0].parent())
        top = min(selection_range.top()
                  for selection_range in selection_model.selection())
        if top == 0:
            if parent.parent and parent.parent.childs_row(model, parent) != 0:
                items = [model.item(index)
                         for selection_range in self.selectionModel().selection()
                         for index in selection_range.indexes()
                     ]
                new_parent = parent.parent.child(
                    model, parent.parent.childs_row(model, parent) - 1)
                parent.delete(items)
                inserted_items = new_parent.insert(items, -1, model)
        else:
            items = [parent.child(model, top -1)]
            bottom = max(selection_range.bottom()
                  for selection_range in selection_model.selection())
            parent.delete(items)
            inserted_items = parent.insert(items, bottom + 1, model)
        for item in inserted_items:
            selection_model.select(item.modelindex(model),QItemSelectionModel.Select)
        selection_model.setCurrentIndex(inserted_items[0].modelindex(model), QItemSelectionModel.NoUpdate)


    def move_down(self):
        pass

    def move_left(self):
        pass

    def move_right(self):
        pass

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
            obj.in_seek = True
            obj.player.setPosition(obj.maximum() * event.x() / obj.width())
        elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            obj.in_seek = False
        return False

def ms_to_hmsms(t):
    t, ms = divmod(t, 1000)
    t, s = divmod(t, 60)
    h, m = divmod(t, 60)
    return h, m, s, ms

def hmsms_to_text(h,m,s,ms,include_ms=True):
    return str(h) + ":" if h else '' + \
        ('{:02d}:{:02d}' if h else '{:2d}:{:02d}').format(m, s) + \
        (':' + ms if include_ms else '')


class InsertPlayTreeItemCommand(QUndoCommand):
    def __init__(self, item, item_parent, row, calling_model, text = None, parent = None, push = True):
        text = 'Insert playtree "{}"'.format(str(item)) \
               if text is None else text
        super().__init__(text, parent)
        self.item = item
        self.item_parent = item_parent
        self.row = row
        self.calling_model = weakref.ref(calling_model)
        item_parent.insert([item], row, calling_model)
        if push:
            undo_stack.push(self)

    def redo(self):
        self.item_parent.insert([self.item], self.row, self.calling_model())

    def undo(self):
        self.item_parent.delete([self.item])
        
