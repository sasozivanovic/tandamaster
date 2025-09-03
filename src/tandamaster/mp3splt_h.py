r"""Wrapper for mp3splt.h

Generated with:
/usr/bin/ctypesgen -lmp3splt /usr/include/libmp3splt/mp3splt.h -o src/tandamaster/mp3splt_h.py

Do not modify this file.
"""

__docformat__ = "restructuredtext"

# Begin preamble for Python

import ctypes
import sys
from ctypes import *  # noqa: F401, F403

_int_types = (ctypes.c_int16, ctypes.c_int32)
if hasattr(ctypes, "c_int64"):
    # Some builds of ctypes apparently do not have ctypes.c_int64
    # defined; it's a pretty good bet that these builds do not
    # have 64-bit pointers.
    _int_types += (ctypes.c_int64,)
for t in _int_types:
    if ctypes.sizeof(t) == ctypes.sizeof(ctypes.c_size_t):
        c_ptrdiff_t = t
del t
del _int_types



class UserString:
    def __init__(self, seq):
        if isinstance(seq, bytes):
            self.data = seq
        elif isinstance(seq, UserString):
            self.data = seq.data[:]
        else:
            self.data = str(seq).encode()

    def __bytes__(self):
        return self.data

    def __str__(self):
        return self.data.decode()

    def __repr__(self):
        return repr(self.data)

    def __int__(self):
        return int(self.data.decode())

    def __long__(self):
        return int(self.data.decode())

    def __float__(self):
        return float(self.data.decode())

    def __complex__(self):
        return complex(self.data.decode())

    def __hash__(self):
        return hash(self.data)

    def __le__(self, string):
        if isinstance(string, UserString):
            return self.data <= string.data
        else:
            return self.data <= string

    def __lt__(self, string):
        if isinstance(string, UserString):
            return self.data < string.data
        else:
            return self.data < string

    def __ge__(self, string):
        if isinstance(string, UserString):
            return self.data >= string.data
        else:
            return self.data >= string

    def __gt__(self, string):
        if isinstance(string, UserString):
            return self.data > string.data
        else:
            return self.data > string

    def __eq__(self, string):
        if isinstance(string, UserString):
            return self.data == string.data
        else:
            return self.data == string

    def __ne__(self, string):
        if isinstance(string, UserString):
            return self.data != string.data
        else:
            return self.data != string

    def __contains__(self, char):
        return char in self.data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        return self.__class__(self.data[index])

    def __getslice__(self, start, end):
        start = max(start, 0)
        end = max(end, 0)
        return self.__class__(self.data[start:end])

    def __add__(self, other):
        if isinstance(other, UserString):
            return self.__class__(self.data + other.data)
        elif isinstance(other, bytes):
            return self.__class__(self.data + other)
        else:
            return self.__class__(self.data + str(other).encode())

    def __radd__(self, other):
        if isinstance(other, bytes):
            return self.__class__(other + self.data)
        else:
            return self.__class__(str(other).encode() + self.data)

    def __mul__(self, n):
        return self.__class__(self.data * n)

    __rmul__ = __mul__

    def __mod__(self, args):
        return self.__class__(self.data % args)

    # the following methods are defined in alphabetical order:
    def capitalize(self):
        return self.__class__(self.data.capitalize())

    def center(self, width, *args):
        return self.__class__(self.data.center(width, *args))

    def count(self, sub, start=0, end=sys.maxsize):
        return self.data.count(sub, start, end)

    def decode(self, encoding=None, errors=None):  # XXX improve this?
        if encoding:
            if errors:
                return self.__class__(self.data.decode(encoding, errors))
            else:
                return self.__class__(self.data.decode(encoding))
        else:
            return self.__class__(self.data.decode())

    def encode(self, encoding=None, errors=None):  # XXX improve this?
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

    def isalpha(self):
        return self.data.isalpha()

    def isalnum(self):
        return self.data.isalnum()

    def isdecimal(self):
        return self.data.isdecimal()

    def isdigit(self):
        return self.data.isdigit()

    def islower(self):
        return self.data.islower()

    def isnumeric(self):
        return self.data.isnumeric()

    def isspace(self):
        return self.data.isspace()

    def istitle(self):
        return self.data.istitle()

    def isupper(self):
        return self.data.isupper()

    def join(self, seq):
        return self.data.join(seq)

    def ljust(self, width, *args):
        return self.__class__(self.data.ljust(width, *args))

    def lower(self):
        return self.__class__(self.data.lower())

    def lstrip(self, chars=None):
        return self.__class__(self.data.lstrip(chars))

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

    def rstrip(self, chars=None):
        return self.__class__(self.data.rstrip(chars))

    def split(self, sep=None, maxsplit=-1):
        return self.data.split(sep, maxsplit)

    def rsplit(self, sep=None, maxsplit=-1):
        return self.data.rsplit(sep, maxsplit)

    def splitlines(self, keepends=0):
        return self.data.splitlines(keepends)

    def startswith(self, prefix, start=0, end=sys.maxsize):
        return self.data.startswith(prefix, start, end)

    def strip(self, chars=None):
        return self.__class__(self.data.strip(chars))

    def swapcase(self):
        return self.__class__(self.data.swapcase())

    def title(self):
        return self.__class__(self.data.title())

    def translate(self, *args):
        return self.__class__(self.data.translate(*args))

    def upper(self):
        return self.__class__(self.data.upper())

    def zfill(self, width):
        return self.__class__(self.data.zfill(width))


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
        if index < 0 or index >= len(self.data):
            raise IndexError
        self.data = self.data[:index] + sub + self.data[index + 1 :]

    def __delitem__(self, index):
        if index < 0:
            index += len(self.data)
        if index < 0 or index >= len(self.data):
            raise IndexError
        self.data = self.data[:index] + self.data[index + 1 :]

    def __setslice__(self, start, end, sub):
        start = max(start, 0)
        end = max(end, 0)
        if isinstance(sub, UserString):
            self.data = self.data[:start] + sub.data + self.data[end:]
        elif isinstance(sub, bytes):
            self.data = self.data[:start] + sub + self.data[end:]
        else:
            self.data = self.data[:start] + str(sub).encode() + self.data[end:]

    def __delslice__(self, start, end):
        start = max(start, 0)
        end = max(end, 0)
        self.data = self.data[:start] + self.data[end:]

    def immutable(self):
        return UserString(self.data)

    def __iadd__(self, other):
        if isinstance(other, UserString):
            self.data += other.data
        elif isinstance(other, bytes):
            self.data += other
        else:
            self.data += str(other).encode()
        return self

    def __imul__(self, n):
        self.data *= n
        return self


class String(MutableString, ctypes.Union):

    _fields_ = [("raw", ctypes.POINTER(ctypes.c_char)), ("data", ctypes.c_char_p)]

    def __init__(self, obj=b""):
        if isinstance(obj, (bytes, UserString)):
            self.data = bytes(obj)
        else:
            self.raw = obj

    def __len__(self):
        return self.data and len(self.data) or 0

    def from_param(cls, obj):
        # Convert None or 0
        if obj is None or obj == 0:
            return cls(ctypes.POINTER(ctypes.c_char)())

        # Convert from String
        elif isinstance(obj, String):
            return obj

        # Convert from bytes
        elif isinstance(obj, bytes):
            return cls(obj)

        # Convert from str
        elif isinstance(obj, str):
            return cls(obj.encode())

        # Convert from c_char_p
        elif isinstance(obj, ctypes.c_char_p):
            return obj

        # Convert from POINTER(ctypes.c_char)
        elif isinstance(obj, ctypes.POINTER(ctypes.c_char)):
            return obj

        # Convert from raw pointer
        elif isinstance(obj, int):
            return cls(ctypes.cast(obj, ctypes.POINTER(ctypes.c_char)))

        # Convert from ctypes.c_char array
        elif isinstance(obj, ctypes.c_char * len(obj)):
            return obj

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
# typechecked, and will be converted to ctypes.c_void_p.
def UNCHECKED(type):
    if hasattr(type, "_type_") and isinstance(type._type_, str) and type._type_ != "P":
        return type
    else:
        return ctypes.c_void_p


# ctypes doesn't have direct support for variadic functions, so we have to write
# our own wrapper class
class _variadic_function(object):
    def __init__(self, func, restype, argtypes, errcheck):
        self.func = func
        self.func.restype = restype
        self.argtypes = argtypes
        if errcheck:
            self.func.errcheck = errcheck

    def _as_parameter_(self):
        # So we can pass this variadic function as a function pointer
        return self.func

    def __call__(self, *args):
        fixed_args = []
        i = 0
        for argtype in self.argtypes:
            # Typecheck what we can
            fixed_args.append(argtype.from_param(args[i]))
            i += 1
        return self.func(*fixed_args + list(args[i:]))


def ord_if_char(value):
    """
    Simple helper used for casts to simple builtin types:  if the argument is a
    string type, it will be converted to it's ordinal value.

    This function will raise an exception if the argument is string with more
    than one characters.
    """
    return ord(value) if (isinstance(value, bytes) or isinstance(value, str)) else value

# End preamble

_libs = {}
_libdirs = []

# Begin loader

"""
Load libraries - appropriately for all our supported platforms
"""
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

import ctypes
import ctypes.util
import glob
import os.path
import platform
import re
import sys


def _environ_path(name):
    """Split an environment variable into a path-like list elements"""
    if name in os.environ:
        return os.environ[name].split(":")
    return []


