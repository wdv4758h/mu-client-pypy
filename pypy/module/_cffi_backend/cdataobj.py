import operator

from pypy.interpreter.baseobjspace import W_Root
from pypy.interpreter.error import OperationError, oefmt
from pypy.interpreter.gateway import interp2app
from pypy.interpreter.typedef import TypeDef, make_weakref_descr

from rpython.rlib import rgc
from rpython.rlib.objectmodel import keepalive_until_here, specialize
from rpython.rtyper.lltypesystem import lltype, rffi
from rpython.tool.sourcetools import func_with_new_name

from pypy.module._cffi_backend import misc


class W_CData(W_Root):
    _attrs_ = ['space', '_ptr', 'ctype', '_lifeline_']
    _immutable_fields_ = ['_ptr', 'ctype']
    _ptr = lltype.nullptr(rffi.CCHARP.TO)

    def __init__(self, space, ptr, ctype):
        from pypy.module._cffi_backend import ctypeobj
        assert lltype.typeOf(ptr) == rffi.CCHARP
        assert isinstance(ctype, ctypeobj.W_CType)
        self.space = space
        self._ptr = ptr    # don't access directly!  use "with cdata as ptr:"
        self.ctype = ctype

    def __enter__(self):
        """Use 'with cdata as ptr:' to access the raw memory.  It will
        stay alive at least until the end of the 'with' block.
        """
        return self._ptr

    def __exit__(self, *args):
        keepalive_until_here(self)

    def unsafe_escaping_ptr(self):
        """Generally unsafe: escape the pointer to raw memory.
        If 'self' is a subclass that frees the pointer in a destructor,
        it may be freed under your feet at any time.
        """
        return self._ptr

    def _repr_extra(self):
        with self as ptr:
            extra = self.ctype.extra_repr(ptr)
        return extra

    def _repr_extra_owning(self):
        from pypy.module._cffi_backend.ctypeptr import W_CTypePointer
        ctype = self.ctype
        if isinstance(ctype, W_CTypePointer):
            num_bytes = ctype.ctitem.size
        else:
            num_bytes = self._sizeof()
        return 'owning %d bytes' % num_bytes

    def repr(self):
        extra2 = self._repr_extra()
        extra1 = ''
        if not isinstance(self, W_CDataNewOwning):
            # it's slightly confusing to get "<cdata 'struct foo' 0x...>"
            # because the struct foo is not owned.  Trying to make it
            # clearer, write in this case "<cdata 'struct foo &' 0x...>".
            from pypy.module._cffi_backend import ctypestruct
            if isinstance(self.ctype, ctypestruct.W_CTypeStructOrUnion):
                extra1 = ' &'
        return self.space.wrap("<cdata '%s%s' %s>" % (
            self.ctype.name, extra1, extra2))

    def nonzero(self):
        with self as ptr:
            nonzero = bool(ptr)
        return self.space.wrap(nonzero)

    def int(self, space):
        with self as ptr:
            w_result = self.ctype.cast_to_int(ptr)
        return w_result

    def long(self, space):
        w_result = self.int(space)
        space = self.space
        if space.is_w(space.type(w_result), space.w_int):
            w_result = space.newlong(space.int_w(w_result))
        return w_result

    def float(self):
        with self as ptr:
            w_result = self.ctype.float(ptr)
        return w_result

    def len(self):
        from pypy.module._cffi_backend import ctypearray
        space = self.space
        if isinstance(self.ctype, ctypearray.W_CTypeArray):
            return space.wrap(self.get_array_length())
        raise oefmt(space.w_TypeError,
                    "cdata of type '%s' has no len()", self.ctype.name)

    def _make_comparison(name):
        op = getattr(operator, name)
        requires_ordering = name not in ('eq', 'ne')
        #
        def _cmp(self, w_other):
            from pypy.module._cffi_backend.ctypeprim import W_CTypePrimitive
            space = self.space
            if not isinstance(w_other, W_CData):
                return space.w_NotImplemented

            with self as ptr1, w_other as ptr2:
                if requires_ordering:
                    if (isinstance(self.ctype, W_CTypePrimitive) or
                        isinstance(w_other.ctype, W_CTypePrimitive)):
                        raise OperationError(space.w_TypeError, space.wrap(
                            "cannot do comparison on a primitive cdata"))
                    ptr1 = rffi.cast(lltype.Unsigned, ptr1)
                    ptr2 = rffi.cast(lltype.Unsigned, ptr2)
                result = op(ptr1, ptr2)
            return space.newbool(result)
        #
        return func_with_new_name(_cmp, name)

    lt = _make_comparison('lt')
    le = _make_comparison('le')
    eq = _make_comparison('eq')
    ne = _make_comparison('ne')
    gt = _make_comparison('gt')
    ge = _make_comparison('ge')

    def hash(self):
        ptr = self.unsafe_escaping_ptr()
        h = rffi.cast(lltype.Signed, ptr)
        # To hash pointers in dictionaries.  Assumes that h shows some
        # alignment (to 4, 8, maybe 16 bytes), so we use the following
        # formula to avoid the trailing bits being always 0.
        h = h ^ (h >> 4)
        return self.space.wrap(h)

    def getitem(self, w_index):
        space = self.space
        if space.isinstance_w(w_index, space.w_slice):
            w_o = self._do_getslice(w_index)
        else:
            i = space.getindex_w(w_index, space.w_IndexError)
            ctype = self.ctype._check_subscript_index(self, i)
            w_o = self._do_getitem(ctype, i)
        return w_o

    def _do_getitem(self, ctype, i):
        ctitem = ctype.ctitem
        with self as ptr:
            return ctitem.convert_to_object(
                rffi.ptradd(ptr, i * ctitem.size))

    def setitem(self, w_index, w_value):
        space = self.space
        if space.isinstance_w(w_index, space.w_slice):
            with self as ptr:
                self._do_setslice(w_index, w_value, ptr)
        else:
            i = space.getindex_w(w_index, space.w_IndexError)
            ctype = self.ctype._check_subscript_index(self, i)
            ctitem = ctype.ctitem
            with self as ptr:
                ctitem.convert_from_object(
                    rffi.ptradd(ptr, i * ctitem.size),
                    w_value)

    def _do_getslicearg(self, w_slice):
        from pypy.module._cffi_backend.ctypeptr import W_CTypePointer
        from pypy.objspace.std.sliceobject import W_SliceObject
        assert isinstance(w_slice, W_SliceObject)
        space = self.space
        #
        if space.is_w(w_slice.w_start, space.w_None):
            raise OperationError(space.w_IndexError,
                                 space.wrap("slice start must be specified"))
        start = space.int_w(w_slice.w_start)
        #
        if space.is_w(w_slice.w_stop, space.w_None):
            raise OperationError(space.w_IndexError,
                                 space.wrap("slice stop must be specified"))
        stop = space.int_w(w_slice.w_stop)
        #
        if not space.is_w(w_slice.w_step, space.w_None):
            raise OperationError(space.w_IndexError,
                                 space.wrap("slice with step not supported"))
        #
        if start > stop:
            raise OperationError(space.w_IndexError,
                                 space.wrap("slice start > stop"))
        #
        ctype = self.ctype._check_slice_index(self, start, stop)
        assert isinstance(ctype, W_CTypePointer)
        #
        return ctype, start, stop - start

    def _do_getslice(self, w_slice):
        ctptr, start, length = self._do_getslicearg(w_slice)
        #
        space = self.space
        ctarray = ctptr.cache_array_type
        if ctarray is None:
            from pypy.module._cffi_backend import newtype
            ctarray = newtype.new_array_type(space, ctptr, space.w_None)
            ctptr.cache_array_type = ctarray
        #
        ptr = self.unsafe_escaping_ptr()
        ptr = rffi.ptradd(ptr, start * ctarray.ctitem.size)
        return W_CDataSliced(space, ptr, ctarray, length)

    def _do_setslice(self, w_slice, w_value, ptr):
        ctptr, start, length = self._do_getslicearg(w_slice)
        ctitem = ctptr.ctitem
        ctitemsize = ctitem.size
        target = rffi.ptradd(ptr, start * ctitemsize)
        #
        if isinstance(w_value, W_CData):
            from pypy.module._cffi_backend import ctypearray
            ctv = w_value.ctype
            if (isinstance(ctv, ctypearray.W_CTypeArray) and
                ctv.ctitem is ctitem and
                w_value.get_array_length() == length):
                # fast path: copying from exactly the correct type
                with w_value as source:
                    rffi.c_memcpy(target, source, ctitemsize * length)
                return
        #
        # A fast path for <char[]>[0:N] = "somestring".
        from pypy.module._cffi_backend import ctypeprim
        space = self.space
        if (space.isinstance_w(w_value, space.w_str) and
                isinstance(ctitem, ctypeprim.W_CTypePrimitiveChar)):
            from rpython.rtyper.annlowlevel import llstr
            from rpython.rtyper.lltypesystem.rstr import copy_string_to_raw
            value = space.str_w(w_value)
            if len(value) != length:
                raise oefmt(space.w_ValueError,
                            "need a string of length %d, got %d",
                            length, len(value))
            copy_string_to_raw(llstr(value), target, 0, length)
            return
        #
        w_iter = space.iter(w_value)
        for i in range(length):
            try:
                w_item = space.next(w_iter)
            except OperationError, e:
                if not e.match(space, space.w_StopIteration):
                    raise
                raise oefmt(space.w_ValueError,
                            "need %d values to unpack, got %d", length, i)
            ctitem.convert_from_object(target, w_item)
            target = rffi.ptradd(target, ctitemsize)
        try:
            space.next(w_iter)
        except OperationError, e:
            if not e.match(space, space.w_StopIteration):
                raise
        else:
            raise oefmt(space.w_ValueError,
                        "got more than %d values to unpack", length)

    def _add_or_sub(self, w_other, sign):
        space = self.space
        i = sign * space.getindex_w(w_other, space.w_OverflowError)
        ptr = self.unsafe_escaping_ptr()
        return self.ctype.add(ptr, i)

    def add(self, w_other):
        return self._add_or_sub(w_other, +1)

    def sub(self, w_other):
        space = self.space
        if isinstance(w_other, W_CData):
            from pypy.module._cffi_backend import ctypeptr, ctypearray
            ct = w_other.ctype
            if isinstance(ct, ctypearray.W_CTypeArray):
                ct = ct.ctptr
            #
            if (ct is not self.ctype or
                   not isinstance(ct, ctypeptr.W_CTypePointer) or
                   (ct.ctitem.size <= 0 and not ct.is_void_ptr)):
                raise oefmt(space.w_TypeError,
                            "cannot subtract cdata '%s' and cdata '%s'",
                            self.ctype.name, ct.name)
            #
            itemsize = ct.ctitem.size
            if itemsize <= 0:
                itemsize = 1
            with self as ptr1, w_other as ptr2:
                diff = (rffi.cast(lltype.Signed, ptr1) -
                        rffi.cast(lltype.Signed, ptr2)) // itemsize
            return space.wrap(diff)
        #
        return self._add_or_sub(w_other, -1)

    def getcfield(self, w_attr):
        return self.ctype.getcfield(self.space.str_w(w_attr))

    def getattr(self, w_attr):
        cfield = self.getcfield(w_attr)
        with self as ptr:
            w_res = cfield.read(ptr)
        return w_res

    def setattr(self, w_attr, w_value):
        cfield = self.getcfield(w_attr)
        with self as ptr:
            cfield.write(ptr, w_value)

    def call(self, args_w):
        with self as ptr:
            w_result = self.ctype.call(ptr, args_w)
        return w_result

    def iter(self):
        return self.ctype.iter(self)

    def unpackiterable_int(self, space):
        from pypy.module._cffi_backend import ctypearray
        ctype = self.ctype
        if isinstance(ctype, ctypearray.W_CTypeArray):
            return ctype.ctitem.unpack_list_of_int_items(self)
        return None

    def unpackiterable_float(self, space):
        from pypy.module._cffi_backend import ctypearray
        ctype = self.ctype
        if isinstance(ctype, ctypearray.W_CTypeArray):
            return ctype.ctitem.unpack_list_of_float_items(self)
        return None

    @specialize.argtype(1)
    def write_raw_signed_data(self, source):
        with self as ptr:
            misc.write_raw_signed_data(ptr, source, self.ctype.size)

    @specialize.argtype(1)
    def write_raw_unsigned_data(self, source):
        with self as ptr:
            misc.write_raw_unsigned_data(ptr, source, self.ctype.size)

    def write_raw_float_data(self, source):
        with self as ptr:
            misc.write_raw_float_data(ptr, source, self.ctype.size)

    def convert_to_object(self):
        with self as ptr:
            w_obj = self.ctype.convert_to_object(ptr)
        return w_obj

    def get_array_length(self):
        from pypy.module._cffi_backend import ctypearray
        ctype = self.ctype
        assert isinstance(ctype, ctypearray.W_CTypeArray)
        length = ctype.length
        assert length >= 0
        return length

    def _sizeof(self):
        return self.ctype.size

    def with_gc(self, w_destructor):
        with self as ptr:
            return W_CDataGCP(self.space, ptr, self.ctype, self, w_destructor)


