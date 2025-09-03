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
#import cProfile

import PyQt5 as qt
from PyQt5.Qt import *   # todo: import only what you need

from .player import TMPlayer, PlayOrder, PlaybackConfig
from .model import *
from .library import Library
from .util import *
from .app import *
from .commands import *

from .replay_gain import TMReplayGain
from gi.repository import GObject, Gst, GLib
import os, os.path, subprocess, platform
from pathlib import Path

import collections, weakref, binascii, datetime

class TMWidget:
    xml_tag_registry = {}

    @classmethod
    def register_xml_tag_handler(cls, tag):
        def f(subcls):
            cls.xml_tag_registry[tag] = subcls
            subcls.xml_tag = tag
            return subcls
        return f

    @classmethod
    def create_from_xml(cls, element, window, parent = None):
        return cls.xml_tag_registry[element.tag]._create_from_xml(element, window, parent)

    def to_xml(self):
        element = etree.Element(self.xml_tag)
        try:
            element.set('state', binascii.hexlify(self.saveState().data()).decode())
        except:
            pass
        return element


@TMWidget.register_xml_tag_handler('Splitter')
class TMSplitter(QSplitter, TMWidget):
    @classmethod
    def _create_from_xml(cls, element, window, parent):
        splitter = cls(parent = parent)
        for subelement in element:
            splitter.addWidget(cls.create_from_xml(subelement, window, splitter))
        splitter.restoreState(binascii.unhexlify(element.get('state', '')))
        return splitter

    def to_xml(self):
        element = super().to_xml()
        for i in range(self.count()):
            element.append(self.widget(i).to_xml())
        return element

