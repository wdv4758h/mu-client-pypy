"""
Define Mu Type System in similar fashion of Low Level Type System.
"""
from rpython.rlib import rarithmetic
from rpython.rtyper.lltypesystem import lltype, rffi


def _setup_consistent_methods(cls):
    tmpcls, mtds = cls._template
    for mtd in mtds:
        setattr(cls, mtd, tmpcls.__dict__[mtd])


class MuType(object):
    _template = (lltype.LowLevelType, (
        '__eq__',
        '__ne__',
        '_is_compatible',
        '__hash_is_not_constant__',
        '__repr__',
        '__str__',
        '_short_name',
        '_defl',
        '_freeze_',
        '_is_varsize',
    ))
    __slots__ = ['__dict__', '__cached_hash']

    def __setattr__(self, attr, nvalue):
        try:
            MuType.__cached_hash.__get__(self)
        except AttributeError:
            pass
        else:
            try:
                reprself = repr(self)
            except:
                try:
                    reprself = str(self)
                except:
                    reprself = object.__repr__(self)
            raise AssertionError("%s: changing the field %r but we already "
                                 "computed the hash" % (reprself, attr))
        object.__setattr__(self, attr, nvalue)

    def _enforce(self, value):
        if mutypeOf(value) != self:
            raise TypeError
        return value

    def _note_inlined_into(self, parent, last=False):
        pass

    def _allocate(self, parent=None, parentindex=None):
        raise NotImplementedError

    def __hash__(self, TLS=lltype.TLS):     # NOTE: copied from lltype
        # cannot use saferecursive() -- see test_lltype.test_hash().
        # NB. the __cached_hash should neither be used nor updated
        # if we enter with hash_level > 0, because the computed
        # __hash__ can be different in this situation.
        hash_level = 0
        try:
            hash_level = TLS.nested_hash_level
            if hash_level == 0:
                return self.__cached_hash
        except AttributeError:
            pass
        if hash_level >= 3:
            return 0
        items = self.__dict__.items()
        items.sort()
        TLS.nested_hash_level = hash_level + 1
        try:
            result = hash((self.__class__,) + tuple(items))
        finally:
            TLS.nested_hash_level = hash_level
        if hash_level == 0:
            self.__cached_hash = result
        return result
_setup_consistent_methods(MuType)


# ----------------------------------------------------------
class MuPrimitive(MuType):
    _template = (lltype.Primitive, (
        '__str__',
        '_defl',
        '_example'
    ))

    def __init__(self, name, default):
        self._name = self.__name__ = name
        self._default = default

    def _allocate(self, parent=None, parentindex=None):
        return self._default
_setup_consistent_methods(MuPrimitive)


class MuNumber(MuPrimitive):
    _template = (lltype.Number, (
        'normalized',
    ))

    _cache = {}
    _val_type = property(lambda self: self._val_t)

    def __new__(cls, *args):
        try:
            return MuNumber._cache[args]
        except KeyError:
            num = super(MuNumber, cls).__new__(cls, *args)
            MuNumber._cache[args] = num
            return num

    def __init__(self, name, type, cast=None):
        MuPrimitive.__init__(self, name, type())
        self._type = type
        if cast is None:
            self._cast = type
        else:
            self._cast = cast
_setup_consistent_methods(MuNumber)


class MuIntType(MuNumber):
    def __init__(self, name, value_type_cls):
        MuNumber.__init__(self, name, value_type_cls)
        self.BITS = value_type_cls.BITS
        self._val_t = value_type_cls


class MuFloatType(MuNumber):
    def __init__(self, name, value_type_cls, bits):
        MuPrimitive.__init__(self, name, value_type_cls(0.0))
        self._type = value_type_cls
        self._cast = value_type_cls
        self.BITS = bits
        self._val_t = value_type_cls


def hex_repr(val):
    MuT = mutypeOf(val)
    assert isinstance(MuT, MuNumber)
    if isinstance(MuT, MuIntType):
        return hex(val)[:-1]
    if isinstance(MuT, MuFloatType):
        import struct
        fmt = 'd' if MuT.BITS == 64 else 'f'
        pkstr = struct.pack('!' + fmt, float(val))
        hexstr = '0x' + ''.join(['%02x' % ord(b) for b in pkstr])
        return hexstr


mu_int1 = rarithmetic.build_int('r_int1', False, 1, True)
mu_int8 = rffi.r_uchar
mu_int16 = rffi.r_ushort
mu_int32 = rffi.r_uint
mu_int64 = rffi.r_ulong
MU_INT1 = MuIntType("MU_INT1", mu_int1)
MU_INT8 = MuIntType("MU_INT8", mu_int8)
MU_INT16 = MuIntType("MU_INT16", mu_int16)
MU_INT32 = MuIntType("MU_INT32", mu_int32)
MU_INT64 = MuIntType("MU_INT64", mu_int64)

