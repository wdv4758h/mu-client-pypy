import os

from rpython.rlib import jit
from rpython.rlib.objectmodel import specialize
from rpython.rlib.rstring import rsplit
from rpython.rtyper.annlowlevel import llhelper
from rpython.rtyper.lltypesystem import rffi, lltype

from pypy.interpreter.baseobjspace import W_Root, DescrMismatch
from pypy.interpreter.error import OperationError
from pypy.interpreter.typedef import GetSetProperty
from pypy.module.__builtin__.abstractinst import abstract_issubclass_w
from pypy.module.cpyext import structmemberdefs
from pypy.module.cpyext.api import (
    cpython_api, cpython_struct, bootstrap_function, Py_ssize_t, Py_ssize_tP,
    generic_cpy_call, Py_TPFLAGS_READY, Py_TPFLAGS_READYING,
    Py_TPFLAGS_HEAPTYPE, METH_VARARGS, METH_KEYWORDS, CANNOT_FAIL,
    Py_TPFLAGS_HAVE_GETCHARBUFFER, build_type_checkers, StaticObjectBuilder)
from pypy.module.cpyext.methodobject import (
    PyDescr_NewWrapper, PyCFunction_NewEx, PyCFunction_typedef)
from pypy.module.cpyext.modsupport import convert_method_defs
from pypy.module.cpyext.pyobject import (
    PyObject, make_ref, create_ref, from_ref, get_typedescr, make_typedescr,
    track_reference, Py_DecRef, as_pyobj)
from pypy.module.cpyext.slotdefs import (
    slotdefs_for_tp_slots, slotdefs_for_wrappers, get_slot_tp_function)
from pypy.module.cpyext.state import State
from pypy.module.cpyext.structmember import PyMember_GetOne, PyMember_SetOne
from pypy.module.cpyext.typeobjectdefs import (
    PyTypeObjectPtr, PyTypeObject, PyGetSetDef, PyMemberDef, newfunc,
    PyNumberMethods, PyMappingMethods, PySequenceMethods, PyBufferProcs)
from pypy.objspace.std.typeobject import W_TypeObject, find_best_base


WARN_ABOUT_MISSING_SLOT_FUNCTIONS = False

PyType_Check, PyType_CheckExact = build_type_checkers("Type", "w_type")

PyHeapTypeObjectStruct = lltype.ForwardReference()
PyHeapTypeObject = lltype.Ptr(PyHeapTypeObjectStruct)
PyHeapTypeObjectFields = (
    ("ht_type", PyTypeObject),
    ("ht_name", PyObject),
    ("as_number", PyNumberMethods),
    ("as_mapping", PyMappingMethods),
    ("as_sequence", PySequenceMethods),
    ("as_buffer", PyBufferProcs),
    )
cpython_struct("PyHeapTypeObject", PyHeapTypeObjectFields, PyHeapTypeObjectStruct,
               level=2)

class W_GetSetPropertyEx(GetSetProperty):
    def __init__(self, getset, w_type):
        self.getset = getset
        self.name = rffi.charp2str(getset.c_name)
        self.w_type = w_type
        doc = set = get = None
        if doc:
            doc = rffi.charp2str(getset.c_doc)
        if getset.c_get:
            get = GettersAndSetters.getter.im_func
        if getset.c_set:
            set = GettersAndSetters.setter.im_func
        GetSetProperty.__init__(self, get, set, None, doc,
                                cls=None, use_closure=True,
                                tag="cpyext_1")

def PyDescr_NewGetSet(space, getset, w_type):
    return space.wrap(W_GetSetPropertyEx(getset, w_type))

class W_MemberDescr(GetSetProperty):
    def __init__(self, member, w_type):
        self.member = member
        self.name = rffi.charp2str(member.c_name)
        self.w_type = w_type
        flags = rffi.cast(lltype.Signed, member.c_flags)
        doc = set = None
        if member.c_doc:
            doc = rffi.charp2str(member.c_doc)
        get = GettersAndSetters.member_getter.im_func
        del_ = GettersAndSetters.member_delete.im_func
        if not (flags & structmemberdefs.READONLY):
            set = GettersAndSetters.member_setter.im_func
        GetSetProperty.__init__(self, get, set, del_, doc,
                                cls=None, use_closure=True,
                                tag="cpyext_2")

