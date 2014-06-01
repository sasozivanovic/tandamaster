from PyQt5.Qt import *   # todo: import only what you need
from app import *
undo_stack = QUndoStack(app)

class TMPlayTreeItemsCommand(QUndoCommand):
    @staticmethod
    def describe_items(items):
        return '"' + str(items[0]) + '"' if len(items) == 1 else '{} items'.format(len(items))
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
                 command_parent = None, push = True):
        super().__init__(items, 
                         command_prefix, command_suffix, command_text, command_parent)
        self.items = items
        self.items_parent = items_parent
        self.before_item = before_item
        if push:
            undo_stack.push(self)

    def redo(self):
        self.items_parent.insert(
            self.items, 
            self.items_parent.childs_row(None, self.before_item)
            if self.before_item is not None else 
            self.items_parent.rowCount(None))

    def undo(self):
        self.items_parent.delete(self.items)

class DeletePlayTreeItemsCommand(TMPlayTreeItemsCommand):
    def __init__(self, items, 
                 command_prefix = 'Delete', command_suffix = None, command_text = None, 
                 command_parent = None, push = True):
        super().__init__(items, 
                         command_prefix, command_suffix, command_text, command_parent)
        self.items = sorted((item.parent, item.row(None), item) for item in items)
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
    