class mu_float(rffi.r_singlefloat):
    def __hash__(self):
        return hash(hex_repr(self))

class mu_double(rarithmetic.r_longfloat):
    def __hash__(self):
        return hash(hex_repr(self))

MU_FLOAT = MuFloatType("MU_FLOAT", mu_float, 32)
mu_float._TYPE = MU_FLOAT
MU_DOUBLE = MuFloatType("MU_DOUBLE", mu_double, 64)
mu_double._TYPE = MU_DOUBLE

MU_VOID = MuPrimitive("MU_VOID", None)


class MuBigIntType(MuIntType):
    def __init__(self, name, bits):
        val_cls = rarithmetic.build_int('r_uint%d' % bits, False, bits, True)

        def get_uint64s(self):
            """
            Convert the number into a list of uint64s (see rmu.MuCtx.handle_from_uint64s)
            :return: [rffi.r_ulong]
            """
            lst = []
            val = long(self)
            int64_t = MU_INT64._val_type
            while(val != 0):
                lst.append(int64_t(val & 0xFFFFFFFFFFFFFFFF))
                val >>= 64
            return lst

        setattr(val_cls, 'get_uint64s', get_uint64s)
        # val_cls.__dict__['get_uint64s'] = get_uint64s
        MuIntType.__init__(self, name, val_cls)

MU_INT128 = MuBigIntType("MU_INT128", 128)
mu_int128 = MU_INT128._val_type


# ----------------------------------------------------------
# Container types
class MuContainerType(MuType):
    _template = (lltype.ContainerType, (
        '_install_extras',
        '_nofield',
        '_container_example'
    ))

    def _note_inlined_into(self, parent, last=False):
        raise TypeError("%r cannot be inlined in %r" % (
            self.__class__.__name__, parent.__class__.__name__))

    def __getattr__(self, name):
        self._nofield(name)
_setup_consistent_methods(MuContainerType)


class MuForwardReference(MuContainerType):
    _template = (lltype.ForwardReference, (
        '__hash__',
    ))

    def become(self, realtype):
        # NOTE: not limited to container types
        if not isinstance(realtype, MuType):
            raise TypeError("MuForwardReference can only be to a MuType, "
                            "not %r" % (realtype,))
        self.__class__ = realtype.__class__
        self.__dict__ = realtype.__dict__
_setup_consistent_methods(MuForwardReference)


class _muparentable(lltype._parentable):
    def _normalizedcontainer(self, check=True):
        # if we are the first inlined substructure of a structure,
        # return the whole (larger) structure instead
        container = self
        while True:
            parent = container._parentstructure(check=check)
            if parent is None:
                break
            index = container._parent_index
            T = mutypeOf(parent)
            if (not isinstance(T, MuStruct) or T._first_struct()[0] != index
                or isinstance(T, MuArray)):
                break
            container = parent
        return container


class MuStruct(MuContainerType):
    _template = (lltype.Struct, (
        '_nofield',
        '_str_fields',
        '__str__',
        '_short_name',
        '_immutable_field',
    ))
    _val_type = property(lambda self: _mustruct)

    def __init__(self, name, *fields, **kwds):
        self._name = self.__name__ = name
        flds = {}
        names = []
        self._arrayfld = None
        for name, typ in fields:
            if name.startswith('_'):
                raise NameError("%s: field name %r should not start with "
                                  "an underscore" % (self._name, name,))
            if typ is MU_VOID:
                raise TypeError("%s: void field '%s" % (self._name, name))

            if name in flds:
                raise TypeError("%s: repeated field name" % self._name)

            typ._note_inlined_into(self)
            names.append(name)
            flds[name] = typ

        self._flds = lltype.frozendict(flds)
        self._names = tuple(names)

        self._install_extras(**kwds)

    def _field_types(self):
        return tuple(self._flds[name] for name in self._names)

    def _is_varsize(self):
        return False    # struct in Mu is always fixed size

    def _first_struct(self):
        if self._names:
            first = self._names[0]
            FIRSTTYPE = self._flds[first]
            if isinstance(FIRSTTYPE, MuStruct):
                return first, FIRSTTYPE
        return None, None

    def __getattr__(self, name):
        try:
            return self._flds[name]
        except KeyError:
            return MuContainerType.__getattr__(self, name)

    def __getitem__(self, idx):     # support indexing into a struct
        return self._flds[self._names[idx]]

    def _index_of(self, fld):
        if fld not in self._names:
            self._nofield(fld)
        return self._names.index(fld)

    def _allocate(self, parent=None, parentindex=None):
        return _mustruct(self, parent=parent, parentindex=parentindex)

    def _container_example(self):
        return _mustruct(self)

    def _note_inlined_into(self, parent, last=False):
        pass
_setup_consistent_methods(MuStruct)