class W_CDataMem(W_CData):
    """This is used only by the results of cffi.cast('int', x)
    or other primitive explicitly-casted types."""
    _attrs_ = []

    def __init__(self, space, ctype):
        cdata = lltype.malloc(rffi.CCHARP.TO, ctype.size, flavor='raw',
                              zero=False)
        W_CData.__init__(self, space, cdata, ctype)

    @rgc.must_be_light_finalizer
    def __del__(self):
        lltype.free(self._ptr, flavor='raw')


class W_CDataNewOwning(W_CData):
    """This is the abstract base class used for cdata objects created
    by newp().  They create and free their own memory according to an
    allocator."""

    # the 'length' is either >= 0 for arrays, or -1 for pointers.
    _attrs_ = ['length']
    _immutable_fields_ = ['length']

    def __init__(self, space, cdata, ctype, length=-1):
        W_CData.__init__(self, space, cdata, ctype)
        self.length = length

    def _repr_extra(self):
        return self._repr_extra_owning()

    def _sizeof(self):
        ctype = self.ctype
        if self.length >= 0:
            from pypy.module._cffi_backend import ctypearray
            assert isinstance(ctype, ctypearray.W_CTypeArray)
            return self.length * ctype.ctitem.size
        else:
            return ctype.size

    def get_array_length(self):
        return self.length