@TMWidget.register_xml_tag_handler('TabbedPlayTreesWidget')
class TabbedPlayTreesWidget(QTabWidget, TMWidget):
    @classmethod
    def _create_from_xml(cls, element, window, parent):
        tw = cls(parent = parent, window = window, tabPosition = int(element.get('tabPosition', 0)))
        for subelement in element:
            widget = cls.create_from_xml(subelement, window, None)
            tw.add_tab(widget = widget)
        return tw

    def to_xml(self):
        element = super().to_xml()
        element.set('tabPosition', str(self.tabPosition()))
        for i in range(self.count()):
            element.append(self.widget(i).to_xml())
        return element

    def __init__(self, parent = None, window = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.setTabsClosable(True)
        self.setUsesScrollButtons(True)
        action_addtab = QAction(
            MyIcon('iconfinder/miniiconsetpart1/add.png'),
            app.tr('Add tab'), self,
            triggered = self.add_tab
        )
        addtab_button = QToolButton(self)
        addtab_button.setDefaultAction(action_addtab)
        self.setCornerWidget(addtab_button, Qt.BottomLeftCorner if self.tabPosition() == QTabWidget.West else Qt.TopRightCorner)
        self.tabBarDoubleClicked.connect(lambda: self.add_tab())
        self.tabCloseRequested.connect(self.removeTab)
        self.setAcceptDrops(True)
        window.player.current_changed.connect(self.on_current_changed)

        self.addAction(QAction(
            self, 
            shortcut = QKeySequence(Qt.CTRL + Qt.Key_PageUp), 
            shortcutContext = Qt.WidgetWithChildrenShortcut,
            triggered = lambda: self.setCurrentIndex(self.currentIndex()-1)))
        self.addAction(QAction(
            self, 
            shortcut = QKeySequence(Qt.CTRL + Qt.Key_PageDown), 
            shortcutContext = Qt.WidgetWithChildrenShortcut,
            triggered = lambda: self.setCurrentIndex(self.currentIndex()+1)))
        
    def add_tab(self, widget = None, root_item = None):
        self.insert_tab(-1, widget = widget, root_item = root_item)

    def insert_tab(self, index, widget = None, root_item = None):
        if not widget:
            widget = PlayTreeWidget(root_id = None, player = self.window().player, root_item = root_item)
        tab_index = self.insertTab(index, widget, '')
        self.update_tab_title(tab_index)
        widget.ptv.model().modelReset.connect(lambda: self.update_tab_title(self.indexOf(widget)))

    def update_tab_title(self, index):
        widget = self.widget(index)
        model = widget.ptv.model()
        icon = model.root_item.data(model, model.root_item.column_to_tag(model, 0), Qt.DecorationRole)
        text = model.root_item.data(model, model.root_item.column_to_tag(model, 0), Qt.DisplayRole)
        self.setTabIcon(index, icon if icon else MyIcon())
        self.setTabText(index, text)
        
    def dragEnterEvent(self, event):
        if isinstance(event.mimeData(), PlayTreeMimeData):
            event.setAccepted(True)

    def dropEvent(self, event):
        index = self.tabBar().tabAt(event.pos())
        if isinstance(event.mimeData(), PlayTreeMimeData):
            for item in event.mimeData().items:
                if not item.isTerminal:
                    self.insert_tab(index, root_item = item)
                    index += 1
            
    def on_current_changed(self):
        if not isinstance(self.window(), TandaMasterWindow):
            return
        old_model = self.window().player.old_current.model
        model = self.window().player.current.model
        if old_model == model:
            return
        for i in range(self.count()):
            m = self.widget(i).ptv.model()
            if m == old_model:
                self.tabBar().setTabTextColor(i, QColor())
            elif m == model:
                self.tabBar().setTabTextColor(i, QColor(Qt.darkGreen))

    def _show(self, child, last_unused_child):
        self.setCurrentWidget(last_unused_child)
                
@TMWidget.register_xml_tag_handler('PlayTreeWidget')
class PlayTreeWidget(QWidget, TMWidget):

    @classmethod
    def _create_from_xml(cls, element, window, parent):
        root_id = element.get('root_id')
        ptw = cls(root_id, window.player, parent)
        xml_columns = element.findall('column')
        if len(xml_columns):
            ptw.ptv.model().columns = [
                col.get('tag')
                for col in xml_columns
            ]
            for i, column in enumerate(xml_columns):
                width = column.get('width')
                if width is not None:
                    ptw.ptv.setColumnWidth(i, int(width))
        if element.get('current'):
            window.player.current = PlaybackConfig(ptw.ptv.model())
        return ptw

    def to_xml(self):
        element = super().to_xml()
        element.set('root_id', str(self.ptv.model().root_item.Id))
        if self.window().player.current.model == self.ptv.model():
            element.set('current', '1')
        for i, column in enumerate(self.ptv.model().columns):
            etree.SubElement(element, 
                             'column', 
                             tag = column, 
                             width = str(self.ptv.columnWidth(i)))
        return element

    def __init__(self, root_id, player, parent = None, root_item = None):
        super().__init__(parent)

        self.search = QLineEdit()
        self.search.setClearButtonEnabled(True)
        self.ptv = PlayTreeView(root_id, player, self, root_item = root_item)

        controls = QToolBar()
        controls.addWidget(self.search)

        widget_layout = QVBoxLayout()
        self.setLayout(widget_layout)
        widget_layout.addWidget(controls)
        widget_layout.addWidget(self.ptv)

        if not config.ui_search_wait_for_enter:
            self.search.textChanged.connect(
                lambda: QTimer.singleShot(50, self.maybe_refilter))
        self.search.returnPressed.connect(self.refilter)

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

    def maybe_refilter(self):
        text = self.search.text()
        if len(text) == 0 or len(text) > 2:
            self.ptv.model().refilter(text)
    def refilter(self):
        self.ptv.model().refilter(self.search.text())

    def _show(self, child, last_used_child):
        pass

        
class PlayTreeView(QTreeView):

    def __init__(self, root_id, player, parent = None, root_item = None):
        super().__init__(parent)
        
        self.setUniformRowHeights(True) 
        # when using QTreeView::branch:selected, images disappear!

        model = PlayTreeModel(root_id, self, root_item = root_item)
        self.setModel(model)
        model.view = self

        self.setExpandsOnDoubleClick(False)
        self.expanded.connect(self.on_expanded)
        self.collapsed.connect(self.on_collapsed)
        self._autoexpanded = None
        self._autoexpand_on = True

        self.player = player
        self.activated.connect(self.on_activated)
        player.current_changed.connect(self.on_current_changed)
        self.model().modelReset.connect(self.on_end_reset_model)

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.selectionModel().selectionChanged.connect(self.on_currentIndex_changed)

        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setEditTriggers(QAbstractItemView.EditKeyPressed)
        self.delegate = TMItemDelegate()
        self.delegate.closeEditor.connect(self.on_close_editor)
        self.setItemDelegate(self.delegate)

    def on_expanded(self, index):
        model = self.model()
        model.item(index).expanded[model] = True
        if model == self.player.current.model and \
           index in model.ancestors(self.player.current.index):
            self._autoexpand_on = True
        self.autosize_columns()

    def on_collapsed(self, index):
        model = self.model()
        model.item(index).expanded[model] = False
        if model == self.player.current.model and \
           index in model.ancestors(self.player.current.index):
            self._autoexpand_on = False

    def on_current_changed(self):
        old_model = self.player.old_current.model
        model = self.player.current.model
        old_index = self.player.old_current.index
        index = self.player.current.index
        if self._autoexpand_on:
            if self._autoexpanded and old_model == self.model():
                current_ancestors = old_model.ancestors(self.currentIndex())
                del current_ancestors[0:1]
                while old_index.isValid():
                    if not old_model.item(old_index).isTerminal and self.isExpanded(old_index) and old_index not in current_ancestors:
                        self.collapse(old_index)
                    if old_index == self._autoexpanded:
                        break
                    old_index = old_model.parent(old_index)
            if model == self.model():
                while index.isValid() and not self.isExpanded(index):
                    if not model.item(index).isTerminal:
                        self.expand(index)
                    self._autoexpanded = index
                    index = model.parent(index)
        self.viewport().update()

    def on_activated(self, index):
        if self.window().action_edit_tags_mode.isChecked():
            self.edit(index)
        else:
            self.play_this(index)
            
    def play_this(self, index = None):
        if index is None:
            index = self.currentIndex()
        if not self.window().action_lock.isChecked() or self.player.current.item.function() == 'cortina':
            self.player.play_index(index)

    def currentChanged(self, current, previous):
        super().currentChanged(current, previous)
        self.update_current_song_from_file(current)
        current_item = self.model().item(current)
        save_revert = isinstance(current_item, PlayTreeFile) and library().dirty(current_item.song_id, self.model().columns[current.column()])
        if isinstance(self.window(), TandaMasterWindow): # workaround!
            self.window().action_save_tag.setEnabled(False) # todo: saving a SINGLE tag
            self.window().action_revert_tag.setEnabled(save_revert)

    def update_current_song_from_file(self, current):
        item = self.model().item(current)
        if isinstance(item, PlayTreeFile):
            librarian.bg_queries(BgQueries([BgQuery(Library.update_song_from_file, (None, item.filename))], item.maybe_refresh_models, relevant = lambda: self.currentIndex() == current))

    def update_selected_from_file(self):
        model = self.model()
        selected_items = set(
            sum(
                list(
                    list(
                        model.item(index).iter(
                            model,
                            lambda it: isinstance(it, PlayTreeFile),
                            lambda it: not isinstance(it, PlayTreeFile))
                    )
                    for index in self.selectionModel().selectedRows()
                ),
                []
            )
        )
        def refresh(dummy):
            for item in selected_items:
                item.refresh_models()
        if selected_items:
            librarian.bg_queries(BgQueries(
                (BgQuery(Library.update_song_from_file, (None, item.filename, True)) for item in selected_items),
                refresh, relevant = lambda: True))
        
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
        self.copy()
        self.delete()

    def delete(self):
        if self.window().action_edit_tags_mode.isChecked():
            self.model().setData(self.currentIndex(), None, role = Qt.EditRole)
        else:
            model = self.model()
            selection_model = self.selectionModel()
            current_index = self.currentIndex()
            current_path = model.index_to_path(current_index)
            DeletePlayTreeItemsCommand(
                [model.item(index) for index in selected_rows(selection_model)])
            current_index = model.path_to_index(current_path)
            if current_index.isValid():
                self.setCurrentIndex(current_index)
            
    def copy(self):
        if self.window().action_edit_tags_mode.isChecked():
            current_index = self.currentIndex()
            model = self.model()
            current_item = model.item(current_index)
            QApplication.clipboard().setText(
                model.data(current_index, role = Qt.EditRole))
        else:
            QApplication.clipboard().setMimeData(
                self.model().mimeData(self.selectedIndexes()))

    def paste(self):
        if self.window().action_edit_tags_mode.isChecked():
            text = QApplication.clipboard().text()
            if not text:
                return
            model = self.model()
            selected_indexes = self.selectionModel().selectedIndexes()
            for index in selected_indexes:
                model.setData(index, text, Qt.EditRole)
        else:
            model = self.model()
            current_index = self.currentIndex()
            current_path = model.index_to_path(current_index)
            if current_index.isValid():
                parent_item = model.item(current_index).parent
                row = current_index.row() + 1 if current_index.row() + 1 < parent_item.rowCount(model) else -1
                column = current_index.column()
            else:
                parent_item, row, column = (model.root_item, -1, -1)
            parent_item.populate(model)
            new_items = parent_item.dropMimeData(QApplication.clipboard().mimeData(), Qt.CopyAction, row, command_prefix = 'Paste')
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
        current_item = model.item(current_index, invalid = None)
        if current_item:
            next_index = model.sibling(current_index.row() + 1, None, current_index)
            next_item = model.item(next_index, invalid = None)
            parent_item = current_item.parent if current_item and current_item.parent else None
        else:
            next_item = None
            parent_item = model.root_item
        new_item = PlayTreeList(name)
        InsertPlayTreeItemsCommand([new_item], parent_item, next_item, Id = 1)
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
        if self.window().action_edit_tags_mode.isChecked():
            return self.selectionModel().hasSelection()
        else:
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
        if not item_selection: return (False,)*8
        parent_index = item_selection[0].parent()
        parent = model.item(parent_index)
        if not parent.are_children_manually_set: return (False,)*8
        for range in item_selection:
            if range.parent() != parent_index:
                return (False,)*8
        ranges = sorted([(range.top(), range.bottom()) for range in item_selection])
        if len(item_selection) > 1:
            for bottom, top in zip([range[1] for range in ranges[1:]],
                                   [range[0] for range in ranges[:-1]]):
                if bottom != top + 1: 
                    return (False,)*8
        top = ranges[0][0]
        bottom = ranges[-1][1]
        top_index = model.index(top, 0, parent_index)
        bottom_index = model.index(bottom, 0, parent_index)
        grandparent_index = model.parent(parent_index)
        grandparent_item = model.item(grandparent_index)
        can_group = True # bottom!=top
        can_move_up = top_index.row() != 0 or (parent_index.isValid() and parent_index.row() != 0 and model.item(model.index(parent_index.row()-1,0,grandparent_index)).are_children_manually_set)
        can_move_down = bottom_index.row() != model.rowCount(parent_index)-1 or (parent_index.isValid() and parent_index.row() != model.rowCount(grandparent_index)-1 and model.item(model.index(parent_index.row()+1,0,grandparent_index)).are_children_manually_set)
        can_move_left = parent_index.isValid()
        can_move_up_right = ranges[0][0] > 0 and model.item(model.index(ranges[0][0]-1, 0, parent_index)).are_children_manually_set
        can_move_down_right = model.rowCount(parent_index) > ranges[-1][1]+1 and model.item(model.index(ranges[-1][1]+1, 0, parent_index)).are_children_manually_set
        can_move_home = top != 0 or (parent_index.isValid() and model.root_item.are_children_manually_set)
        can_move_end = bottom != model.rowCount(parent_index)-1 or (parent_index.isValid() and model.root_item.are_children_manually_set)
        return can_group, can_move_up, can_move_down, can_move_left, can_move_up_right, can_move_down_right, can_move_home, can_move_end

    def on_selection_changed(self):
        self.window().statusBar().clearMessage()
        can_cut = self.can_cut()
        self.window().action_cut.setEnabled(can_cut)
        self.window().action_delete.setEnabled(can_cut)
        self.window().action_copy.setEnabled(self.can_copy())
        can_group, can_move_up, can_move_down, can_move_left, can_move_up_right, can_move_down_right, can_move_home, can_move_end = self.can_move()
        self.window().action_group.setEnabled(can_group)
        self.window().action_move_up.setEnabled(can_move_up)
        self.window().action_move_down.setEnabled(can_move_down)
        self.window().action_move_up_left.setEnabled(can_move_left)
        self.window().action_move_down_left.setEnabled(can_move_left)
        self.window().action_move_up_right.setEnabled(can_move_up_right)
        self.window().action_move_down_right.setEnabled(can_move_down_right)
        self.window().action_move_home.setEnabled(can_move_home)
        self.window().action_move_end.setEnabled(can_move_end)

    def milonga_info(self):
        model = self.model()
        model.root_item.populate(model, recursive = True)
        can_group, can_move_up, can_move_down, can_move_left, can_move_up_right, can_move_down_right, can_move_home, can_move_end = self.can_move()
        mode = PlayTreeItem.duration_mode_cortinas
        selected_indexes = selected_rows(self.selectionModel())
        duration_playtree = model.root_item.duration(model, mode)
        if selected_indexes:
            try:
                duration = sum(model.item(index).duration(model, mode) for index in selected_indexes)
            except TypeError:
                duration = None
            if can_group:
                parent_item = model.item(selected_indexes[0].parent())
                try:
                    duration_before = sum(parent_item.child(model, r).duration(model, mode)
                                          for r in range(0, min(index.row() for index in selected_indexes)))
                except TypeError:
                    duration_before = None
                try:
                    duration_after = sum(
                        parent_item.child(model, r).duration(model, mode)
                        for r in range(
                                1+max(index.row() for index in selected_indexes),
                                parent_item.rowCount(model)))
                except TypeError:
                    duration_after = None
                
                msg = 'Duration before {}, selection {}, after {}, playtree {}'.format(
                    time_to_text(duration_before,include_ms=False),
                    time_to_text(duration,include_ms=False),
                    time_to_text(duration_after,include_ms=False),
                    time_to_text(duration_playtree,include_ms=False))
            else:
                msg = 'Duration of the selection: {}'.format(
                    time_to_text(duration,include_ms=False),
                    time_to_text(duration_playtree,include_ms=False))
        else:
            msg = 'Duration of the playtree: {}'.format(
                time_to_text(duration_playtree,include_ms=False))
        if mode == PlayTreeItem.duration_mode_cortinas:
            msg += ' (cortina={}s)'.format(PlayTreeFile.cortina_duration)

        index = self.player.current.index
        model = self.player.current.model
        remaining = ''
        # todo: query the position of the current song
        if index and index.isValid():
            duration_after_current = 0
            mode = PlayTreeItem.duration_mode_cortinas
            ind = index
            while ind.isValid():
                d = model.item(ind).duration(model, mode)
                if d is None:
                    duration_after_current = None
                    break
                duration_after_current += d
                ind = model.next(ind, descend = False)
            else:
                remaining = 'Milonga ends at ' + (datetime.datetime.now() + datetime.timedelta(seconds = duration_after_current)).strftime('%H:%M')
            
        self.window().update_status_bar(duration = msg, remaining = remaining)

    def check_availability(self):
        if self.currentIndex().isValid():
            current_item = self.model().item(self.currentIndex())
            if current_item.isPlayable:
                current_item.unavailable = not os.path.isfile(current_item.filename)
    
    def on_currentIndex_changed(self):
        self.window().action_paste.setEnabled(self.can_paste())
        self.window().action_insert.setEnabled(self.can_insert())
        self.check_availability()

    def other(self):
        for w in self.window().findChildren(PlayTreeView):
            if w != self and w.isVisibleTo(self.window()):
                return w

    def focusNextPrevChild(self, next):
        self.other().setFocus(Qt.TabFocusReason if next else Qt.BacktabFocusReason)
        return True

    def focusInEvent(self, event):
        r = super().focusInEvent(event)
        QWidget.setTabOrder(self, self.other())
        self.on_selection_changed()
        self.on_currentIndex_changed()
        self.update_current_song_from_file(self.currentIndex())
        return r

    def move_up(self):
        model = self.model()
        selection_model = self.selectionModel()
        selected_indexes = selected_rows(selection_model)
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
        selected_indexes = selected_rows(selection_model)
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


    def move_up_left(self):
        model = self.model()
        selection_model = self.selectionModel()
        selected_indexes = selected_rows(selection_model)
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

    def move_down_left(self):
        model = self.model()
        selection_model = self.selectionModel()
        selected_indexes = selected_rows(selection_model)
        selected_items = [model.item(index) for index in selected_indexes]
        current_item = model.item(self.currentIndex())
        parent_index = selected_indexes[0].parent()
        parent_item = model.item(parent_index)
        after_parent_index = model.sibling(parent_index.row() + 1, None, parent_index)
        after_parent_item = model.item(after_parent_index, invalid = None)
        grandparent_index = model.parent(parent_index)
        grandparent_item = model.item(grandparent_index)
        MovePlayTreeItemsCommand(
            selected_items, grandparent_item, after_parent_item,
            command_prefix = "Move", command_suffix = "after parent")
        for item in selected_items:
            selection_model.select(item.index(model),QItemSelectionModel.Select|QItemSelectionModel.Rows)
        selection_model.setCurrentIndex(current_item.index(model), QItemSelectionModel.NoUpdate)

    def move_down_right(self):
        model = self.model()
        selection_model = self.selectionModel()
        selected_indexes = selected_rows(selection_model)
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
            command_prefix = "Move", command_suffix = "into next sibling")
        for item in selected_items:
            selection_model.select(item.index(model),QItemSelectionModel.Select|QItemSelectionModel.Rows)
        selection_model.setCurrentIndex(current_item.index(model), QItemSelectionModel.NoUpdate)

    def move_up_right(self):
        model = self.model()
        selection_model = self.selectionModel()
        selected_indexes = selected_rows(selection_model)
        selected_items = [model.item(index) for index in selected_indexes]
        current_item = model.item(self.currentIndex())
        parent_index = selected_indexes[0].parent()
        parent_item = model.item(parent_index)
        top = min(index.row() for index in selected_indexes)
        new_parent_index = model.index(top-1, 0, parent_index)
        new_parent_item = model.item(new_parent_index)
        MovePlayTreeItemsCommand(
            selected_items, new_parent_item, None,
            command_prefix = "Move", command_suffix = "into previous sibling")
        for item in selected_items:
            selection_model.select(item.index(model),QItemSelectionModel.Select|QItemSelectionModel.Rows)
        selection_model.setCurrentIndex(current_item.index(model), QItemSelectionModel.NoUpdate)

    def move_home(self):
        model = self.model()
        selection_model = self.selectionModel()
        selected_indexes = selected_rows(selection_model)
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
        selected_indexes = selected_rows(selection_model)
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

    def group(self):
        model = self.model()
        selection_model = self.selectionModel()
        selected_indexes = selected_rows(selection_model)
        selected_items = sorted((model.item(index) for index in selected_indexes),
                                key = lambda ind: ind.row(model))
        parent_index = selected_indexes[0].parent()
        #parent_item = model.item(parent_index)
        #top = min(index.row() for index in selected_indexes)
        top_index = selected_indexes[0]
        #top_index = model.index(top, 0, parent_index)
        top_item = model.item(top_index)
        #common_tags = dict(self.common_tags(selected_items))
        #if 'GENRE' in common_tags.keys():
        #    genre = common_tags['GENRE']
        #    del common_tags['GENRE']
        #else:
        #    genre = 'Tanda'
        #name = genre + ': ' + ", ".join(common_tags.values())
        #new_item = PlayTreeList(name)
        group_command = TMPlayTreeItemsCommand(selected_items, command_prefix = 'Group')
        new_items = self._group(model, selected_items, group_command)
        if not new_items:
            return
        new_item = new_items[0]
        #InsertPlayTreeItemsCommand([new_item], parent_item, top_item, command_parent = group_command, push = False)
        #MovePlayTreeItemsCommand(selected_items, new_item, None, command_parent = group_command, push = False)
        #self.setExpanded(new_item.index(model), True)
        undo_stack.push(group_command)
        new_item.populate(model)
        self.setExpanded(new_item.index(model), True)        
        selection_model.select(new_item.index(model),QItemSelectionModel.Select|QItemSelectionModel.Rows)
        selection_model.setCurrentIndex(new_item.index(model), QItemSelectionModel.NoUpdate)

    max_tanda_length = 0
    def group_into_tandas(self):
        model = self.model()
        selection_model = self.selectionModel()
        selected_indexes = selected_rows(selection_model)
        selected_items = sorted((model.item(index) for index in selected_indexes),
                                key = lambda ind: ind.row(model))
        parent_index = selected_indexes[0].parent()
        top = min(index.row() for index in selected_indexes)
        top_index = model.index(top, 0, parent_index)
        top_item = model.item(top_index)
        bottom = max(index.row() for index in selected_indexes)
        group_command = TMPlayTreeItemsCommand(selected_items, command_prefix = 'Group tandas')
        tanda_items = []
        new_items = []
        for item in selected_items:
            if self.max_tanda_length and len(tanda_items) == self.max_tanda_length:
                new_items.extend(self._group(model, tanda_items, group_command))
                tanda_items = []
            index = item.index(model)
            if not isinstance(item, PlayTreeFile) or item.function() != 'tanda':
                new_items.extend(self._group(model, tanda_items, group_command))
                tanda_items = []
            else:
                tanda_items.append(item)
        new_items.extend(self._group(model, tanda_items, group_command))
        tanda_items = []
        undo_stack.push(group_command)
        for new_item in new_items:
            new_item.populate(model)
            self.setExpanded(new_item.index(model), True)
        for item in selected_items:
            selection_model.select(item.index(model),QItemSelectionModel.Select|QItemSelectionModel.Rows)
        selection_model.setCurrentIndex(model.index(0,0,parent_index), QItemSelectionModel.NoUpdate)

    def _group(self, model, items, group_command):
        if not items:
            return []
        #if len(items) <= 1: 
        #    return [items] if items else []
        common_tags = collections.OrderedDict(self.common_tags(items))
        if 'GENRE' in common_tags.keys():
            genre = common_tags['GENRE']
            del common_tags['GENRE']
        else:
            genre = 'Tanda'
        name = genre + ': ' + ", ".join(common_tags.values())
        new_item = PlayTreeList(name)
        InsertPlayTreeItemsCommand([new_item], items[0].parent, items[0], command_parent = group_command, push = False)
        MovePlayTreeItemsCommand(items, new_item, None, command_parent = group_command, push = False)
        return [new_item]
        
    def ungroup(self):
        pass
    
    def common_tags(self, items):
        if not items or any(not isinstance(item, PlayTreeFile) for item in items): 
            return []
        tags = ['ARTIST', 'PERFORMER:VOCALS', 'GENRE'] #, 'QUODLIBET::RECORDINGDATE']
        values = dict((tag, first(items[0].get_tag(tag), default='')) for tag in tags)
        for item in items[1:]:
            for tag in tags:
                if values[tag] != first(item.get_tag(tag),default=''):
                    values[tag] = None
        return [(tag,values[tag]) for tag in tags if values[tag]] 

    def dragEnterEvent(self, event):
        if event.source() == self:
            event.setDropAction(Qt.MoveAction if event.keyboardModifiers() == Qt.NoModifier else event.proposedAction())
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.source() == self:
            event.setDropAction(Qt.MoveAction if event.keyboardModifiers() == Qt.NoModifier else event.proposedAction())
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.source() == self:
            event.setDropAction(Qt.MoveAction if event.keyboardModifiers() == Qt.NoModifier else event.proposedAction())
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
            
    def set_columns(self, columns):
        root_item = self.model().root_item
        columns = list(columns)
        if isinstance(root_item, PlayTreeBrowse):
            for tag in root_item.browse_by_tags[0:-1]:
                try:
                    del columns[columns.index(tag)]
                except ValueError:
                    pass
        self.model().beginResetModel()
        self.model().columns = tuple(columns)
        self.model().endResetModel()
        self.autoresize_columns()

    def autoresize_columns(self):
        for i in range(len(self.model().columns)):
            self.resizeColumnToContents(i)

    def edit_tag(self):
        self.edit(self.currentIndex())
    def save_tag(self):
        pass
    def revert_tag(self):
        current_index = self.currentIndex()
        item = self.model().item(current_index)
        tag = self.model().columns[current_index.column()]
        old_value = library().tag_by_song_id(item.song_id, tag, sources = ('file',))
        EditTagsCommand(self.model(), [item], tag, old_value, command_prefix = 'Revert')

    def edit_tags(self):
        item = self.model().item(self.currentIndex())
        if isinstance(item, PlayTreeFile):
            EditTags(item)

    def change_case(self):
        current_index = self.currentIndex()
        value = self.model().data(current_index, role = Qt.EditRole)
        if value == value.capitalize():
            value = value.title()
        elif value == value.title():
            value = value.lower()
        else:
            value = value.capitalize()
        self.model().setData(current_index, value, role = Qt.EditRole)
            
    def on_close_editor(self, editor, hint):
        model = self.model()
        current_index = self.currentIndex()
        next_index = QModelIndex()
        if hint == QAbstractItemDelegate.EditNextItem:
            if current_index.row() == model.columnCount(current_index)-1:
                next_index = model.next_song(current_index)
                next_index = model.sibling(None, 0, next_index)
            else:
                next_index = model.sibling(None, current_index.column() + 1, current_index)
        elif hint == QAbstractItemDelegate.EditPreviousItem:
            if current_index.row() == 0:
                next_index = model.previous_song(current_index)
                next_index = model.sibling(None, model.columnCount(next_index)-1, next_index)
            else:
                next_index = model.sibling(None, current_index.column() - 1, current_index)
        elif hint == TMItemDelegate.EditPreviousRow:
            next_index = model.previous_song(current_index)
            if next_index.isValid():
                next_index = model.sibling(None, current_index.column(), next_index)
        elif hint == TMItemDelegate.EditNextRow:
            next_index = model.next_song(current_index)
            if next_index.isValid():
                next_index = model.sibling(None, current_index.column(), next_index)
        
        if next_index.isValid():
            self.setCurrentIndex(next_index)
            self.edit(next_index)

    def _show(self, index, dummy):
        self.scrollTo(index)
        self.setCurrentIndex(index)
        
    def drawBranches(self, painter, rect, index):
        if self.selectionModel().isSelected(index):
            if index.model().mark_as_playing(index):
                painter.fillRect(rect, Qt.darkGreen)
            elif not index.model().view.hasFocus():
                painter.fillRect(rect, Qt.lightGray)
        super().drawBranches(painter, rect, index)
    
        
