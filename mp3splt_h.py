'''Wrapper for splt.h

Generated with:
/usr/bin/ctypesgen.py -lmp3splt -Ilibmp3splt-0.9.2/include/libmp3splt libmp3splt-0.9.2/src/splt.h

Do not modify this file.
'''

__docformat__ =  'restructuredtext'

# Begin preamble

import ctypes, os, sys
from ctypes import *

_int_types = (c_int16, c_int32)
if hasattr(ctypes, 'c_int64'):
    # Some builds of ctypes apparently do not have c_int64
    # defined; it's a pretty good bet that these builds do not
    # have 64-bit pointers.
    _int_types += (c_int64,)
for t in _int_types:
    if sizeof(t) == sizeof(c_size_t):
        c_ptrdiff_t = t
del t
del _int_types

class c_void(Structure):
    # c_void_p is a buggy return type, converting to int, so
    # POINTER(None) == c_void_p is actually written as
    # POINTER(c_void), so it can be treated as a real pointer.
    _fields_ = [('dummy', c_int)]

def POINTER(obj):
    p = ctypes.POINTER(obj)

    # Convert None to a real NULL pointer to work around bugs
    # in how ctypes handles None on 64-bit platforms
    if not isinstance(p.from_param, classmethod):
        def from_param(cls, x):
            if x is None:
                return cls()
            else:
                return x
        p.from_param = classmethod(from_param)

    return p

class UserString:
    def __init__(self, seq):
        if isinstance(seq, str):
            self.data = seq
        elif isinstance(seq, UserString):
            self.data = seq.data[:]
        else:
            self.data = str(seq)
    def __str__(self): return str(self.data)
    def __repr__(self): return repr(self.data)
    def __int__(self): return int(self.data)
    def __long__(self): return int(self.data)
    def __float__(self): return float(self.data)
    def __complex__(self): return complex(self.data)
    def __hash__(self): return hash(self.data)

    def __cmp__(self, string):
        if isinstance(string, UserString):
            return cmp(self.data, string.data)
        else:
            return cmp(self.data, string)
    def __contains__(self, char):
        return char in self.data

    def __len__(self): return len(self.data)
    def __getitem__(self, index): return self.__class__(self.data[index])
    def __getslice__(self, start, end):
        start = max(start, 0); end = max(end, 0)
        return self.__class__(self.data[start:end])

    def __add__(self, other):
        if isinstance(other, UserString):
            return self.__class__(self.data + other.data)
        elif isinstance(other, str):
            return self.__class__(self.data + other)
        else:
            return self.__class__(self.data + str(other))
    def __radd__(self, other):
        if isinstance(other, str):
            return self.__class__(other + self.data)
        else:
            return self.__class__(str(other) + self.data)
    def __mul__(self, n):
        return self.__class__(self.data*n)
    __rmul__ = __mul__
    def __mod__(self, args):
        return self.__class__(self.data % args)

    # the following methods are defined in alphabetical order:
    def capitalize(self): return self.__class__(self.data.capitalize())
    def center(self, width, *args):
        return self.__class__(self.data.center(width, *args))
    def count(self, sub, start=0, end=sys.maxsize):
        return self.data.count(sub, start, end)
    def decode(self, encoding=None, errors=None): # XXX improve this?
        if encoding:
            if errors:
                return self.__class__(self.data.decode(encoding, errors))
            else:
                return self.__class__(self.data.decode(encoding))
        else:
            return self.__class__(self.data.decode())
    def encode(self, encoding=None, errors=None): # XXX improve this?
        if encoding:
            if errors:
                return self.__class__(self.data.encode(encoding, errors))
            else:
                return self.__class__(self.data.encode(encoding))
        else:
            return self.__class__(self.data.encode())
    def endswith(self, suffix, start=0, end=sys.maxsize):
        return self.data.endswith(suffix, start, end)
    def expandtabs(self, tabsize=8):
        return self.__class__(self.data.expandtabs(tabsize))
    def find(self, sub, start=0, end=sys.maxsize):
        return self.data.find(sub, start, end)
    def index(self, sub, start=0, end=sys.maxsize):
        return self.data.index(sub, start, end)
    def isalpha(self): return self.data.isalpha()
    def isalnum(self): return self.data.isalnum()
    def isdecimal(self): return self.data.isdecimal()
    def isdigit(self): return self.data.isdigit()
    def islower(self): return self.data.islower()
    def isnumeric(self): return self.data.isnumeric()
    def isspace(self): return self.data.isspace()
    def istitle(self): return self.data.istitle()
    def isupper(self): return self.data.isupper()
    def join(self, seq): return self.data.join(seq)
    def ljust(self, width, *args):
        return self.__class__(self.data.ljust(width, *args))
    def lower(self): return self.__class__(self.data.lower())
    def lstrip(self, chars=None): return self.__class__(self.data.lstrip(chars))
    def partition(self, sep):
        return self.data.partition(sep)
    def replace(self, old, new, maxsplit=-1):
        return self.__class__(self.data.replace(old, new, maxsplit))
    def rfind(self, sub, start=0, end=sys.maxsize):
        return self.data.rfind(sub, start, end)
    def rindex(self, sub, start=0, end=sys.maxsize):
        return self.data.rindex(sub, start, end)
    def rjust(self, width, *args):
        return self.__class__(self.data.rjust(width, *args))
    def rpartition(self, sep):
        return self.data.rpartition(sep)
    def rstrip(self, chars=None): return self.__class__(self.data.rstrip(chars))
    def split(self, sep=None, maxsplit=-1):
        return self.data.split(sep, maxsplit)
    def rsplit(self, sep=None, maxsplit=-1):
        return self.data.rsplit(sep, maxsplit)
    def splitlines(self, keepends=0): return self.data.splitlines(keepends)
    def startswith(self, prefix, start=0, end=sys.maxsize):
        return self.data.startswith(prefix, start, end)
    def strip(self, chars=None): return self.__class__(self.data.strip(chars))
    def swapcase(self): return self.__class__(self.data.swapcase())
    def title(self): return self.__class__(self.data.title())
    def translate(self, *args):
        return self.__class__(self.data.translate(*args))
    def upper(self): return self.__class__(self.data.upper())
    def zfill(self, width): return self.__class__(self.data.zfill(width))