def convert_getset_defs(space, dict_w, getsets, w_type):
    getsets = rffi.cast(rffi.CArrayPtr(PyGetSetDef), getsets)
    if getsets:
        i = -1
        while True:
            i = i + 1
            getset = getsets[i]
            name = getset.c_name
            if not name:
                break
            name = rffi.charp2str(name)
            w_descr = PyDescr_NewGetSet(space, getset, w_type)
            dict_w[name] = w_descr

def convert_member_defs(space, dict_w, members, w_type):
    members = rffi.cast(rffi.CArrayPtr(PyMemberDef), members)
    if members:
        i = 0
        while True:
            member = members[i]
            name = member.c_name
            if not name:
                break
            name = rffi.charp2str(name)
            w_descr = space.wrap(W_MemberDescr(member, w_type))
            dict_w[name] = w_descr
            i += 1

def update_all_slots(space, w_type, pto):
    #  XXX fill slots in pto

    typedef = w_type.layout.typedef
    for method_name, slot_name, slot_names, slot_func in slotdefs_for_tp_slots:
        w_descr = w_type.lookup(method_name)
        if w_descr is None:
            # XXX special case iternext
            continue

        slot_func_helper = None

        if slot_func is None and typedef is not None:
            get_slot = get_slot_tp_function(space, typedef, slot_name)
            if get_slot:
                slot_func_helper = get_slot()
        elif slot_func:
            slot_func_helper = llhelper(slot_func.api_func.functype,
                                        slot_func.api_func.get_wrapper(space))

        if slot_func_helper is None:
            if WARN_ABOUT_MISSING_SLOT_FUNCTIONS:
                os.write(2, method_name + " defined by the type but no slot function defined!\n")
            continue

        # XXX special case wrapper-functions and use a "specific" slot func

        if len(slot_names) == 1:
            setattr(pto, slot_names[0], slot_func_helper)
        else:
            assert len(slot_names) == 2
            struct = getattr(pto, slot_names[0])
            if not struct:
                #assert not space.config.translating
                assert not pto.c_tp_flags & Py_TPFLAGS_HEAPTYPE
                if slot_names[0] == 'c_tp_as_number':
                    STRUCT_TYPE = PyNumberMethods
                elif slot_names[0] == 'c_tp_as_sequence':
                    STRUCT_TYPE = PySequenceMethods
                else:
                    raise AssertionError(
                        "Structure not allocated: %s" % (slot_names[0],))
                struct = lltype.malloc(STRUCT_TYPE, flavor='raw', zero=True)
                setattr(pto, slot_names[0], struct)

            setattr(struct, slot_names[1], slot_func_helper)

def add_operators(space, dict_w, pto):
    # XXX support PyObject_HashNotImplemented
    for method_name, slot_names, wrapper_func, wrapper_func_kwds, doc in slotdefs_for_wrappers:
        if method_name in dict_w:
            continue
        if len(slot_names) == 1:
            func = getattr(pto, slot_names[0])
        else:
            assert len(slot_names) == 2
            struct = getattr(pto, slot_names[0])
            if not struct:
                continue
            func = getattr(struct, slot_names[1])
        func_voidp = rffi.cast(rffi.VOIDP, func)
        if not func:
            continue
        if wrapper_func is None and wrapper_func_kwds is None:
            continue
        dict_w[method_name] = PyDescr_NewWrapper(space, pto, method_name, wrapper_func,
                wrapper_func_kwds, doc, func_voidp)
    if pto.c_tp_new:
        add_tp_new_wrapper(space, dict_w, pto)

@cpython_api([PyObject, PyObject, PyObject], PyObject, header=None)
def tp_new_wrapper(space, self, w_args, w_kwds):
    tp_new = rffi.cast(PyTypeObjectPtr, self).c_tp_new

    # Check that the user doesn't do something silly and unsafe like
    # object.__new__(dict).  To do this, we check that the most
    # derived base that's not a heap type is this type.
    # XXX do it

    args_w = space.fixedview(w_args)
    w_subtype = args_w[0]
    w_args = space.newtuple(args_w[1:])

    subtype = rffi.cast(PyTypeObjectPtr, make_ref(space, w_subtype))
    try:
        w_obj = generic_cpy_call(space, tp_new, subtype, w_args, w_kwds)
    finally:
        Py_DecRef(space, w_subtype)
    return w_obj