class TMItemDelegate(QStyledItemDelegate):
    EditNextRow = 11
    EditPreviousRow = 12
    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        editor.addAction(QAction(self, shortcut='up', triggered = lambda: self.closeEditor.emit(editor, self.EditPreviousRow)))
        editor.addAction(QAction(self, shortcut='down', triggered = lambda: self.closeEditor.emit(editor, self.EditNextRow)))
        tag = index.model().columns[index.column()]
        if tag and isinstance(editor, qt.QtWidgets.QLineEdit):
            completer = QCompleter()
            completer.setCompletionMode(QCompleter.PopupCompletion)
            completer.setCaseSensitivity(False)
            completer.setModel(QStringListModel(
                [str(v) for v,sid,n in library().query_tags_iter((('_library', 'tango'),), '', [tag])])) # todo: 'tango' -> whatever lib
            editor.setCompleter(completer)
        return editor

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        if index.model().mark_as_playing(index):
            option.font.setWeight(QFont.Bold)
            if option.state & QStyle.State_Selected:
                option.state &= ~QStyle.State_Selected
                option.backgroundBrush = QBrush(QColor(Qt.darkGreen))
                option.palette.setColor(QPalette.Text, QColor(Qt.white))
            else:
                option.palette.setColor(QPalette.Text, QColor(Qt.darkGreen))
        elif option.state & QStyle.State_Selected and not index.model().view.hasFocus():
            option.state &= ~QStyle.State_Selected
            option.backgroundBrush = QBrush(QColor(Qt.lightGray))
            option.palette.setColor(QPalette.Text, QColor(Qt.white))


