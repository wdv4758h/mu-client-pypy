"""Annotation and rtyping support for the result of os.stat(), os.lstat()
and os.fstat().  In RPython like in plain Python the stat result can be
indexed like a tuple but also exposes the st_xxx attributes.
"""

import os, sys

from rpython.flowspace.model import Constant
from rpython.flowspace.operation import op
from rpython.annotator import model as annmodel
from rpython.rtyper import extregistry
from rpython.tool.pairtype import pairtype
from rpython.rtyper.tool import rffi_platform as platform
from rpython.rtyper.llannotation import lltype_to_annotation
from rpython.rtyper.rmodel import Repr
from rpython.rtyper.rint import IntegerRepr
from rpython.rtyper.error import TyperError

from rpython.rlib._os_support import _preferred_traits, string_traits
from rpython.rlib.objectmodel import specialize
from rpython.rtyper.lltypesystem import lltype, rffi
from rpython.translator.tool.cbuild import ExternalCompilationInfo
from rpython.rlib.rarithmetic import intmask
from rpython.rlib.rposix import (
    replace_os_function, handle_posix_error, _as_bytes0)

_WIN32 = sys.platform.startswith('win')
_LINUX = sys.platform.startswith('linux')

if _WIN32:
    from rpython.rlib import rwin32
    from rpython.rlib.rwin32file import make_win32_traits

# Support for float times is here.
# - ALL_STAT_FIELDS contains Float fields if the system can retrieve
#   sub-second timestamps.
# - TIMESPEC is defined when the "struct stat" contains st_atim field.

if sys.platform.startswith('linux') or sys.platform.startswith('openbsd'):
    TIMESPEC = platform.Struct('struct timespec',
                               [('tv_sec', rffi.TIME_T),
                                ('tv_nsec', rffi.LONG)])
else:
    TIMESPEC = None

# all possible fields - some of them are not available on all platforms
ALL_STAT_FIELDS = [
    ("st_mode",      lltype.Signed),
    ("st_ino",       lltype.SignedLongLong),
    ("st_dev",       lltype.SignedLongLong),
    ("st_nlink",     lltype.Signed),
    ("st_uid",       lltype.Signed),
    ("st_gid",       lltype.Signed),
    ("st_size",      lltype.SignedLongLong),
    ("st_atime",     lltype.Float),
    ("st_mtime",     lltype.Float),
    ("st_ctime",     lltype.Float),
    ("st_blksize",   lltype.Signed),
    ("st_blocks",    lltype.Signed),
    ("st_rdev",      lltype.Signed),
    ("st_flags",     lltype.Signed),
    #("st_gen",       lltype.Signed),     -- new in CPy 2.5, not implemented
    #("st_birthtime", lltype.Float),      -- new in CPy 2.5, not implemented
]
N_INDEXABLE_FIELDS = 10

# For OO backends, expose only the portable fields (the first 10).
PORTABLE_STAT_FIELDS = ALL_STAT_FIELDS[:N_INDEXABLE_FIELDS]

STATVFS_FIELDS = [
    ("f_bsize", lltype.Signed),
    ("f_frsize", lltype.Signed),
    ("f_blocks", lltype.Signed),
    ("f_bfree", lltype.Signed),
    ("f_bavail", lltype.Signed),
    ("f_files", lltype.Signed),
    ("f_ffree", lltype.Signed),
    ("f_favail", lltype.Signed),
    ("f_flag", lltype.Signed),
    ("f_namemax", lltype.Signed),
]


# ____________________________________________________________
#
# Annotation support

class SomeStatResult(annmodel.SomeObject):
    knowntype = os.stat_result

    def rtyper_makerepr(self, rtyper):
        return StatResultRepr(rtyper)

    def rtyper_makekey(self):
        return self.__class__,

    def getattr(self, s_attr):
        assert s_attr.is_constant(), "non-constant attr name in getattr()"
        attrname = s_attr.const
        TYPE = STAT_FIELD_TYPES[attrname]
        return lltype_to_annotation(TYPE)

    def _get_rmarshall_support_(self):     # for rlib.rmarshal
        # reduce and recreate stat_result objects from 10-tuples
        # (we ignore the extra values here for simplicity and portability)
        def stat_result_reduce(st):
            return (st[0], st[1], st[2], st[3], st[4],
                    st[5], st[6], st[7], st[8], st[9])

        def stat_result_recreate(tup):
            return make_stat_result(tup + extra_zeroes)
        s_reduced = annmodel.SomeTuple([lltype_to_annotation(TYPE)
                                       for name, TYPE in PORTABLE_STAT_FIELDS])
        extra_zeroes = (0,) * (len(STAT_FIELDS) - len(PORTABLE_STAT_FIELDS))
        return s_reduced, stat_result_reduce, stat_result_recreate