class MutableString(UserString):
    """mutable string objects

    Python strings are immutable objects.  This has the advantage, that
    strings may be used as dictionary keys.  If this property isn't needed
    and you insist on changing string values in place instead, you may cheat
    and use MutableString.

    But the purpose of this class is an educational one: to prevent
    people from inventing their own mutable string class derived
    from UserString and than forget thereby to remove (override) the
    __hash__ method inherited from UserString.  This would lead to
    errors that would be very hard to track down.

    A faster and better solution is to rewrite your program using lists."""
    def __init__(self, string=""):
        self.data = string
    def __hash__(self):
        raise TypeError("unhashable type (it is mutable)")
    def __setitem__(self, index, sub):
        if index < 0:
            index += len(self.data)
        if index < 0 or index >= len(self.data): raise IndexError
        self.data = self.data[:index] + sub + self.data[index+1:]
    def __delitem__(self, index):
        if index < 0:
            index += len(self.data)
        if index < 0 or index >= len(self.data): raise IndexError
        self.data = self.data[:index] + self.data[index+1:]
    def __setslice__(self, start, end, sub):
        start = max(start, 0); end = max(end, 0)
        if isinstance(sub, UserString):
            self.data = self.data[:start]+sub.data+self.data[end:]
        elif isinstance(sub, str):
            self.data = self.data[:start]+sub+self.data[end:]
        else:
            self.data =  self.data[:start]+str(sub)+self.data[end:]
    def __delslice__(self, start, end):
        start = max(start, 0); end = max(end, 0)
        self.data = self.data[:start] + self.data[end:]
    def immutable(self):
        return UserString(self.data)
    def __iadd__(self, other):
        if isinstance(other, UserString):
            self.data += other.data
        elif isinstance(other, str):
            self.data += other
        else:
            self.data += str(other)
        return self
    def __imul__(self, n):
        self.data *= n
        return self

class String(MutableString, Union):

    _fields_ = [('raw', POINTER(c_char)),
                ('data', c_char_p)]

    def __init__(self, obj=""):
        if isinstance(obj, (str, UserString)):
            self.data = str(obj)
        else:
            self.raw = obj

    def __len__(self):
        return self.data and len(self.data) or 0

    def from_param(cls, obj):
        # Convert None or 0
        if obj is None or obj == 0:
            return cls(POINTER(c_char)())

        # Convert from String
        elif isinstance(obj, String):
            return obj

        # Convert from str
        elif isinstance(obj, str):
            return cls(obj)

        # Convert from c_char_p
        elif isinstance(obj, c_char_p):
            return obj

        # Convert from POINTER(c_char)
        elif isinstance(obj, POINTER(c_char)):
            return obj

        # Convert from raw pointer
        elif isinstance(obj, int):
            return cls(cast(obj, POINTER(c_char)))

        # Convert from object
        else:
            return String.from_param(obj._as_parameter_)
    from_param = classmethod(from_param)

def ReturnString(obj, func=None, arguments=None):
    return String.from_param(obj)

# As of ctypes 1.0, ctypes does not support custom error-checking
# functions on callbacks, nor does it support custom datatypes on
# callbacks, so we must ensure that all callbacks return
# primitive datatypes.
#
# Non-primitive return values wrapped with UNCHECKED won't be
# typechecked, and will be converted to c_void_p.
def UNCHECKED(type):
    if (hasattr(type, "_type_") and isinstance(type._type_, str)
        and type._type_ != "P"):
        return type
    else:
        return c_void_p

# ctypes doesn't have direct support for variadic functions, so we have to write
# our own wrapper class
class _variadic_function(object):
    def __init__(self,func,restype,argtypes):
        self.func=func
        self.func.restype=restype
        self.argtypes=argtypes
    def _as_parameter_(self):
        # So we can pass this variadic function as a function pointer
        return self.func
    def __call__(self,*args):
        fixed_args=[]
        i=0
        for argtype in self.argtypes:
            # Typecheck what we can
            fixed_args.append(argtype.from_param(args[i]))
            i+=1
        return self.func(*fixed_args+list(args[i:]))

# End preamble

_libs = {}
_libdirs = []

# Begin loader

# ----------------------------------------------------------------------------
# Copyright (c) 2008 David James
# Copyright (c) 2006-2008 Alex Holkner
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

import os.path, re, sys, glob
import platform
import ctypes
import ctypes.util

def _environ_path(name):
    if name in os.environ:
        return os.environ[name].split(":")
    else:
        return []

class LibraryLoader(object):
    def __init__(self):
        self.other_dirs=[]

    def load_library(self,libname):
        """Given the name of a library, load it."""
        paths = self.getpaths(libname)

        for path in paths:
            if os.path.exists(path):
                return self.load(path)

        raise ImportError("%s not found." % libname)

    def load(self,path):
        """Given a path to a library, load it."""
        try:
            # Darwin requires dlopen to be called with mode RTLD_GLOBAL instead
            # of the default RTLD_LOCAL.  Without this, you end up with
            # libraries not being loadable, resulting in "Symbol not found"
            # errors
            if sys.platform == 'darwin':
                return ctypes.CDLL(path, ctypes.RTLD_GLOBAL)
            else:
                return ctypes.cdll.LoadLibrary(path)
        except OSError as e:
            raise ImportError(e)

    def getpaths(self,libname):
        """Return a list of paths where the library might be found."""
        if os.path.isabs(libname):
            yield libname
        else:
            # FIXME / TODO return '.' and os.path.dirname(__file__)
            for path in self.getplatformpaths(libname):
                yield path

            path = ctypes.util.find_library(libname)
            if path: yield path

    def getplatformpaths(self, libname):
        return []

# Darwin (Mac OS X)