class TMProgressBar(QProgressBar):
    """Draws text manually *into* the progress bar, on all platforms.

    Text is drawn in the center. textDirection is ignored.
    """
    _draw_text_manually = (platform.system != 'Linux')
    if _draw_text_manually:
        def __init__(self, *args, ** kwargs):
            super().__init__(*args, ** kwargs)
            self._tm_text_visible = True
            super().setTextVisible(False)
        def setTextVisible(self, value):
            self._tm_text_visible = value
        def isTextVisible(self):
            return self._tm_text_visible
        def paintEvent(self, paintevent):
            super().paintEvent(paintevent)
            if self._tm_text_visible:
                painter = QPainter(self)
                painter.setPen(QColor(Qt.black))
                painter.drawText(QRectF(0, 0, self.width(), self.height()), Qt.AlignCenter, self.text())
            
class TMPositionProgressBar(TMProgressBar):
    def __init__(self, player, interactive = True, parent = None):
        super().__init__(parent)
        self.setMinimum(0)
        self.setValue(0)
        self.player = player
        player.duration_changed.connect(self.on_duration_changed)
        player.position_changed.connect(self.on_position_changed)
        player.state_changed.connect(self.on_state_changed)
        self.on_state_changed(TMPlayer.STOPPED)
        self.update()

        if interactive:
            self.in_seek = False
            self.setMouseTracking(True)
            self.installEventFilter(TMPositionProgressBar_Interaction(self))

    def on_duration_changed(self, duration):
        self.setMaximum(int(duration/Gst.MSECOND))
        self.update()
        
    def on_position_changed(self, position):
        self.setValue(int(position/Gst.MSECOND))
        self.update()

    def text(self):
        return time_to_text(
            self.value(), unit = 'ms',
            include_ms = self.player.state == TMPlayer.PAUSED)
        
    def on_state_changed(self, state):
        self.player_state = state
        self.setTextVisible(state != TMPlayer.STOPPED)
        self.update()

    def paintEvent(self, paintevent):
        super().paintEvent(paintevent)
        if not self.player.current or not self.maximum():
            return
        painter = QPainter(self)
        song_begin = self.player.current.song_begin
        song_end = self.player.current.song_end
        # calculate manually: setting scale to use ms produces numbers that are too large?
        song_begin =int(self.width() * song_begin / Gst.MSECOND / self.maximum()) if song_begin else None
        song_end = int(self.width() * song_end / Gst.MSECOND / self.maximum()) if song_end else None
        painter.setPen(QColor(Qt.red))
        if song_begin:
            painter.drawLine(song_begin, 0, song_begin, self.height())
        if song_end:
            painter.drawLine(song_end, 0, song_end, self.height())
        del painter
            