class _mustruct(_muparentable):
    _kind = "structure"
    _template = (lltype._struct, (
        '__repr__',
        '_str_fields',
        '__str__',
        '_getattr',
    ))

    __slots__ = ('_hash_cache_', '_compilation_info')

    def __new__(self, TYPE, parent=None, parentindex=None):
        def _struct_variety(flds, cache={}):
            flds = list(flds)
            flds.sort()
            tag = tuple(flds)
            try:
                return cache[tag]
            except KeyError:
                class _mustruct1(_mustruct):
                    # __slots__ = tag + ('__arena_location__',)
                    __slots__ = tag

                cache[tag] = _mustruct1
                return _mustruct1

        variety = _struct_variety(TYPE._names)
        return object.__new__(variety)

    def __init__(self, TYPE, parent=None, parentindex=None):
        _muparentable.__init__(self, TYPE)
        for fld, typ in TYPE._flds.items():
            value = typ._allocate(parent=self, parentindex=fld)
            setattr(self, fld, value)

        if parent is not None:
            self._setparentstructure(parent, parentindex)

    def __getitem__(self, idx):     # support indexing into fields
        return getattr(self, self._TYPE._names[idx])
_setup_consistent_methods(_mustruct)


class _MuMemArray(MuContainerType):
    """
    A helper array type reflecting lltype.Array.
    """
    __name__ = 'memarr'
    _template = (lltype.Array, (
        '_is_varsize',
        '__str__',
        '_short_name',
        '_immutable_field'
    ))

    def __init__(self, OF, **kwds):
        self.OF = OF
        OF._note_inlined_into(self)
        self._install_extras(**kwds)

    def _str_fields(self):
        if isinstance(self.OF, MuStruct):
            of = self.OF
            return "%s { %s }" % (of._name, of._str_fields())
        elif self._hints.get('render_as_void'):
            return 'void'
        else:
            return str(self.OF)
    _str_fields = lltype.saferecursive(_str_fields, '...')

    def _container_example(self):
        return _mumemarray(self, 1)

    def _note_inlined_into(self, parent, last=False):
        if not isinstance(parent, MuHybrid):
            raise TypeError("_MuMemArray can only be inlined into MuHybrid")

        if not last:
            raise TypeError("_MuMemArray can only be the last field of MuHybrid")
_setup_consistent_methods(_MuMemArray)


class _mumemarray(_muparentable):
    __slots__ = ('items',)

    _template = (lltype._array, (
        '__repr__',
        '_check_range',
        '__str__',
        'getlength',
        'shrinklength',
        'getbounds',
        'getitem',
    ))

    def __init__(self, TYPE, n, parent=None, parentindex=None):
        if not lltype.is_valid_int(n):
            raise TypeError("array length must be an int")
        if n < 0:
            raise ValueError("negative array length")
        _muparentable.__init__(self, TYPE)
        myrange = self._check_range(n)
        self.items = [TYPE.OF._allocate(parent=self, parentindex=j)
                      for j in myrange]
        if parent is not None:
            self._setparentstructure(parent, parentindex)

    def setitem(self, index, value):
        assert mutypeOf(value) == self._TYPE.OF
        self.items[index] = value

    def __getitem__(self, idx):
        return self.getitem(idx)

    def __setitem__(self, idx, value):
        self.setitem(idx, value)

    def __len__(self):
        return self.getlength()

    def _str_item(self, item):
        if isinstance(self._TYPE.OF, MuStruct):
            of = self._TYPE.OF
            return "%s {%s}" % (of._name, item._str_fields())
        else:
            return repr(item)
_setup_consistent_methods(_mumemarray)


class MuHybrid(MuContainerType):
    _template = (MuStruct, (
        '_first_struct',
        '__getattr__',
        '_nofield',
        '_str_fields',
        '__str__',
        '_short_name',
        '_immutable_field',
    ))
    _val_type = property(lambda self: _muhybrid)

    def __init__(self, name, *fields, **kwds):
        """
        NOTE: must define a variable field with wrapped by lltype.Array
        """
        assert len(fields) > 0, \
            "%s: hybrid type must have a variable type"

        self._name = self.__name__ = name
        flds = {}
        names = []
        self._arrayfld = None

        for name, typ in fields[:-1]:
            if name.startswith('_'):
                raise NameError("%s: field name %r should not start with "
                                "an underscore" % (self._name, name,))
            if typ is MU_VOID:
                raise TypeError("%s: void field '%s" % (self._name, name))

            if name in flds:
                raise TypeError("%s: repeated field name" % self._name)
            typ._note_inlined_into(self)
            names.append(name)
            flds[name] = typ

        name, var_t = fields[-1]
        var_t._note_inlined_into(self, last=True)
        names.append(name)
        self._vartype = _MuMemArray(var_t)  # wrap with _MuMemArray
        flds[name] = self._vartype
        self._arrayfld = name
        self._varfld = self._arrayfld

        self._flds = lltype.frozendict(flds)
        self._names = tuple(names)

        self._install_extras(**kwds)

    def _fixed_field_types(self):
        return tuple(self._flds[name] for name in self._names[:-1])

    def _var_field_type(self):
        return self._vartype.OF

    def _is_varsize(self):
        return True  # hybrid in Mu is always fixed size

    def __getitem__(self, idx):  # support indexing into the fixed part only
        return self._flds[self._names[:-1][idx]]

    def _index_of(self, fld):
        if fld not in self._names:
            self._nofield(fld)
        if fld == self._varfld:
            raise AttributeError("cannot index variable field %s in %s" % (fld, self))
        return self._names.index(fld)

    def _container_example(self):
        return _muhybrid(self, 1)

    def _note_inlined_into(self, parent, last=False):
        raise TypeError("MuHybrid can not be inlined")