class LibraryLoader:
    """
    A base class For loading of libraries ;-)
    Subclasses load libraries for specific platforms.
    """

    # library names formatted specifically for platforms
    name_formats = ["%s"]

    class Lookup:
        """Looking up calling conventions for a platform"""

        mode = ctypes.DEFAULT_MODE

        def __init__(self, path):
            super(LibraryLoader.Lookup, self).__init__()
            self.access = dict(cdecl=ctypes.CDLL(path, self.mode))

        def get(self, name, calling_convention="cdecl"):
            """Return the given name according to the selected calling convention"""
            if calling_convention not in self.access:
                raise LookupError(
                    "Unknown calling convention '{}' for function '{}'".format(
                        calling_convention, name
                    )
                )
            return getattr(self.access[calling_convention], name)

        def has(self, name, calling_convention="cdecl"):
            """Return True if this given calling convention finds the given 'name'"""
            if calling_convention not in self.access:
                return False
            return hasattr(self.access[calling_convention], name)

        def __getattr__(self, name):
            return getattr(self.access["cdecl"], name)

    def __init__(self):
        self.other_dirs = []

    def __call__(self, libname):
        """Given the name of a library, load it."""
        paths = self.getpaths(libname)

        for path in paths:
            # noinspection PyBroadException
            try:
                return self.Lookup(path)
            except Exception:  # pylint: disable=broad-except
                pass

        raise ImportError("Could not load %s." % libname)

    def getpaths(self, libname):
        """Return a list of paths where the library might be found."""
        if os.path.isabs(libname):
            yield libname
        else:
            # search through a prioritized series of locations for the library

            # we first search any specific directories identified by user
            for dir_i in self.other_dirs:
                for fmt in self.name_formats:
                    # dir_i should be absolute already
                    yield os.path.join(dir_i, fmt % libname)

            # check if this code is even stored in a physical file
            try:
                this_file = __file__
            except NameError:
                this_file = None

            # then we search the directory where the generated python interface is stored
            if this_file is not None:
                for fmt in self.name_formats:
                    yield os.path.abspath(os.path.join(os.path.dirname(__file__), fmt % libname))

            # now, use the ctypes tools to try to find the library
            for fmt in self.name_formats:
                path = ctypes.util.find_library(fmt % libname)
                if path:
                    yield path

            # then we search all paths identified as platform-specific lib paths
            for path in self.getplatformpaths(libname):
                yield path

            # Finally, we'll try the users current working directory
            for fmt in self.name_formats:
                yield os.path.abspath(os.path.join(os.path.curdir, fmt % libname))

    def getplatformpaths(self, _libname):  # pylint: disable=no-self-use
        """Return all the library paths available in this platform"""
        return []


# Darwin (Mac OS X)


class DarwinLibraryLoader(LibraryLoader):
    """Library loader for MacOS"""

    name_formats = [
        "lib%s.dylib",
        "lib%s.so",
        "lib%s.bundle",
        "%s.dylib",
        "%s.so",
        "%s.bundle",
        "%s",
    ]

    class Lookup(LibraryLoader.Lookup):
        """
        Looking up library files for this platform (Darwin aka MacOS)
        """

        # Darwin requires dlopen to be called with mode RTLD_GLOBAL instead
        # of the default RTLD_LOCAL.  Without this, you end up with
        # libraries not being loadable, resulting in "Symbol not found"
        # errors
        mode = ctypes.RTLD_GLOBAL

    def getplatformpaths(self, libname):
        if os.path.pathsep in libname:
            names = [libname]
        else:
            names = [fmt % libname for fmt in self.name_formats]

        for directory in self.getdirs(libname):
            for name in names:
                yield os.path.join(directory, name)

    @staticmethod
    def getdirs(libname):
        """Implements the dylib search as specified in Apple documentation:

        http://developer.apple.com/documentation/DeveloperTools/Conceptual/
            DynamicLibraries/Articles/DynamicLibraryUsageGuidelines.html

        Before commencing the standard search, the method first checks
        the bundle's ``Frameworks`` directory if the application is running
        within a bundle (OS X .app).
        """

        dyld_fallback_library_path = _environ_path("DYLD_FALLBACK_LIBRARY_PATH")
        if not dyld_fallback_library_path:
            dyld_fallback_library_path = [
                os.path.expanduser("~/lib"),
                "/usr/local/lib",
                "/usr/lib",
            ]

        dirs = []

        if "/" in libname:
            dirs.extend(_environ_path("DYLD_LIBRARY_PATH"))
        else:
            dirs.extend(_environ_path("LD_LIBRARY_PATH"))
            dirs.extend(_environ_path("DYLD_LIBRARY_PATH"))
            dirs.extend(_environ_path("LD_RUN_PATH"))

        if hasattr(sys, "frozen") and getattr(sys, "frozen") == "macosx_app":
            dirs.append(os.path.join(os.environ["RESOURCEPATH"], "..", "Frameworks"))

        dirs.extend(dyld_fallback_library_path)

        return dirs


# Posix


class PosixLibraryLoader(LibraryLoader):
    """Library loader for POSIX-like systems (including Linux)"""

    _ld_so_cache = None

    _include = re.compile(r"^\s*include\s+(?P<pattern>.*)")

    name_formats = ["lib%s.so", "%s.so", "%s"]

    class _Directories(dict):
        """Deal with directories"""

        def __init__(self):
            dict.__init__(self)
            self.order = 0

        def add(self, directory):
            """Add a directory to our current set of directories"""
            if len(directory) > 1:
                directory = directory.rstrip(os.path.sep)
            # only adds and updates order if exists and not already in set
            if not os.path.exists(directory):
                return
            order = self.setdefault(directory, self.order)
            if order == self.order:
                self.order += 1

        def extend(self, directories):
            """Add a list of directories to our set"""
            for a_dir in directories:
                self.add(a_dir)

        def ordered(self):
            """Sort the list of directories"""
            return (i[0] for i in sorted(self.items(), key=lambda d: d[1]))

    def _get_ld_so_conf_dirs(self, conf, dirs):
        """
        Recursive function to help parse all ld.so.conf files, including proper
        handling of the `include` directive.
        """

        try:
            with open(conf) as fileobj:
                for dirname in fileobj:
                    dirname = dirname.strip()
                    if not dirname:
                        continue

                    match = self._include.match(dirname)
                    if not match:
                        dirs.add(dirname)
                    else:
                        for dir2 in glob.glob(match.group("pattern")):
                            self._get_ld_so_conf_dirs(dir2, dirs)
        except IOError:
            pass

    def _create_ld_so_cache(self):
        # Recreate search path followed by ld.so.  This is going to be
        # slow to build, and incorrect (ld.so uses ld.so.cache, which may
        # not be up-to-date).  Used only as fallback for distros without
        # /sbin/ldconfig.
        #
        # We assume the DT_RPATH and DT_RUNPATH binary sections are omitted.

        directories = self._Directories()
        for name in (
            "LD_LIBRARY_PATH",
            "SHLIB_PATH",  # HP-UX
            "LIBPATH",  # OS/2, AIX
            "LIBRARY_PATH",  # BE/OS
        ):
            if name in os.environ:
                directories.extend(os.environ[name].split(os.pathsep))

        self._get_ld_so_conf_dirs("/etc/ld.so.conf", directories)

        bitage = platform.architecture()[0]

        unix_lib_dirs_list = []
        if bitage.startswith("64"):
            # prefer 64 bit if that is our arch
            unix_lib_dirs_list += ["/lib64", "/usr/lib64"]

        # must include standard libs, since those paths are also used by 64 bit
        # installs
        unix_lib_dirs_list += ["/lib", "/usr/lib"]
        if sys.platform.startswith("linux"):
            # Try and support multiarch work in Ubuntu
            # https://wiki.ubuntu.com/MultiarchSpec
            if bitage.startswith("32"):
                # Assume Intel/AMD x86 compat
                unix_lib_dirs_list += ["/lib/i386-linux-gnu", "/usr/lib/i386-linux-gnu"]
            elif bitage.startswith("64"):
                # Assume Intel/AMD x86 compatible
                unix_lib_dirs_list += [
                    "/lib/x86_64-linux-gnu",
                    "/usr/lib/x86_64-linux-gnu",
                ]
            else:
                # guess...
                unix_lib_dirs_list += glob.glob("/lib/*linux-gnu")
        directories.extend(unix_lib_dirs_list)

        cache = {}
        lib_re = re.compile(r"lib(.*)\.s[ol]")
        # ext_re = re.compile(r"\.s[ol]$")
        for our_dir in directories.ordered():
            try:
                for path in glob.glob("%s/*.s[ol]*" % our_dir):
                    file = os.path.basename(path)

                    # Index by filename
                    cache_i = cache.setdefault(file, set())
                    cache_i.add(path)

                    # Index by library name
                    match = lib_re.match(file)
                    if match:
                        library = match.group(1)
                        cache_i = cache.setdefault(library, set())
                        cache_i.add(path)
            except OSError:
                pass

        self._ld_so_cache = cache

    def getplatformpaths(self, libname):
        if self._ld_so_cache is None:
            self._create_ld_so_cache()

        result = self._ld_so_cache.get(libname, set())
        for i in result:
            # we iterate through all found paths for library, since we may have
            # actually found multiple architectures or other library types that
            # may not load
            yield i


# Windows


class WindowsLibraryLoader(LibraryLoader):
    """Library loader for Microsoft Windows"""

    name_formats = ["%s.dll", "lib%s.dll", "%slib.dll", "%s"]

    class Lookup(LibraryLoader.Lookup):
        """Lookup class for Windows libraries..."""

        def __init__(self, path):
            super(WindowsLibraryLoader.Lookup, self).__init__(path)
            self.access["stdcall"] = ctypes.windll.LoadLibrary(path)


# Platform switching

# If your value of sys.platform does not appear in this dict, please contact
# the Ctypesgen maintainers.

loaderclass = {
    "darwin": DarwinLibraryLoader,
    "cygwin": WindowsLibraryLoader,
    "win32": WindowsLibraryLoader,
    "msys": WindowsLibraryLoader,
}

load_library = loaderclass.get(sys.platform, PosixLibraryLoader)()


def add_library_search_dirs(other_dirs):
    """
    Add libraries to search paths.
    If library paths are relative, convert them to absolute with respect to this
    file's directory
    """
    for path in other_dirs:
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        load_library.other_dirs.append(path)


del loaderclass

# End loader

add_library_search_dirs([])

# Begin libraries
_libs["mp3splt"] = load_library("mp3splt")

# 1 libraries
# End libraries

# No modules

__off_t = c_long# /usr/include/bits/types.h: 152

off_t = __off_t# /usr/include/sys/types.h: 85