class DarwinLibraryLoader(LibraryLoader):
    name_formats = ["lib%s.dylib", "lib%s.so", "lib%s.bundle", "%s.dylib",
                "%s.so", "%s.bundle", "%s"]

    def getplatformpaths(self,libname):
        if os.path.pathsep in libname:
            names = [libname]
        else:
            names = [format % libname for format in self.name_formats]

        for dir in self.getdirs(libname):
            for name in names:
                yield os.path.join(dir,name)

    def getdirs(self,libname):
        '''Implements the dylib search as specified in Apple documentation:

        http://developer.apple.com/documentation/DeveloperTools/Conceptual/
            DynamicLibraries/Articles/DynamicLibraryUsageGuidelines.html

        Before commencing the standard search, the method first checks
        the bundle's ``Frameworks`` directory if the application is running
        within a bundle (OS X .app).
        '''

        dyld_fallback_library_path = _environ_path("DYLD_FALLBACK_LIBRARY_PATH")
        if not dyld_fallback_library_path:
            dyld_fallback_library_path = [os.path.expanduser('~/lib'),
                                          '/usr/local/lib', '/usr/lib']

        dirs = []

        if '/' in libname:
            dirs.extend(_environ_path("DYLD_LIBRARY_PATH"))
        else:
            dirs.extend(_environ_path("LD_LIBRARY_PATH"))
            dirs.extend(_environ_path("DYLD_LIBRARY_PATH"))

        dirs.extend(self.other_dirs)
        dirs.append(".")
        dirs.append(os.path.dirname(__file__))

        if hasattr(sys, 'frozen') and sys.frozen == 'macosx_app':
            dirs.append(os.path.join(
                os.environ['RESOURCEPATH'],
                '..',
                'Frameworks'))

        dirs.extend(dyld_fallback_library_path)

        return dirs

# Posix

class PosixLibraryLoader(LibraryLoader):
    _ld_so_cache = None

    def _create_ld_so_cache(self):
        # Recreate search path followed by ld.so.  This is going to be
        # slow to build, and incorrect (ld.so uses ld.so.cache, which may
        # not be up-to-date).  Used only as fallback for distros without
        # /sbin/ldconfig.
        #
        # We assume the DT_RPATH and DT_RUNPATH binary sections are omitted.

        directories = []
        for name in ("LD_LIBRARY_PATH",
                     "SHLIB_PATH", # HPUX
                     "LIBPATH", # OS/2, AIX
                     "LIBRARY_PATH", # BE/OS
                    ):
            if name in os.environ:
                directories.extend(os.environ[name].split(os.pathsep))
        directories.extend(self.other_dirs)
        directories.append(".")
        directories.append(os.path.dirname(__file__))

        try: directories.extend([dir.strip() for dir in open('/etc/ld.so.conf')])
        except IOError: pass

        unix_lib_dirs_list = ['/lib', '/usr/lib', '/lib64', '/usr/lib64']
        if sys.platform.startswith('linux'):
            # Try and support multiarch work in Ubuntu
            # https://wiki.ubuntu.com/MultiarchSpec
            bitage = platform.architecture()[0]
            if bitage.startswith('32'):
                # Assume Intel/AMD x86 compat
                unix_lib_dirs_list += ['/lib/i386-linux-gnu', '/usr/lib/i386-linux-gnu']
            elif bitage.startswith('64'):
                # Assume Intel/AMD x86 compat
                unix_lib_dirs_list += ['/lib/x86_64-linux-gnu', '/usr/lib/x86_64-linux-gnu']
            else:
                # guess...
                unix_lib_dirs_list += glob.glob('/lib/*linux-gnu')
        directories.extend(unix_lib_dirs_list)

        cache = {}
        lib_re = re.compile(r'lib(.*)\.s[ol]')
        ext_re = re.compile(r'\.s[ol]$')
        for dir in directories:
            try:
                for path in glob.glob("%s/*.s[ol]*" % dir):
                    file = os.path.basename(path)

                    # Index by filename
                    if file not in cache:
                        cache[file] = path

                    # Index by library name
                    match = lib_re.match(file)
                    if match:
                        library = match.group(1)
                        if library not in cache:
                            cache[library] = path
            except OSError:
                pass

        self._ld_so_cache = cache

    def getplatformpaths(self, libname):
        if self._ld_so_cache is None:
            self._create_ld_so_cache()

        result = self._ld_so_cache.get(libname)
        if result: yield result

        path = ctypes.util.find_library(libname)
        if path: yield os.path.join("/lib",path)

# Windows

class _WindowsLibrary(object):
    def __init__(self, path):
        self.cdll = ctypes.cdll.LoadLibrary(path)
        self.windll = ctypes.windll.LoadLibrary(path)

    def __getattr__(self, name):
        try: return getattr(self.cdll,name)
        except AttributeError:
            try: return getattr(self.windll,name)
            except AttributeError:
                raise

class WindowsLibraryLoader(LibraryLoader):
    name_formats = ["%s.dll", "lib%s.dll", "%slib.dll"]

    def load_library(self, libname):
        try:
            result = LibraryLoader.load_library(self, libname)
        except ImportError:
            result = None
            if os.path.sep not in libname:
                for name in self.name_formats:
                    try:
                        result = getattr(ctypes.cdll, name % libname)
                        if result:
                            break
                    except WindowsError:
                        result = None
            if result is None:
                try:
                    result = getattr(ctypes.cdll, libname)
                except WindowsError:
                    result = None
            if result is None:
                raise ImportError("%s not found." % libname)
        return result

    def load(self, path):
        return _WindowsLibrary(path)

    def getplatformpaths(self, libname):
        if os.path.sep not in libname:
            for name in self.name_formats:
                dll_in_current_dir = os.path.abspath(name % libname)
                if os.path.exists(dll_in_current_dir):
                    yield dll_in_current_dir
                path = ctypes.util.find_library(name % libname)
                if path:
                    yield path

# Platform switching

# If your value of sys.platform does not appear in this dict, please contact
# the Ctypesgen maintainers.

loaderclass = {
    "darwin":   DarwinLibraryLoader,
    "cygwin":   WindowsLibraryLoader,
    "win32":    WindowsLibraryLoader
}

loader = loaderclass.get(sys.platform, PosixLibraryLoader)()

def add_library_search_dirs(other_dirs):
    loader.other_dirs = other_dirs

load_library = loader.load_library

del loaderclass

# End loader

add_library_search_dirs([])

# Begin libraries

_libs["mp3splt"] = load_library("mp3splt")

# 1 libraries
# End libraries

# No modules