_setup_consistent_methods(MuHybrid)


class _muhybrid(_muparentable):
    _kind = "hybrid"
    _template = (lltype._struct, (
        '__repr__',
        '_str_fields',
        '_getattr',
    ))

    __slots__ = ('_hash_cache_', '_compilation_info')

    def __new__(self, TYPE, n, parent=None, parentindex=None):
        def _hybrid_variety(flds, cache={}):
            flds = list(flds)
            flds.sort()
            tag = tuple(flds)
            try:
                return cache[tag]
            except KeyError:
                class _muhybrid1(_muhybrid):
                    # __slots__ = tag + ('__arena_location__',)
                    __slots__ = tag

                cache[tag] = _muhybrid1
                return _muhybrid1

        variety = _hybrid_variety(TYPE._names)
        return object.__new__(variety)

    def __init__(self, TYPE, n, parent=None, parentindex=None):
        _muparentable.__init__(self, TYPE)
        for fld, typ in TYPE._flds.items():
            if fld == TYPE._varfld:
                value = _mumemarray(typ, n, parent=self, parentindex=fld)
            else:
                value = typ._allocate(parent=self, parentindex=fld)
            setattr(self, fld, value)

        if parent is not None:
            self._setparentstructure(parent, parentindex)

    def __str__(self):
        return 'hybrid %s { %s }' % (self._TYPE._name, self._str_fields())
_setup_consistent_methods(_muhybrid)


class MuArray(MuContainerType):
    _template = (lltype.FixedSizeArray, (
        '_str_fields',
        '__str__',
        '_short_name',
        '_first_struct'
    ))
    _val_type = property(lambda self: _muarray)

    def __init__(self, OF, length, **kwds):
        self.OF = OF
        OF._note_inlined_into(self)
        self.length = length

    def _is_varsize(self):
        return False    # arrays in Mu have fixed size

    def _allocate(self, parent=None, parentindex=None):
        return _muarray(self, parent=parent, parentindex=parentindex)

    def _note_inlined_into(self, parent, last=False):
        pass
_setup_consistent_methods(MuArray)


class _muarray(_muparentable):
    _template = (lltype._fixedsizearray, (
        'getlength',
        'getbounds',
        'getitem',
        'setitem',
    ))

    def __init__(self, TYPE, parent=None, parentindex=None):
        _muparentable.__init__(self, TYPE)

        typ = TYPE.OF
        storage = []
        for i in range(TYPE.length):
            value = typ._allocate(parent=self, parentindex=i)
            storage.append(value)
        self._items = storage
        if parent is not None:
            self._setparentstructure(parent, parentindex)

    # support __get/setitem__ rather than __get/setattr__
    def __getitem__(self, idx):
        return self.getitem(idx)

    def __setitem__(self, idx, value):
        self.setitem(idx, value)

    def __len__(self):
        return self.getlength()
_setup_consistent_methods(_muarray)


class MuFuncSig(MuContainerType):
    def __init__(self, arg_ts, res_ts):
        for arg in arg_ts + res_ts:
            assert isinstance(arg, MuType)

        self.ARGS = tuple(arg_ts)
        self.RESULTS = tuple(res_ts)

    def __str__(self):
        return "( %s ) -> ( %s )" % (
            ", ".join(map(str, self.ARGS)),
            ", ".join(map(str, self.RESULTS))
        )
    __str__ = lltype.saferecursive(__str__, '...')

    def _short_name(self):
        return "(%s)->(%s)" % (
            ", ".join(map(str, self.ARGS)),
            ", ".join(map(str, self.RESULTS))
        )
    _short_name = lltype.saferecursive(_short_name, '...')


# ----------------------------------------------------------
class MuReferenceType(MuType):
    _template = (lltype.Ptr, (

    ))
    _suffix = None     # child class must specify
    _symbol = None     # child class must specify
    _val_type = property(lambda self: _mugeneral_reference)

    def __str__(self):
        raise NotImplementedError

    def _defl(self, parent=None, parentindex=None):
        return self._null()

    def _null(self):
        raise NotImplementedError

    def _allocate(self, parent=None, parentindex=None):
        return self._defl(parent, parentindex)

    def _example(self):
        raise NotImplementedError