class __extend__(pairtype(SomeStatResult, annmodel.SomeInteger)):
    def getitem((s_sta, s_int)):
        assert s_int.is_constant(), "os.stat()[index]: index must be constant"
        index = s_int.const
        assert 0 <= index < N_INDEXABLE_FIELDS, "os.stat()[index] out of range"
        name, TYPE = STAT_FIELDS[index]
        return lltype_to_annotation(TYPE)


class StatResultRepr(Repr):

    def __init__(self, rtyper):
        self.rtyper = rtyper
        self.stat_field_indexes = {}
        for i, (name, TYPE) in enumerate(STAT_FIELDS):
            self.stat_field_indexes[name] = i

        self.s_tuple = annmodel.SomeTuple(
            [lltype_to_annotation(TYPE) for name, TYPE in STAT_FIELDS])
        self.r_tuple = rtyper.getrepr(self.s_tuple)
        self.lowleveltype = self.r_tuple.lowleveltype

    def redispatch_getfield(self, hop, index):
        rtyper = self.rtyper
        s_index = rtyper.annotator.bookkeeper.immutablevalue(index)
        hop2 = hop.copy()
        spaceop = op.getitem(hop.args_v[0], Constant(index))
        spaceop.result = hop.spaceop.result
        hop2.spaceop = spaceop
        hop2.args_v = spaceop.args
        hop2.args_s = [self.s_tuple, s_index]
        hop2.args_r = [self.r_tuple, rtyper.getrepr(s_index)]
        return hop2.dispatch()

    def rtype_getattr(self, hop):
        s_attr = hop.args_s[1]
        attr = s_attr.const
        try:
            index = self.stat_field_indexes[attr]
        except KeyError:
            raise TyperError("os.stat().%s: field not available" % (attr,))
        return self.redispatch_getfield(hop, index)


class __extend__(pairtype(StatResultRepr, IntegerRepr)):
    def rtype_getitem((r_sta, r_int), hop):
        s_int = hop.args_s[1]
        index = s_int.const
        return r_sta.redispatch_getfield(hop, index)

s_StatResult = SomeStatResult()

def make_stat_result(tup):
    """Turn a tuple into an os.stat_result object."""
    positional = tuple(
        lltype.cast_primitive(TYPE, value) for value, (name, TYPE) in
            zip(tup, STAT_FIELDS)[:N_INDEXABLE_FIELDS])
    kwds = {}
    for value, (name, TYPE) in zip(tup, STAT_FIELDS)[N_INDEXABLE_FIELDS:]:
        kwds[name] = lltype.cast_primitive(TYPE, value)
    return os.stat_result(positional, kwds)


class MakeStatResultEntry(extregistry.ExtRegistryEntry):
    _about_ = make_stat_result

    def compute_result_annotation(self, s_tup):
        return s_StatResult

    def specialize_call(self, hop):
        r_StatResult = hop.rtyper.getrepr(s_StatResult)
        [v_result] = hop.inputargs(r_StatResult.r_tuple)
        # no-op conversion from r_StatResult.r_tuple to r_StatResult
        hop.exception_cannot_occur()
        return v_result


class SomeStatvfsResult(annmodel.SomeObject):
    if hasattr(os, 'statvfs_result'):
        knowntype = os.statvfs_result
    else:
        knowntype = None # will not be used

    def rtyper_makerepr(self, rtyper):
        return StatvfsResultRepr(rtyper)

    def rtyper_makekey(self):
        return self.__class__,

    def getattr(self, s_attr):
        assert s_attr.is_constant()
        TYPE = STATVFS_FIELD_TYPES[s_attr.const]
        return lltype_to_annotation(TYPE)