class W_CDataNewStd(W_CDataNewOwning):
    """Subclass using the standard allocator, lltype.malloc()/lltype.free()"""
    _attrs_ = []

    @rgc.must_be_light_finalizer
    def __del__(self):
        lltype.free(self._ptr, flavor='raw')


class W_CDataNewNonStdNoFree(W_CDataNewOwning):
    """Subclass using a non-standard allocator, no free()"""
    _attrs_ = ['w_raw_cdata']

class W_CDataNewNonStdFree(W_CDataNewNonStdNoFree):
    """Subclass using a non-standard allocator, with a free()"""
    _attrs_ = ['w_free']

    def __del__(self):
        self.clear_all_weakrefs()
        self.enqueue_for_destruction(self.space,
                                     W_CDataNewNonStdFree.call_destructor,
                                     'destructor of ')

    def call_destructor(self):
        assert isinstance(self, W_CDataNewNonStdFree)
        self.space.call_function(self.w_free, self.w_raw_cdata)


class W_CDataPtrToStructOrUnion(W_CData):
    """This subclass is used for the pointer returned by new('struct foo *').
    It has a strong reference to a W_CDataNewOwning that really owns the
    struct, which is the object returned by the app-level expression 'p[0]'.
    But it is not itself owning any memory, although its repr says so;
    it is merely a co-owner."""
    _attrs_ = ['structobj']
    _immutable_fields_ = ['structobj']

    def __init__(self, space, cdata, ctype, structobj):
        W_CData.__init__(self, space, cdata, ctype)
        self.structobj = structobj

    def _repr_extra(self):
        return self._repr_extra_owning()

    def _do_getitem(self, ctype, i):
        assert i == 0
        return self.structobj