@specialize.memo()
def get_new_method_def(space):
    state = space.fromcache(State)
    if state.new_method_def:
        return state.new_method_def
    from pypy.module.cpyext.modsupport import PyMethodDef
    ptr = lltype.malloc(PyMethodDef, flavor="raw", zero=True,
                        immortal=True)
    ptr.c_ml_name = rffi.str2charp("__new__")
    lltype.render_immortal(ptr.c_ml_name)
    rffi.setintfield(ptr, 'c_ml_flags', METH_VARARGS | METH_KEYWORDS)
    ptr.c_ml_doc = rffi.str2charp(
        "T.__new__(S, ...) -> a new object with type S, a subtype of T")
    lltype.render_immortal(ptr.c_ml_doc)
    state.new_method_def = ptr
    return ptr

def setup_new_method_def(space):
    ptr = get_new_method_def(space)
    ptr.c_ml_meth = rffi.cast(PyCFunction_typedef,
        llhelper(tp_new_wrapper.api_func.functype,
                 tp_new_wrapper.api_func.get_wrapper(space)))

def add_tp_new_wrapper(space, dict_w, pto):
    if "__new__" in dict_w:
        return
    pyo = rffi.cast(PyObject, pto)
    dict_w["__new__"] = PyCFunction_NewEx(space, get_new_method_def(space),
                                          from_ref(space, pyo), None)

def inherit_special(space, pto, base_pto):
    # XXX missing: copy basicsize and flags in a magical way
    # (minimally, if tp_basicsize is zero we copy it from the base)
    if not pto.c_tp_basicsize:
        pto.c_tp_basicsize = base_pto.c_tp_basicsize
    flags = rffi.cast(lltype.Signed, pto.c_tp_flags)
    base_object_pyo = make_ref(space, space.w_object)
    base_object_pto = rffi.cast(PyTypeObjectPtr, base_object_pyo)
    if base_pto != base_object_pto or flags & Py_TPFLAGS_HEAPTYPE:
        if not pto.c_tp_new:
            pto.c_tp_new = base_pto.c_tp_new
    Py_DecRef(space, base_object_pyo)

def check_descr(space, w_self, w_type):
    if not space.isinstance_w(w_self, w_type):
        raise DescrMismatch()

class GettersAndSetters:
    def getter(self, space, w_self):
        assert isinstance(self, W_GetSetPropertyEx)
        check_descr(space, w_self, self.w_type)
        return generic_cpy_call(
            space, self.getset.c_get, w_self,
            self.getset.c_closure)

    def setter(self, space, w_self, w_value):
        assert isinstance(self, W_GetSetPropertyEx)
        check_descr(space, w_self, self.w_type)
        res = generic_cpy_call(
            space, self.getset.c_set, w_self, w_value,
            self.getset.c_closure)
        if rffi.cast(lltype.Signed, res) < 0:
            state = space.fromcache(State)
            state.check_and_raise_exception()

    def member_getter(self, space, w_self):
        assert isinstance(self, W_MemberDescr)
        check_descr(space, w_self, self.w_type)
        return PyMember_GetOne(space, w_self, self.member)

    def member_delete(self, space, w_self):
        assert isinstance(self, W_MemberDescr)
        check_descr(space, w_self, self.w_type)
        PyMember_SetOne(space, w_self, self.member, None)

    def member_setter(self, space, w_self, w_value):
        assert isinstance(self, W_MemberDescr)
        check_descr(space, w_self, self.w_type)
        PyMember_SetOne(space, w_self, self.member, w_value)