__off_t = c_long # /usr/include/bits/types.h: 131

__off64_t = c_long # /usr/include/bits/types.h: 132

# /usr/include/libio.h: 241
class struct__IO_FILE(Structure):
    pass

FILE = struct__IO_FILE # /usr/include/stdio.h: 48

_IO_lock_t = None # /usr/include/libio.h: 150

# /usr/include/libio.h: 156
class struct__IO_marker(Structure):
    pass

struct__IO_marker.__slots__ = [
    '_next',
    '_sbuf',
    '_pos',
]
struct__IO_marker._fields_ = [
    ('_next', POINTER(struct__IO_marker)),
    ('_sbuf', POINTER(struct__IO_FILE)),
    ('_pos', c_int),
]

struct__IO_FILE.__slots__ = [
    '_flags',
    '_IO_read_ptr',
    '_IO_read_end',
    '_IO_read_base',
    '_IO_write_base',
    '_IO_write_ptr',
    '_IO_write_end',
    '_IO_buf_base',
    '_IO_buf_end',
    '_IO_save_base',
    '_IO_backup_base',
    '_IO_save_end',
    '_markers',
    '_chain',
    '_fileno',
    '_flags2',
    '_old_offset',
    '_cur_column',
    '_vtable_offset',
    '_shortbuf',
    '_lock',
    '_offset',
    '__pad1',
    '__pad2',
    '__pad3',
    '__pad4',
    '__pad5',
    '_mode',
    '_unused2',
]
struct__IO_FILE._fields_ = [
    ('_flags', c_int),
    ('_IO_read_ptr', String),
    ('_IO_read_end', String),
    ('_IO_read_base', String),
    ('_IO_write_base', String),
    ('_IO_write_ptr', String),
    ('_IO_write_end', String),
    ('_IO_buf_base', String),
    ('_IO_buf_end', String),
    ('_IO_save_base', String),
    ('_IO_backup_base', String),
    ('_IO_save_end', String),
    ('_markers', POINTER(struct__IO_marker)),
    ('_chain', POINTER(struct__IO_FILE)),
    ('_fileno', c_int),
    ('_flags2', c_int),
    ('_old_offset', __off_t),
    ('_cur_column', c_ushort),
    ('_vtable_offset', c_char),
    ('_shortbuf', c_char * 1),
    ('_lock', POINTER(_IO_lock_t)),
    ('_offset', __off64_t),
    ('__pad1', POINTER(None)),
    ('__pad2', POINTER(None)),
    ('__pad3', POINTER(None)),
    ('__pad4', POINTER(None)),
    ('__pad5', c_size_t),
    ('_mode', c_int),
    ('_unused2', c_char * (((15 * sizeof(c_int)) - (4 * sizeof(POINTER(None)))) - sizeof(c_size_t))),
]

off_t = __off_t # /usr/include/stdio.h: 90

# /usr/include/stdio.h: 749
if hasattr(_libs['mp3splt'], 'fseek'):
    fseek = _libs['mp3splt'].fseek
    fseek.argtypes = [POINTER(FILE), c_long, c_int]
    fseek.restype = c_int

# /usr/include/stdio.h: 754
if hasattr(_libs['mp3splt'], 'ftell'):
    ftell = _libs['mp3splt'].ftell
    ftell.argtypes = [POINTER(FILE)]
    ftell.restype = c_long

enum_anon_29 = c_int # libmp3splt-0.9.2/include/libmp3splt/mp3splt.h: 215

splt_code = enum_anon_29 # libmp3splt-0.9.2/include/libmp3splt/mp3splt.h: 215

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 559
class struct__splt_state(Structure):
    pass

splt_state = struct__splt_state # libmp3splt-0.9.2/include/libmp3splt/mp3splt.h: 231

enum_anon_31 = c_int # libmp3splt-0.9.2/include/libmp3splt/mp3splt.h: 758

splt_split_mode_options = enum_anon_31 # libmp3splt-0.9.2/include/libmp3splt/mp3splt.h: 758

enum_anon_33 = c_int # libmp3splt-0.9.2/include/libmp3splt/mp3splt.h: 799

splt_output_filenames_options = enum_anon_33 # libmp3splt-0.9.2/include/libmp3splt/mp3splt.h: 799

enum_anon_34 = c_int # libmp3splt-0.9.2/include/libmp3splt/mp3splt.h: 862

splt_tags_options = enum_anon_34 # libmp3splt-0.9.2/include/libmp3splt/mp3splt.h: 862

enum_anon_36 = c_int # libmp3splt-0.9.2/include/libmp3splt/mp3splt.h: 1128

splt_message_type = enum_anon_36 # libmp3splt-0.9.2/include/libmp3splt/mp3splt.h: 1128

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 237
class struct_splt_progres(Structure):
    pass

splt_progress = struct_splt_progres # libmp3splt-0.9.2/include/libmp3splt/mp3splt.h: 1229

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 212
class struct__splt_point(Structure):
    pass

splt_point = struct__splt_point # libmp3splt-0.9.2/include/libmp3splt/mp3splt.h: 1333

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 228
class struct__splt_points(Structure):
    pass

splt_points = struct__splt_points # libmp3splt-0.9.2/include/libmp3splt/mp3splt.h: 1386

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 139
class struct__splt_tags(Structure):
    pass

splt_tags = struct__splt_tags # libmp3splt-0.9.2/include/libmp3splt/mp3splt.h: 1512

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 192
class struct__splt_tags_group(Structure):
    pass

splt_tags_group = struct__splt_tags_group # libmp3splt-0.9.2/include/libmp3splt/mp3splt.h: 1564

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 69
class struct__splt_freedb_results(Structure):
    pass

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 44
class struct__splt_freedb_one_result(Structure):
    pass

splt_freedb_one_result = struct__splt_freedb_one_result # libmp3splt-0.9.2/include/libmp3splt/mp3splt.h: 1851

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 112
class struct__splt_wrap(Structure):
    pass

splt_wrap = struct__splt_wrap # libmp3splt-0.9.2/include/libmp3splt/mp3splt.h: 2020

# libmp3splt-0.9.2/include/libmp3splt/mp3splt.h: 2152
class struct_anon_42(Structure):
    pass