class W_CDataSliced(W_CData):
    """Subclass with an explicit length, for slices."""
    _attrs_ = ['length']
    _immutable_fields_ = ['length']

    def __init__(self, space, cdata, ctype, length):
        W_CData.__init__(self, space, cdata, ctype)
        self.length = length

    def _repr_extra(self):
        return "sliced length %d" % (self.length,)

    def get_array_length(self):
        return self.length

    def _sizeof(self):
        from pypy.module._cffi_backend.ctypeptr import W_CTypePtrOrArray
        ctype = self.ctype
        assert isinstance(ctype, W_CTypePtrOrArray)
        return self.length * ctype.ctitem.size


class W_CDataHandle(W_CData):
    _attrs_ = ['w_keepalive']
    _immutable_fields_ = ['w_keepalive']

    def __init__(self, space, cdata, ctype, w_keepalive):
        W_CData.__init__(self, space, cdata, ctype)
        self.w_keepalive = w_keepalive

    def _repr_extra(self):
        w_repr = self.space.repr(self.w_keepalive)
        return "handle to %s" % (self.space.str_w(w_repr),)


class W_CDataFromBuffer(W_CData):
    _attrs_ = ['buf', 'length', 'w_keepalive']
    _immutable_fields_ = ['buf', 'length', 'w_keepalive']

    def __init__(self, space, cdata, ctype, buf, w_object):
        W_CData.__init__(self, space, cdata, ctype)
        self.buf = buf
        self.length = buf.getlength()
        self.w_keepalive = w_object

    def get_array_length(self):
        return self.length

    def _repr_extra(self):
        w_repr = self.space.repr(self.w_keepalive)
        return "buffer len %d from '%s' object" % (
            self.length, self.space.type(self.w_keepalive).name)