class __extend__(pairtype(SomeStatvfsResult, annmodel.SomeInteger)):
    def getitem((s_stat, s_int)):
        assert s_int.is_constant()
        name, TYPE = STATVFS_FIELDS[s_int.const]
        return lltype_to_annotation(TYPE)


s_StatvfsResult = SomeStatvfsResult()


class StatvfsResultRepr(Repr):
    def __init__(self, rtyper):
        self.rtyper = rtyper
        self.statvfs_field_indexes = {}
        for i, (name, TYPE) in enumerate(STATVFS_FIELDS):
            self.statvfs_field_indexes[name] = i

        self.s_tuple = annmodel.SomeTuple(
            [lltype_to_annotation(TYPE) for name, TYPE in STATVFS_FIELDS])
        self.r_tuple = rtyper.getrepr(self.s_tuple)
        self.lowleveltype = self.r_tuple.lowleveltype

    def redispatch_getfield(self, hop, index):
        rtyper = self.rtyper
        s_index = rtyper.annotator.bookkeeper.immutablevalue(index)
        hop2 = hop.copy()
        spaceop = op.getitem(hop.args_v[0], Constant(index))
        spaceop.result = hop.spaceop.result
        hop2.spaceop = spaceop
        hop2.args_v = spaceop.args
        hop2.args_s = [self.s_tuple, s_index]
        hop2.args_r = [self.r_tuple, rtyper.getrepr(s_index)]
        return hop2.dispatch()

    def rtype_getattr(self, hop):
        s_attr = hop.args_s[1]
        attr = s_attr.const
        try:
            index = self.statvfs_field_indexes[attr]
        except KeyError:
            raise TyperError("os.statvfs().%s: field not available" % (attr,))
        return self.redispatch_getfield(hop, index)


class __extend__(pairtype(StatvfsResultRepr, IntegerRepr)):
    def rtype_getitem((r_sta, r_int), hop):
        s_int = hop.args_s[1]
        index = s_int.const
        return r_sta.redispatch_getfield(hop, index)


def make_statvfs_result(tup):
    args = tuple(
        lltype.cast_primitive(TYPE, value) for value, (name, TYPE) in
            zip(tup, STATVFS_FIELDS))
    return os.statvfs_result(args)

class MakeStatvfsResultEntry(extregistry.ExtRegistryEntry):
    _about_ = make_statvfs_result

    def compute_result_annotation(self, s_tup):
        return s_StatvfsResult

    def specialize_call(self, hop):
        r_StatvfsResult = hop.rtyper.getrepr(s_StatvfsResult)
        [v_result] = hop.inputargs(r_StatvfsResult.r_tuple)
        hop.exception_cannot_occur()
        return v_result

# ____________________________________________________________
#
# RFFI support

if sys.platform.startswith('win'):
    _name_struct_stat = '_stati64'
    INCLUDES = ['sys/types.h', 'sys/stat.h', 'sys/statvfs.h']
else:
    if _LINUX:
        _name_struct_stat = 'stat64'
    else:
        _name_struct_stat = 'stat'
    INCLUDES = ['sys/types.h', 'sys/stat.h', 'sys/statvfs.h', 'unistd.h']

compilation_info = ExternalCompilationInfo(
    # This must be set to 64 on some systems to enable large file support.
    #pre_include_bits = ['#define _FILE_OFFSET_BITS 64'],
    # ^^^ nowadays it's always set in all C files we produce.
    includes=INCLUDES
)

if TIMESPEC is not None:
    class CConfig_for_timespec:
        _compilation_info_ = compilation_info
        TIMESPEC = TIMESPEC
    TIMESPEC = lltype.Ptr(
        platform.configure(CConfig_for_timespec)['TIMESPEC'])


