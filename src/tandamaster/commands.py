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

from PyQt5.Qt import *   # todo: import only what you need
from .app import *
undo_stack = QUndoStack(app)
from .library import library
from .util import *

import collections

class TMPlayTreeItemsCommand(QUndoCommand):
    @staticmethod
    def describe_items(items):
        n_other = len(items)-1
        if n_other == -1:
            return 'nothing'
        return '"{}"{}'.format(
            str(items[0]),
            app.tr(' and %n other item(s)', '', n_other) if n_other else '')

    def __init__(self, items, 
                 command_prefix = '', command_suffix = '', command_text = None, 
                 command_parent = None):
        command_text = ((command_prefix + ' ' if command_prefix else '') +
                        self.describe_items(items) +
                        (command_suffix + ' ' if command_suffix else '')) \
            if command_text is None else command_text
        super().__init__(command_text, command_parent)

class InsertPlayTreeItemsCommand(TMPlayTreeItemsCommand):
    def __init__(self, items, items_parent, before_item, 
                 command_prefix = 'Insert', command_suffix = None, command_text = None, 
                 Id = -1, command_parent = None, push = True):
        super().__init__(items, 
                         command_prefix, command_suffix, command_text, command_parent)
        self._id = Id
        self.items = items
        self.items_parent = items_parent
        self.before_item = before_item
        if push:
            undo_stack.push(self)
    def id(self):
        return self._id
    def redo(self):
        self.items_parent.insert(
            self.items, 
            self.items_parent.childs_row(None, self.before_item)
            if self.before_item is not None else 
            self.items_parent.rowCount(None))

    def undo(self):
        self.items_parent.delete(self.items)

    def mergeWith(self, other):
        if isinstance(other, EditPlayTreeNameCommand) and len(self.items) == 1 and self.items[0] == other.item:
            self.setText(self.text().replace(other.old_name, other.new_name))
            return True
        return False

class DeletePlayTreeItemsCommand(TMPlayTreeItemsCommand):
    def __init__(self, items, 
                 command_prefix = 'Delete', command_suffix = None, command_text = None, 
                 command_parent = None, push = True):
        super().__init__(items, 
                         command_prefix, command_suffix, command_text, command_parent)
        self.items = sorted(((item.parent, item.row(None), item) for item in items), 
                            key = lambda triplet: triplet[2].path(None))
        if push:
            undo_stack.push(self)

    def redo(self):
        for parent, row, item in self.items:
            parent.delete([item])

    def undo(self):
        for parent, row, item in self.items:
            parent.insert([item], row)

class MovePlayTreeItemsCommand(TMPlayTreeItemsCommand):
    def __init__(self, items, items_parent, before_item,
                 command_prefix = 'Move', command_suffix = None, command_text = None,
                 command_parent = None, push = True):
        super().__init__(items, 
                         command_prefix, command_suffix, command_text, command_parent)
        DeletePlayTreeItemsCommand(items, command_parent = self, push = False)
        InsertPlayTreeItemsCommand(items, items_parent, before_item,
                                   command_parent = self, push = False)
        if push:
            undo_stack.push(self)
    

class EditPlayTreeNameCommand(QUndoCommand):
    @classmethod
    def id(self):
        return 1
    def __init__(self, item, new_name, command_text = None, command_parent = None, push = True):
        command_text = 'Rename "{}" to "{}"'.format(item.name, new_name) \
                       if command_text is None else command_text
        super().__init__(command_text, command_parent)
        self.item = item
        self.old_name = item.name
        self.new_name = new_name
        if push:
            undo_stack.push(self)
    def redo(self):
        self.do_rename(self.new_name)
    def undo(self):
        self.do_rename(self.old_name)
    def do_rename(self, name):
        self.item.name = name
        for model in self.item.children.keys():
            if model:
                index = self.item.index(model, 0)
                model.dataChanged.emit(index, index, [Qt.EditRole])
        

class EditTagsCommand(TMPlayTreeItemsCommand):
    def __init__(self, model, items, tag, value, only_first = False,
                 command_prefix = 'Change', command_suffix = '', command_text = None, 
                 command_parent = None, push = True):
        self.model = model
        self.tag = tag
        self.old_values = collections.OrderedDict()
        self.only_first = only_first
        for item in items:
            for it in item.iter_depth(model, lambda i: i.isTerminal, lambda i: not i.isTerminal):
                self.old_values[it] = it.get_tag(tag)
        self.value = value
        command_prefix = '{} tag "{}" to "{}" for '.format(command_prefix, tag, value)
        super().__init__(items, command_prefix = command_prefix, command_suffix = command_suffix, command_text = command_text, command_parent = command_parent)
        if push:
            undo_stack.push(self)
    def redo(self):
        for item in self.old_values.keys():
            if self.only_first:
                values = item.get_tag(self.tag, only_first = False)
                if values:
                    values[0] = self.value
                else:
                    values = [self.value]
            else:
                values = self.value
            library().set_tag(item.song_id, self.tag, values)
            item.refresh_models()
    def undo(self):
        for item, old_values in self.old_values.items():
            library().set_tag(item.song_id, self.tag, old_values)
            item.refresh_models()