struct_anon_42.__slots__ = [
    'version',
    'name',
    'extension',
    'upper_extension',
]
struct_anon_42._fields_ = [
    ('version', c_float),
    ('name', String),
    ('extension', String),
    ('upper_extension', String),
]

splt_plugin_info = struct_anon_42 # libmp3splt-0.9.2/include/libmp3splt/mp3splt.h: 2152

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 186
class struct__splt_original_tags(Structure):
    pass

splt_original_tags = struct__splt_original_tags # libmp3splt-0.9.2/include/libmp3splt/mp3splt.h: 2157

# libmp3splt-0.9.2/include/libmp3splt/mp3splt.h: 2313
class struct_anon_43(Structure):
    pass

struct_anon_43.__slots__ = [
    'splt_pl_init',
    'splt_pl_end',
    'splt_pl_check_plugin_is_for_file',
    'splt_pl_set_plugin_info',
    'splt_pl_split',
    'splt_pl_set_original_tags',
    'splt_pl_clear_original_tags',
    'splt_pl_scan_silence',
    'splt_pl_scan_trim_silence',
    'splt_pl_search_syncerrors',
    'splt_pl_offset_split',
    'splt_pl_dewrap',
    'splt_pl_import_internal_sheets',
]
struct_anon_43._fields_ = [
    ('splt_pl_init', CFUNCTYPE(UNCHECKED(None), POINTER(splt_state), POINTER(splt_code))),
    ('splt_pl_end', CFUNCTYPE(UNCHECKED(None), POINTER(splt_state), POINTER(splt_code))),
    ('splt_pl_check_plugin_is_for_file', CFUNCTYPE(UNCHECKED(c_int), POINTER(splt_state), POINTER(splt_code))),
    ('splt_pl_set_plugin_info', CFUNCTYPE(UNCHECKED(None), POINTER(splt_plugin_info), POINTER(splt_code))),
    ('splt_pl_split', CFUNCTYPE(UNCHECKED(c_double), POINTER(splt_state), String, c_double, c_double, POINTER(splt_code), c_int)),
    ('splt_pl_set_original_tags', CFUNCTYPE(UNCHECKED(None), POINTER(splt_state), POINTER(splt_code))),
    ('splt_pl_clear_original_tags', CFUNCTYPE(UNCHECKED(None), POINTER(splt_original_tags))),
    ('splt_pl_scan_silence', CFUNCTYPE(UNCHECKED(c_int), POINTER(splt_state), POINTER(splt_code))),
    ('splt_pl_scan_trim_silence', CFUNCTYPE(UNCHECKED(c_int), POINTER(splt_state), POINTER(splt_code))),
    ('splt_pl_search_syncerrors', CFUNCTYPE(UNCHECKED(None), POINTER(splt_state), POINTER(splt_code))),
    ('splt_pl_offset_split', CFUNCTYPE(UNCHECKED(c_int), POINTER(splt_state), String, off_t, off_t)),
    ('splt_pl_dewrap', CFUNCTYPE(UNCHECKED(None), POINTER(splt_state), c_int, String, POINTER(splt_code))),
    ('splt_pl_import_internal_sheets', CFUNCTYPE(UNCHECKED(None), POINTER(splt_state), POINTER(splt_code))),
]

splt_plugin_func = struct_anon_43 # libmp3splt-0.9.2/include/libmp3splt/mp3splt.h: 2313

struct__splt_freedb_one_result.__slots__ = [
    'name',
    'id',
    'revision_number',
    'revisions',
]
struct__splt_freedb_one_result._fields_ = [
    ('name', String),
    ('id', c_int),
    ('revision_number', c_int),
    ('revisions', POINTER(c_int)),
]

struct__splt_freedb_results.__slots__ = [
    'results',
    'number',
    'iterator_counter',
]
struct__splt_freedb_results._fields_ = [
    ('results', POINTER(splt_freedb_one_result)),
    ('number', c_int),
    ('iterator_counter', c_int),
]

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 90
class struct_splt_cd(Structure):
    pass

struct_splt_cd.__slots__ = [
    'discid',
    'category',
]
struct_splt_cd._fields_ = [
    ('discid', c_char * (8 + 1)),
    ('category', c_char * 20),
]

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 98
class struct_anon_44(Structure):
    pass

struct_anon_44.__slots__ = [
    'discs',
    'foundcd',
]
struct_anon_44._fields_ = [
    ('discs', struct_splt_cd * 512),
    ('foundcd', c_int),
]

splt_cd_state = struct_anon_44 # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 98

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 108
class struct_anon_45(Structure):
    pass

struct_anon_45.__slots__ = [
    'search_results',
    'cdstate',
]
struct_anon_45._fields_ = [
    ('search_results', POINTER(struct__splt_freedb_results)),
    ('cdstate', POINTER(splt_cd_state)),
]

splt_freedb = struct_anon_45 # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 108

_splt_one_wrap = c_char # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 110

struct__splt_wrap.__slots__ = [
    'wrap_files_num',
    'wrap_files',
    'iterator_counter',
]
struct__splt_wrap._fields_ = [
    ('wrap_files_num', c_int),
    ('wrap_files', POINTER(POINTER(c_char))),
    ('iterator_counter', c_int),
]

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 124
class struct__splt_syncerrors(Structure):
    pass

struct__splt_syncerrors.__slots__ = [
    'serrors_points',
    'serrors_points_num',
]
struct__splt_syncerrors._fields_ = [
    ('serrors_points', POINTER(off_t)),
    ('serrors_points_num', c_long),
]

splt_syncerrors = struct__splt_syncerrors # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 137

struct__splt_tags.__slots__ = [
    'title',
    'artist',
    'album',
    'performer',
    'year',
    'comment',
    'track',
    'genre',
    'tags_version',
    'set_original_tags',
    'was_auto_incremented',
]
struct__splt_tags._fields_ = [
    ('title', String),
    ('artist', String),
    ('album', String),
    ('performer', String),
    ('year', String),
    ('comment', String),
    ('track', c_int),
    ('genre', String),
    ('tags_version', c_int),
    ('set_original_tags', c_int),
    ('was_auto_incremented', c_int),
]