class W_PyCTypeObject(W_TypeObject):
    @jit.dont_look_inside
    def __init__(self, space, pto):
        bases_w = space.fixedview(from_ref(space, pto.c_tp_bases))
        dict_w = {}

        add_operators(space, dict_w, pto)
        convert_method_defs(space, dict_w, pto.c_tp_methods, self)
        convert_getset_defs(space, dict_w, pto.c_tp_getset, self)
        convert_member_defs(space, dict_w, pto.c_tp_members, self)

        name = rffi.charp2str(pto.c_tp_name)

        W_TypeObject.__init__(self, space, name,
            bases_w or [space.w_object], dict_w, force_new_layout=True)
        if not space.is_true(space.issubtype(self, space.w_type)):
            self.flag_cpytype = True
        self.flag_heaptype = False
        if pto.c_tp_doc:
            self.w_doc = space.wrap(rffi.charp2str(pto.c_tp_doc))

@bootstrap_function
def init_typeobject(space):
    make_typedescr(space.w_type.layout.typedef,
                   basestruct=PyTypeObject,
                   alloc=type_alloc,
                   attach=type_attach,
                   realize=type_realize,
                   dealloc=type_dealloc)


@cpython_api([PyObject], lltype.Void, header=None)
def subtype_dealloc(space, obj):
    pto = obj.c_ob_type
    base = pto
    this_func_ptr = llhelper(subtype_dealloc.api_func.functype,
            subtype_dealloc.api_func.get_wrapper(space))
    while base.c_tp_dealloc == this_func_ptr:
        base = base.c_tp_base
        assert base
    dealloc = base.c_tp_dealloc
    # XXX call tp_del if necessary
    generic_cpy_call(space, dealloc, obj)
    # XXX cpy decrefs the pto here but we do it in the base-dealloc
    # hopefully this does not clash with the memory model assumed in
    # extension modules

@cpython_api([PyObject, Py_ssize_tP], lltype.Signed, header=None,
             error=CANNOT_FAIL)
def str_segcount(space, w_obj, ref):
    if ref:
        ref[0] = space.len_w(w_obj)
    return 1

@cpython_api([PyObject, Py_ssize_t, rffi.VOIDPP], lltype.Signed,
             header=None, error=-1)
def str_getreadbuffer(space, w_str, segment, ref):
    from pypy.module.cpyext.bytesobject import PyString_AsString
    if segment != 0:
        raise OperationError(space.w_SystemError, space.wrap
                             ("accessing non-existent string segment"))
    pyref = make_ref(space, w_str)
    ref[0] = PyString_AsString(space, pyref)
    # Stolen reference: the object has better exist somewhere else
    Py_DecRef(space, pyref)
    return space.len_w(w_str)

@cpython_api([PyObject, Py_ssize_t, rffi.CCHARPP], lltype.Signed,
             header=None, error=-1)
def str_getcharbuffer(space, w_str, segment, ref):
    from pypy.module.cpyext.bytesobject import PyString_AsString
    if segment != 0:
        raise OperationError(space.w_SystemError, space.wrap
                             ("accessing non-existent string segment"))
    pyref = make_ref(space, w_str)
    ref[0] = PyString_AsString(space, pyref)
    # Stolen reference: the object has better exist somewhere else
    Py_DecRef(space, pyref)
    return space.len_w(w_str)

@cpython_api([PyObject, Py_ssize_t, rffi.VOIDPP], lltype.Signed,
             header=None, error=-1)
def buf_getreadbuffer(space, pyref, segment, ref):
    from pypy.module.cpyext.bufferobject import PyBufferObject
    if segment != 0:
        raise OperationError(space.w_SystemError, space.wrap
                             ("accessing non-existent string segment"))
    py_buf = rffi.cast(PyBufferObject, pyref)
    ref[0] = py_buf.c_b_ptr
    #Py_DecRef(space, pyref)
    return py_buf.c_b_size

def setup_string_buffer_procs(space, pto):
    c_buf = lltype.malloc(PyBufferProcs, flavor='raw', zero=True)
    lltype.render_immortal(c_buf)
    c_buf.c_bf_getsegcount = llhelper(str_segcount.api_func.functype,
                                      str_segcount.api_func.get_wrapper(space))
    c_buf.c_bf_getreadbuffer = llhelper(str_getreadbuffer.api_func.functype,
                                 str_getreadbuffer.api_func.get_wrapper(space))
    c_buf.c_bf_getcharbuffer = llhelper(str_getcharbuffer.api_func.functype,
                                 str_getcharbuffer.api_func.get_wrapper(space))
    pto.c_tp_as_buffer = c_buf
    pto.c_tp_flags |= Py_TPFLAGS_HAVE_GETCHARBUFFER