_setup_consistent_methods(MuReferenceType)


class _mugeneral_reference(object):
    _template = (lltype._abstract_ptr, (
        '__ne__',
        '__hash__',
        '__repr__',
    ))

    def __eq__(self, other):
        return (self is other) or (self._is_null() and other._is_null())

    def __str__(self):
        if self._is_null():
            return "NULL"
        else:
            return self._non_null_str()

    def __nonzero__(self):
        return not self._is_null()

    def _non_null_str(self):
        raise NotImplementedError

    def _is_null(self):
        raise NotImplementedError
_setup_consistent_methods(_mugeneral_reference)


class MuOpaqueRef(MuReferenceType):
    _suffix = 'OpqRef'
    _symbol = '@pq'
    _val_type = property(lambda self: _muopqref)

    def __init__(self, ref_name, obj_name=None):
        self.ref_name = ref_name
        if obj_name is None:
            obj_name = ref_name.lower()[:-3]
        self.obj_name = obj_name

    def __str__(self):
        return self._suffix + self.ref_name

    def _null(self):
        return self._val_type(self, _nullref=True)

    def _example(self):
        return _muopqref(self)


class _muopqref(_mugeneral_reference):
    def __init__(self, TYPE, **attrs):
        self._TYPE = TYPE
        self.__dict__.update(attrs)

    def _non_null_str(self):
        return "%s (%s)" % (self._TYPE._symbol, self.ref_name)

    def _is_null(self):
        return hasattr(self, '_nullref') and self._nullref

class MuGeneralFunctionReference(MuOpaqueRef):
    def __init__(self, SIG):
        self.Sig = SIG

    def __str__(self):
        return self._suffix + str(self.Sig)

    def _example(self):
        def f(*args):
            return tuple(T._defl() for T in self.Sig.RESULTS)
        return self._val_type(self, _callable=f)

class _mufunction_reference(_muopqref):
    def __init__(self, TYPE, **attrs):
        attrs.setdefault('_TYPE', TYPE)
        attrs.setdefault('_name', '?')
        attrs.setdefault('_callable', None)
        self.__dict__.update(attrs)
        if '_callable' in attrs and hasattr(attrs['_callable'],
                                            '_compilation_info'):
            self.__dict__['compilation_info'] = \
                attrs['_callable']._compilation_info

    def _non_null_str(self):
        return "%s %s" % (self._TYPE._symbol, self._name)

    def __call__(self, *args):
        Sig = self._TYPE.Sig
        if len(args) != len(Sig.ARGS):
            raise TypeError("calling %r with wrong argument number: %r" %
                            (self._TYPE, args))
        for i, a, ARG in zip(range(len(Sig.ARGS)), args, Sig.ARGS):
            if mutypeOf(a) != ARG:
                # be either None or 0 (MuUPtr)
                if isinstance(ARG, MuReferenceType):
                    if a == ARG._defl()._obj:
                        pass

                    # Any ref is convertible to ref<void> of same ref type
                    elif ARG.TO is MU_VOID and \
                            isinstance(mutypeOf(a), ARG):
                        pass
                # # special case: ARG can be a container type, in which
                # # case a should be a pointer to it.  This must also be
                # # special-cased in the backends.
                # elif (isinstance(ARG, ContainerType) and
                #       typeOf(a) == Ptr(ARG)):
                #     pass
                else:
                    args_repr = [mutypeOf(arg) for arg in args]
                    raise TypeError("calling %r with wrong argument "
                                    "types: %r" % (self._T, args_repr))
        callb = self._callable
        if callb is None:
            raise RuntimeError("calling undefined function")
        return callb(*args)     # call the callbale

class MuFuncRef(MuGeneralFunctionReference):
    _suffix = 'FncRef'
    _symbol = '@#'
    _val_type = property(lambda self: _mufuncref)

class _mufuncref(_mufunction_reference):
    _template = (lltype._func, (
        '__repr__',
        '__eq__',
        '__ne__',
        '__hash__',
        '_getid'
    ))
_setup_consistent_methods(_mufuncref)

class MuUFuncPtr(MuGeneralFunctionReference):
    _suffix = 'UFncPtr'  # child class must specify
    _symbol = '*#'  # child class must specify
    _val_type = property(lambda self: _muufuncptr)

class _muufuncptr(_mufunction_reference):
    _template = (_mufuncref, (
        "__repr__",
        "__eq__",
        "__ne__",
        "__hash__",
        "_getid"
    ))
_setup_consistent_methods(_muufuncptr)


# ----------------------------------------------------------
class MuObjectRef(MuReferenceType):
    _val_type = property(lambda self: _muobject_reference)

    def __init__(self, TO):
        self.TO = TO

    def __str__(self):
        return "%s %s" % (self._symbol, self.TO)