class TandaMasterWindow(QMainWindow):

    def __init__(self, parent = None):
        super().__init__(parent)
        self.profiler = None
        self.setWindowTitle('TandaMaster')        
        self.setWindowIcon(MyIcon('iconarchive/icons8/tandamaster-Sports-Dancing-icon.png'))

        self.player = TMPlayer()
        #self.player2 = TMPlayer() # pre-listening

        self.ui_xml_filename = locate_file(QStandardPaths.AppDataLocation, 'ui.xml')
        self.ui_xml = etree.parse(self.ui_xml_filename)
        
        geometry = self.ui_xml.getroot().get('geometry')
        if geometry:
            self.restoreGeometry(binascii.unhexlify(geometry))
        self.setCentralWidget(TMWidget.create_from_xml(self.ui_xml.find('CentralWidget')[0],self))

        if self.player.current and self.player.current.model:
            widget = self.player.current.model.view
            while widget.parent():
                widget.setFocus(Qt.OtherFocusReason)
                widget = widget.parent()
                
        menubar = QMenuBar()

        self.musicmenu = QMenu(self.tr('&Music'))
        
        action_save_playtree = QAction(
            self.tr("&Save"), self,
            shortcut=QKeySequence.Save,
            triggered = self.save)
        self.musicmenu.addAction(action_save_playtree)
        
        action_save_tags = QAction(
            self.tr("&Save tags"), self,
            shortcut=QKeySequence('ctrl+shift+s'),
            triggered = self.save_tags)
        self.musicmenu.addAction(action_save_tags)
        
        self.action_update_library = QAction(
            self.tr("&Update library"), self,
            triggered = self.update_library)
        self.musicmenu.addAction(self.action_update_library)

        self.action_update_library = QAction(
            self.tr("&Update library (forced)"), self,
            triggered = lambda: self.update_library(force = True))
        self.musicmenu.addAction(self.action_update_library)

        self.action_update_selected = QAction(
            self.tr("&Update selected (forced)"), self,
            triggered = swcm(PlayTreeView, PlayTreeView.update_selected_from_file))
        self.musicmenu.addAction(self.action_update_selected)
        
        action_save_playtree_to_folder = QAction(
            self.tr("&Save playtree files to folder in order ..."), self,
            triggered=self.save_playtree_to_folder)
        self.musicmenu.addAction(action_save_playtree_to_folder)
        
        if not getattr(sys, 'frozen', False):
            action_adhoc = QAction(
                self.tr("&AdHoc"), self,
                statusTip="Adhoc action", triggered=self.adhoc)
            self.musicmenu.addAction(action_adhoc)
        
        action_quit = QAction(
            self.tr("&Quit"), self, shortcut=QKeySequence.Quit,
            statusTip="Quit the program", triggered=self.close)
        self.musicmenu.addAction(action_quit)
        
        menubar.addMenu(self.musicmenu)

        self.playbackmenu = QMenu(self.tr('&Playback'))
        
        self.action_back = QAction(
            #self.style().standardIcon(QStyle.SP_MediaSkipBackward), 
            #MyIcon('Tango', 'actions', 'media-skip-backward'),
            MyIcon('button_rewind_green.png'),
            #MyIcon('iconfinder/32pxmania/previous.png'),
            self.tr('P&revious'), self, triggered = self.player.play_previous)
        self.playbackmenu.addAction(self.action_back)
        
        self.action_play = QAction(
            #self.style().standardIcon(QStyle.SP_MediaPlay), 
            #MyIcon('Tango', 'actions', 'media-playback-start'),
            MyIcon('button_play_green.png'),
            #MyIcon('iconfinder/32pxmania/play.png'),
            self.tr('&Play'), 
            self,
            shortcut = QKeySequence('space'),
            triggered = self.play)
        self.playbackmenu.addAction(self.action_play)

        action_play_this = QAction(
            #self.style().standardIcon(QStyle.SP_MediaPlay), 
            #MyIcon('Tango', 'actions', 'media-playback-start'),
            MyIcon('button_play_green.png'),
            #MyIcon('iconfinder/32pxmania/play.png'),
            self.tr('Play this'), 
            self,
            shortcut = QKeySequence('ctrl+space'),
            triggered = swcm(PlayTreeView, PlayTreeView.play_this))
        self.addAction(action_play_this)
        
        self.action_pause =  QAction(
            #self.style().standardIcon(QStyle.SP_MediaPause), 
            #MyIcon('Tango', 'actions', 'media-playback-pause'),
            MyIcon('button_pause_green.png'),
            #MyIcon('iconfinder/32pxmania/pause.png'),
            self.tr('&Pause'), self, 
            shortcut = QKeySequence('space'),
            triggered = self.player.pause)
        self.playbackmenu.addAction(self.action_pause)
        
        self.action_stop = QAction(
            #self.style().standardIcon(QStyle.SP_MediaStop), 
            #MyIcon('Tango', 'actions', 'media-playback-stop'),
            MyIcon('button_stop_green.png'),
            #MyIcon('iconfinder/32pxmania/stop.png'),
            self.tr('&Stop'), self, triggered = self.player.stop)
        self.playbackmenu.addAction(self.action_stop)
        
        self.action_forward = QAction(
            #self.style().standardIcon(QStyle.SP_MediaSkipForward), 
            #MyIcon('Tango', 'actions', 'media-skip-forward'),
            MyIcon('button_fastforward_green.png'),
            #MyIcon('iconfinder/32pxmania/next.png'),
            self.tr('&Next'), self, triggered = self.player.play_next,
            shortcut = QKeySequence('ctrl+n'),
        )
        self.playbackmenu.addAction(self.action_forward)
        
        self.playbackmenu.addSeparator()
        
        # todo: disablaj lock kadar je state STOPPED, na koncu seznama pa avtomatsko odkleni
        self.action_lock = QAction(
            MyIcon('iconfinder/iconza/unlocked.png'),
            self.tr('Un&locked'), self, toggled = self.lock)
        self.action_lock.setCheckable(True)
        self.playbackmenu.addAction(self.action_lock)
        
        self.playbackmenu.addSeparator()
        
        self.action_mark_start_end = QAction(
            self.tr('Mark start/end'), self,
            triggered = self.mark_start_end,
            shortcut = QKeySequence('.'))
        self.playbackmenu.addAction(self.action_mark_start_end)
        
        menubar.addMenu(self.playbackmenu)

        self.editmenu = QMenu(self.tr('&Edit'))
        
        self.action_cut = QAction(
            #MyIcon('Tango', 'actions', 'edit-cut'),
            #MyIcon('tango/edit-cut'),
            MyIcon('iconfinder/farm-fresh/cut.png'),
            self.tr('Cu&t'), self, triggered = swcm(PlayTreeView, PlayTreeView.cut),
            shortcut = QKeySequence(QKeySequence.Cut))
        
        self.action_copy = QAction(
            #MyIcon('tango/edit-copy'),
            #MyIcon('Tango', 'actions', 'edit-copy'),
            MyIcon('iconfinder/farm-fresh/copy.png'),
            self.tr('&Copy'), self, triggered = swcm(PlayTreeView, PlayTreeView.copy),
            shortcut = QKeySequence(QKeySequence.Copy))
        
        self.action_paste = QAction(
            #MyIcon('Tango', 'actions', 'edit-paste'),
            #MyIcon('tango/edit-paste'),
            MyIcon('iconfinder/farm-fresh/paste.png'),
            self.tr('&Paste'), self, triggered = swcm(PlayTreeView, PlayTreeView.paste),
            shortcut = QKeySequence(QKeySequence.Paste))
        
        self.action_insert = QAction(
            MyIcon('iconfinder/32pxmania/insert.png'),
            self.tr('&Insert'), self, triggered = swcm(PlayTreeView, PlayTreeView.insert),
            shortcut = QKeySequence('insert'))
        
        self.action_delete = QAction(
            MyIcon('iconfinder/32pxmania/delete.png'),
            self.tr('&Delete'), self, triggered = swcm(PlayTreeView, PlayTreeView.delete),
            shortcut = QKeySequence(QKeySequence.Delete))
        
        self.action_group = QAction(
            MyIcon('iconfinder/farm-fresh/group.png'),
            self.tr('&Group'), self, triggered = swcm(PlayTreeView, PlayTreeView.group),
            shortcut = QKeySequence('Ctrl+g'))
        
        self.action_group_into_tandas = QAction(
            MyIcon('iconfinder/farm-fresh/group.png'),
            self.tr('Group into tandas'), self, triggered = swcm(PlayTreeView, PlayTreeView.group_into_tandas),
            shortcut = QKeySequence('Ctrl+Shift+g'))
        
        self.action_ungroup = QAction(
            MyIcon('iconfinder/farm-fresh/ungroup.png'),
            self.tr('&Ungroup'), self, triggered = swcm(PlayTreeView, PlayTreeView.ungroup),
            shortcut = QKeySequence('Ctrl+u'))
        
        self.action_move_up = QAction(
            #MyIcon('iconfinder/32pxmania/up.png'),
            MyIcon('iconfinder/momentum_glossy/arrow-up.png'),
            self.tr('Move &up'), self,
            triggered = swcm(PlayTreeView, PlayTreeView.move_up),
            shortcut = QKeySequence('alt+up'))
        
        self.action_move_down = QAction(
            #MyIcon('iconfinder/32pxmania/down.png'),
            MyIcon('iconfinder/momentum_glossy/arrow-down.png'),
            self.tr('Move &down'), self, triggered = swcm(PlayTreeView, PlayTreeView.move_down),
            shortcut = QKeySequence('alt+down'))
        
        self.action_move_up_left = QAction(
            MyIcon('iconfinder/momentum_glossy/arrow-up-left.png'),
            self.tr('Move up &out of parent'), self, triggered = swcm(PlayTreeView, PlayTreeView.move_up_left))
        
        self.action_move_down_right = QAction(
            MyIcon('iconfinder/momentum_glossy/arrow-down-right.png'),
            self.tr('Move into &next sibling'), self, triggered = swcm(PlayTreeView, PlayTreeView.move_down_right))
        
        self.action_move_down_left = QAction(
            MyIcon('iconfinder/momentum_glossy/arrow-down-left.png'),
            self.tr('Move down &out of parent'), self,
            triggered = swcm(PlayTreeView, PlayTreeView.move_down_left),
            shortcut = QKeySequence('alt+left'))
        
        self.action_move_up_right = QAction(
            MyIcon('iconfinder/momentum_glossy/arrow-up-right.png'),
            self.tr('Move into &previous sibling'), self,
            triggered = swcm(PlayTreeView, PlayTreeView.move_up_right),
            shortcut = QKeySequence('alt+right'))

        self.action_move_home = QAction(
            MyIcon('iconfinder/momentum_glossy/move_top.png'),
            self.tr('Move to &top'), self, triggered = swcm(PlayTreeView, PlayTreeView.move_home),
            shortcut = QKeySequence('alt+home'))
        
        self.action_move_end = QAction(
            MyIcon('iconfinder/momentum_glossy/move_bottom.png'),
            self.tr('Move to &bottom'), self, triggered = swcm(PlayTreeView, PlayTreeView.move_end),
            shortcut = QKeySequence('alt+end'))

        self.action_edit_tag = QAction(
            #MyIcon('iconfinder/32pxmania/up.png'),
            self.tr('&Edit tag'), self, triggered = swcm(PlayTreeView, PlayTreeView.edit_tag))
        
        self.action_save_tag = QAction(
            #MyIcon('iconfinder/32pxmania/up.png'),
            self.tr('&Save tag'), self, triggered = swcm(PlayTreeView, PlayTreeView.save_tag))
        
        self.action_revert_tag = QAction(
            #MyIcon('iconfinder/32pxmania/up.png'),
            self.tr('&Revert tag'), self, triggered = swcm(PlayTreeView, PlayTreeView.revert_tag))

        self.action_edit_tags = QAction(
            #MyIcon('iconfinder/32pxmania/up.png'),
            self.tr('&Edit tags'), self, triggered = swcm(PlayTreeView, PlayTreeView.edit_tags), shortcut='ctrl+e')

        self.action_edit_tags_mode = QAction(
            MyIcon('iconfinder/farm-fresh/edit.png'),
            self.tr('Edit &tags mode'), self, toggled = self.edit_tags_mode)
        self.action_edit_tags_mode.setCheckable(True)

        self.action_change_case = QAction(
            MyIcon('iconfinder/retina/font_case.png'),
            self.tr('Change &case'), self, triggered = swcm(PlayTreeView, PlayTreeView.change_case), shortcut='shift+f3')
        
        action_undo = undo_stack.createUndoAction(self)
        action_redo = undo_stack.createRedoAction(self)
        action_undo.setIcon(MyIcon('iconfinder/32pxmania/undo.png'))
        action_redo.setIcon(MyIcon('iconfinder/32pxmania/redo.png'))
        action_undo.setShortcut(QKeySequence(QKeySequence.Undo))
        action_redo.setShortcut(QKeySequence(QKeySequence.Redo))
        
        self.editmenu.addAction(action_undo)
        self.editmenu.addAction(action_redo)
        self.editmenu.addSeparator()
        self.editmenu.addAction(self.action_cut)
        self.editmenu.addAction(self.action_copy)
        self.editmenu.addAction(self.action_paste)
        self.editmenu.addSeparator()
        self.editmenu.addAction(self.action_insert)
        self.editmenu.addAction(self.action_delete)
        self.editmenu.addAction(self.action_group)
        self.editmenu.addAction(self.action_move_home)
        self.editmenu.addAction(self.action_move_up)
        self.editmenu.addAction(self.action_move_down)
        self.editmenu.addAction(self.action_move_end)
        self.editmenu.addAction(self.action_move_up_left)
        self.editmenu.addAction(self.action_move_down_right)
        self.editmenu.addSeparator()
        self.editmenu.addAction(self.action_edit_tag)
        self.editmenu.addAction(self.action_change_case)
        self.editmenu.addAction(self.action_save_tag)
        self.editmenu.addAction(self.action_revert_tag)
        self.editmenu.addAction(self.action_edit_tags)
        self.editmenu.addAction(self.action_edit_tags_mode)
        self.editmenu.addSeparator()
        self.editmenu.addAction(self.action_group_into_tandas)
        
        menubar.addMenu(self.editmenu)

        self.viewmenu = QMenu(self.tr('View'))

        self.action_columns_minimal = QAction(
            app.tr('Columns: minimal'), 
            self,
            triggered = swcm(PlayTreeView, PlayTreeView.set_columns, ('title',) ))
        
        self.action_columns_normal = QAction(
            app.tr('Columns: Alja'), 
            self,
            triggered = swcm(
                PlayTreeView, PlayTreeView.set_columns,
                ('title', 'artist', 'performer:vocals', 'date', 'genre', '_length')))
        
        self.action_columns_Dawn = QAction(
            app.tr('Columns: Dawn'), 
            self,
            triggered = swcm(
                PlayTreeView, PlayTreeView.set_columns,
                ('title', '_length', 'genre', 'artist', 'comment', 'date',
                 '_bitrate', 'album', 'tracknumber', 'albumartist')))
        
        self.action_columns_all = QAction(
            app.tr('Columns: all'), 
            self,
            triggered = swcm(PlayTreeView, PlayTreeView.set_columns, PlayTreeModel.columns))

        self.action_autoresize = QAction(
            app.tr('Resize columns to contents'),
            self,
            triggered = swcm(PlayTreeView, PlayTreeView.autoresize_columns))
        
        self.action_expand_all = QAction(
            app.tr('&Expand all'),
            self,
            triggered = swcm(PlayTreeView, PlayTreeView.expandAll)
        )

        self.action_collapse_all = QAction(
            app.tr('&Collapse all'),
            self,
            triggered = swcm(PlayTreeView, PlayTreeView.collapseAll)
        )

        self.action_show_current = QAction(
            app.tr('&Show current'),
            self,
            triggered = self.show_current
        )

        self.viewmenu.addAction(self.action_columns_minimal)
        self.viewmenu.addAction(self.action_columns_normal)
        self.viewmenu.addAction(self.action_columns_Dawn)
        self.viewmenu.addAction(self.action_columns_all)
        self.viewmenu.addSeparator()
        self.viewmenu.addAction(self.action_autoresize)
        self.viewmenu.addSeparator()
        self.viewmenu.addAction(self.action_expand_all)
        self.viewmenu.addAction(self.action_collapse_all)
        self.viewmenu.addAction(self.action_show_current)

        menubar.addMenu(self.viewmenu)

        self.toolsmenu = QMenu(self.tr('Tools'))
        
        self.action_calculate_replay_gain = QAction(
            self.tr('Calculate &replay gain of songs in playtree'), self,
            triggered = swcm(PlayTreeView, lambda ptv: TMReplayGain(ptv.model())))
        self.toolsmenu.addAction(self.action_calculate_replay_gain)
        
        self.action_calculate_start_end = QAction(
            self.tr('Calculate &start and end of songs in playtree'), self,
            triggered = swcm(PlayTreeView, self.trim))
        self.toolsmenu.addAction(self.action_calculate_start_end)

        self.action_milonga_info = QAction(
            self.tr('Milonga &info'), self,
            triggered = swcm(PlayTreeView, PlayTreeView.milonga_info),
            shortcut = QKeySequence('ctrl+shift+i'))
        self.toolsmenu.addAction(self.action_milonga_info)

        if platform.system() == 'Linux':
            self.action_getfilesfromalja = QAction(
                self.tr('Get files from &Alja'), self,
                triggered = lambda: self.run_on_selected_rows(GetFilesFromAlja))
            self.toolsmenu.addAction(self.action_getfilesfromalja)

            self.action_latexsonginfo = QAction(
                self.tr('Make PDF for songs'), self,
                triggered = lambda: self.run_on_selected_rows(LaTeXSongInfo))
            self.toolsmenu.addAction(self.action_latexsonginfo)
        
        self.action_report = QAction(
            self.tr('Report'), self,
            triggered = lambda: Report(self.current_playtree()))
        self.toolsmenu.addAction(self.action_report)

        menubar.addMenu(self.toolsmenu)

        self.musicmenu.addAction(action_quit)
        
        self.setMenuBar(menubar)

        toolbar = QToolBar('ProgressBar', self)
        pb = TMPositionProgressBar(self.player)
        toolbar.addWidget(pb)
        self.addToolBar(Qt.BottomToolBarArea, toolbar)

        self.addToolBarBreak(Qt.BottomToolBarArea)

        toolbar = QToolBar('Play controls', self)
        toolbar.setAllowedAreas(Qt.TopToolBarArea | Qt.BottomToolBarArea)
        toolbar.setFloatable(False)
        toolbar.addAction(self.action_back)
        toolbar.addAction(self.action_play)
        toolbar.addAction(self.action_pause)
        toolbar.addAction(self.action_stop)
        toolbar.addAction(self.action_forward)
        toolbar.addSeparator()
        toolbar.addAction(self.action_lock)
        self.stopafter_spinbox = QSpinBox()
        self.stopafter_spinbox.setMinimum(0)
        self.stopafter_spinbox.valueChanged.connect(self.player.play_order.set_stop_after)
        toolbar.addWidget(self.stopafter_spinbox)
        toolbar.addSeparator()
        toolbar.addWidget(TMVolumeControl(Qt.Horizontal, self.player))
        toolbar.addSeparator()
        self.play_orders_combo = QComboBox()
        for name, cls in PlayOrder.play_orders:
            self.play_orders_combo.addItem(name, cls)
        self.play_orders_combo.setCurrentText(self.player.play_order.name)
        def set_play_order(index):
            self.player.set_play_order(self.play_orders_combo.currentData()())
        self.play_orders_combo.currentIndexChanged.connect(set_play_order)
        toolbar.addWidget(self.play_orders_combo)

        self.addToolBar(Qt.BottomToolBarArea, toolbar)
        
        toolbar = QToolBar('Edit', self)
        
        def add_actions_to_toolbar(*actions):
            inner = QToolBar()
            inner.setFloatable(False)
            inner.setMovable(False)
            inner.setOrientation(Qt.Vertical)
            for action in actions:
                inner.addAction(action)
            toolbar.addWidget(inner)
        
        add_actions_to_toolbar(self.action_cut, action_undo)
        add_actions_to_toolbar(self.action_copy, action_redo)
        add_actions_to_toolbar(self.action_paste)
        toolbar.addSeparator()
        add_actions_to_toolbar(self.action_insert, self.action_delete)
        add_actions_to_toolbar(self.action_group, self.action_ungroup)
        add_actions_to_toolbar(self.action_move_home, self.action_move_end)
        toolbar.addSeparator()
        add_actions_to_toolbar(self.action_move_up_left, self.action_move_down_left)
        add_actions_to_toolbar(self.action_move_up, self.action_move_down)
        add_actions_to_toolbar(self.action_move_up_right, self.action_move_down_right)
        toolbar.addSeparator()
        add_actions_to_toolbar(self.action_edit_tags_mode, self.action_change_case)
        self.addToolBar(toolbar)
        #self.toolbar = toolbar

        self.setStatusBar(QStatusBar())
        app.info.connect(self.status_bar_message)
        app.error.connect(self.status_bar_error_message)
        self.fadeout_gap_pb = TMGapAndFadeoutProgressBar(self.player)

        self.song_info = QLabel()
        self.song_info.setContentsMargins(8,0,8,0)
        self.statusBar().addPermanentWidget(self.song_info)
        self.next_song_info = QLabel()
        self.next_song_info.setContentsMargins(8,0,8,0)
        self.next_song_info.hide()

        self.player.current_changed.connect(self.update_song_info, type = Qt.QueuedConnection)
        self.player.duration_changed.connect(self.update_song_info, type = Qt.QueuedConnection)
        self.player.next_changed.connect(self.update_next_song_info, type = Qt.QueuedConnection)
        self.player.current_changed.connect(lambda: self.lock_action_forward(), type = Qt.QueuedConnection)
        self.player.current_changed.connect(lambda: self.lock_action_playpause(), type = Qt.QueuedConnection)
        self.player.state_changed.connect(self.on_player_state_changed, type = Qt.QueuedConnection)
        self.on_player_state_changed(TMPlayer.STOPPED)
        QApplication.clipboard().changed.connect(self.on_clipboard_data_changed)

        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.save)
        self.autosave_timer.start(config.autosave_interval*60*1000)
        
    def sizeHint(self):
        return QSize(1800, 800)

    def update_song_info(self):
        if self.player.current:
            song_info_formatter = SongInfoFormatter(self.player.current.item)
            self.setWindowTitle(song_info_formatter.format(
                "{artist} - {title} | TandaMaster"))
            self.song_info.setText(song_info_formatter.format(
                "{artist} <b>{title}</b>{duration}", duration = ' ' + time_to_text(self.player.duration,unit='ns',include_ms=False) if self.player.duration else ''))
        else:
            self.setWindowTitle("TandaMaster")
            self.song_info.setText("")
            
    def update_next_song_info(self):
        next = self.player.concrete(self.player.next)
        if next:
            song_info_formatter = SongInfoFormatter(next.item)
            self.next_song_info.setText(song_info_formatter.format(
                "{artist} <b>{title}</b>"))
        else:
            self.next_song_info.setText('')
        self.next_song_info.update()
            
    def on_player_state_changed(self, state):
        if state in (TMPlayer.PLAYING, TMPlayer.PLAYING_FADEOUT, TMPlayer.PLAYING_GAP, TMPlayer.PLAYING_FADEOUT):
            self.action_play.setVisible(False)
            self.action_pause.setVisible(True)
            self.action_stop.setEnabled(not self.action_lock.isChecked())
        else:
            self.action_play.setVisible(True)
            self.action_pause.setVisible(False)
            self.action_stop.setEnabled(state != TMPlayer.STOPPED and not self.action_lock.isChecked())
        if state in (TMPlayer.PLAYING_FADEOUT, TMPlayer.PLAYING_GAP):
            self.fadeout_gap_pb.setMaximumHeight(self.song_info.height())
            self.statusBar().addPermanentWidget(self.fadeout_gap_pb)
            self.update_next_song_info()
            self.statusBar().addPermanentWidget(self.next_song_info)
            self.fadeout_gap_pb.show()
            self.next_song_info.show()
        else:
            self.statusBar().removeWidget(self.fadeout_gap_pb)
            self.statusBar().removeWidget(self.next_song_info)
        #self.toolbar.update()

    def update_library(self, force = False):
        #thread = QThread(self)
        #thread.library = Library(connect = False)
        #thread.library.moveToThread(thread)
        #thread.started.connect(thread.library.connect)
        update_progress = TMProgressBar()
        update_progress.setMaximumWidth(150)
        update_progress.setMinimum(0)
        update_progress.setMaximum(library().connection.execute('SELECT COUNT(*) FROM files;').fetchone()[0])
        update_progress.setFormat('Updating library: %p%')
        self.statusBar().addPermanentWidget(update_progress)
        def update_library_progress():
            if update_progress.value() == update_progress.maximum():
                update_progress.setMaximum(0)
            else:
                update_progress.setValue(update_progress.value()+1)
        #print("main  ",library(),QThread.currentThread())#,threading.current_thread())
        def finished():
            self.statusBar().showMessage('Finished updating library')
            self.statusBar().removeWidget(update_progress)
            self.action_update_library.setEnabled(True)
        thread = UpdateLibraryThread(parent = self, force = force)
        thread.progress.connect(update_library_progress)
        thread.finished.connect(finished)
        app.aboutToQuit.connect(thread.exit)
        def _update_library_thread_started():
            #print("thread",library(),QThread.currentThread(),threading.current_thread())
            library().refresh_all_libraries()
            #library().refresh_finished.connect(thread.exit)
            library().refresh_finished.connect(lambda: print('Finished updating library'))
            library().refresh_finished.connect(lambda: self.statusBar().showMessage('Finished updating library'))
            library().refresh_finished.connect(lambda: self.statusBar().removeWidget(update_progress))
            library().refresh_next.connect(_update_library_progress)
        #thread.started.connect(_update_library_thread_started)
        #library().refresh_finished.connect(self.reset_all)
        #thread.library.refreshing.connect(self.statusBar().showMessage)
        self.action_update_library.setEnabled(False)
        thread.start()

    def reset_all(self):
        for w in self.window().findChildren(PlayTreeView):
            model = w.model()
            model.beginResetModel()
            model.root_item.populate(model, force = True)
            model.endResetModel()

    def play(self):
        if self.player.state == self.player.STOPPED:
            ptv = app.focusWidget()
            if isinstance(ptv, PlayTreeView):
                self.player.play_index(ptv.currentIndex())
            else:
                self.player.play_next()
        else:
            self.player.play()

    def on_clipboard_data_changed(self, mode):
        if mode == QClipboard.Clipboard:
            ptv = app.focusWidget()
            if not isinstance(ptv, PlayTreeView): return
            self.window().action_paste.setEnabled(ptv.can_paste())

    def lock(self, locked):
        if locked:
            self.action_lock.setIcon(MyIcon('iconfinder/iconza/locked.png'))
            self.action_lock.setText(app.tr('&Locked'))
            self.action_play.setEnabled(locked)
        else:
            self.action_lock.setIcon(MyIcon('iconfinder/iconza/unlocked.png'))
            self.action_lock.setText(app.tr('Un&locked'))
        self.action_back.setEnabled(not locked)
        #self.action_play.setEnabled(not locked)
        #self.action_pause.setEnabled(not locked)
        self.lock_action_playpause(locked)
        self.action_stop.setEnabled(not locked)
        self.stopafter_spinbox.setEnabled(not locked)
        self.play_orders_combo.setEnabled(not locked)
        self.lock_action_forward(locked)
        self.player.current.model.view.parent().search.setEnabled(not locked)

    def lock_action_forward(self, locked = None):
        if locked is None:
            locked = self.action_lock.isChecked()
        self.action_forward.setEnabled(not locked or (self.player.current and self.player.current.item.function() == 'cortina'))

    def lock_action_playpause(self, locked = None):
        if locked is None:
            locked = self.action_lock.isChecked()
        self.action_play.setEnabled(not locked or (self.player.current and self.player.current.item.function() == 'cortina'))
        self.action_pause.setEnabled(not locked or (self.player.current and self.player.current.item.function() == 'cortina'))

    # todo: update duration on play
    def mark_start_end(self):
        position = self.player.playbin.query_position(Gst.Format.TIME)
        if position[0]:
            duration = self.player.playbin.query_duration(Gst.Format.TIME)
            if not duration[0] or position[1] < duration[1] / 2:
                self.player.current.song_begin = position[1]
                self.player.current.item.set_tag(# todo: undoable!
                    'tm:song_start',
                    [float(position[1])/Gst.SECOND])
            else:
                self.player.current.song_end = position[1]
                self.player.current.item.set_tag(
                    'tm:song_end',
                    [float(position[1])/Gst.SECOND])
                
    def mark_end_cut(self):
        position = self.player.playbin.query_position(Gst.Format.TIME)
        if position[0]:
            self.player.current.song_end = position[1]
            self.player.current.item.set_tag(
                'tm:song_end',
                [float(position[1])/Gst.SECOND])
        
    def adhoc(self):
        print(blabla)

    def run_on_selected_rows(self, qrunnable):
        ptv = app.focusWidget()
        if not isinstance(ptv, PlayTreeView): return
        QThreadPool.globalInstance().start(qrunnable(selected_rows(ptv.selectionModel())))

    def save_playtree_to_folder(self):
        ptv = app.focusWidget()
        if not isinstance(ptv, PlayTreeView): return
        model = ptv.model()
        directory = QFileDialog.getSaveFileName(
            self,
            "Copy playtree to directory",
            os.path.expanduser("~"),
            "",
            "",
            QFileDialog.ShowDirsOnly
        )[0]
        if not directory:
            return
        os.makedirs(directory)
        if platform.system() == 'Linux':
            subprocess.call(['xdg-open', directory])
        error = []
        model.root_item.populate(model, recursive = True)
        for item in model.root_item.iter_depth(
                model,
                lambda item: isinstance(item, PlayTreeFile),
                lambda item: isinstance(item, PlayTreeList)):
            p = "-".join("{:03}".format(part) 
                         for part in model.index_to_path(item.index(model)))
            new_fn = os.path.join(directory, p + "-" + os.path.basename(item.filename))
            try:
                #self.info.progress.emit(item.filename, new_fn)
                shutil.copyfile(item.filename, new_fn)
            except:
                print("Could not copy", item.filename, "to", new_fn)
                error.append("{} -> {}".format(item.filename, new_fn))
        if error:
            mb = QMessageBox(
                QMessageBox.Warning,
                "Warning",
                "Some files could not be copied.",
                QMessageBox.Ok,
                None,
                Qt.Window,
            )
            mb.setDetailedText("\n".join(error))
            mb.exec()
        
    def closeEvent(self, event):
        if self.action_lock.isChecked():
            event.ignore()
        else:
            self.save()
            for w in EditTags.windows:
                w.close()
            super().closeEvent(event)

    def save(self):
        self.ui_xml.getroot().set(
            'geometry', 
            binascii.hexlify(self.saveGeometry().data()).decode())
        cw = self.ui_xml.find('CentralWidget')
        cw.clear()
        cw.append(self.centralWidget().to_xml())
        with open_autobackup(self.ui_xml_filename, 'w') as outfile:
            self.ui_xml.write(outfile, encoding='unicode')
        save_playtree()

    def save_tags(self):
        librarian.bg_queries(BgQueries([BgQuery(Library.save_changed_tags, ())], lambda qs: self.statusBar().showMessage('Finished saving tags')))
    
    _status_bar_duration = ''
    _status_bar_remaining = ''
    def update_status_bar(self, duration = None, remaining = None, remaining_color = None):
        if duration is not None:
            self._status_bar_duration = duration
        if remaining is not None:
            self._status_bar_remaining = remaining
        msg = " | ".join([m for m in (self._status_bar_duration, self._status_bar_remaining) if m])
        if remaining_color:
            self.window().statusBar().setStyleSheet(f"color:{remaining_color}")
        else:
            self.window().statusBar().setStyleSheet("")
        self.window().statusBar().showMessage(msg)

    def status_bar_message(self, msg):
        self.update_status_bar(remaining = msg)

    def status_bar_error_message(self, msg):
        self.update_status_bar(remaining = msg, remaining_color = "red")
        
    def edit_tags_mode(self, checked):
        for ptv in self.window().findChildren(PlayTreeView):
            #ptv.setAllColumnsShowFocus(not checked)
            ptv.setSelectionBehavior(QAbstractItemView.SelectItems if checked else QAbstractItemView.SelectRows)
            ptv.setEditTriggers(QAbstractItemView.EditKeyPressed | QAbstractItemView.SelectedClicked)
            ptv.setCurrentIndex(ptv.currentIndex())

    def show_current(self):
        child = self.player.current.index
        last_unused_child = child
        parent = self.player.current.model.view
        while parent:
            try:
                self.setFocus(Qt.OtherFocusReason)
                parent._show(child, last_unused_child)
                last_unused_child = parent
            except AttributeError:
                pass
            child = parent
            parent = parent.parent()


    def current_playtree(self):
        ptv = self.focusWidget()
        return ptv if isinstance(ptv, PlayTreeView) else None

    def trim(self, ptv):
        from .mp3splt import Mp3Splt
        model = ptv.model()
        model.root_item.populate(model, recursive = True)
        Mp3Splt().trim.emit([
            item for item
            in model.root_item.iter(
                model,
                lambda it: it.isPlayable,
                lambda it: not it.isTerminal)
        ])

            
