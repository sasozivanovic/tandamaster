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

from PyQt5.Qt import QIcon
import functools
@functools.lru_cache()
def MyIcon(repository, category, name):
    return QIcon('/usr/share/icons/{}/scalable/{}/{}'.format(repository, category, name))

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
    ts = datetime.datetime.now().isoformat(sep)
    return ts[0:ts.index('.')]
        

def first(lst, default = None):
    return lst[0] if lst else default


from contextlib import contextmanager
import filecmp, os.path

@contextmanager
def open_autobackup(filename, *args, prepare = lambda: os.mkdir('bak'), tmp = lambda fn: fn + '.tmp', bak = lambda fn: os.path.join('bak', fn + '.' + tm_timestamp('_') + '.bak'), **kwargs):
    try:
        prepare()
    except:
        pass
    file = open(tmp(filename), *args, **kwargs)
    yield file
    try:
        same = filecmp.cmp(filename, tmp(filename))
    except:
        same = False
    if same:
        os.remove(tmp(filename))
    else:
        try:
            os.rename(filename, bak(filename))
        except OSError:
            pass
        os.rename(tmp(filename), filename)

import unidecode
def search_value(value):
    return unidecode.unidecode(value).lower() if isinstance(value, str) else value