class W_CDataGCP(W_CData):
    """For ffi.gc()."""
    _attrs_ = ['w_original_cdata', 'w_destructor']
    _immutable_fields_ = ['w_original_cdata', 'w_destructor']

    def __init__(self, space, cdata, ctype, w_original_cdata, w_destructor):
        W_CData.__init__(self, space, cdata, ctype)
        self.w_original_cdata = w_original_cdata
        self.w_destructor = w_destructor

    def __del__(self):
        self.clear_all_weakrefs()
        self.enqueue_for_destruction(self.space, W_CDataGCP.call_destructor,
                                     'destructor of ')

    def call_destructor(self):
        assert isinstance(self, W_CDataGCP)
        self.space.call_function(self.w_destructor, self.w_original_cdata)


W_CData.typedef = TypeDef(
    '_cffi_backend.CData',
    __module__ = '_cffi_backend',
    __name__ = '<cdata>',
    __repr__ = interp2app(W_CData.repr),
    __nonzero__ = interp2app(W_CData.nonzero),
    __int__ = interp2app(W_CData.int),
    __long__ = interp2app(W_CData.long),
    __float__ = interp2app(W_CData.float),
    __len__ = interp2app(W_CData.len),
    __lt__ = interp2app(W_CData.lt),
    __le__ = interp2app(W_CData.le),
    __eq__ = interp2app(W_CData.eq),
    __ne__ = interp2app(W_CData.ne),
    __gt__ = interp2app(W_CData.gt),
    __ge__ = interp2app(W_CData.ge),
    __hash__ = interp2app(W_CData.hash),
    __getitem__ = interp2app(W_CData.getitem),
    __setitem__ = interp2app(W_CData.setitem),
    __add__ = interp2app(W_CData.add),
    __radd__ = interp2app(W_CData.add),
    __sub__ = interp2app(W_CData.sub),
    __getattr__ = interp2app(W_CData.getattr),
    __setattr__ = interp2app(W_CData.setattr),
    __call__ = interp2app(W_CData.call),
    __iter__ = interp2app(W_CData.iter),
    __weakref__ = make_weakref_descr(W_CData),
    )
W_CData.typedef.acceptable_as_base_class = False