enum_anon_15 = c_int# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_OK = 0# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_OK_SPLIT = 1# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_SPLITPOINT_BIGGER_THAN_LENGTH = 4# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_SILENCE_OK = 5# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_TIME_SPLIT_OK = 6# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_NO_SILENCE_SPLITPOINTS_FOUND = 7# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_OK_SPLIT_EOF = 8# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_LENGTH_SPLIT_OK = 9# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_TRIM_SILENCE_OK = 10# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_FREEDB_OK = 100# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_FREEDB_FILE_OK = 101# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_CDDB_OK = 102# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_CUE_OK = 103# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_FREEDB_MAX_CD_REACHED = 104# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_AUDACITY_OK = 105# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_DEWRAP_OK = 200# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_SYNC_OK = 300# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_MIGHT_BE_VBR = 301# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERR_SYNC = (-300)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERR_NO_SYNC_FOUND = (-301)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERR_TOO_MANY_SYNC_ERR = (-302)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_OUTPUT_FORMAT_OK = 400# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_OUTPUT_FORMAT_AMBIGUOUS = 401# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_REGEX_OK = 800# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_SPLITPOINTS = (-1)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_CANNOT_OPEN_FILE = (-2)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_INVALID = (-3)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_EQUAL_SPLITPOINTS = (-5)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_SPLITPOINTS_NOT_IN_ORDER = (-6)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_NEGATIVE_SPLITPOINT = (-7)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_INCORRECT_PATH = (-8)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_INCOMPATIBLE_OPTIONS = (-10)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_INPUT_OUTPUT_SAME_FILE = (-12)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_CANNOT_ALLOCATE_MEMORY = (-15)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_CANNOT_OPEN_DEST_FILE = (-16)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_CANT_WRITE_TO_OUTPUT_FILE = (-17)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_WHILE_READING_FILE = (-18)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_SEEKING_FILE = (-19)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_BEGIN_OUT_OF_FILE = (-20)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_INEXISTENT_FILE = (-21)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_SPLIT_CANCELLED = (-22)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_LIBRARY_LOCKED = (-24)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_STATE_NULL = (-25)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_NEGATIVE_TIME_SPLIT = (-26)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_CANNOT_CREATE_DIRECTORY = (-27)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_CANNOT_CLOSE_FILE = (-28)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_NO_PLUGIN_FOUND = (-29)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_CANNOT_INIT_LIBLTDL = (-30)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_CRC_FAILED = (-31)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_NO_PLUGIN_FOUND_FOR_FILE = (-32)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_PLUGIN_ERROR = (-33)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_TIME_SPLIT_VALUE_INVALID = (-34)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_LENGTH_SPLIT_VALUE_INVALID = (-35)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_CANNOT_GET_TOTAL_TIME = (-36)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_LIBID3 = (-37)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_FAILED_BITRESERVOIR = (-38)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_FREEDB_ERROR_INITIALISE_SOCKET = (-101)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_FREEDB_ERROR_CANNOT_GET_HOST = (-102)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_FREEDB_ERROR_CANNOT_OPEN_SOCKET = (-103)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_FREEDB_ERROR_CANNOT_CONNECT = (-104)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_FREEDB_ERROR_CANNOT_SEND_MESSAGE = (-105)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_FREEDB_ERROR_INVALID_SERVER_ANSWER = (-106)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_FREEDB_ERROR_SITE_201 = (-107)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_FREEDB_ERROR_SITE_200 = (-108)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_FREEDB_ERROR_BAD_COMMUNICATION = (-109)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_FREEDB_ERROR_GETTING_INFOS = (-110)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_FREEDB_NO_CD_FOUND = (-111)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_FREEDB_ERROR_CANNOT_RECV_MESSAGE = (-112)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_INVALID_CUE_FILE = (-115)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_INVALID_CDDB_FILE = (-116)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_FREEDB_NO_SUCH_CD_IN_DATABASE = (-118)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_FREEDB_ERROR_SITE = (-119)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_FREEDB_ERROR_CANNOT_DISCONNECT = (-120)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_FREEDB_ERROR_PROXY_NOT_SUPPORTED = (-121)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_INTERNAL_SHEET = (-122)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_INTERNAL_SHEET_TYPE_NOT_SUPPORTED = (-123)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_DEWRAP_ERR_FILE_LENGTH = (-200)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_DEWRAP_ERR_VERSION_OLD = (-201)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_DEWRAP_ERR_NO_FILE_OR_BAD_INDEX = (-202)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_DEWRAP_ERR_FILE_DAMAGED_INCOMPLETE = (-203)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_DEWRAP_ERR_FILE_NOT_WRAPED_DAMAGED = (-204)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_OUTPUT_FORMAT_ERROR = (-400)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_INEXISTENT_SPLITPOINT = (-500)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_PLUGIN_ERROR_UNSUPPORTED_FEATURE = (-600)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_INVALID_AUDACITY_FILE = (-700)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_INVALID_REGEX = (-800)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_REGEX_NO_MATCH = (-801)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_REGEX_UNAVAILABLE = (-802)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_NO_AUTO_ADJUST_FOUND = (-900)# /usr/include/libmp3splt/mp3splt.h: 215

SPLT_ERROR_INVALID_CODE = (-1000)# /usr/include/libmp3splt/mp3splt.h: 215

splt_code = enum_anon_15# /usr/include/libmp3splt/mp3splt.h: 215

# /usr/include/libmp3splt/mp3splt.h: 231
class struct__splt_state(Structure):
    pass

splt_state = struct__splt_state# /usr/include/libmp3splt/mp3splt.h: 231

# /usr/include/libmp3splt/mp3splt.h: 243
if _libs["mp3splt"].has("mp3splt_new_state", "cdecl"):
    mp3splt_new_state = _libs["mp3splt"].get("mp3splt_new_state", "cdecl")
    mp3splt_new_state.argtypes = [POINTER(splt_code)]
    mp3splt_new_state.restype = POINTER(splt_state)

# /usr/include/libmp3splt/mp3splt.h: 253
if _libs["mp3splt"].has("mp3splt_free_state", "cdecl"):
    mp3splt_free_state = _libs["mp3splt"].get("mp3splt_free_state", "cdecl")
    mp3splt_free_state.argtypes = [POINTER(splt_state)]
    mp3splt_free_state.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 264
if _libs["mp3splt"].has("mp3splt_append_plugins_scan_dir", "cdecl"):
    mp3splt_append_plugins_scan_dir = _libs["mp3splt"].get("mp3splt_append_plugins_scan_dir", "cdecl")
    mp3splt_append_plugins_scan_dir.argtypes = [POINTER(splt_state), String]
    mp3splt_append_plugins_scan_dir.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 275
if _libs["mp3splt"].has("mp3splt_find_plugins", "cdecl"):
    mp3splt_find_plugins = _libs["mp3splt"].get("mp3splt_find_plugins", "cdecl")
    mp3splt_find_plugins.argtypes = [POINTER(splt_state)]
    mp3splt_find_plugins.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 293
if _libs["mp3splt"].has("mp3splt_get_strerror", "cdecl"):
    mp3splt_get_strerror = _libs["mp3splt"].get("mp3splt_get_strerror", "cdecl")
    mp3splt_get_strerror.argtypes = [POINTER(splt_state), splt_code]
    if sizeof(c_int) == sizeof(c_void_p):
        mp3splt_get_strerror.restype = ReturnString
    else:
        mp3splt_get_strerror.restype = String
        mp3splt_get_strerror.errcheck = ReturnString

enum_anon_16 = c_int# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_PRETEND_TO_SPLIT = 1# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_QUIET_MODE = (SPLT_OPT_PRETEND_TO_SPLIT + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_DEBUG_MODE = (SPLT_OPT_QUIET_MODE + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_SPLIT_MODE = (SPLT_OPT_DEBUG_MODE + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_TAGS = (SPLT_OPT_SPLIT_MODE + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_XING = (SPLT_OPT_TAGS + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_CREATE_DIRS_FROM_FILENAMES = (SPLT_OPT_XING + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_OUTPUT_FILENAMES = (SPLT_OPT_CREATE_DIRS_FROM_FILENAMES + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_FRAME_MODE = (SPLT_OPT_OUTPUT_FILENAMES + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_AUTO_ADJUST = (SPLT_OPT_FRAME_MODE + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_INPUT_NOT_SEEKABLE = (SPLT_OPT_AUTO_ADJUST + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_PARAM_NUMBER_TRACKS = (SPLT_OPT_INPUT_NOT_SEEKABLE + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_PARAM_SHOTS = (SPLT_OPT_PARAM_NUMBER_TRACKS + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_PARAM_REMOVE_SILENCE = (SPLT_OPT_PARAM_SHOTS + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_PARAM_GAP = (SPLT_OPT_PARAM_REMOVE_SILENCE + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_ENABLE_SILENCE_LOG = (SPLT_OPT_PARAM_GAP + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_FORCE_TAGS_VERSION = (SPLT_OPT_ENABLE_SILENCE_LOG + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_LENGTH_SPLIT_FILE_NUMBER = (SPLT_OPT_FORCE_TAGS_VERSION + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_REPLACE_TAGS_IN_TAGS = (SPLT_OPT_LENGTH_SPLIT_FILE_NUMBER + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_OVERLAP_TIME = (SPLT_OPT_REPLACE_TAGS_IN_TAGS + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_SPLIT_TIME = (SPLT_OPT_OVERLAP_TIME + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_PARAM_THRESHOLD = (SPLT_OPT_SPLIT_TIME + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_PARAM_OFFSET = (SPLT_OPT_PARAM_THRESHOLD + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_PARAM_MIN_LENGTH = (SPLT_OPT_PARAM_OFFSET + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_PARAM_MIN_TRACK_LENGTH = (SPLT_OPT_PARAM_MIN_LENGTH + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_PARAM_MIN_TRACK_JOIN = (SPLT_OPT_PARAM_MIN_TRACK_LENGTH + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_ARTIST_TAG_FORMAT = (SPLT_OPT_PARAM_MIN_TRACK_JOIN + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_ALBUM_TAG_FORMAT = (SPLT_OPT_ARTIST_TAG_FORMAT + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_TITLE_TAG_FORMAT = (SPLT_OPT_ALBUM_TAG_FORMAT + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_COMMENT_TAG_FORMAT = (SPLT_OPT_TITLE_TAG_FORMAT + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_REPLACE_UNDERSCORES_TAG_FORMAT = (SPLT_OPT_COMMENT_TAG_FORMAT + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_SET_FILE_FROM_CUE_IF_FILE_TAG_FOUND = (SPLT_OPT_REPLACE_UNDERSCORES_TAG_FORMAT + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_KEEP_SILENCE_LEFT = (SPLT_OPT_SET_FILE_FROM_CUE_IF_FILE_TAG_FOUND + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_KEEP_SILENCE_RIGHT = (SPLT_OPT_KEEP_SILENCE_LEFT + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_CUE_SET_SPLITPOINT_NAMES_FROM_REM_NAME = (SPLT_OPT_KEEP_SILENCE_RIGHT + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_CUE_DISABLE_CUE_FILE_CREATED_MESSAGE = (SPLT_OPT_CUE_SET_SPLITPOINT_NAMES_FROM_REM_NAME + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_CUE_CDDB_ADD_TAGS_WITH_KEEP_ORIGINAL_TAGS = (SPLT_OPT_CUE_DISABLE_CUE_FILE_CREATED_MESSAGE + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_ID3V2_ENCODING = (SPLT_OPT_CUE_CDDB_ADD_TAGS_WITH_KEEP_ORIGINAL_TAGS + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_INPUT_TAGS_ENCODING = (SPLT_OPT_ID3V2_ENCODING + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_TIME_MINIMUM_THEORETICAL_LENGTH = (SPLT_OPT_INPUT_TAGS_ENCODING + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_WARN_IF_NO_AUTO_ADJUST_FOUND = (SPLT_OPT_TIME_MINIMUM_THEORETICAL_LENGTH + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_STOP_IF_NO_AUTO_ADJUST_FOUND = (SPLT_OPT_WARN_IF_NO_AUTO_ADJUST_FOUND + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_DECODE_AND_WRITE_FLAC_MD5SUM_FOR_CREATED_FILES = (SPLT_OPT_STOP_IF_NO_AUTO_ADJUST_FOUND + 1)# /usr/include/libmp3splt/mp3splt.h: 719