struct__splt_original_tags.__slots__ = [
    'tags',
    'all_original_tags',
    'last_plugin_used',
]
struct__splt_original_tags._fields_ = [
    ('tags', splt_tags),
    ('all_original_tags', POINTER(None)),
    ('last_plugin_used', c_int),
]

struct__splt_tags_group.__slots__ = [
    'tags',
    'real_tagsnumber',
    'iterator_counter',
]
struct__splt_tags_group._fields_ = [
    ('tags', POINTER(splt_tags)),
    ('real_tagsnumber', c_int),
    ('iterator_counter', c_int),
]

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 210
class struct_anon_46(Structure):
    pass

struct_anon_46.__slots__ = [
    'format_string',
    'output_format_digits',
    'output_alpha_format_digits',
    'format',
]
struct_anon_46._fields_ = [
    ('format_string', String),
    ('output_format_digits', c_char),
    ('output_alpha_format_digits', c_int),
    ('format', (c_char * 255) * (20 + 1)),
]

splt_oformat = struct_anon_46 # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 210

struct__splt_point.__slots__ = [
    'value',
    'name',
    'type',
]
struct__splt_point._fields_ = [
    ('value', c_long),
    ('name', String),
    ('type', c_int),
]

struct__splt_points.__slots__ = [
    'points',
    'real_splitnumber',
    'iterator_counter',
]
struct__splt_points._fields_ = [
    ('points', POINTER(splt_point)),
    ('real_splitnumber', c_int),
    ('iterator_counter', c_int),
]

struct_splt_progres.__slots__ = [
    'progress_text_max_char',
    'filename_shorted',
    'percent_progress',
    'current_split',
    'max_splits',
    'progress_type',
    'silence_found_tracks',
    'silence_db_level',
    'progress',
    'progress_cb_data',
]
struct_splt_progres._fields_ = [
    ('progress_text_max_char', c_int),
    ('filename_shorted', c_char * 512),
    ('percent_progress', c_float),
    ('current_split', c_int),
    ('max_splits', c_int),
    ('progress_type', c_int),
    ('silence_found_tracks', c_int),
    ('silence_db_level', c_float),
    ('progress', CFUNCTYPE(UNCHECKED(None), POINTER(struct_splt_progres), POINTER(None))),
    ('progress_cb_data', POINTER(None)),
]

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 312
class struct_anon_47(Structure):
    pass

struct_anon_47.__slots__ = [
    'total_time',
    'current_split',
    'current_split_file_number',
    'splitnumber',
    'file_split',
    'file_split_cb_data',
    'write_cb',
    'write_cb_data',
    'p_bar',
    'get_silence_level',
    'silence_level_client_data',
    'put_message',
    'put_message_cb_data',
    'points',
    'tags_like_x',
    'tags_group',
]
struct_anon_47._fields_ = [
    ('total_time', c_long),
    ('current_split', c_int),
    ('current_split_file_number', c_int),
    ('splitnumber', c_int),
    ('file_split', CFUNCTYPE(UNCHECKED(None), String, POINTER(None))),
    ('file_split_cb_data', POINTER(None)),
    ('write_cb', CFUNCTYPE(UNCHECKED(None), POINTER(None), c_size_t, c_size_t, POINTER(None))),
    ('write_cb_data', POINTER(None)),
    ('p_bar', POINTER(splt_progress)),
    ('get_silence_level', CFUNCTYPE(UNCHECKED(None), c_long, c_float, POINTER(None))),
    ('silence_level_client_data', POINTER(None)),
    ('put_message', CFUNCTYPE(UNCHECKED(None), String, splt_message_type, POINTER(None))),
    ('put_message_cb_data', POINTER(None)),
    ('points', POINTER(splt_points)),
    ('tags_like_x', splt_tags),
    ('tags_group', POINTER(splt_tags_group)),
]

splt_struct = struct_anon_47 # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 312

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 497
class struct_anon_48(Structure):
    pass

struct_anon_48.__slots__ = [
    'split_mode',
    'tags',
    'xing',
    'output_filenames',
    'quiet_mode',
    'pretend_to_split',
    'option_frame_mode',
    'split_time',
    'overlap_time',
    'option_auto_adjust',
    'option_input_not_seekable',
    'create_dirs_from_filenames',
    'parameter_threshold',
    'parameter_offset',
    'parameter_number_tracks',
    'parameter_shots',
    'parameter_minimum_length',
    'parameter_min_track_length',
    'parameter_min_track_join',
    'artist_tag_format',
    'album_tag_format',
    'title_tag_format',
    'comment_tag_format',
    'replace_underscores_tag_format',
    'set_file_from_cue_if_file_tag_found',
    'parameter_remove_silence',
    'keep_silence_left',
    'keep_silence_right',
    'parameter_gap',
    'remaining_tags_like_x',
    'auto_increment_tracknumber_tags',
    'enable_silence_log',
    'force_tags_version',
    'length_split_file_number',
    'replace_tags_in_tags',
    'cue_set_splitpoint_names_from_rem_name',
    'cue_disable_cue_file_created_message',
    'cue_cddb_add_tags_with_keep_original_tags',
    'warn_if_no_auto_adjust_found',
    'stop_if_no_auto_adjust_found',
    'decode_and_write_flac_md5sum',
    'handle_bit_reservoir',
    'id3v2_encoding',
    'input_tags_encoding',
    'time_minimum_length',
]
struct_anon_48._fields_ = [
    ('split_mode', splt_split_mode_options),
    ('tags', splt_tags_options),
    ('xing', c_int),
    ('output_filenames', splt_output_filenames_options),
    ('quiet_mode', c_int),
    ('pretend_to_split', c_int),
    ('option_frame_mode', c_int),
    ('split_time', c_long),
    ('overlap_time', c_long),
    ('option_auto_adjust', c_int),
    ('option_input_not_seekable', c_int),
    ('create_dirs_from_filenames', c_int),
    ('parameter_threshold', c_float),
    ('parameter_offset', c_float),
    ('parameter_number_tracks', c_int),
    ('parameter_shots', c_int),
    ('parameter_minimum_length', c_float),
    ('parameter_min_track_length', c_float),
    ('parameter_min_track_join', c_float),
    ('artist_tag_format', c_int),
    ('album_tag_format', c_int),
    ('title_tag_format', c_int),
    ('comment_tag_format', c_int),
    ('replace_underscores_tag_format', c_int),
    ('set_file_from_cue_if_file_tag_found', c_int),
    ('parameter_remove_silence', c_int),
    ('keep_silence_left', c_float),
    ('keep_silence_right', c_float),
    ('parameter_gap', c_int),
    ('remaining_tags_like_x', c_int),
    ('auto_increment_tracknumber_tags', c_int),
    ('enable_silence_log', c_int),
    ('force_tags_version', c_int),
    ('length_split_file_number', c_int),
    ('replace_tags_in_tags', c_int),
    ('cue_set_splitpoint_names_from_rem_name', c_int),
    ('cue_disable_cue_file_created_message', c_int),
    ('cue_cddb_add_tags_with_keep_original_tags', c_int),
    ('warn_if_no_auto_adjust_found', c_int),
    ('stop_if_no_auto_adjust_found', c_int),
    ('decode_and_write_flac_md5sum', c_int),
    ('handle_bit_reservoir', c_int),
    ('id3v2_encoding', c_int),
    ('input_tags_encoding', c_int),
    ('time_minimum_length', c_long),
]