def posix_declaration(try_to_add=None):
    global STAT_STRUCT, STATVFS_STRUCT

    LL_STAT_FIELDS = STAT_FIELDS[:]
    if try_to_add:
        LL_STAT_FIELDS.append(try_to_add)

    if TIMESPEC is not None:

        def _expand(lst, originalname, timespecname):
            for i, (_name, _TYPE) in enumerate(lst):
                if _name == originalname:
                    # replace the 'st_atime' field of type rffi.DOUBLE
                    # with a field 'st_atim' of type 'struct timespec'
                    lst[i] = (timespecname, TIMESPEC.TO)
                    break

        _expand(LL_STAT_FIELDS, 'st_atime', 'st_atim')
        _expand(LL_STAT_FIELDS, 'st_mtime', 'st_mtim')
        _expand(LL_STAT_FIELDS, 'st_ctime', 'st_ctim')

        del _expand
    else:
        # Replace float fields with integers
        for name in ('st_atime', 'st_mtime', 'st_ctime', 'st_birthtime'):
            for i, (_name, _TYPE) in enumerate(LL_STAT_FIELDS):
                if _name == name:
                    LL_STAT_FIELDS[i] = (_name, lltype.Signed)
                    break

    class CConfig:
        _compilation_info_ = compilation_info
        STAT_STRUCT = platform.Struct('struct %s' % _name_struct_stat, LL_STAT_FIELDS)
        STATVFS_STRUCT = platform.Struct('struct statvfs', STATVFS_FIELDS)

    try:
        config = platform.configure(CConfig, ignore_errors=try_to_add is not None)
    except platform.CompilationError:
        if try_to_add:
            return    # failed to add this field, give up
        raise

    STAT_STRUCT = lltype.Ptr(config['STAT_STRUCT'])
    STATVFS_STRUCT = lltype.Ptr(config['STATVFS_STRUCT'])
    if try_to_add:
        STAT_FIELDS.append(try_to_add)


# This lists only the fields that have been found on the underlying platform.
# Initially only the PORTABLE_STAT_FIELDS, but more may be added by the
# following loop.
STAT_FIELDS = PORTABLE_STAT_FIELDS[:]

if sys.platform != 'win32':
    posix_declaration()
    for _i in range(len(PORTABLE_STAT_FIELDS), len(ALL_STAT_FIELDS)):
        posix_declaration(ALL_STAT_FIELDS[_i])
    del _i

# these two global vars only list the fields defined in the underlying platform
STAT_FIELD_TYPES = dict(STAT_FIELDS)      # {'st_xxx': TYPE}
STAT_FIELD_NAMES = [_name for (_name, _TYPE) in STAT_FIELDS]
del _name, _TYPE

STATVFS_FIELD_TYPES = dict(STATVFS_FIELDS)
STATVFS_FIELD_NAMES = [name for name, tp in STATVFS_FIELDS]

def build_stat_result(st):
    # only for LL backends
    if TIMESPEC is not None:
        atim = st.c_st_atim; atime = int(atim.c_tv_sec) + 1E-9 * int(atim.c_tv_nsec)
        mtim = st.c_st_mtim; mtime = int(mtim.c_tv_sec) + 1E-9 * int(mtim.c_tv_nsec)
        ctim = st.c_st_ctim; ctime = int(ctim.c_tv_sec) + 1E-9 * int(ctim.c_tv_nsec)
    else:
        atime = st.c_st_atime
        mtime = st.c_st_mtime
        ctime = st.c_st_ctime

    result = (st.c_st_mode,
              st.c_st_ino,
              st.c_st_dev,
              st.c_st_nlink,
              st.c_st_uid,
              st.c_st_gid,
              st.c_st_size,
              atime,
              mtime,
              ctime)

    if "st_blksize" in STAT_FIELD_TYPES: result += (st.c_st_blksize,)
    if "st_blocks"  in STAT_FIELD_TYPES: result += (st.c_st_blocks,)
    if "st_rdev"    in STAT_FIELD_TYPES: result += (st.c_st_rdev,)
    if "st_flags"   in STAT_FIELD_TYPES: result += (st.c_st_flags,)

    return make_stat_result(result)


def build_statvfs_result(st):
    return make_statvfs_result((
        st.c_f_bsize,
        st.c_f_frsize,
        st.c_f_blocks,
        st.c_f_bfree,
        st.c_f_bavail,
        st.c_f_files,
        st.c_f_ffree,
        st.c_f_favail,
        st.c_f_flag,
        st.c_f_namemax
    ))


# Implement and register os.stat() & variants