class TMPositionProgressBar_Interaction(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseMove:   
            if obj.in_seek:
                obj.player.seek(obj.maximum() * Gst.MSECOND * event.x() / obj.width())
            if obj.player_state != TMPlayer.STOPPED:
                QToolTip.showText(event.globalPos(),
                                  hmsms_to_text(*ms_to_hmsms(int(
                                      obj.maximum() * event.x() / obj.width())),
                                                include_ms = False),
                                  obj, QRect())
        elif event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            if obj.window().action_lock.isChecked():
                return False
            obj.in_seek = True
            obj.player.seek(obj.maximum() * Gst.MSECOND * event.x() / obj.width())
        elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            if obj.window().action_lock.isChecked():
                return False
            obj.in_seek = False
        return False

class TMGapAndFadeoutProgressBar(TMProgressBar):
    def __init__(self, player, parent = None):
        super().__init__(parent)
        self.setMaximumWidth(100)
        self.player = player
        self.setMinimum(0)
        player.state_changed.connect(self.on_state_changed)
        player.gap_position_changed.connect(self.on_value_changed)
        player.fadeout_position_changed.connect(self.on_value_changed)
        self.on_state_changed(TMPlayer.STOPPED)
        self.update()
        self._text = ''
        
    def on_state_changed(self, state):
        if state == TMPlayer.PLAYING_FADEOUT:
            fadeout_duration = self.player.current.fadeout_duration
            self.setMaximum(int(fadeout_duration/Gst.MSECOND))
            self.setValue(int(fadeout_duration/Gst.MSECOND))
            self.setEnabled(True)
            self._text = 'fadeout {:1g}s'.format(fadeout_duration/Gst.SECOND)
        elif state == TMPlayer.PLAYING_GAP:
            gap_duration = self.player.current.gap_duration
            self.setMaximum(int(gap_duration/Gst.MSECOND))
            self.setValue(0)
            self.setEnabled(True)
            self._text = 'gap {:1g}s'.format(gap_duration/Gst.SECOND)
        else:
            self.setValue(0)
            self.setEnabled(False)
            self._text = ''
        self.update()

    def on_value_changed(self, position):
        self.setValue(int(position/Gst.MSECOND))
        self.update()

    def text(self):
        return time_to_text(self.value(), unit = 'ms')

    def text(self):
        return self._text

class TMVolumeControl(QSlider):
    def __init__(self, orientation, player, parent = None):
        super().__init__(orientation, parent)
        self.player = player
        self.setMinimum(0)
        self.setMaximum(1000)
        self.on_volume_changed(self.player.volume)
        self.player.volume_changed.connect(self.on_volume_changed)
        self.valueChanged.connect(self.on_value_changed)

    def on_volume_changed(self, volume):
        self.blockSignals(True)
        #self.setValue(int(1000*GstAudio.stream_volume_convert_volume(
        #        GstAudio.StreamVolumeFormat.LINEAR,
        #        GstAudio.StreamVolumeFormat.CUBIC,
        #        volume)))
        self.setValue(int(1000 * (volume ** (1/3))))
        self.blockSignals(False)

    def on_value_changed(self, value):
        #self.player.volume = GstAudio.stream_volume_convert_volume(
        #            GstAudio.StreamVolumeFormat.CUBIC,
        #            GstAudio.StreamVolumeFormat.LINEAR,
        #            value/1000)
        self.player.volume = (value/1000) ** 3
        
class GetFilesFromAlja(QRunnable):
    def __init__(self, selected_indexes):
        super().__init__()
        if selected_indexes:
            model = selected_indexes[0].model()
            self.items = [child_item for index in selected_indexes for child_item in model.item(index).iter(model, lambda it: it.isTerminal, lambda it: not it.isTerminal)]
        else:
            self.items = []
        
    def run(self):
        import paramiko
        ssh_client = paramiko.SSHClient()
        ssh_client.load_system_host_keys()
        ssh_client.set_missing_host_key_policy(paramiko.WarningPolicy())
        ssh_client.connect('localhost', port = 22000, username = 'alja')
        ftp = ssh_client.open_sftp()
        for item in self.items:
            target = item.filename
            source = target.replace('/home/saso/', '/home/alja/')
            fileinfo = QFileInfo(target)
            if not fileinfo.exists():
                app.info.emit('Downloading {} from Alja ...'.format(target))
                try:
                    os.makedirs(os.path.dirname(target))
                except:
                    pass
                ftp.get(source, target)
        ssh_client.close()
        app.info.emit('Downloading from Alja finished.')

class LaTeXSongInfo(QRunnable):
    def __init__(self, selected_indexes):
        super().__init__()
        if selected_indexes:
            model = selected_indexes[0].model()
            self.items = [child_item for index in selected_indexes for child_item in model.item(index).iter(model, lambda it: it.isTerminal, lambda it: not it.isTerminal)]
        else:
            self.items = []
        self.items = [
            (item.get_tag('artist', only_first = True, default = ''),
             item.get_tag('title', only_first = True, default = ''),
             item.get_tag('date', only_first = True, default = ''),
             item.get_tag('performer:vocals', only_first = True, default = ''),
             item.get_tag('genre', only_first = True, default = ''),             
         ) for item in self.items]
    def run(self):
        pdf = Path(config.song_pdf)
        with open(pdf.with_suffix('.tex'), 'w') as f:
            print(r"""\documentclass[tikz]{standalone}
\usepackage{fontspec}
\def\mypaperwidth{297mm}
\def\mypaperheight{210mm}
\def\myleftrightmargin{10mm}
\def\mytopbottommargin{10mm}
\def\napis#1{%
  \begin{tikzpicture}[x=.5*\mypaperwidth-\myleftrightmargin,y=.5*\mypaperheight-\mytopbottommargin] % 297x210mm = a4 landscape
    \path[use as bounding box] (-1,-1) -- +(-\myleftrightmargin,-\mytopbottommargin) -- (1,1) -- +(\myleftrightmargin,\mytopbottommargin);
    #1%
  \end{tikzpicture}
}
\def\fs#1{\fontsize{#1}{#1}\selectfont}
\newlength\myfs
\begin{document}
            """, file = f)
            for author, title, year, singer, genre in self.items:
                if singer.lower() == 'instrumental':
                    singer = ''
                year = str(year)
                if '-' in year:
                    year = year[0:year.find('-')]
                print(r"""\napis{%
\node at (0,0.5)[anchor=center,align=center,font=\fs{3cm}]{""" + author + r"""};
\node at (0,-0.2)[anchor=center,align=center,font=\fs{3cm}\it]{""" + title + r"""};
\node at (-1,-1)[anchor=south west,align=center,font=\fs{2cm}]{""" + year + r"""};
\node at (1,-1)[anchor=south east,align=center,font=\fs{2cm}]{""" + singer + r"""};
""" + ((r"""\node at (1,1)[anchor=north east,align=center,outer ysep=5mm,font=\fs{2cm}]{\textsc{""" + genre.lower() + r"""}};
""") if genre.lower() in ('vals', 'milonga') else '') + """}""", file = f)
            print(r"""\end{document}""", file=f)
        import subprocess
        subprocess.call(['xelatex', '-interaction', 'nonstopmode', pdf.stem],
                        cwd = pdf.parent)
        subprocess.call(['xdg-open', pdf], cwd = pdf.parent)


# icon sets:
# https://www.iconfinder.com/iconsets/Momentum_GlossyEntireSet
# https://www.iconfinder.com/iconsets/fatcow


import shutil
class EditTags(QWidget):
    windows = []
    def __init__(self, fileitem):
        super().__init__()
        self.setWindowTitle(str(fileitem))
        self.windows.append(self)

        self.view = EditTagsView(fileitem)

        layout = QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)
        self.show()

    def sizeHint(self):
        return self.view.viewportSizeHint() + QSize(0,50)