splt_options_variables = struct_anon_48 # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 497

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 511
class struct_anon_49(Structure):
    pass

struct_anon_49.__slots__ = [
    'frame_mode_enabled',
    'current_refresh_rate',
    'messages_locked',
    'library_locked',
    'new_filename_path',
]
struct_anon_49._fields_ = [
    ('frame_mode_enabled', c_int),
    ('current_refresh_rate', c_int),
    ('messages_locked', c_int),
    ('library_locked', c_int),
    ('new_filename_path', String),
]

splt_internal = struct_anon_49 # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 511

enum_anon_50 = c_int # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 516

SPLT_OPT_ALL_REMAINING_TAGS_LIKE_X = 10000 # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 516

SPLT_OPT_AUTO_INCREMENT_TRACKNUMBER_TAGS = (SPLT_OPT_ALL_REMAINING_TAGS_LIKE_X + 1) # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 516

splt_internal_options = enum_anon_50 # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 516

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 527
class struct_anon_51(Structure):
    pass

struct_anon_51.__slots__ = [
    'info',
    'plugin_filename',
    'plugin_handle',
    'func',
]
struct_anon_51._fields_ = [
    ('info', splt_plugin_info),
    ('plugin_filename', String),
    ('plugin_handle', POINTER(None)),
    ('func', POINTER(splt_plugin_func)),
]

splt_plugin_data = struct_anon_51 # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 527

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 538
class struct_anon_52(Structure):
    pass

struct_anon_52.__slots__ = [
    'plugins_scan_dirs',
    'number_of_dirs_to_scan',
    'number_of_plugins_found',
    'data',
]
struct_anon_52._fields_ = [
    ('plugins_scan_dirs', POINTER(POINTER(c_char))),
    ('number_of_dirs_to_scan', c_int),
    ('number_of_plugins_found', c_int),
    ('data', POINTER(splt_plugin_data)),
]

splt_plugins = struct_anon_52 # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 538

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 544
class struct_anon_53(Structure):
    pass

struct_anon_53.__slots__ = [
    'error_data',
    'strerror_msg',
]
struct_anon_53._fields_ = [
    ('error_data', String),
    ('strerror_msg', String),
]

splt_error = struct_anon_53 # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 544

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 546
class struct_splt_ssplit(Structure):
    pass

struct_splt_ssplit.__slots__ = [
    'begin_position',
    'end_position',
    'len',
    'next',
]
struct_splt_ssplit._fields_ = [
    ('begin_position', c_double),
    ('end_position', c_double),
    ('len', c_long),
    ('next', POINTER(struct_splt_ssplit)),
]

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 557
class struct_anon_54(Structure):
    pass

struct_anon_54.__slots__ = [
    'proxy_address',
    'proxy_port',
    'authentification',
]
struct_anon_54._fields_ = [
    ('proxy_address', String),
    ('proxy_port', c_int),
    ('authentification', String),
]

splt_proxy = struct_anon_54 # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 557