SPLT_OPT_HANDLE_BIT_RESERVOIR = (SPLT_OPT_DECODE_AND_WRITE_FLAC_MD5SUM_FOR_CREATED_FILES + 1)# /usr/include/libmp3splt/mp3splt.h: 719

splt_options = enum_anon_16# /usr/include/libmp3splt/mp3splt.h: 719

enum_anon_17 = c_int# /usr/include/libmp3splt/mp3splt.h: 758

SPLT_OPTION_NORMAL_MODE = 0# /usr/include/libmp3splt/mp3splt.h: 758

SPLT_OPTION_WRAP_MODE = (SPLT_OPTION_NORMAL_MODE + 1)# /usr/include/libmp3splt/mp3splt.h: 758

SPLT_OPTION_SILENCE_MODE = (SPLT_OPTION_WRAP_MODE + 1)# /usr/include/libmp3splt/mp3splt.h: 758

SPLT_OPTION_TRIM_SILENCE_MODE = (SPLT_OPTION_SILENCE_MODE + 1)# /usr/include/libmp3splt/mp3splt.h: 758

SPLT_OPTION_ERROR_MODE = (SPLT_OPTION_TRIM_SILENCE_MODE + 1)# /usr/include/libmp3splt/mp3splt.h: 758

SPLT_OPTION_TIME_MODE = (SPLT_OPTION_ERROR_MODE + 1)# /usr/include/libmp3splt/mp3splt.h: 758

SPLT_OPTION_LENGTH_MODE = (SPLT_OPTION_TIME_MODE + 1)# /usr/include/libmp3splt/mp3splt.h: 758

splt_split_mode_options = enum_anon_17# /usr/include/libmp3splt/mp3splt.h: 758

enum_anon_18 = c_int# /usr/include/libmp3splt/mp3splt.h: 776

SPLT_ID3V2_LATIN1 = 0# /usr/include/libmp3splt/mp3splt.h: 776

SPLT_ID3V2_UTF8 = (SPLT_ID3V2_LATIN1 + 1)# /usr/include/libmp3splt/mp3splt.h: 776

SPLT_ID3V2_UTF16 = (SPLT_ID3V2_UTF8 + 1)# /usr/include/libmp3splt/mp3splt.h: 776

splt_id3v2_encoding = enum_anon_18# /usr/include/libmp3splt/mp3splt.h: 776

enum_anon_19 = c_int# /usr/include/libmp3splt/mp3splt.h: 799

SPLT_OUTPUT_FORMAT = 0# /usr/include/libmp3splt/mp3splt.h: 799

SPLT_OUTPUT_DEFAULT = (SPLT_OUTPUT_FORMAT + 1)# /usr/include/libmp3splt/mp3splt.h: 799

SPLT_OUTPUT_CUSTOM = (SPLT_OUTPUT_DEFAULT + 1)# /usr/include/libmp3splt/mp3splt.h: 799

splt_output_filenames_options = enum_anon_19# /usr/include/libmp3splt/mp3splt.h: 799

enum_anon_20 = c_int# /usr/include/libmp3splt/mp3splt.h: 862

SPLT_TAGS_ORIGINAL_FILE = 0# /usr/include/libmp3splt/mp3splt.h: 862

SPLT_CURRENT_TAGS = (SPLT_TAGS_ORIGINAL_FILE + 1)# /usr/include/libmp3splt/mp3splt.h: 862

SPLT_NO_TAGS = (SPLT_CURRENT_TAGS + 1)# /usr/include/libmp3splt/mp3splt.h: 862

SPLT_TAGS_FROM_FILENAME_REGEX = (SPLT_NO_TAGS + 1)# /usr/include/libmp3splt/mp3splt.h: 862

splt_tags_options = enum_anon_20# /usr/include/libmp3splt/mp3splt.h: 862

enum_anon_21 = c_int# /usr/include/libmp3splt/mp3splt.h: 917

SPLT_NO_CONVERSION = 0# /usr/include/libmp3splt/mp3splt.h: 917

SPLT_TO_LOWERCASE = (SPLT_NO_CONVERSION + 1)# /usr/include/libmp3splt/mp3splt.h: 917

SPLT_TO_UPPERCASE = (SPLT_TO_LOWERCASE + 1)# /usr/include/libmp3splt/mp3splt.h: 917

SPLT_TO_FIRST_UPPERCASE = (SPLT_TO_UPPERCASE + 1)# /usr/include/libmp3splt/mp3splt.h: 917

SPLT_TO_WORD_FIRST_UPPERCASE = (SPLT_TO_FIRST_UPPERCASE + 1)# /usr/include/libmp3splt/mp3splt.h: 917

splt_str_format = enum_anon_21# /usr/include/libmp3splt/mp3splt.h: 917

# /usr/include/libmp3splt/mp3splt.h: 927
if _libs["mp3splt"].has("mp3splt_set_int_option", "cdecl"):
    mp3splt_set_int_option = _libs["mp3splt"].get("mp3splt_set_int_option", "cdecl")
    mp3splt_set_int_option.argtypes = [POINTER(splt_state), splt_options, c_int]
    mp3splt_set_int_option.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 937
if _libs["mp3splt"].has("mp3splt_set_long_option", "cdecl"):
    mp3splt_set_long_option = _libs["mp3splt"].get("mp3splt_set_long_option", "cdecl")
    mp3splt_set_long_option.argtypes = [POINTER(splt_state), splt_options, c_long]
    mp3splt_set_long_option.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 947
if _libs["mp3splt"].has("mp3splt_set_float_option", "cdecl"):
    mp3splt_set_float_option = _libs["mp3splt"].get("mp3splt_set_float_option", "cdecl")
    mp3splt_set_float_option.argtypes = [POINTER(splt_state), splt_options, c_float]
    mp3splt_set_float_option.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 957
if _libs["mp3splt"].has("mp3splt_get_int_option", "cdecl"):
    mp3splt_get_int_option = _libs["mp3splt"].get("mp3splt_get_int_option", "cdecl")
    mp3splt_get_int_option.argtypes = [POINTER(splt_state), splt_options, POINTER(splt_code)]
    mp3splt_get_int_option.restype = c_int

# /usr/include/libmp3splt/mp3splt.h: 967
if _libs["mp3splt"].has("mp3splt_get_long_option", "cdecl"):
    mp3splt_get_long_option = _libs["mp3splt"].get("mp3splt_get_long_option", "cdecl")
    mp3splt_get_long_option.argtypes = [POINTER(splt_state), splt_options, POINTER(splt_code)]
    mp3splt_get_long_option.restype = c_long

# /usr/include/libmp3splt/mp3splt.h: 977
if _libs["mp3splt"].has("mp3splt_get_float_option", "cdecl"):
    mp3splt_get_float_option = _libs["mp3splt"].get("mp3splt_get_float_option", "cdecl")
    mp3splt_get_float_option.argtypes = [POINTER(splt_state), splt_options, POINTER(splt_code)]
    mp3splt_get_float_option.restype = c_float

# /usr/include/libmp3splt/mp3splt.h: 986
if _libs["mp3splt"].has("mp3splt_set_oformat", "cdecl"):
    mp3splt_set_oformat = _libs["mp3splt"].get("mp3splt_set_oformat", "cdecl")
    mp3splt_set_oformat.argtypes = [POINTER(splt_state), String]
    mp3splt_set_oformat.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 1003
if _libs["mp3splt"].has("mp3splt_set_filename_to_split", "cdecl"):
    mp3splt_set_filename_to_split = _libs["mp3splt"].get("mp3splt_set_filename_to_split", "cdecl")
    mp3splt_set_filename_to_split.argtypes = [POINTER(splt_state), String]
    mp3splt_set_filename_to_split.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 1012
if _libs["mp3splt"].has("mp3splt_set_path_of_split", "cdecl"):
    mp3splt_set_path_of_split = _libs["mp3splt"].get("mp3splt_set_path_of_split", "cdecl")
    mp3splt_set_path_of_split.argtypes = [POINTER(splt_state), String]
    mp3splt_set_path_of_split.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 1025
if _libs["mp3splt"].has("mp3splt_get_filename_to_split", "cdecl"):
    mp3splt_get_filename_to_split = _libs["mp3splt"].get("mp3splt_get_filename_to_split", "cdecl")
    mp3splt_get_filename_to_split.argtypes = [POINTER(splt_state)]
    mp3splt_get_filename_to_split.restype = c_char_p