class _muobject_reference(_mugeneral_reference):
    def _non_null_str(self):
        return "%s %s" % (self._TYPE._symbol, self._obj)

    def _cast_to(self, REFTYPE):
        CURTYPE = self._TYPE
        down_or_up = castable(REFTYPE, CURTYPE)
        if down_or_up == 0:
            return self

        if not self:    # null pointer cast
            return REFTYPE._defl()

        cls = type(self)

        if isinstance(self._obj, int):
            return cls(REFTYPE, self._obj)

        if down_or_up > 0:
            p = self
            while down_or_up:
                p = getattr(p, mutypeOf(p).TO._names[0])
                down_or_up -= 1
            return cls(REFTYPE, p._obj)

        u = -down_or_up
        struc = self._obj
        PARENTTYPE = None
        while u:
            parent = struc._parentstructure()
            if parent is None:
                raise RuntimeError("widening to trash: %r" % self)
            PARENTTYPE = struc._parent_type
            if getattr(parent, PARENTTYPE._names[0]) != struc:
                raise lltype.InvalidCast(CURTYPE, REFTYPE)
            struc = parent
            u -= 1
        if PARENTTYPE != REFTYPE.TO:
            raise RuntimeError("widening %r inside %r instead of %r" %
                               (CURTYPE, PARENTTYPE, REFTYPE.TO))
        return cls(REFTYPE, struc)

    def __hash__(self):
        return hash((self.__class__, self._obj))


class MuRef(MuObjectRef):
    _suffix = 'Ref'
    _symbol = '@'
    _val_type = property(lambda self: _muref)

    def _null(self):
        return _muref(self, None)

class MuIRef(MuObjectRef):
    _suffix = 'IRef'
    _symbol = '&'
    _val_type = property(lambda self: _muiref)

    def _null(self):
        return _muiref(self, MuRef(self.TO)._null(), [])

class MuUPtr(MuObjectRef):
    _suffix = 'UPtr'
    _symbol = '*'
    _val_type = property(lambda self: _muuptr)

    def _null(self):
        nullref = MuRef(self.TO)._null()
        return nullref._pin()  # hack!

class MuWeakRef(MuObjectRef):
    _suffix = 'WkRef'
    _symbol = '@wk'
    _val_type = None    # not implemented


class _muref(_muobject_reference):
    __slots__ = ('_TYPE', '_T', '_obj', '_pin_count')
    _template = (lltype._ptr, (
    ))

    def __init__(self, TYPE, pointing_to):
        self._TYPE = TYPE
        self._T = TYPE.TO
        self._obj = pointing_to
        self._pin_count = 0

    def _getiref(self):
        return _muiref(MuIRef(self._T), self, [])

    def _pin(self):
        self._pin_count += 1
        return _muuptr(MuUPtr(self._T), self, [])

    def _unpin(self):
        if not self._ispinned():
            raise RuntimeError("can not unpin %s that is not pinned." % self)
        self._pin_count -= 1

    def _ispinned(self):
        return self._pin_count > 0

    def _is_null(self):
        return self._obj is None
_setup_consistent_methods(_muref)

def _getobjfield(obj, offsets):
    for o in offsets:
        if isinstance(o, str):
            assert isinstance(obj, (_mustruct, _muhybrid))
            obj = obj._getattr(o)
        else:
            assert isinstance(obj, (_muarray, _mumemarray))
            obj = obj[o]
    return obj