class EditTagsView(QTreeView):
    def __init__(self, fileitem, parent = None):
        super().__init__(parent)
        self.setModel(EditTagsModel(fileitem))
        self.setIndentation(0)
        for column in range(self.model().columnCount(QModelIndex())):
            self.resizeColumnToContents(column)
    def viewportSizeHint(self):
        qs = super().viewportSizeHint()
        return QSize(sum(self.columnWidth(column) for column in range(self.model().columnCount(QModelIndex()))), qs.height())
        
        
class EditTagsModel(QAbstractTableModel):
    def __init__(self, fileitem, parent = None):
        super().__init__(parent)
        self._fileitem = fileitem
        self.values = []
        self.populate()
        
    def columnCount(self, parent):
        return len(self.sources) + 1  if not parent.isValid() else 0

    def rowCount(self, parent):
        return len(self.values) if not parent.isValid() else 0
    
    sources = ['file', 'user']
    
    def populate(self):
        if not self._fileitem.song_id:
            return
        cursor = library().connection.execute(
            "SELECT tag, source, value FROM tags WHERE song_id = ?",
            (self._fileitem.song_id, ))
        row = cursor.fetchone()
        while row:
            value = [row[0]] + [None]*len(self.sources)
            value[self.sources.index(row[1])+1] = row[2]
            self.values.append(value)
            row = cursor.fetchone()
    
    def data(self, index, role = Qt.DisplayRole):
        if role in (Qt.DisplayRole, Qt.EditRole):
            return self.values[index.row()][index.column()]

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            self.values[index.row()][index.column()] = value
            return True
        return False

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | (
            Qt.ItemIsEditable
            if self.values[index.row()][0] != '_'
            else 0)

    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return 'Tag' if section == 0 else self.sources[section-1].title()



