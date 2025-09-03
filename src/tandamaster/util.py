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

# from http://stackoverflow.com/questions/20248355/how-to-get-python-to-gracefully-format-none-and-non-existing-fields
import string
class PartialFormatter(string.Formatter):
    def __init__(self, missing='?', bad_fmt='!!'):
        self.missing, self.bad_fmt=missing, bad_fmt

    def get_field(self, field_name, args, kwargs):
        # Handle a key not found
        try:
            val=super(PartialFormatter, self).get_field(field_name, args, kwargs)
            # Python 3, 'super().get_field(field_name, args, kwargs)' works
        except (KeyError, AttributeError):
            val=None,field_name 
        return val 

    def format_field(self, value, spec):
        # handle an invalid format
        if value==None: return self.missing
        try:
            return super(PartialFormatter, self).format_field(value, spec)
        except ValueError:
            if self.bad_fmt is not None: return self.bad_fmt   
            else: raise

class SongInfoFormatter(PartialFormatter):
    def __init__(self, item, missing='?', bad_fmt='!!'):
        super().__init__(missing = missing, bad_fmt = bad_fmt)
        self.tags = item.get_tags(only_first = True)
        if not 'title' in self.tags:
            try:
                self.tags['title'] = self.tags['_filename']
            except KeyError:
                pass
    def format(self, format_string, *args, **kwargs):
        # we use python 3.5 under windows, so this doesn't work
        # return super().format(format_string, *args, **self.tags, **kwargs)
        tags = self.tags.copy()
        tags.update(kwargs)
        return super().format(format_string, *args, **tags)
            
from pathlib import Path
icon_prefix = Path(__file__).parent / 'icons'
# but see https://stackoverflow.com/a/58941536/624872
# I used a bad way because I don't know how the recommended way would play with QIcon.
from PyQt5.Qt import QIcon
def MyIcon(filename):
    return QIcon(str(icon_prefix / filename))

def common_prefix_length(list1, list2):
    i = 0
    while i<l1 and i<l2 and list1[i] == list2[i]:
        i+=1
    return i
    
def common_suffix_length(list1, list2):
    i = 0
    l1,l2 = len(list2), len(list2)
    while i<l1 and i<l2 and list1[l1-i-1] == list2[l2-i-1]:
        i+=1
    return i

def ms_to_hmsms(t):
    t, ms = divmod(t, 1000)
    t, s = divmod(t, 60)
    h, m = divmod(t, 60)
    return h, m, s, ms

def hmsms_to_text(h,m,s,ms,include_ms=True):
    h,m,s,ms = int(h),int(m),int(s),int(ms)
    return (str(h) + ":" if h else '') + \
        ('{:02d}:{:02d}' if h else '{}:{:02d}').format(m, s) + \
        ('.' + str(ms) if include_ms else '')


time_unit_factors = { 's': 1000, 'ms': 1, 'ns': 0.000001 }
def time_to_text(t, include_ms = False, unit = 's', fail_text = '?'):
    if t is None:
        return fail_text
    return hmsms_to_text(*ms_to_hmsms(t*time_unit_factors[unit]), include_ms = include_ms)

import datetime
def tm_timestamp(sep = ' '):
    # ts = datetime.datetime.now().isoformat(sep) # : is invalid filename char on WindowsError
    # return ts[0:ts.index('.')]
    return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def first(lst, default = None):
    return lst[0] if lst else default


from contextlib import contextmanager
import filecmp, os.path
import shutil
import tempfile, zipfile

@contextmanager
def open_autobackup(
        filename, *args,
        bak_dir_f = lambda fn: os.path.join(os.path.dirname(fn), 'bak'),
        bak_basename_f = lambda fn: os.path.basename(fn) + '.' + tm_timestamp('_') + '.zip',
        **kwargs):
    filename = os.path.normpath(filename)
    tmp = tempfile.NamedTemporaryFile(prefix = os.path.basename(filename), delete = False)
    tmp.close()
    try:
        shutil.copy(filename, tmp.name)
    except FileNotFoundError:
        pass

    file = open(filename, *args, **kwargs)
    yield file
    file.close()
    
    try:
        if not filecmp.cmp(filename, tmp.name, shallow = False):
            bak_dir = bak_dir_f(filename)
            try:
                os.mkdir(bak_dir)
            except FileExistsError:
                pass
            bak_basename = bak_basename_f(filename)
            with zipfile.ZipFile(os.path.join(bak_dir, bak_basename),
                                 'w', compression = zipfile.ZIP_DEFLATED) as bak_zip:
                bak_zip.write(tmp.name, arcname = os.path.basename(filename))
        os.remove(tmp.name)
    except FileNotFoundError:
        pass
        

import unidecode
def search_value(value):
    return unidecode.unidecode(value).lower() if isinstance(value, str) else value

# for gstreamer rgain
def normalize_tag_name(tag):
    return tag.lower().replace('-','_')

from PyQt5.Qt import QStandardPaths
def locate_file(location_type, basename):
    filename = QStandardPaths.locate(location_type, basename)
    if not filename:
        print(os.path.join('initial_config', basename),
            QStandardPaths.writableLocation(location_type))
        dirname = QStandardPaths.writableLocation(location_type)
        try:
            os.makedirs(dirname)
        except FileExistsError:
            pass
        shutil.copy(
            os.path.join('initial_config', basename),
            QStandardPaths.writableLocation(location_type))
        filename = QStandardPaths.locate(location_type, basename)
    assert filename
    return filename