# /usr/include/libmp3splt/mp3splt.h: 1039
if _libs["mp3splt"].has("mp3splt_set_m3u_filename", "cdecl"):
    mp3splt_set_m3u_filename = _libs["mp3splt"].get("mp3splt_set_m3u_filename", "cdecl")
    mp3splt_set_m3u_filename.argtypes = [POINTER(splt_state), String]
    mp3splt_set_m3u_filename.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 1066
if _libs["mp3splt"].has("mp3splt_set_silence_log_filename", "cdecl"):
    mp3splt_set_silence_log_filename = _libs["mp3splt"].get("mp3splt_set_silence_log_filename", "cdecl")
    mp3splt_set_silence_log_filename.argtypes = [POINTER(splt_state), String]
    mp3splt_set_silence_log_filename.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 1100
if _libs["mp3splt"].has("mp3splt_set_silence_full_log_filename", "cdecl"):
    mp3splt_set_silence_full_log_filename = _libs["mp3splt"].get("mp3splt_set_silence_full_log_filename", "cdecl")
    mp3splt_set_silence_full_log_filename.argtypes = [POINTER(splt_state), String]
    mp3splt_set_silence_full_log_filename.restype = splt_code

enum_anon_22 = c_int# /usr/include/libmp3splt/mp3splt.h: 1128

SPLT_MESSAGE_INFO = 0# /usr/include/libmp3splt/mp3splt.h: 1128

SPLT_MESSAGE_WARNING = (SPLT_MESSAGE_INFO + 1)# /usr/include/libmp3splt/mp3splt.h: 1128

SPLT_MESSAGE_DEBUG = (SPLT_MESSAGE_WARNING + 1)# /usr/include/libmp3splt/mp3splt.h: 1128

splt_message_type = enum_anon_22# /usr/include/libmp3splt/mp3splt.h: 1128

# /usr/include/libmp3splt/mp3splt.h: 1146
if _libs["mp3splt"].has("mp3splt_set_message_function", "cdecl"):
    mp3splt_set_message_function = _libs["mp3splt"].get("mp3splt_set_message_function", "cdecl")
    mp3splt_set_message_function.argtypes = [POINTER(splt_state), CFUNCTYPE(UNCHECKED(None), String, splt_message_type, POINTER(None)), POINTER(None)]
    mp3splt_set_message_function.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 1162
if _libs["mp3splt"].has("mp3splt_set_split_filename_function", "cdecl"):
    mp3splt_set_split_filename_function = _libs["mp3splt"].get("mp3splt_set_split_filename_function", "cdecl")
    mp3splt_set_split_filename_function.argtypes = [POINTER(splt_state), CFUNCTYPE(UNCHECKED(None), String, POINTER(None)), POINTER(None)]
    mp3splt_set_split_filename_function.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 1186
if _libs["mp3splt"].has("mp3splt_set_pretend_to_split_write_function", "cdecl"):
    mp3splt_set_pretend_to_split_write_function = _libs["mp3splt"].get("mp3splt_set_pretend_to_split_write_function", "cdecl")
    mp3splt_set_pretend_to_split_write_function.argtypes = [POINTER(splt_state), CFUNCTYPE(UNCHECKED(None), POINTER(None), c_size_t, c_size_t, POINTER(None)), POINTER(None)]
    mp3splt_set_pretend_to_split_write_function.restype = splt_code

enum_anon_23 = c_int# /usr/include/libmp3splt/mp3splt.h: 1212

SPLT_PROGRESS_PREPARE = 0# /usr/include/libmp3splt/mp3splt.h: 1212

SPLT_PROGRESS_CREATE = (SPLT_PROGRESS_PREPARE + 1)# /usr/include/libmp3splt/mp3splt.h: 1212

SPLT_PROGRESS_SEARCH_SYNC = (SPLT_PROGRESS_CREATE + 1)# /usr/include/libmp3splt/mp3splt.h: 1212

SPLT_PROGRESS_SCAN_SILENCE = (SPLT_PROGRESS_SEARCH_SYNC + 1)# /usr/include/libmp3splt/mp3splt.h: 1212

splt_progress_messages = enum_anon_23# /usr/include/libmp3splt/mp3splt.h: 1212

# /usr/include/libmp3splt/mp3splt.h: 1229
class struct_splt_progres(Structure):
    pass

splt_progress = struct_splt_progres# /usr/include/libmp3splt/mp3splt.h: 1229

# /usr/include/libmp3splt/mp3splt.h: 1244
if _libs["mp3splt"].has("mp3splt_set_progress_function", "cdecl"):
    mp3splt_set_progress_function = _libs["mp3splt"].get("mp3splt_set_progress_function", "cdecl")
    mp3splt_set_progress_function.argtypes = [POINTER(splt_state), CFUNCTYPE(UNCHECKED(None), POINTER(splt_progress), POINTER(None)), POINTER(None)]
    mp3splt_set_progress_function.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 1250
if _libs["mp3splt"].has("mp3splt_progress_get_type", "cdecl"):
    mp3splt_progress_get_type = _libs["mp3splt"].get("mp3splt_progress_get_type", "cdecl")
    mp3splt_progress_get_type.argtypes = [POINTER(splt_progress)]
    mp3splt_progress_get_type.restype = c_int

# /usr/include/libmp3splt/mp3splt.h: 1255
if _libs["mp3splt"].has("mp3splt_progress_get_filename_shorted", "cdecl"):
    mp3splt_progress_get_filename_shorted = _libs["mp3splt"].get("mp3splt_progress_get_filename_shorted", "cdecl")
    mp3splt_progress_get_filename_shorted.argtypes = [POINTER(splt_progress)]
    if sizeof(c_int) == sizeof(c_void_p):
        mp3splt_progress_get_filename_shorted.restype = ReturnString
    else:
        mp3splt_progress_get_filename_shorted.restype = String
        mp3splt_progress_get_filename_shorted.errcheck = ReturnString

# /usr/include/libmp3splt/mp3splt.h: 1260
if _libs["mp3splt"].has("mp3splt_progress_get_current_split", "cdecl"):
    mp3splt_progress_get_current_split = _libs["mp3splt"].get("mp3splt_progress_get_current_split", "cdecl")
    mp3splt_progress_get_current_split.argtypes = [POINTER(splt_progress)]
    mp3splt_progress_get_current_split.restype = c_int

# /usr/include/libmp3splt/mp3splt.h: 1265
if _libs["mp3splt"].has("mp3splt_progress_get_max_splits", "cdecl"):
    mp3splt_progress_get_max_splits = _libs["mp3splt"].get("mp3splt_progress_get_max_splits", "cdecl")
    mp3splt_progress_get_max_splits.argtypes = [POINTER(splt_progress)]
    mp3splt_progress_get_max_splits.restype = c_int

# /usr/include/libmp3splt/mp3splt.h: 1270
if _libs["mp3splt"].has("mp3splt_progress_get_silence_found_tracks", "cdecl"):
    mp3splt_progress_get_silence_found_tracks = _libs["mp3splt"].get("mp3splt_progress_get_silence_found_tracks", "cdecl")
    mp3splt_progress_get_silence_found_tracks.argtypes = [POINTER(splt_progress)]
    mp3splt_progress_get_silence_found_tracks.restype = c_int

# /usr/include/libmp3splt/mp3splt.h: 1275
if _libs["mp3splt"].has("mp3splt_progress_get_silence_db_level", "cdecl"):
    mp3splt_progress_get_silence_db_level = _libs["mp3splt"].get("mp3splt_progress_get_silence_db_level", "cdecl")
    mp3splt_progress_get_silence_db_level.argtypes = [POINTER(splt_progress)]
    mp3splt_progress_get_silence_db_level.restype = c_float

# /usr/include/libmp3splt/mp3splt.h: 1280
if _libs["mp3splt"].has("mp3splt_progress_get_percent_progress", "cdecl"):
    mp3splt_progress_get_percent_progress = _libs["mp3splt"].get("mp3splt_progress_get_percent_progress", "cdecl")
    mp3splt_progress_get_percent_progress.argtypes = [POINTER(splt_progress)]
    mp3splt_progress_get_percent_progress.restype = c_float

# /usr/include/libmp3splt/mp3splt.h: 1297
if _libs["mp3splt"].has("mp3splt_set_silence_level_function", "cdecl"):
    mp3splt_set_silence_level_function = _libs["mp3splt"].get("mp3splt_set_silence_level_function", "cdecl")
    mp3splt_set_silence_level_function.argtypes = [POINTER(splt_state), CFUNCTYPE(UNCHECKED(None), c_long, c_float, POINTER(None)), POINTER(None)]
    mp3splt_set_silence_level_function.restype = splt_code

enum_anon_24 = c_int# /usr/include/libmp3splt/mp3splt.h: 1323

SPLT_SPLITPOINT = 0# /usr/include/libmp3splt/mp3splt.h: 1323

SPLT_SKIPPOINT = (SPLT_SPLITPOINT + 1)# /usr/include/libmp3splt/mp3splt.h: 1323

splt_type_of_splitpoint = enum_anon_24# /usr/include/libmp3splt/mp3splt.h: 1323

# /usr/include/libmp3splt/mp3splt.h: 1333
class struct__splt_point(Structure):
    pass

splt_point = struct__splt_point# /usr/include/libmp3splt/mp3splt.h: 1333

# /usr/include/libmp3splt/mp3splt.h: 1348
if _libs["mp3splt"].has("mp3splt_point_new", "cdecl"):
    mp3splt_point_new = _libs["mp3splt"].get("mp3splt_point_new", "cdecl")
    mp3splt_point_new.argtypes = [c_long, POINTER(splt_code)]
    mp3splt_point_new.restype = POINTER(splt_point)

# /usr/include/libmp3splt/mp3splt.h: 1357
if _libs["mp3splt"].has("mp3splt_point_set_name", "cdecl"):
    mp3splt_point_set_name = _libs["mp3splt"].get("mp3splt_point_set_name", "cdecl")
    mp3splt_point_set_name.argtypes = [POINTER(splt_point), String]
    mp3splt_point_set_name.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 1366
if _libs["mp3splt"].has("mp3splt_point_set_type", "cdecl"):
    mp3splt_point_set_type = _libs["mp3splt"].get("mp3splt_point_set_type", "cdecl")
    mp3splt_point_set_type.argtypes = [POINTER(splt_point), splt_type_of_splitpoint]
    mp3splt_point_set_type.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 1377