if not _WIN32:
  c_fstat = rffi.llexternal('fstat64' if _LINUX else 'fstat',
                            [rffi.INT, STAT_STRUCT], rffi.INT,
                            compilation_info=compilation_info,
                            save_err=rffi.RFFI_SAVE_ERRNO,
                            macro=True)
  c_stat = rffi.llexternal('stat64' if _LINUX else 'stat',
                           [rffi.CCHARP, STAT_STRUCT], rffi.INT,
                           compilation_info=compilation_info,
                           save_err=rffi.RFFI_SAVE_ERRNO,
                           macro=True)
  c_lstat = rffi.llexternal('lstat64' if _LINUX else 'lstat',
                            [rffi.CCHARP, STAT_STRUCT], rffi.INT,
                            compilation_info=compilation_info,
                            save_err=rffi.RFFI_SAVE_ERRNO,
                            macro=True)

  c_fstatvfs = rffi.llexternal('fstatvfs',
                               [rffi.INT, STATVFS_STRUCT], rffi.INT,
                               compilation_info=compilation_info,
                               save_err=rffi.RFFI_SAVE_ERRNO)
  c_statvfs = rffi.llexternal('statvfs',
                              [rffi.CCHARP, STATVFS_STRUCT], rffi.INT,
                              compilation_info=compilation_info,
                              save_err=rffi.RFFI_SAVE_ERRNO)

@replace_os_function('fstat')
def fstat(fd):
    if not _WIN32:
        with lltype.scoped_alloc(STAT_STRUCT.TO) as stresult:
            handle_posix_error('fstat', c_fstat(fd, stresult))
            return build_stat_result(stresult)
    else:
        handle = rwin32.get_osfhandle(fd)
        win32traits = make_win32_traits(string_traits)
        filetype = win32traits.GetFileType(handle)
        if filetype == win32traits.FILE_TYPE_CHAR:
            # console or LPT device
            return make_stat_result((win32traits._S_IFCHR,
                                     0, 0, 0, 0, 0,
                                     0, 0, 0, 0))
        elif filetype == win32traits.FILE_TYPE_PIPE:
            # socket or named pipe
            return make_stat_result((win32traits._S_IFIFO,
                                     0, 0, 0, 0, 0,
                                     0, 0, 0, 0))
        elif filetype == win32traits.FILE_TYPE_UNKNOWN:
            error = rwin32.GetLastError_saved()
            if error != 0:
                raise WindowsError(error, "os_fstat failed")
            # else: unknown but valid file

        # normal disk file (FILE_TYPE_DISK)
        info = lltype.malloc(win32traits.BY_HANDLE_FILE_INFORMATION,
                             flavor='raw', zero=True)
        try:
            res = win32traits.GetFileInformationByHandle(handle, info)
            if res == 0:
                raise WindowsError(rwin32.GetLastError_saved(),
                                   "os_fstat failed")
            return win32_by_handle_info_to_stat(win32traits, info)
        finally:
            lltype.free(info, flavor='raw')

@replace_os_function('stat')
@specialize.argtype(0)
def stat(path):
    if not _WIN32:
        with lltype.scoped_alloc(STAT_STRUCT.TO) as stresult:
            arg = _as_bytes0(path)
            handle_posix_error('stat', c_stat(arg, stresult))
            return build_stat_result(stresult)
    else:
        traits = _preferred_traits(path)
        path = traits.as_str0(path)
        return win32_xstat(traits, path, traverse=True)

@replace_os_function('lstat')
@specialize.argtype(0)
def lstat(path):
    if not _WIN32:
        with lltype.scoped_alloc(STAT_STRUCT.TO) as stresult:
            arg = _as_bytes0(path)
            handle_posix_error('lstat', c_lstat(arg, stresult))
            return build_stat_result(stresult)
    else:
        traits = _preferred_traits(path)
        path = traits.as_str0(path)
        return win32_xstat(traits, path, traverse=False)

@replace_os_function('fstatvfs')
def fstatvfs(fd):
    with lltype.scoped_alloc(STATVFS_STRUCT.TO) as stresult:
        handle_posix_error('fstatvfs', c_fstatvfs(fd, stresult))
        return build_statvfs_result(stresult)

@replace_os_function('statvfs')
@specialize.argtype(0)
def statvfs(path):
    with lltype.scoped_alloc(STATVFS_STRUCT.TO) as stresult:
        arg = _as_bytes0(path)
        handle_posix_error('statvfs', c_statvfs(arg, stresult))
        return build_statvfs_result(stresult)

