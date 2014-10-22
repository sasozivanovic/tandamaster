from PyQt5.QtCore import pyqtRemoveInputHook; from IPython import embed; pyqtRemoveInputHook()

from PyQt5.Qt import *   # todo: import only what you need

from player import TandaMasterPlayer
from model import *
from library import Library
from util import *
from app import *
from commands import *
import config

import collections, weakref, binascii, datetime

class TandaMasterWindow(QMainWindow):

    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle('TandaMaster')        
        self.setWindowIcon(QIcon('icons/iconarchive/icons8/tandamaster-Sports-Dancing-icon.png'))

        self.player = TandaMasterPlayer()
        #self.player2 = TandaMasterPlayer() # pre-listening

        try:
            self.ui_xml = etree.parse('ui.xml')
        except:
            self.ui_xml = etree.ElementTree(etree.fromstring(b'<MainWindow><CentralWidget><Splitter><TabbedPlayTreesWidget tabPosition="2"><PlayTreeWidget/></TabbedPlayTreesWidget><TabbedPlayTreesWidget tabPosition="0"><PlayTreeWidget/></TabbedPlayTreesWidget></Splitter></CentralWidget></MainWindow>'))

        geometry = self.ui_xml.getroot().get('geometry')
        if geometry:
            self.restoreGeometry(binascii.unhexlify(geometry))
        self.setCentralWidget(TMWidget.create_from_xml(self.ui_xml.find('CentralWidget')[0],self))

        menubar = QMenuBar()

        self.musicmenu = QMenu(self.tr('&Music'))
        action_save_playtree = QAction(
            self.tr("&Save"), self,
            shortcut=QKeySequence.Save,
            triggered = self.save)
        self.musicmenu.addAction(action_save_playtree)
        action_save_tags = QAction(
            self.tr("&Save tags"), self,
            triggered = self.save_tags)
        self.musicmenu.addAction(action_save_tags)
        self.action_update_library = QAction(
            self.tr("&Update library"), self,
            triggered = self.update_library)
        self.musicmenu.addAction(self.action_update_library)
        action_save_playtree_to_folder = QAction(
            self.tr("&Save playtree files to folder in order"), self,
            triggered=self.save_playtree_to_folder)
        self.musicmenu.addAction(action_save_playtree_to_folder)
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
        self.action_milonga_mode = QAction(
            QIcon('icons/iconarchive/icons8/tandamaster-Sports-Dancing-icon.png'),
            self.tr('&Milonga mode'), self)
        self.action_milonga_mode.setCheckable(True)
        self.playbackmenu.addAction(self.action_milonga_mode)
        menubar.addMenu(self.playbackmenu)

        self.editmenu = QMenu(self.tr('&Edit'))
        self.action_cut = QAction(
            #MyIcon('Tango', 'actions', 'edit-cut'),
            QIcon('icons/tango/edit-cut'),
            self.tr('Cu&t'), self, triggered = self.playtree_cut,
            shortcut = QKeySequence(QKeySequence.Cut))
        self.action_copy = QAction(
            QIcon('icons/tango/edit-copy'),
            #MyIcon('Tango', 'actions', 'edit-copy'),
            self.tr('&Copy'), self, triggered = self.playtree_copy,
            shortcut = QKeySequence(QKeySequence.Copy))
        self.action_paste = QAction(
            #MyIcon('Tango', 'actions', 'edit-paste'),
            QIcon('icons/tango/edit-paste'),
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
        self.action_group = QAction(
            QIcon('icons/iconfinder/farm-fresh/group.png'),
            self.tr('&Group'), self, triggered = self.playtree_group,
            shortcut = QKeySequence('Ctrl+g'))
        self.action_group_into_tandas = QAction(
            QIcon('icons/iconfinder/farm-fresh/group.png'),
            self.tr('Group into tandas'), self, triggered = self.playtree_group_into_tandas,
            shortcut = QKeySequence('Ctrl+Shift+g'))
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
        self.action_edit_tag = QAction(
            #QIcon('icons/iconfinder/32pxmania/up.png'),
            self.tr('&Edit tag'), self, triggered = self.edit_tag)
        self.action_save_tag = QAction(
            #QIcon('icons/iconfinder/32pxmania/up.png'),
            self.tr('&Save tag'), self, triggered = self.save_tag)
        self.action_revert_tag = QAction(
            #QIcon('icons/iconfinder/32pxmania/up.png'),
            self.tr('&Revert tag'), self, triggered = self.revert_tag)
        action_undo = undo_stack.createUndoAction(self)
        action_redo = undo_stack.createRedoAction(self)
        action_undo.setIcon(QIcon('icons/iconfinder/32pxmania/undo.png'))
        action_redo.setIcon(QIcon('icons/iconfinder/32pxmania/redo.png'))
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
        self.editmenu.addAction(self.action_move_left)
        self.editmenu.addAction(self.action_move_right)
        self.editmenu.addSeparator()
        self.editmenu.addAction(self.action_edit_tag)
        self.editmenu.addAction(self.action_save_tag)
        self.editmenu.addAction(self.action_revert_tag)
        self.editmenu.addSeparator()
        self.editmenu.addAction(self.action_group_into_tandas)
        menubar.addMenu(self.editmenu)

        self.viewmenu = QMenu(self.tr('View'))
        self.action_columns_minimal = QAction(
            app.tr('Columns: minimal'), 
            self,
            triggered = self.set_columns_minimal)
        self.action_columns_singer_year = QAction(
            app.tr('Columns: singer and year'), 
            self,
            triggered = self.set_columns_singer_year)
        self.viewmenu.addAction(self.action_columns_minimal)
        self.viewmenu.addAction(self.action_columns_singer_year)  
        menubar.addMenu(self.viewmenu)


        self.setMenuBar(menubar)

        toolbar = QToolBar('ProgressBar', self)
        pb = TMProgressBar(self.player)
        toolbar.addWidget(pb)
        self.addToolBar(Qt.BottomToolBarArea, toolbar)

        self.addToolBarBreak(Qt.BottomToolBarArea)

        volume_control = QSlider(Qt.Horizontal)
        volume_control.setMaximumWidth(100)
        volume_control.setMinimum(0)
        volume_control.setMaximum(100)
        volume_control.setValue(self.player.volume())
        volume_control.valueChanged.connect(self.player.set_volume)

        toolbar = QToolBar('Play controls', self)
        toolbar.setAllowedAreas(Qt.TopToolBarArea | Qt.BottomToolBarArea)
        toolbar.setFloatable(False)
        #toolbar.setIconSize(2*toolbar.iconSize())
        toolbar.addWidget(volume_control)
        toolbar.addAction(self.action_back)
        toolbar.addAction(self.action_play)
        toolbar.addAction(self.action_pause)
        toolbar.addAction(self.action_stop)
        toolbar.addAction(self.action_forward)
        toolbar.addSeparator()
        toolbar.addAction(self.action_lock)
        toolbar.addAction(self.action_milonga_mode)
        self.stopafter_spinbox = QSpinBox()
        self.stopafter_spinbox.setMinimum(0)
        self.stopafter_spinbox.valueChanged.connect(self.player.set_stop_after)
        toolbar.addWidget(self.stopafter_spinbox)
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
        toolbar.addAction(self.action_group)
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
        self.player.current_changed.connect(self.update_milonga_end)

        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.save)
        self.autosave_timer.start(config.autosave_interval*60*1000)

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
        thread = QThread(self)
        app.aboutToQuit.connect(thread.exit)
        thread.library = Library(connect = False)
        thread.library.moveToThread(thread)
        thread.started.connect(thread.library.connect)
        thread.started.connect(thread.library.refresh_all_libraries)
        thread.library.refresh_finished.connect(thread.exit)
        thread.library.refresh_finished.connect(lambda: print('Finished updating library'))
        thread.library.refresh_finished.connect(lambda: self.statusBar().showMessage('Finished updating library'))
        thread.library.refresh_finished.connect(self.reset_all)
        thread.finished.connect(lambda: self.action_update_library.setEnabled(True))
        #thread.library.refreshing.connect(self.statusBar().showMessage)
        self.action_update_library.setEnabled(False)
        thread.start()

    def reset_all(self):
        for w in self.window().findChildren(PlayTreeView):
            model = w.model()
            model.beginResetModel()
            model.root_item.populate(model, force = True)
            model.endResetModel()

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

    def playtree_group(self):
        ptv = app.focusWidget()
        if not isinstance(ptv, PlayTreeView): return
        ptv.group()

    def playtree_group_into_tandas(self):
        ptv = app.focusWidget()
        if not isinstance(ptv, PlayTreeView): return
        ptv.group_into_tandas()

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

    def edit_tag(self):
        ptv = app.focusWidget()
        if not isinstance(ptv, PlayTreeView): return
        ptv.edit_tag()
    def save_tag(self):
        ptv = app.focusWidget()
        if not isinstance(ptv, PlayTreeView): return
        ptv.save_tag()
    def revert_tag(self):
        ptv = app.focusWidget()
        if not isinstance(ptv, PlayTreeView): return
        ptv.revert_tag()

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

    def adhoc(self):
        ptv = app.focusWidget()
        if not isinstance(ptv, PlayTreeView): return
        current_index = ptv.currentIndex()
        model = ptv.model()
        current_item = model.item(current_index)
        filename = current_item.filename
        path = os.path.dirname(filename)
        config = [line.strip() for line in open('/home/alja/.audacity-data/audacity.cfg')]
        in_export = False
        for n, line in enumerate(config):
            if line == '[Export]':
                in_export = True
            elif in_export and line.startswith('Path='):
                config[n] = 'Path=' + path
                break
        with open('/home/alja/.audacity-data/audacity.cfg', 'w') as f:
            for line in config:
                print(line, file = f)
        import subprocess
        subprocess.Popen(['/usr/bin/audacity', filename])

    def adhoc(self):
        ptv = app.focusWidget()
        if not isinstance(ptv, PlayTreeView): return
        current_index = ptv.currentIndex()
        model = ptv.model()
        current_item = model.item(current_index)
        print(current_item in current_item.parent.children[ptv.model()])
        print(repr(current_item))
        print(repr(current_item.parent))
        print(current_item.parent.children[ptv.model()])
        print(current_item.parent.children[None])        
        print()
        
    def save_playtree_to_folder(self):
        ptv = app.focusWidget()
        if not isinstance(ptv, PlayTreeView): return
        import shutil
        for item in ptv.model().root_item.iter_depth(
                ptv.model(),
                lambda item: isinstance(item, PlayTreeFile),
                lambda item: isinstance(item, PlayTreeList)):
            p = "-".join("{:03}".format(part) 
                         for part in ptv.model().index_to_path(item.index(ptv.model())))
            new_fn = "/home/alja/temp/milonga_backup/" + p + "-" + os.path.basename(item.filename)
            shutil.copyfile(item.filename, new_fn)

    def closeEvent(self, event):
        self.save()
        super().closeEvent(event)

    def save(self):
        self.ui_xml.getroot().set(
            'geometry', 
            binascii.hexlify(self.saveGeometry().data()).decode())
        cw = self.ui_xml.find('CentralWidget')
        cw.clear()
        cw.append(self.centralWidget().to_xml())
        with open_autobackup('ui.xml', 'w') as outfile:
            self.ui_xml.write(outfile, encoding='unicode')
        save_playtree()

    def save_tags(self):
        librarian.bg_queries(BgQueries([BgQuery(Library.save_changed_tags, ())], lambda qs: self.statusBar().showMessage('Finished saving tags')))
    
    def set_columns_minimal(self):
        ptv = app.focusWidget()
        if not isinstance(ptv, PlayTreeView): return
        ptv.set_columns( ('',) )

    def set_columns_singer_year(self):
        ptv = app.focusWidget()
        if not isinstance(ptv, PlayTreeView): return
        ptv.set_columns( ('', 'ARTIST', 'PERFORMER:VOCALS', 'QUODLIBET::RECORDINGDATE', 'GENRE', '_length') )

    _status_bar_duration = ''
    _status_bar_remaining = ''
    def update_status_bar(self, duration = None, remaining = None):
        if duration is not None:
            self._status_bar_duration = duration
        if remaining is not None:
            self._status_bar_remaining = remaining
        msg = " | ".join([m for m in (self._status_bar_duration, self._status_bar_remaining) if m])
        self.window().statusBar().showMessage(msg)

    def update_milonga_end(self):
        index = self.player.current_index
        model = self.player.current_model
        if index and index.isValid():
            duration_after_current = 0
            mode = PlayTreeItem.duration_mode_cortinas
            ind = index
            while ind.isValid():
                duration_after_current += model.item(ind).duration(model, mode)
                ind = model.next(ind, descend = False)
            self.update_status_bar(remaining = 'Milonga ends at ' + 
                                   (datetime.datetime.now() + datetime.timedelta(seconds = duration_after_current)).strftime('%H:%M'))
        else:
            self.update_status_bar(remaining = '')



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
            QIcon('icons/iconfinder/miniiconsetpart1/add.png'),
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
        icon = model.root_item.data(model, '', Qt.DecorationRole)
        text = model.root_item.data(model, '', Qt.DisplayRole)
        self.setTabIcon(index, icon if icon else QIcon())
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
            
    def on_current_changed(self, old_model, old_index, model, index):
        if old_model == model:
            return
        for i in range(self.count()):
            m = self.widget(i).ptv.model()
            if m == old_model:
                self.tabBar().setTabTextColor(i, QColor())
            elif m == model:
                self.tabBar().setTabTextColor(i, QColor(Qt.darkGreen))