if _libs["mp3splt"].has("mp3splt_append_splitpoint", "cdecl"):
    mp3splt_append_splitpoint = _libs["mp3splt"].get("mp3splt_append_splitpoint", "cdecl")
    mp3splt_append_splitpoint.argtypes = [POINTER(splt_state), POINTER(splt_point)]
    mp3splt_append_splitpoint.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 1386
class struct__splt_points(Structure):
    pass

splt_points = struct__splt_points# /usr/include/libmp3splt/mp3splt.h: 1386

# /usr/include/libmp3splt/mp3splt.h: 1398
if _libs["mp3splt"].has("mp3splt_get_splitpoints", "cdecl"):
    mp3splt_get_splitpoints = _libs["mp3splt"].get("mp3splt_get_splitpoints", "cdecl")
    mp3splt_get_splitpoints.argtypes = [POINTER(splt_state), POINTER(splt_code)]
    mp3splt_get_splitpoints.restype = POINTER(splt_points)

# /usr/include/libmp3splt/mp3splt.h: 1407
if _libs["mp3splt"].has("mp3splt_points_init_iterator", "cdecl"):
    mp3splt_points_init_iterator = _libs["mp3splt"].get("mp3splt_points_init_iterator", "cdecl")
    mp3splt_points_init_iterator.argtypes = [POINTER(splt_points)]
    mp3splt_points_init_iterator.restype = None

# /usr/include/libmp3splt/mp3splt.h: 1419
if _libs["mp3splt"].has("mp3splt_points_next", "cdecl"):
    mp3splt_points_next = _libs["mp3splt"].get("mp3splt_points_next", "cdecl")
    mp3splt_points_next.argtypes = [POINTER(splt_points)]
    mp3splt_points_next.restype = POINTER(splt_point)

# /usr/include/libmp3splt/mp3splt.h: 1429
if _libs["mp3splt"].has("mp3splt_point_get_value", "cdecl"):
    mp3splt_point_get_value = _libs["mp3splt"].get("mp3splt_point_get_value", "cdecl")
    mp3splt_point_get_value.argtypes = [POINTER(splt_point)]
    mp3splt_point_get_value.restype = c_long

# /usr/include/libmp3splt/mp3splt.h: 1440
if _libs["mp3splt"].has("mp3splt_point_get_type", "cdecl"):
    mp3splt_point_get_type = _libs["mp3splt"].get("mp3splt_point_get_type", "cdecl")
    mp3splt_point_get_type.argtypes = [POINTER(splt_point)]
    mp3splt_point_get_type.restype = splt_type_of_splitpoint

# /usr/include/libmp3splt/mp3splt.h: 1450
if _libs["mp3splt"].has("mp3splt_point_get_name", "cdecl"):
    mp3splt_point_get_name = _libs["mp3splt"].get("mp3splt_point_get_name", "cdecl")
    mp3splt_point_get_name.argtypes = [POINTER(splt_point)]
    if sizeof(c_int) == sizeof(c_void_p):
        mp3splt_point_get_name.restype = ReturnString
    else:
        mp3splt_point_get_name.restype = String
        mp3splt_point_get_name.errcheck = ReturnString

# /usr/include/libmp3splt/mp3splt.h: 1458
if _libs["mp3splt"].has("mp3splt_erase_all_splitpoints", "cdecl"):
    mp3splt_erase_all_splitpoints = _libs["mp3splt"].get("mp3splt_erase_all_splitpoints", "cdecl")
    mp3splt_erase_all_splitpoints.argtypes = [POINTER(splt_state)]
    mp3splt_erase_all_splitpoints.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 1482
try:
    splt_id3v1_genres = ((c_char * int(25)) * int(127)).in_dll(_libs["mp3splt"], "splt_id3v1_genres")
except:
    pass

enum_anon_25 = c_int# /usr/include/libmp3splt/mp3splt.h: 1501

SPLT_TAGS_TITLE = 1# /usr/include/libmp3splt/mp3splt.h: 1501

SPLT_TAGS_ARTIST = 2# /usr/include/libmp3splt/mp3splt.h: 1501

SPLT_TAGS_ALBUM = 3# /usr/include/libmp3splt/mp3splt.h: 1501

SPLT_TAGS_YEAR = 4# /usr/include/libmp3splt/mp3splt.h: 1501

SPLT_TAGS_COMMENT = 5# /usr/include/libmp3splt/mp3splt.h: 1501

SPLT_TAGS_TRACK = 6# /usr/include/libmp3splt/mp3splt.h: 1501

SPLT_TAGS_GENRE = 7# /usr/include/libmp3splt/mp3splt.h: 1501

SPLT_TAGS_PERFORMER = 8# /usr/include/libmp3splt/mp3splt.h: 1501

SPLT_TAGS_ORIGINAL = 900# /usr/include/libmp3splt/mp3splt.h: 1501

splt_tag_key = enum_anon_25# /usr/include/libmp3splt/mp3splt.h: 1501

# /usr/include/libmp3splt/mp3splt.h: 1512
class struct__splt_tags(Structure):
    pass

splt_tags = struct__splt_tags# /usr/include/libmp3splt/mp3splt.h: 1512

# /usr/include/libmp3splt/mp3splt.h: 1523
if _libs["mp3splt"].has("mp3splt_tags_new", "cdecl"):
    mp3splt_tags_new = _libs["mp3splt"].get("mp3splt_tags_new", "cdecl")
    mp3splt_tags_new.argtypes = [POINTER(splt_code)]
    mp3splt_tags_new.restype = POINTER(splt_tags)

# /usr/include/libmp3splt/mp3splt.h: 1544
if _libs["mp3splt"].has("mp3splt_tags_set", "cdecl"):
    _func = _libs["mp3splt"].get("mp3splt_tags_set", "cdecl")
    _restype = splt_code
    _errcheck = None
    _argtypes = [POINTER(splt_tags)]
    mp3splt_tags_set = _variadic_function(_func,_restype,_argtypes,_errcheck)

# /usr/include/libmp3splt/mp3splt.h: 1558
if _libs["mp3splt"].has("mp3splt_append_tags", "cdecl"):
    mp3splt_append_tags = _libs["mp3splt"].get("mp3splt_append_tags", "cdecl")
    mp3splt_append_tags.argtypes = [POINTER(splt_state), POINTER(splt_tags)]
    mp3splt_append_tags.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 1564
class struct__splt_tags_group(Structure):
    pass

splt_tags_group = struct__splt_tags_group# /usr/include/libmp3splt/mp3splt.h: 1564

# /usr/include/libmp3splt/mp3splt.h: 1576
if _libs["mp3splt"].has("mp3splt_get_tags_group", "cdecl"):
    mp3splt_get_tags_group = _libs["mp3splt"].get("mp3splt_get_tags_group", "cdecl")
    mp3splt_get_tags_group.argtypes = [POINTER(splt_state), POINTER(splt_code)]
    mp3splt_get_tags_group.restype = POINTER(splt_tags_group)

# /usr/include/libmp3splt/mp3splt.h: 1584
if _libs["mp3splt"].has("mp3splt_remove_tags_of_skippoints", "cdecl"):
    mp3splt_remove_tags_of_skippoints = _libs["mp3splt"].get("mp3splt_remove_tags_of_skippoints", "cdecl")
    mp3splt_remove_tags_of_skippoints.argtypes = [POINTER(splt_state)]
    mp3splt_remove_tags_of_skippoints.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 1593
if _libs["mp3splt"].has("mp3splt_tags_group_init_iterator", "cdecl"):
    mp3splt_tags_group_init_iterator = _libs["mp3splt"].get("mp3splt_tags_group_init_iterator", "cdecl")
    mp3splt_tags_group_init_iterator.argtypes = [POINTER(splt_tags_group)]
    mp3splt_tags_group_init_iterator.restype = None

# /usr/include/libmp3splt/mp3splt.h: 1603
if _libs["mp3splt"].has("mp3splt_tags_group_next", "cdecl"):
    mp3splt_tags_group_next = _libs["mp3splt"].get("mp3splt_tags_group_next", "cdecl")
    mp3splt_tags_group_next.argtypes = [POINTER(splt_tags_group)]
    mp3splt_tags_group_next.restype = POINTER(splt_tags)

# /usr/include/libmp3splt/mp3splt.h: 1608
if _libs["mp3splt"].has("mp3splt_tags_get", "cdecl"):
    mp3splt_tags_get = _libs["mp3splt"].get("mp3splt_tags_get", "cdecl")
    mp3splt_tags_get.argtypes = [POINTER(splt_tags), splt_tag_key]
    if sizeof(c_int) == sizeof(c_void_p):
        mp3splt_tags_get.restype = ReturnString
    else:
        mp3splt_tags_get.restype = String
        mp3splt_tags_get.errcheck = ReturnString

# /usr/include/libmp3splt/mp3splt.h: 1638
if _libs["mp3splt"].has("mp3splt_put_tags_from_string", "cdecl"):
    mp3splt_put_tags_from_string = _libs["mp3splt"].get("mp3splt_put_tags_from_string", "cdecl")
    mp3splt_put_tags_from_string.argtypes = [POINTER(splt_state), String, POINTER(splt_code)]
    mp3splt_put_tags_from_string.restype = c_int

# /usr/include/libmp3splt/mp3splt.h: 1648
if _libs["mp3splt"].has("mp3splt_read_original_tags", "cdecl"):
    mp3splt_read_original_tags = _libs["mp3splt"].get("mp3splt_read_original_tags", "cdecl")
    mp3splt_read_original_tags.argtypes = [POINTER(splt_state)]
    mp3splt_read_original_tags.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 1656
if _libs["mp3splt"].has("mp3splt_erase_all_tags", "cdecl"):
    mp3splt_erase_all_tags = _libs["mp3splt"].get("mp3splt_erase_all_tags", "cdecl")
    mp3splt_erase_all_tags.argtypes = [POINTER(splt_state)]
    mp3splt_erase_all_tags.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 1671