def setup_buffer_buffer_procs(space, pto):
    c_buf = lltype.malloc(PyBufferProcs, flavor='raw', zero=True)
    lltype.render_immortal(c_buf)
    c_buf.c_bf_getsegcount = llhelper(str_segcount.api_func.functype,
                                      str_segcount.api_func.get_wrapper(space))
    c_buf.c_bf_getreadbuffer = llhelper(buf_getreadbuffer.api_func.functype,
                                 buf_getreadbuffer.api_func.get_wrapper(space))
    pto.c_tp_as_buffer = c_buf

@cpython_api([PyObject], lltype.Void, header=None)
def type_dealloc(space, obj):
    from pypy.module.cpyext.object import PyObject_dealloc
    obj_pto = rffi.cast(PyTypeObjectPtr, obj)
    base_pyo = rffi.cast(PyObject, obj_pto.c_tp_base)
    Py_DecRef(space, obj_pto.c_tp_bases)
    Py_DecRef(space, obj_pto.c_tp_mro)
    Py_DecRef(space, obj_pto.c_tp_cache) # let's do it like cpython
    Py_DecRef(space, obj_pto.c_tp_dict)
    if obj_pto.c_tp_flags & Py_TPFLAGS_HEAPTYPE:
        heaptype = rffi.cast(PyHeapTypeObject, obj)
        Py_DecRef(space, heaptype.c_ht_name)
        Py_DecRef(space, base_pyo)
        PyObject_dealloc(space, obj)


def type_alloc(space, w_metatype):
    metatype = rffi.cast(PyTypeObjectPtr, make_ref(space, w_metatype))
    # Don't increase refcount for non-heaptypes
    if metatype:
        flags = rffi.cast(lltype.Signed, metatype.c_tp_flags)
        if not flags & Py_TPFLAGS_HEAPTYPE:
            Py_DecRef(space, w_metatype)

    heaptype = lltype.malloc(PyHeapTypeObject.TO,
                             flavor='raw', zero=True,
                             add_memory_pressure=True)
    pto = heaptype.c_ht_type
    pto.c_ob_refcnt = 1
    pto.c_ob_type = metatype
    pto.c_tp_flags |= Py_TPFLAGS_HEAPTYPE
    pto.c_tp_as_number = heaptype.c_as_number
    pto.c_tp_as_sequence = heaptype.c_as_sequence
    pto.c_tp_as_mapping = heaptype.c_as_mapping
    pto.c_tp_as_buffer = heaptype.c_as_buffer
    pto.c_tp_basicsize = -1 # hopefully this makes malloc bail out
    pto.c_tp_itemsize = 0

    return rffi.cast(PyObject, heaptype)