@TMWidget.register_xml_tag_handler('PlayTreeWidget')
class PlayTreeWidget(QWidget, TMWidget):

    @classmethod
    def _create_from_xml(cls, element, window, parent):
        # transitory:
        root_id = element.get('root_id', element.get('id'))
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
            window.player.set_current(model = ptw.ptv.model())
        ptw.ptv.model().rowsInserted.connect(ptw.ptv.update_milonga_end)
        ptw.ptv.model().rowsMoved.connect(ptw.ptv.update_milonga_end)
        ptw.ptv.model().rowsRemoved.connect(ptw.ptv.update_milonga_end)
        return ptw

    def to_xml(self):
        element = super().to_xml()
        element.set('root_id', str(self.ptv.model().root_item.Id))
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

    def refilter(self):
        self.ptv.model().refilter(self.search.text())
        
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
        if not player.current_model:
            player.set_current(model = self.model())
        self.model().modelReset.connect(self.on_end_reset_model)

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.selectionModel().selectionChanged.connect(self.on_currentIndex_changed)

        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setEditTriggers(QAbstractItemView.EditKeyPressed)
        self.setItemDelegate(TMItemDelegate())

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
        if not self.window().action_lock.isChecked() or self.player.current_item.function() == 'cortina':
            self.player.play_index(index)

    def currentChanged(self, current, previous):
        super().currentChanged(current, previous)
        self.update_current_song_from_file(current)
        current_item = self.model().item(current)
        save_revert = isinstance(current_item, PlayTreeLibraryFile) and library.dirty(current_item.library, current_item.song_id, self.model().columns[current.column()])
        self.window().action_save_tag.setEnabled(False) # todo: saving a SINGLE tag
        self.window().action_revert_tag.setEnabled(save_revert)

    def update_current_song_from_file(self, current):
        item = self.model().item(current)
        if isinstance(item, PlayTreeFile):
            librarian.bg_queries(BgQueries([BgQuery(Library.update_song, (item.library if isinstance(item, PlayTreeLibraryFile) else None, item.filename))], lambda qs: item.refresh_models(), relevant = lambda: self.currentIndex() == current))


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
        current_index = self.currentIndex()
        current_path = model.index_to_path(current_index)
        DeletePlayTreeItemsCommand(
            [model.item(index) for index in selection_model.selectedRows()])
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
        if not item_selection: return (False,)*7
        parent_index = item_selection[0].parent()
        parent = model.item(parent_index)
        if not parent.are_children_manually_set: return (False,)*7
        for range in item_selection:
            if range.parent() != parent_index:
                return (False,)*7
        ranges = sorted([(range.top(), range.bottom()) for range in item_selection])
        if len(item_selection) > 1:
            for bottom, top in zip([range[1] for range in ranges[1:]],
                                   [range[0] for range in ranges[:-1]]):
                if bottom != top + 1: 
                    return (False,)*7
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
        can_move_right = model.rowCount(parent_index) > ranges[-1][1]+1 and model.item(model.index(ranges[-1][1]+1, 0, parent_index)).are_children_manually_set
        can_move_home = top != 0 or (parent_index.isValid() and model.root_item.are_children_manually_set)
        can_move_end = bottom != model.rowCount(parent_index)-1 or (parent_index.isValid() and model.root_item.are_children_manually_set)
        return can_group, can_move_up, can_move_down, can_move_left, can_move_right, can_move_home, can_move_end

    def on_selection_changed(self):
        can_cut = self.can_cut()
        self.window().action_cut.setEnabled(can_cut)
        self.window().action_delete.setEnabled(can_cut)
        self.window().action_copy.setEnabled(self.can_copy())
        can_group, can_move_up, can_move_down, can_move_left, can_move_right, can_move_home, can_move_end = self.can_move()
        self.window().action_group.setEnabled(can_group)
        self.window().action_move_up.setEnabled(can_move_up)
        self.window().action_move_down.setEnabled(can_move_down)
        self.window().action_move_left.setEnabled(can_move_left)
        self.window().action_move_right.setEnabled(can_move_right)
        self.window().action_move_home.setEnabled(can_move_home)
        self.window().action_move_end.setEnabled(can_move_end)
        model = self.model()
        mode = PlayTreeItem.duration_mode_cortinas
        selected_indexes = self.selectionModel().selectedRows()
        duration_playtree = model.root_item.duration(model, mode)
        if selected_indexes:
            duration = sum(model.item(index).duration(model, mode) for index in selected_indexes)
            if can_group:
                parent_item = model.item(selected_indexes[0].parent())
                duration_before = sum(parent_item.child(model, r).duration(model, mode)
                                      for r in range(0, min(index.row() for index in selected_indexes)))
                duration_after = sum(parent_item.child(model, r).duration(model, mode)
                                      for r in range(
                                              1+max(index.row() for index in selected_indexes),
                                              parent_item.rowCount(model)))
                msg = 'Duration before {}, selection {}, after {}, playtree {}'.format(
                    hmsms_to_text(*ms_to_hmsms(1000*duration_before),include_ms=False),
                    hmsms_to_text(*ms_to_hmsms(1000*duration),include_ms=False),
                    hmsms_to_text(*ms_to_hmsms(1000*duration_after),include_ms=False),
                    hmsms_to_text(*ms_to_hmsms(1000*duration_playtree),include_ms=False))
            else:
                msg = 'Duration of the selection: {}'.format(
                    hmsms_to_text(*ms_to_hmsms(1000*duration),include_ms=False),
                    hmsms_to_text(*ms_to_hmsms(1000*duration_playtree),include_ms=False))
        else:
            msg = 'Duration of the playtree: {}'.format(
                hmsms_to_text(*ms_to_hmsms(1000*duration_playtree),include_ms=False))
        if mode == PlayTreeItem.duration_mode_cortinas:
            msg += ' (cortina={}s)'.format(PlayTreeFile.cortina_duration)
        self.window().update_status_bar(duration = msg)

    def on_currentIndex_changed(self):
        self.window().action_paste.setEnabled(self.can_paste())
        self.window().action_insert.setEnabled(self.can_insert())

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
        self.setStyleSheet("")
        self.on_selection_changed()
        self.on_currentIndex_changed()
        self.update_current_song_from_file(self.currentIndex())
        return r

    def focusOutEvent(self, event):
        r = super().focusInEvent(event)
        self.setStyleSheet("""QTreeView::item:selected { background-color: lightgray; }""")
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

    def group(self):
        model = self.model()
        selection_model = self.selectionModel()
        selected_indexes = selection_model.selectedRows()
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
        selected_indexes = selection_model.selectedRows()
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
        self.model().beginResetModel()
        self.model().columns = columns
        self.model().endResetModel()

    def update_milonga_end(self, parent_index, first, last, dest = QModelIndex(), dest_first = None, dest_last = None):
        if self.player.current_model == self.model():
            self.window().update_milonga_end()

    def edit_tag(self):
        self.edit(self.currentIndex())
    def save_tag(self):
        pass
    def revert_tag(self):
        current_index = self.currentIndex()
        item = self.model().item(current_index)
        tag = self.model().columns[current_index.column()]
        dirty, old_value = library.dirty(item.library, item.song_id, tag, get_old_value = True)
        EditTagsCommand(self.model(), [item], tag, old_value, command_prefix = 'Revert')

class TMItemDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        tag = index.model().columns[index.column()]
        if tag:
            completer = QCompleter()
            completer.setCompletionMode(QCompleter.PopupCompletion)
            completer.setCaseSensitivity(False)
            completer.setModel(QStringListModel(
                [v for v,n in library.query_tags_iter('tango', tag, [], '')]))
            editor.setCompleter(completer)
        return editor


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