class _muiref(_muobject_reference):
    __slots__ = ('_TYPE', '_T', '_root_ref', '_offsets')
    _template = (_muref, (
    ))

    def __init__(self, TYPE, root_ref, offsets):
        _muiref._TYPE.__set__(self, TYPE)
        _muiref._T.__set__(self, TYPE.TO)
        if not isinstance(mutypeOf(root_ref), MuRef):
            raise TypeError("root reference of iref must be ref, not %s" % root_ref)
        _muiref._root_ref.__set__(self, root_ref)
        _muiref._offsets.__set__(self, offsets)

    def _pin(self):
        uptr = self._root_ref._pin()    # pin the root ref

        # move uptr to this field
        for o in self._offsets:
            if isinstance(o, str):
                uptr = getattr(uptr, o)
            else:
                uptr = uptr[o]
        return uptr

    def _getobj(self):
        return _getobjfield(self._root_ref._obj, self._offsets)

    def _setobj(self, value):
        if mutypeOf(value) != self._T:
            raise TypeError("storing %s of type %s to %s" %
                            (value, mutypeOf(value), mutypeOf(self)))

        if len(self._offsets) == 0:
            self._root_ref._obj = value
        else:
            obj = _getobjfield(self._root_ref._obj, self._offsets[:-1])
            ofs = self._offsets[-1]
            if isinstance(mutypeOf(obj), (MuStruct, MuHybrid)):
                setattr(obj, ofs, value)
            else:
                obj[ofs] = value

    _obj = property(_getobj, _setobj)
    _store = _setobj

    def _load(self):
        obj = self._obj
        if isinstance(mutypeOf(obj), MuHybrid):
            raise TypeError("can not load a MuHybrid type %s" % mutypeOf(obj))
        return obj

    def _unpin(self):
        self._root_ref.unpin()

    def _is_null(self):
        return self._root_ref._is_null()

    def _expose(self, offset, val):
        T = mutypeOf(val)
        return _muiref(MuIRef(T), self._root_ref, self._offsets + [offset])

    def __getattr__(self, field_name):
        if isinstance(self._T, (MuStruct, MuHybrid)):
            if field_name in self._T._flds:
                o = self._obj._getattr(field_name)
                return self._expose(field_name, o)
        raise AttributeError("%r instance has no field %r" % (self._T,
                                                              field_name))

    def __setattr__(self, field_name, val):
        if isinstance(self._T, (MuStruct, MuHybrid)):
            if field_name in self._T._flds:
                T1 = self._T._flds[field_name]
                T2 = mutypeOf(val)
                if T1 != T2:
                    raise TypeError(
                        "%r instance field %r:\nexpects %r\n    got %r" %
                        (self._T, field_name, T1, T2))
                setattr(self._obj, field_name, val)
        raise AttributeError("%r instance has no field %r" %
                             (self._T, field_name))

    def __getitem__(self, i):
        if isinstance(self._T, (_MuMemArray, MuArray)):
            start, stop = self._obj.getbounds()
            if not (start <= i < stop):
                if isinstance(i, slice):
                    raise TypeError("array slicing not supported")
                raise IndexError("array index out of bounds")
            o = self._obj.getitem(i)
            return self._expose(i, o)
        raise TypeError("%r instance is not an array" % (self._T,))

    def __setitem__(self, i, val):
        if isinstance(self._T, (_MuMemArray, MuArray)):
            T1 = self._T.OF
            if isinstance(T1, MuContainerType):
                raise TypeError("cannot directly assign to container array items")
            T2 = mutypeOf(val)
            if T2 != T1:
                from rpython.rtyper.lltypesystem import rffi
                if T1.TO is MU_VOID and type(T1) == type(T2):
                    # same type of reference is castable to void ref
                    # val = rffi.cast(rffi.VOIDP, val)
                    raise NotImplementedError
                else:
                    raise TypeError("%r items:\n"
                                    "expect %r\n"
                                    "   got %r" % (self._T, T1, T2))
            start, stop = self._obj.getbounds()
            if not (start <= i < stop):
                if isinstance(i, slice):
                    raise TypeError("array slicing not supported")
                raise IndexError("array index out of bounds")
            self._obj.setitem(i, val)
            return
        raise TypeError("%r instance is not an array" % (self._T,))

    def __len__(self):
        if isinstance(self._T, (_MuMemArray, MuArray)):
            # if self._T._hints.get('nolength', False):
            #     raise TypeError("%r instance has no length attribute" %
            #                         (self._T,))
            return self._obj.getlength()
        raise TypeError("%r instance is not an array" % (self._T,))
_setup_consistent_methods(_muiref)


class _muuptr(_muobject_reference):
    __slots__ = ('_TYPE', '_T', '_root_ref', '_offsets')

    _template = (_muiref, (
        '_is_null',
        '__getattr__',
        '__setattr__',
        '__getitem__',
        '__setitem__',
        '__len__'
    ))

    def __init__(self, TYPE, root_ref, offsets):
        """
        NOTE: this assumes that the uptr is obtained through pinning a ref.
        In the case of 'raw' malloc, we can fake it by creating a ref then pin it.
        """
        _muuptr._TYPE.__set__(self, TYPE)
        _muuptr._T.__set__(self, TYPE.TO)
        if not isinstance(mutypeOf(root_ref), MuRef):
            raise TypeError("root reference of uptr must be ref, not %s" % root_ref)
        _muuptr._root_ref.__set__(self, root_ref)
        _muuptr._offsets.__set__(self, offsets)

    def _getobj(self):
        if not self._root_ref._ispinned():
            raise RuntimeError("root reference of %s is not pinned" % self)
        return _getobjfield(self._root_ref._obj, self._offsets)

    def _setobj(self, value):
        if mutypeOf(value) != self._T:
            raise TypeError("storing %s of type %s to %s" %
                            (value, mutypeOf(value), mutypeOf(self)))

        if isinstance(mutypeOf(value), (MuRef, MuIRef)):
            raise TypeError("can not store Mu memory reference %s of type %s to untraced pointer %s" %
                            (value, mutypeOf(value), mutypeOf(self)))

        if not self._root_ref._ispinned():
            raise RuntimeError("root reference of %s is not pinned" % self)

        if len(self._offsets) == 0:
            self._root_ref._obj = value
        else:
            obj = _getobjfield(self._root_ref._obj, self._offsets[:-1])
            ofs = self._offsets[-1]
            if isinstance(mutypeOf(obj), (MuStruct, MuHybrid)):
                setattr(obj, ofs, value)
            else:
                obj[ofs] = value

    _obj = property(_getobj, _setobj)
    _store = _setobj

    def _load(self):
        obj = self._obj
        if not self._root_ref._ispinned():
            raise RuntimeError("root reference of %s is not pinned" % self)
        if isinstance(mutypeOf(obj), MuHybrid):
            raise TypeError("can not load a MuHybrid type %s" % mutypeOf(obj))
        if isinstance(mutypeOf(obj), (MuRef, MuIRef)):
            raise TypeError("can not load Mu memory reference %s from %s" %
                            (mutypeOf(obj), mutypeOf(self)))
        return obj

    def _expose(self, offset, val):
        T = mutypeOf(val)
        return _muuptr(MuIRef(T), self._root_ref, self._offsets + [offset])