#__________________________________________________
# Helper functions for win32
if _WIN32:
    from rpython.rlib.rwin32file import FILE_TIME_to_time_t_float

    def make_longlong(high, low):
        return (rffi.r_longlong(high) << 32) + rffi.r_longlong(low)

    # Seconds between 1.1.1601 and 1.1.1970
    secs_between_epochs = rffi.r_longlong(11644473600)

    @specialize.arg(0)
    def win32_xstat(traits, path, traverse=False):
        win32traits = make_win32_traits(traits)
        with lltype.scoped_alloc(
                win32traits.WIN32_FILE_ATTRIBUTE_DATA) as data:
            res = win32traits.GetFileAttributesEx(
                path, win32traits.GetFileExInfoStandard, data)
            if res == 0:
                errcode = rwin32.GetLastError_saved()
                if errcode == win32traits.ERROR_SHARING_VIOLATION:
                    res = win32_attributes_from_dir(
                        win32traits, path, data)
            if res == 0:
                errcode = rwin32.GetLastError_saved()
                raise WindowsError(errcode, "os_stat failed")
            return win32_attribute_data_to_stat(win32traits, data)

    @specialize.arg(0)
    def win32_attributes_to_mode(win32traits, attributes):
        m = 0
        attributes = intmask(attributes)
        if attributes & win32traits.FILE_ATTRIBUTE_DIRECTORY:
            m |= win32traits._S_IFDIR | 0111 # IFEXEC for user,group,other
        else:
            m |= win32traits._S_IFREG
        if attributes & win32traits.FILE_ATTRIBUTE_READONLY:
            m |= 0444
        else:
            m |= 0666
        return m

    @specialize.arg(0)
    def win32_attribute_data_to_stat(win32traits, info):
        st_mode = win32_attributes_to_mode(win32traits, info.c_dwFileAttributes)
        st_size = make_longlong(info.c_nFileSizeHigh, info.c_nFileSizeLow)
        ctime = FILE_TIME_to_time_t_float(info.c_ftCreationTime)
        mtime = FILE_TIME_to_time_t_float(info.c_ftLastWriteTime)
        atime = FILE_TIME_to_time_t_float(info.c_ftLastAccessTime)

        result = (st_mode,
                  0, 0, 0, 0, 0,
                  st_size,
                  atime, mtime, ctime)

        return make_stat_result(result)

    def win32_by_handle_info_to_stat(win32traits, info):
        # similar to the one above
        st_mode = win32_attributes_to_mode(win32traits, info.c_dwFileAttributes)
        st_size = make_longlong(info.c_nFileSizeHigh, info.c_nFileSizeLow)
        ctime = FILE_TIME_to_time_t_float(info.c_ftCreationTime)
        mtime = FILE_TIME_to_time_t_float(info.c_ftLastWriteTime)
        atime = FILE_TIME_to_time_t_float(info.c_ftLastAccessTime)

        # specific to fstat()
        st_ino = make_longlong(info.c_nFileIndexHigh, info.c_nFileIndexLow)
        st_nlink = info.c_nNumberOfLinks

        result = (st_mode,
                  st_ino, 0, st_nlink, 0, 0,
                  st_size,
                  atime, mtime, ctime)

        return make_stat_result(result)

    @specialize.arg(0)
    def win32_attributes_from_dir(win32traits, path, data):
        filedata = lltype.malloc(win32traits.WIN32_FIND_DATA, flavor='raw')
        try:
            hFindFile = win32traits.FindFirstFile(path, filedata)
            if hFindFile == rwin32.INVALID_HANDLE_VALUE:
                return 0
            win32traits.FindClose(hFindFile)
            data.c_dwFileAttributes = filedata.c_dwFileAttributes
            rffi.structcopy(data.c_ftCreationTime, filedata.c_ftCreationTime)
            rffi.structcopy(data.c_ftLastAccessTime, filedata.c_ftLastAccessTime)
            rffi.structcopy(data.c_ftLastWriteTime, filedata.c_ftLastWriteTime)
            data.c_nFileSizeHigh    = filedata.c_nFileSizeHigh
            data.c_nFileSizeLow     = filedata.c_nFileSizeLow
            return 1
        finally:
            lltype.free(filedata, flavor='raw')