def type_attach(space, py_obj, w_type):
    """
    Fills a newly allocated PyTypeObject from an existing type.
    """
    from pypy.module.cpyext.object import PyObject_Del

    assert isinstance(w_type, W_TypeObject)

    pto = rffi.cast(PyTypeObjectPtr, py_obj)

    typedescr = get_typedescr(w_type.layout.typedef)

    # dealloc
    pto.c_tp_dealloc = typedescr.get_dealloc(space)
    # buffer protocol
    if space.is_w(w_type, space.w_str):
        setup_string_buffer_procs(space, pto)
    if space.is_w(w_type, space.w_buffer):
        setup_buffer_buffer_procs(space, pto)

    pto.c_tp_free = llhelper(PyObject_Del.api_func.functype,
            PyObject_Del.api_func.get_wrapper(space))
    pto.c_tp_alloc = llhelper(PyType_GenericAlloc.api_func.functype,
            PyType_GenericAlloc.api_func.get_wrapper(space))
    if pto.c_tp_flags & Py_TPFLAGS_HEAPTYPE:
        w_typename = space.getattr(w_type, space.wrap('__name__'))
        heaptype = rffi.cast(PyHeapTypeObject, pto)
        heaptype.c_ht_name = make_ref(space, w_typename)
        from pypy.module.cpyext.bytesobject import PyString_AsString
        pto.c_tp_name = PyString_AsString(space, heaptype.c_ht_name)
    else:
        pto.c_tp_name = rffi.str2charp(w_type.name)
    # uninitialized fields:
    # c_tp_print, c_tp_getattr, c_tp_setattr
    # XXX implement
    # c_tp_compare and the following fields (see http://docs.python.org/c-api/typeobj.html )
    w_base = best_base(space, w_type.bases_w)
    pto.c_tp_base = rffi.cast(PyTypeObjectPtr, make_ref(space, w_base))

    builder = space.fromcache(StaticObjectBuilder)
    if builder.cpyext_type_init is not None:
        builder.cpyext_type_init.append((pto, w_type))
    else:
        finish_type_1(space, pto)
        finish_type_2(space, pto, w_type)

    pto.c_tp_basicsize = rffi.sizeof(typedescr.basestruct)
    if pto.c_tp_base:
        if pto.c_tp_base.c_tp_basicsize > pto.c_tp_basicsize:
            pto.c_tp_basicsize = pto.c_tp_base.c_tp_basicsize

    # will be filled later on with the correct value
    # may not be 0
    if space.is_w(w_type, space.w_object):
        pto.c_tp_new = rffi.cast(newfunc, 1)
    update_all_slots(space, w_type, pto)
    pto.c_tp_flags |= Py_TPFLAGS_READY
    return pto

def py_type_ready(space, pto):
    if pto.c_tp_flags & Py_TPFLAGS_READY:
        return
    type_realize(space, rffi.cast(PyObject, pto))

@cpython_api([PyTypeObjectPtr], rffi.INT_real, error=-1)
def PyType_Ready(space, pto):
    py_type_ready(space, pto)
    return 0

def type_realize(space, py_obj):
    pto = rffi.cast(PyTypeObjectPtr, py_obj)
    assert pto.c_tp_flags & Py_TPFLAGS_READY == 0
    assert pto.c_tp_flags & Py_TPFLAGS_READYING == 0
    pto.c_tp_flags |= Py_TPFLAGS_READYING
    try:
        w_obj = _type_realize(space, py_obj)
    finally:
        pto.c_tp_flags &= ~Py_TPFLAGS_READYING
    pto.c_tp_flags |= Py_TPFLAGS_READY
    return w_obj

def solid_base(space, w_type):
    typedef = w_type.layout.typedef
    return space.gettypeobject(typedef)

def best_base(space, bases_w):
    if not bases_w:
        return None
    return find_best_base(bases_w)

def inherit_slots(space, pto, w_base):
    # XXX missing: nearly everything
    base_pyo = make_ref(space, w_base)
    try:
        base = rffi.cast(PyTypeObjectPtr, base_pyo)
        if not pto.c_tp_dealloc:
            pto.c_tp_dealloc = base.c_tp_dealloc
        if not pto.c_tp_init:
            pto.c_tp_init = base.c_tp_init
        if not pto.c_tp_alloc:
            pto.c_tp_alloc = base.c_tp_alloc
        # XXX check for correct GC flags!
        if not pto.c_tp_free:
            pto.c_tp_free = base.c_tp_free
        if not pto.c_tp_setattro:
            pto.c_tp_setattro = base.c_tp_setattro
        if not pto.c_tp_getattro:
            pto.c_tp_getattro = base.c_tp_getattro
    finally:
        Py_DecRef(space, base_pyo)

def _type_realize(space, py_obj):
    """
    Creates an interpreter type from a PyTypeObject structure.
    """
    # missing:
    # inheriting tp_as_* slots
    # unsupported:
    # tp_mro, tp_subclasses
    py_type = rffi.cast(PyTypeObjectPtr, py_obj)

    if not py_type.c_tp_base:
        # borrowed reference, but w_object is unlikely to disappear
        base = as_pyobj(space, space.w_object)
        py_type.c_tp_base = rffi.cast(PyTypeObjectPtr, base)

    finish_type_1(space, py_type)

    w_metatype = from_ref(space, rffi.cast(PyObject, py_type.c_ob_type))

    w_obj = space.allocate_instance(W_PyCTypeObject, w_metatype)
    track_reference(space, py_obj, w_obj)
    w_obj.__init__(space, py_type)
    w_obj.ready()

    finish_type_2(space, py_type, w_obj)

    return w_obj