_setup_consistent_methods(_muuptr)


class MuGlobalCell(MuIRef):
    _suffix = 'Glb'
    _symbol = '&g'
    _val_type = property(lambda self: _muglobalcell)

    def __init__(self, TO):
        if isinstance(TO, MuHybrid):
            raise TypeError("%s can not be contained in global cell")
        super(MuGlobalCell, self).__init__(TO)


class _muglobalcell(_muiref):
    pass

class MuWeakRef(MuRef):
    _suffix = "WkRef"
    _symbol = "~"
    _val_type = property(lambda self: _muweakref)

MU_WEAKREF_VOID = MuWeakRef(MU_VOID)

class _muweakref(_muref):
    pass

def _castdepth(OUTSIDE, INSIDE):
    if OUTSIDE == INSIDE:
        return 0
    dwn = 0
    while isinstance(OUTSIDE, MuStruct):
        first, FIRSTTYPE = OUTSIDE._first_struct()
        if first is None:
            break
        dwn += 1
        if FIRSTTYPE == INSIDE:
            return dwn
        OUTSIDE = getattr(OUTSIDE, first)
    return -1


def castable(REFTYPE, CURTYPE):
    if type(REFTYPE) != type(CURTYPE):
        raise TypeError("can not cast across reference types: %s to %s" %
                        (CURTYPE, REFTYPE))

    if CURTYPE == REFTYPE:
        return 0

    # can only cast between reference to structs
    if (not isinstance(CURTYPE.TO, MuStruct) or
        not isinstance(REFTYPE.TO, MuStruct)):
        raise lltype.InvalidCast(CURTYPE, REFTYPE)

    CURSTRUC = CURTYPE.TO
    REFSTRUC = REFTYPE.TO

    d = _castdepth(CURSTRUC, REFSTRUC)
    if d >= 0:
        return d
    u = _castdepth(REFSTRUC, CURSTRUC)
    if u == -1:
        raise lltype.InvalidCast(CURTYPE, REFTYPE)
    return -u


# ----------------------------------------------------------
_prim_val_type_map = {
        mu_int1: MU_INT1,
        mu_int8: MU_INT8,
        mu_int16: MU_INT16,
        mu_int32: MU_INT32,
        mu_int64: MU_INT64,
        mu_int128: MU_INT128,
        mu_float: MU_FLOAT,
        mu_double: MU_DOUBLE,
        type(None): MU_VOID
    }


def mutypeOf(val):
    try:
        return val._TYPE
    except AttributeError:
        tp = type(val)
        if tp in _prim_val_type_map:
            return _prim_val_type_map[tp]

        raise TypeError("mutypeOf(%r object)" % (tp.__name__,))


def new(T):
    if isinstance(T, MuGlobalCell):
        ref = new(T.TO)
        return _muglobalcell(T, ref, [])

    if isinstance(T, MuStruct):
        o = _mustruct(T)
    elif isinstance(T, MuArray):
        o = _muarray(T)
    elif isinstance(T, MuNumber):
        o = T._defl()
    elif isinstance(T, MuReferenceType):
        o = T._null()
    else:
        raise TypeError("do know how to new %s" % T)
    return _muref(MuRef(T), o)


def newhybrid(T, n):
    if not isinstance(T, MuHybrid):
        raise TypeError("newhybrid can only allocate MuHybrid type")

    o = _muhybrid(T, n)
    return _muref(MuRef(T), o)

isCompatibleType = lltype.isCompatibleType
enforce = lltype.enforce


def mu_barebonearray(ARRAY):
    # counterpart of rpython.translator.c.support.barebonearray
    assert isinstance(ARRAY, MuHybrid)
    return len(ARRAY._names) == 1 and \
           (not'length' in ARRAY._names) and \
           ARRAY._vartype.OF is not MU_VOID

# TODO: follow the pattern in lltype, write implementations of mu instructions based on mutype