def selected_rows(selection):
    if not selection.hasSelection():
        return []
    indexes = selection.selectedIndexes()
    model = indexes[0].model()
    items = collections.OrderedDict()
    for index in indexes:
        items[model.item(index)] = None
    return [item.index(model) for item in items.keys()]


        
    
class Report(QWidget):
    def __init__(self, playtreeview):
        super().__init__()
        if not playtreeview:
            return
        layout = QVBoxLayout()

        option = QWidget()
        option_layout = QHBoxLayout()
        self.output_types = QButtonGroup(self)
        for output_type in ('text', 'LaTeX'):
            radio_button = QRadioButton(output_type)
            option_layout.addWidget(radio_button)
            self.output_types.addButton(radio_button)
        self.output_types.buttons()[0].setChecked(True)
        self.output_types.buttonToggled.connect(self.update_report)
        option.setLayout(option_layout)
        layout.addWidget(option)

        option = QWidget()
        option_layout = QHBoxLayout()
        self.languages = QButtonGroup(self)
        for language in ('Slovene', 'English'):
            radio_button = QRadioButton(language)
            option_layout.addWidget(radio_button)
            self.languages.addButton(radio_button)
        self.languages.buttons()[0].setChecked(True)
        self.languages.buttonToggled.connect(self.update_report)
        option.setLayout(option_layout)
        layout.addWidget(option)

        self.result_box = QPlainTextEdit()
        layout.addWidget(self.result_box)
        self.setLayout(layout)
        swcm(PlayTreeView, PlayTreeView.paste)
        self.selection_model = playtreeview.selectionModel()
        self.selection_model.selectionChanged.connect(self.update_report)
        self.update_report()
        self.show()
        self._keepalive = self # does this work?

    def update_report(self):
        self.result_box.setPlainText(self.create_report(
            self.selection_model.selectedRows(),
            self.output_types.checkedButton().text(),
            self.languages.checkedButton().text()
        ))

    def create_report(self, selected_indexes, output_type, language):
        if not selected_indexes:
            return ''
        report = ''
        model = selected_indexes[0].model()
        for index in selected_indexes:
            item = model.item(index)
            if isinstance(item, PlayTreeFile):
                artist = item.get_tag("artist", only_first = True, default = '')
                title = item.get_tag("title", only_first = True, default = '')
                year = str(item.get_tag("date", only_first = True, default = ''))
                if year.find('-') != -1:
                    year = year[0:year.find('-')]
                singer = item.get_tag("performer:vocals", only_first = True, default = '')
                if singer.lower() == 'instrumental':
                    singer = ''
                report += "{}{}: {} ({}{})\n".format(
                    r'\item ' if output_type == 'LaTeX' else '',
                    artist, title, year,
                    ', {}: {}'.format(
                        'poje' if language == 'Slovene' else 'singer',
                        singer) if singer else ''
                )
        return report

def swcm(cls, f, *args, **kwargs):
    """"Return Selected Widget's Class Method."""
    def bound_method():
        w = app.focusWidget()
        if not isinstance(w, cls): return
        f(w, *args, **kwargs)
    return bound_method