if _libs["mp3splt"].has("mp3splt_set_input_filename_regex", "cdecl"):
    mp3splt_set_input_filename_regex = _libs["mp3splt"].get("mp3splt_set_input_filename_regex", "cdecl")
    mp3splt_set_input_filename_regex.argtypes = [POINTER(splt_state), String]
    mp3splt_set_input_filename_regex.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 1682
if _libs["mp3splt"].has("mp3splt_set_default_comment_tag", "cdecl"):
    mp3splt_set_default_comment_tag = _libs["mp3splt"].get("mp3splt_set_default_comment_tag", "cdecl")
    mp3splt_set_default_comment_tag.argtypes = [POINTER(splt_state), String]
    mp3splt_set_default_comment_tag.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 1693
if _libs["mp3splt"].has("mp3splt_set_default_genre_tag", "cdecl"):
    mp3splt_set_default_genre_tag = _libs["mp3splt"].get("mp3splt_set_default_genre_tag", "cdecl")
    mp3splt_set_default_genre_tag.argtypes = [POINTER(splt_state), String]
    mp3splt_set_default_genre_tag.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 1707
if _libs["mp3splt"].has("mp3splt_parse_filename_regex", "cdecl"):
    mp3splt_parse_filename_regex = _libs["mp3splt"].get("mp3splt_parse_filename_regex", "cdecl")
    mp3splt_parse_filename_regex.argtypes = [POINTER(splt_state), POINTER(splt_code)]
    mp3splt_parse_filename_regex.restype = POINTER(splt_tags)

# /usr/include/libmp3splt/mp3splt.h: 1716
if _libs["mp3splt"].has("mp3splt_free_one_tag", "cdecl"):
    mp3splt_free_one_tag = _libs["mp3splt"].get("mp3splt_free_one_tag", "cdecl")
    mp3splt_free_one_tag.argtypes = [POINTER(splt_tags)]
    mp3splt_free_one_tag.restype = None

# /usr/include/libmp3splt/mp3splt.h: 1738
if _libs["mp3splt"].has("mp3splt_split", "cdecl"):
    mp3splt_split = _libs["mp3splt"].get("mp3splt_split", "cdecl")
    mp3splt_split.argtypes = [POINTER(splt_state)]
    mp3splt_split.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 1748
if _libs["mp3splt"].has("mp3splt_stop_split", "cdecl"):
    mp3splt_stop_split = _libs["mp3splt"].get("mp3splt_stop_split", "cdecl")
    mp3splt_stop_split.argtypes = [POINTER(splt_state)]
    mp3splt_stop_split.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 1761
if _libs["mp3splt"].has("mp3splt_find_filenames", "cdecl"):
    mp3splt_find_filenames = _libs["mp3splt"].get("mp3splt_find_filenames", "cdecl")
    mp3splt_find_filenames.argtypes = [POINTER(splt_state), String, POINTER(c_int), POINTER(splt_code)]
    mp3splt_find_filenames.restype = POINTER(POINTER(c_char))

enum_anon_26 = c_int# /usr/include/libmp3splt/mp3splt.h: 1782

CUE_IMPORT = 0# /usr/include/libmp3splt/mp3splt.h: 1782

CDDB_IMPORT = (CUE_IMPORT + 1)# /usr/include/libmp3splt/mp3splt.h: 1782

AUDACITY_LABELS_IMPORT = (CDDB_IMPORT + 1)# /usr/include/libmp3splt/mp3splt.h: 1782

PLUGIN_INTERNAL_IMPORT = (AUDACITY_LABELS_IMPORT + 1)# /usr/include/libmp3splt/mp3splt.h: 1782

splt_import_type = enum_anon_26# /usr/include/libmp3splt/mp3splt.h: 1782

# /usr/include/libmp3splt/mp3splt.h: 1794
if _libs["mp3splt"].has("mp3splt_import", "cdecl"):
    mp3splt_import = _libs["mp3splt"].get("mp3splt_import", "cdecl")
    mp3splt_import.argtypes = [POINTER(splt_state), splt_import_type, String]
    mp3splt_import.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 1842
class struct__splt_freedb_results(Structure):
    pass

splt_freedb_results = struct__splt_freedb_results# /usr/include/libmp3splt/mp3splt.h: 1842

# /usr/include/libmp3splt/mp3splt.h: 1851
class struct__splt_freedb_one_result(Structure):
    pass

splt_freedb_one_result = struct__splt_freedb_one_result# /usr/include/libmp3splt/mp3splt.h: 1851

# /usr/include/libmp3splt/mp3splt.h: 1861
if _libs["mp3splt"].has("mp3splt_use_proxy", "cdecl"):
    mp3splt_use_proxy = _libs["mp3splt"].get("mp3splt_use_proxy", "cdecl")
    mp3splt_use_proxy.argtypes = [POINTER(splt_state), String, c_int]
    mp3splt_use_proxy.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 1874
if _libs["mp3splt"].has("mp3splt_use_base64_authentification", "cdecl"):
    mp3splt_use_base64_authentification = _libs["mp3splt"].get("mp3splt_use_base64_authentification", "cdecl")
    mp3splt_use_base64_authentification.argtypes = [POINTER(splt_state), String]
    mp3splt_use_base64_authentification.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 1887
if _libs["mp3splt"].has("mp3splt_encode_in_base64", "cdecl"):
    mp3splt_encode_in_base64 = _libs["mp3splt"].get("mp3splt_encode_in_base64", "cdecl")
    mp3splt_encode_in_base64.argtypes = [POINTER(splt_state), String, POINTER(c_int)]
    if sizeof(c_int) == sizeof(c_void_p):
        mp3splt_encode_in_base64.restype = ReturnString
    else:
        mp3splt_encode_in_base64.restype = String
        mp3splt_encode_in_base64.errcheck = ReturnString

# /usr/include/libmp3splt/mp3splt.h: 1895
if _libs["mp3splt"].has("mp3splt_clear_proxy", "cdecl"):
    mp3splt_clear_proxy = _libs["mp3splt"].get("mp3splt_clear_proxy", "cdecl")
    mp3splt_clear_proxy.argtypes = [POINTER(splt_state)]
    mp3splt_clear_proxy.restype = None

# /usr/include/libmp3splt/mp3splt.h: 1913
if _libs["mp3splt"].has("mp3splt_get_freedb_search", "cdecl"):
    mp3splt_get_freedb_search = _libs["mp3splt"].get("mp3splt_get_freedb_search", "cdecl")
    mp3splt_get_freedb_search.argtypes = [POINTER(splt_state), String, POINTER(splt_code), c_int, String, c_int]
    mp3splt_get_freedb_search.restype = POINTER(splt_freedb_results)

# /usr/include/libmp3splt/mp3splt.h: 1924
if _libs["mp3splt"].has("mp3splt_freedb_init_iterator", "cdecl"):
    mp3splt_freedb_init_iterator = _libs["mp3splt"].get("mp3splt_freedb_init_iterator", "cdecl")
    mp3splt_freedb_init_iterator.argtypes = [POINTER(splt_freedb_results)]
    mp3splt_freedb_init_iterator.restype = None

# /usr/include/libmp3splt/mp3splt.h: 1936
if _libs["mp3splt"].has("mp3splt_freedb_next", "cdecl"):
    mp3splt_freedb_next = _libs["mp3splt"].get("mp3splt_freedb_next", "cdecl")
    mp3splt_freedb_next.argtypes = [POINTER(splt_freedb_results)]
    mp3splt_freedb_next.restype = POINTER(splt_freedb_one_result)

# /usr/include/libmp3splt/mp3splt.h: 1942
if _libs["mp3splt"].has("mp3splt_freedb_get_id", "cdecl"):
    mp3splt_freedb_get_id = _libs["mp3splt"].get("mp3splt_freedb_get_id", "cdecl")
    mp3splt_freedb_get_id.argtypes = [POINTER(splt_freedb_one_result)]
    mp3splt_freedb_get_id.restype = c_int

# /usr/include/libmp3splt/mp3splt.h: 1947
if _libs["mp3splt"].has("mp3splt_freedb_get_name", "cdecl"):
    mp3splt_freedb_get_name = _libs["mp3splt"].get("mp3splt_freedb_get_name", "cdecl")
    mp3splt_freedb_get_name.argtypes = [POINTER(splt_freedb_one_result)]
    mp3splt_freedb_get_name.restype = c_char_p

# /usr/include/libmp3splt/mp3splt.h: 1952
if _libs["mp3splt"].has("mp3splt_freedb_get_number_of_revisions", "cdecl"):
    mp3splt_freedb_get_number_of_revisions = _libs["mp3splt"].get("mp3splt_freedb_get_number_of_revisions", "cdecl")
    mp3splt_freedb_get_number_of_revisions.argtypes = [POINTER(splt_freedb_one_result)]
    mp3splt_freedb_get_number_of_revisions.restype = c_int

# /usr/include/libmp3splt/mp3splt.h: 1970
if _libs["mp3splt"].has("mp3splt_write_freedb_file_result", "cdecl"):
    mp3splt_write_freedb_file_result = _libs["mp3splt"].get("mp3splt_write_freedb_file_result", "cdecl")
    mp3splt_write_freedb_file_result.argtypes = [POINTER(splt_state), c_int, String, c_int, String, c_int]
    mp3splt_write_freedb_file_result.restype = splt_code

enum_anon_27 = c_int# /usr/include/libmp3splt/mp3splt.h: 1989

CUE_EXPORT = 0# /usr/include/libmp3splt/mp3splt.h: 1989

splt_export_type = enum_anon_27# /usr/include/libmp3splt/mp3splt.h: 1989

# /usr/include/libmp3splt/mp3splt.h: 2001
if _libs["mp3splt"].has("mp3splt_export", "cdecl"):
    mp3splt_export = _libs["mp3splt"].get("mp3splt_export", "cdecl")
    mp3splt_export.argtypes = [POINTER(splt_state), splt_export_type, String, c_int]
    mp3splt_export.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 2020
class struct__splt_wrap(Structure):
    pass

splt_wrap = struct__splt_wrap# /usr/include/libmp3splt/mp3splt.h: 2020

# /usr/include/libmp3splt/mp3splt.h: 2028
class struct__splt_one_wrap(Structure):
    pass

splt_one_wrap = struct__splt_one_wrap# /usr/include/libmp3splt/mp3splt.h: 2028