struct__splt_state.__slots__ = [
    'cancel_split',
    'fname_to_split',
    'path_of_split',
    'm3u_filename',
    'input_fname_regex',
    'default_comment_tag',
    'default_genre_tag',
    'original_tags',
    'options',
    'split',
    'oformat',
    'wrap',
    'serrors',
    'syncerrors',
    'fdb',
    'iopts',
    'silence_list',
    'proxy',
    'codec',
    'err',
    'plug',
    'current_plugin',
    'silence_log_fname',
    'silence_full_log_fname',
    'full_log_file_descriptor',
]
struct__splt_state._fields_ = [
    ('cancel_split', c_int),
    ('fname_to_split', String),
    ('path_of_split', String),
    ('m3u_filename', String),
    ('input_fname_regex', String),
    ('default_comment_tag', String),
    ('default_genre_tag', String),
    ('original_tags', splt_original_tags),
    ('options', splt_options_variables),
    ('split', splt_struct),
    ('oformat', splt_oformat),
    ('wrap', POINTER(splt_wrap)),
    ('serrors', POINTER(splt_syncerrors)),
    ('syncerrors', c_ulong),
    ('fdb', splt_freedb),
    ('iopts', splt_internal),
    ('silence_list', POINTER(struct_splt_ssplit)),
    ('proxy', splt_proxy),
    ('codec', POINTER(None)),
    ('err', splt_error),
    ('plug', POINTER(splt_plugins)),
    ('current_plugin', c_int),
    ('silence_log_fname', String),
    ('silence_full_log_fname', String),
    ('full_log_file_descriptor', POINTER(FILE)),
]

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 694
if hasattr(_libs['mp3splt'], 'splt_s_error_split'):
    splt_s_error_split = _libs['mp3splt'].splt_s_error_split
    splt_s_error_split.argtypes = [POINTER(splt_state), POINTER(c_int)]
    splt_s_error_split.restype = None

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 695
if hasattr(_libs['mp3splt'], 'splt_s_multiple_split'):
    splt_s_multiple_split = _libs['mp3splt'].splt_s_multiple_split
    splt_s_multiple_split.argtypes = [POINTER(splt_state), POINTER(c_int)]
    splt_s_multiple_split.restype = None

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 696
if hasattr(_libs['mp3splt'], 'splt_s_normal_split'):
    splt_s_normal_split = _libs['mp3splt'].splt_s_normal_split
    splt_s_normal_split.argtypes = [POINTER(splt_state), POINTER(c_int)]
    splt_s_normal_split.restype = None

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 701
if hasattr(_libs['mp3splt'], 'splt_s_time_split'):
    splt_s_time_split = _libs['mp3splt'].splt_s_time_split
    splt_s_time_split.argtypes = [POINTER(splt_state), POINTER(c_int)]
    splt_s_time_split.restype = None

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 702
if hasattr(_libs['mp3splt'], 'splt_s_equal_length_split'):
    splt_s_equal_length_split = _libs['mp3splt'].splt_s_equal_length_split
    splt_s_equal_length_split.argtypes = [POINTER(splt_state), POINTER(c_int)]
    splt_s_equal_length_split.restype = None

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 707
if hasattr(_libs['mp3splt'], 'splt_s_set_silence_splitpoints'):
    splt_s_set_silence_splitpoints = _libs['mp3splt'].splt_s_set_silence_splitpoints
    splt_s_set_silence_splitpoints.argtypes = [POINTER(splt_state), POINTER(c_int)]
    splt_s_set_silence_splitpoints.restype = c_int

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 708
if hasattr(_libs['mp3splt'], 'splt_s_set_trim_silence_splitpoints'):
    splt_s_set_trim_silence_splitpoints = _libs['mp3splt'].splt_s_set_trim_silence_splitpoints
    splt_s_set_trim_silence_splitpoints.argtypes = [POINTER(splt_state), POINTER(c_int)]
    splt_s_set_trim_silence_splitpoints.restype = c_int

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 709
if hasattr(_libs['mp3splt'], 'splt_s_silence_split'):
    splt_s_silence_split = _libs['mp3splt'].splt_s_silence_split
    splt_s_silence_split.argtypes = [POINTER(splt_state), POINTER(c_int)]
    splt_s_silence_split.restype = None

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 710
if hasattr(_libs['mp3splt'], 'splt_s_trim_silence_split'):
    splt_s_trim_silence_split = _libs['mp3splt'].splt_s_trim_silence_split
    splt_s_trim_silence_split.argtypes = [POINTER(splt_state), POINTER(c_int)]
    splt_s_trim_silence_split.restype = None

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 715
if hasattr(_libs['mp3splt'], 'splt_s_wrap_split'):
    splt_s_wrap_split = _libs['mp3splt'].splt_s_wrap_split
    splt_s_wrap_split.argtypes = [POINTER(splt_state), POINTER(c_int)]
    splt_s_wrap_split.restype = None

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 84
try:
    SPLT_MAXCD = 512
except:
    pass

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 87
try:
    SPLT_DISCIDLEN = 8
except:
    pass

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 198
try:
    SPLT_MAXOLEN = 255
except:
    pass

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 199
try:
    SPLT_OUTNUM = 20
except:
    pass

# /usr/include/limits.h: 80
try:
    INT_MAX = 2147483647
except:
    pass

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 677
try:
    fseeko = fseek
except:
    pass

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 678
try:
    ftello = ftell
except:
    pass

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 688
def _(STR):
    return STR

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 719
try:
    SPLT_DEFAULT_PROGRESS_RATE = 350
except:
    pass

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 720
try:
    SPLT_DEFAULT_PROGRESS_RATE2 = 50
except:
    pass

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 722
try:
    SPLT_DEFAULTSILLEN = 10
except:
    pass

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 724
try:
    SPLT_VARCHAR = '@'
except:
    pass

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 728
try:
    SPLT_MAXSYNC = INT_MAX
except:
    pass

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 729
try:
    SPLT_MAXSILENCE = INT_MAX
except:
    pass

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 732
try:
    SPLT_IERROR_INT = (-1)
except:
    pass

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 733
try:
    SPLT_IERROR_SET_ORIGINAL_TAGS = (-2)
except:
    pass

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 734
try:
    SPLT_IERROR_CHAR = (-3)
except:
    pass

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 737
try:
    SPLT_TAGS_VERSION = 800
except:
    pass

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 739
try:
    SPLT_ORIGINAL_TAGS_DEFAULT = '%[@o,@N=1]'
except:
    pass

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 741
try:
    SPLT_INTERNAL_PROGRESS_RATE = 1
except:
    pass

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 742
try:
    SPLT_INTERNAL_FRAME_MODE_ENABLED = 2
except:
    pass

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 749
try:
    SPLT_PACKAGE_NAME = 'libmp3splt'
except:
    pass

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 762
try:
    SPLT_AUTHOR = 'Matteo Trotta | Munteanu Alexandru'
except:
    pass

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 763
try:
    SPLT_EMAIL = '<mtrotta@users.sourceforge.net> | <m@ioalex.net>'
except:
    pass

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 767
try:
    SPLT_WEBSITE = 'http://mp3splt.sourceforge.net'
except:
    pass

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 772
try:
    SPLT_FREEDB_SEARCH_TYPE_CDDB = 2
except:
    pass

# /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 778
try:
    SPLT_NDIRCHAR = '\\\\'
except:
    pass

_splt_state = struct__splt_state # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 559

splt_progres = struct_splt_progres # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 237

_splt_point = struct__splt_point # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 212

_splt_points = struct__splt_points # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 228

_splt_tags = struct__splt_tags # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 139

_splt_tags_group = struct__splt_tags_group # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 192

_splt_freedb_results = struct__splt_freedb_results # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 69

_splt_freedb_one_result = struct__splt_freedb_one_result # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 44

_splt_wrap = struct__splt_wrap # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 112

_splt_original_tags = struct__splt_original_tags # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 186

splt_cd = struct_splt_cd # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 90

_splt_syncerrors = struct__splt_syncerrors # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 124

splt_ssplit = struct_splt_ssplit # /home/saso/tango.org/tm/libmp3splt-0.9.2/src/splt.h: 546

# No inserted files