def finish_type_1(space, pto):
    """
    Sets up tp_bases, necessary before creating the interpreter type.
    """
    base = pto.c_tp_base
    base_pyo = rffi.cast(PyObject, pto.c_tp_base)
    if base and not base.c_tp_flags & Py_TPFLAGS_READY:
        type_realize(space, rffi.cast(PyObject, base_pyo))
    if base and not pto.c_ob_type: # will be filled later
        pto.c_ob_type = base.c_ob_type
    if not pto.c_tp_bases:
        if not base:
            bases = space.newtuple([])
        else:
            bases = space.newtuple([from_ref(space, base_pyo)])
        pto.c_tp_bases = make_ref(space, bases)

def finish_type_2(space, pto, w_obj):
    """
    Sets up other attributes, when the interpreter type has been created.
    """
    pto.c_tp_mro = make_ref(space, space.newtuple(w_obj.mro_w))
    base = pto.c_tp_base
    if base:
        inherit_special(space, pto, base)
    for w_base in space.fixedview(from_ref(space, pto.c_tp_bases)):
        inherit_slots(space, pto, w_base)

    if not pto.c_tp_setattro:
        from pypy.module.cpyext.object import PyObject_GenericSetAttr
        pto.c_tp_setattro = llhelper(
            PyObject_GenericSetAttr.api_func.functype,
            PyObject_GenericSetAttr.api_func.get_wrapper(space))

    if not pto.c_tp_getattro:
        from pypy.module.cpyext.object import PyObject_GenericGetAttr
        pto.c_tp_getattro = llhelper(
            PyObject_GenericGetAttr.api_func.functype,
            PyObject_GenericGetAttr.api_func.get_wrapper(space))

    if w_obj.is_cpytype():
        Py_DecRef(space, pto.c_tp_dict)
        w_dict = w_obj.getdict(space)
        pto.c_tp_dict = make_ref(space, w_dict)

@cpython_api([PyTypeObjectPtr, PyTypeObjectPtr], rffi.INT_real, error=CANNOT_FAIL)
def PyType_IsSubtype(space, a, b):
    """Return true if a is a subtype of b.
    """
    w_type1 = from_ref(space, rffi.cast(PyObject, a))
    w_type2 = from_ref(space, rffi.cast(PyObject, b))
    return int(abstract_issubclass_w(space, w_type1, w_type2)) #XXX correct?

@cpython_api([PyTypeObjectPtr, Py_ssize_t], PyObject)
def PyType_GenericAlloc(space, type, nitems):
    from pypy.module.cpyext.object import _PyObject_NewVar
    return _PyObject_NewVar(space, type, nitems)

@cpython_api([PyTypeObjectPtr, PyObject, PyObject], PyObject)
def PyType_GenericNew(space, type, w_args, w_kwds):
    return generic_cpy_call(
        space, type.c_tp_alloc, type, 0)

@cpython_api([PyTypeObjectPtr, PyObject], PyObject, error=CANNOT_FAIL,
             result_borrowed=True)
def _PyType_Lookup(space, type, w_name):
    """Internal API to look for a name through the MRO.
    This returns a borrowed reference, and doesn't set an exception!"""
    w_type = from_ref(space, rffi.cast(PyObject, type))
    assert isinstance(w_type, W_TypeObject)

    if not space.isinstance_w(w_name, space.w_str):
        return None
    name = space.str_w(w_name)
    w_obj = w_type.lookup(name)
    # this assumes that w_obj is not dynamically created, but will stay alive
    # until w_type is modified or dies.  Assuming this, we return a borrowed ref
    return w_obj

@cpython_api([PyTypeObjectPtr], lltype.Void)
def PyType_Modified(space, w_obj):
    """Invalidate the internal lookup cache for the type and all of its
    subtypes.  This function must be called after any manual
    modification of the attributes or base classes of the type.
    """
    # Invalidate the type cache in case of a builtin type.
    if not isinstance(w_obj, W_TypeObject):
        return
    if w_obj.is_cpytype():
        w_obj.mutated(None)