# /usr/include/libmp3splt/mp3splt.h: 2041
if _libs["mp3splt"].has("mp3splt_get_wrap_files", "cdecl"):
    mp3splt_get_wrap_files = _libs["mp3splt"].get("mp3splt_get_wrap_files", "cdecl")
    mp3splt_get_wrap_files.argtypes = [POINTER(splt_state), POINTER(splt_code)]
    mp3splt_get_wrap_files.restype = POINTER(splt_wrap)

# /usr/include/libmp3splt/mp3splt.h: 2050
if _libs["mp3splt"].has("mp3splt_wrap_init_iterator", "cdecl"):
    mp3splt_wrap_init_iterator = _libs["mp3splt"].get("mp3splt_wrap_init_iterator", "cdecl")
    mp3splt_wrap_init_iterator.argtypes = [POINTER(splt_wrap)]
    mp3splt_wrap_init_iterator.restype = None

# /usr/include/libmp3splt/mp3splt.h: 2060
if _libs["mp3splt"].has("mp3splt_wrap_next", "cdecl"):
    mp3splt_wrap_next = _libs["mp3splt"].get("mp3splt_wrap_next", "cdecl")
    mp3splt_wrap_next.argtypes = [POINTER(splt_wrap)]
    mp3splt_wrap_next.restype = POINTER(splt_one_wrap)

# /usr/include/libmp3splt/mp3splt.h: 2065
if _libs["mp3splt"].has("mp3splt_wrap_get_wrapped_file", "cdecl"):
    mp3splt_wrap_get_wrapped_file = _libs["mp3splt"].get("mp3splt_wrap_get_wrapped_file", "cdecl")
    mp3splt_wrap_get_wrapped_file.argtypes = [POINTER(splt_one_wrap)]
    if sizeof(c_int) == sizeof(c_void_p):
        mp3splt_wrap_get_wrapped_file.restype = ReturnString
    else:
        mp3splt_wrap_get_wrapped_file.restype = String
        mp3splt_wrap_get_wrapped_file.errcheck = ReturnString

# /usr/include/libmp3splt/mp3splt.h: 2082
if _libs["mp3splt"].has("mp3splt_set_silence_points", "cdecl"):
    mp3splt_set_silence_points = _libs["mp3splt"].get("mp3splt_set_silence_points", "cdecl")
    mp3splt_set_silence_points.argtypes = [POINTER(splt_state), POINTER(splt_code)]
    mp3splt_set_silence_points.restype = c_int

# /usr/include/libmp3splt/mp3splt.h: 2090
if _libs["mp3splt"].has("mp3splt_set_trim_silence_points", "cdecl"):
    mp3splt_set_trim_silence_points = _libs["mp3splt"].get("mp3splt_set_trim_silence_points", "cdecl")
    mp3splt_set_trim_silence_points.argtypes = [POINTER(splt_state)]
    mp3splt_set_trim_silence_points.restype = splt_code

# /usr/include/libmp3splt/mp3splt.h: 2095
if _libs["mp3splt"].has("mp3splt_get_version", "cdecl"):
    mp3splt_get_version = _libs["mp3splt"].get("mp3splt_get_version", "cdecl")
    mp3splt_get_version.argtypes = []
    if sizeof(c_int) == sizeof(c_void_p):
        mp3splt_get_version.restype = ReturnString
    else:
        mp3splt_get_version.restype = String
        mp3splt_get_version.errcheck = ReturnString

# /usr/include/libmp3splt/mp3splt.h: 2107
if _libs["mp3splt"].has("mp3splt_check_if_directory", "cdecl"):
    mp3splt_check_if_directory = _libs["mp3splt"].get("mp3splt_check_if_directory", "cdecl")
    mp3splt_check_if_directory.argtypes = [String]
    mp3splt_check_if_directory.restype = c_int

# /usr/include/libmp3splt/mp3splt.h: 2152
class struct_anon_28(Structure):
    pass

struct_anon_28.__slots__ = [
    'version',
    'name',
    'extension',
    'upper_extension',
]
struct_anon_28._fields_ = [
    ('version', c_float),
    ('name', String),
    ('extension', String),
    ('upper_extension', String),
]

splt_plugin_info = struct_anon_28# /usr/include/libmp3splt/mp3splt.h: 2152

# /usr/include/libmp3splt/mp3splt.h: 2157
class struct__splt_original_tags(Structure):
    pass

splt_original_tags = struct__splt_original_tags# /usr/include/libmp3splt/mp3splt.h: 2157

# /usr/include/libmp3splt/mp3splt.h: 2313
class struct_anon_29(Structure):
    pass

struct_anon_29.__slots__ = [
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
struct_anon_29._fields_ = [
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

splt_plugin_func = struct_anon_29# /usr/include/libmp3splt/mp3splt.h: 2313

# /usr/include/libmp3splt/mp3splt.h: 90
try:
    SPLT_TRUE = 1
except:
    pass

# /usr/include/libmp3splt/mp3splt.h: 94
try:
    SPLT_FALSE = 0
except:
    pass

# /usr/include/libmp3splt/mp3splt.h: 804
try:
    SPLT_DEFAULT_PARAM_THRESHOLD = (-48.0)
except:
    pass

# /usr/include/libmp3splt/mp3splt.h: 808
try:
    SPLT_DEFAULT_PARAM_OFFSET = 0.8
except:
    pass

# /usr/include/libmp3splt/mp3splt.h: 812
try:
    SPLT_DEFAULT_PARAM_MINIMUM_LENGTH = 0.0
except:
    pass

# /usr/include/libmp3splt/mp3splt.h: 816
try:
    SPLT_DEFAULT_PARAM_MINIMUM_TRACK_LENGTH = 0.0
except:
    pass

# /usr/include/libmp3splt/mp3splt.h: 820
try:
    SPLT_DEFAULT_PARAM_MIN_TRACK_JOIN = 0.0
except:
    pass

# /usr/include/libmp3splt/mp3splt.h: 824
try:
    SPLT_DEFAULT_PARAM_GAP = 30
except:
    pass

# /usr/include/libmp3splt/mp3splt.h: 828
try:
    SPLT_DEFAULT_PARAM_TRACKS = 0
except:
    pass

# /usr/include/libmp3splt/mp3splt.h: 832
try:
    SPLT_DEFAULT_PARAM_SHOTS = 25
except:
    pass

# /usr/include/libmp3splt/mp3splt.h: 836
try:
    SPLT_DEFAULT_KEEP_SILENCE_LEFT = 0
except:
    pass

# /usr/include/libmp3splt/mp3splt.h: 840
try:
    SPLT_DEFAULT_KEEP_SILENCE_RIGHT = 0
except:
    pass

# /usr/include/libmp3splt/mp3splt.h: 868
try:
    SPLT_DEFAULT_OUTPUT = '@f_@mm_@ss_@h0h__@Mm_@Ss_@H0h'
except:
    pass

# /usr/include/libmp3splt/mp3splt.h: 874
try:
    SPLT_DEFAULT_CDDB_CUE_OUTPUT = '@A - @n - @t'
except:
    pass

# /usr/include/libmp3splt/mp3splt.h: 879
try:
    SPLT_DEFAULT_SYNCERROR_OUTPUT = '@f_error_@n'
except:
    pass

# /usr/include/libmp3splt/mp3splt.h: 884
try:
    SPLT_DEFAULT_SILENCE_OUTPUT = '@f_silence_@n'
except:
    pass

# /usr/include/libmp3splt/mp3splt.h: 889
try:
    SPLT_DEFAULT_TRIM_SILENCE_OUTPUT = '@f_trimmed'
except:
    pass

# /usr/include/libmp3splt/mp3splt.h: 1471
try:
    SPLT_UNDEFINED_GENRE = 'Other'
except:
    pass

# /usr/include/libmp3splt/mp3splt.h: 1477
try:
    SPLT_ID3V1_NUMBER_OF_GENRES = 127
except:
    pass

# /usr/include/libmp3splt/mp3splt.h: 1801
try:
    SPLT_FREEDB_SEARCH_TYPE_CDDB_CGI = 1
except:
    pass

# /usr/include/libmp3splt/mp3splt.h: 1808
try:
    SPLT_FREEDB_GET_FILE_TYPE_CDDB_CGI = 3
except:
    pass

# /usr/include/libmp3splt/mp3splt.h: 1815
try:
    SPLT_FREEDB_GET_FILE_TYPE_CDDB = 4
except:
    pass

# /usr/include/libmp3splt/mp3splt.h: 1823
try:
    SPLT_FREEDB_CDDB_CGI_PORT = 80
except:
    pass

# /usr/include/libmp3splt/mp3splt.h: 1832
try:
    SPLT_FREEDB2_CGI_SITE = 'tracktype.org/~cddb/cddb.cgi'
except:
    pass

# /usr/include/libmp3splt/mp3splt.h: 2117
try:
    SPLT_DIRCHAR = '/'
except:
    pass

# /usr/include/libmp3splt/mp3splt.h: 2121
try:
    SPLT_DIRSTR = '/'
except:
    pass

_splt_state = struct__splt_state# /usr/include/libmp3splt/mp3splt.h: 231

splt_progres = struct_splt_progres# /usr/include/libmp3splt/mp3splt.h: 1229

_splt_point = struct__splt_point# /usr/include/libmp3splt/mp3splt.h: 1333

_splt_points = struct__splt_points# /usr/include/libmp3splt/mp3splt.h: 1386

_splt_tags = struct__splt_tags# /usr/include/libmp3splt/mp3splt.h: 1512

_splt_tags_group = struct__splt_tags_group# /usr/include/libmp3splt/mp3splt.h: 1564

_splt_freedb_results = struct__splt_freedb_results# /usr/include/libmp3splt/mp3splt.h: 1842

_splt_freedb_one_result = struct__splt_freedb_one_result# /usr/include/libmp3splt/mp3splt.h: 1851

_splt_wrap = struct__splt_wrap# /usr/include/libmp3splt/mp3splt.h: 2020

_splt_one_wrap = struct__splt_one_wrap# /usr/include/libmp3splt/mp3splt.h: 2028

_splt_original_tags = struct__splt_original_tags# /usr/include/libmp3splt/mp3splt.h: 2157

# No inserted files

# No prefix-stripping

