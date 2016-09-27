"""
Define Mu Type System in similar fashion of Low Level Type System.
"""
from rpython.rlib import rarithmetic
from rpython.rtyper.lltypesystem import lltype, rffi


class MuType(lltype.LowLevelType):
    pass


# ----------------------------------------------------------
class MuPrimitive(MuType, lltype.Primitive):
    def _allocate(self, initialization='raw', parent=None, parentindex=None):
        return lltype.Primitive._allocate(self, initialization, parent, parentindex)


class MuNumber(MuPrimitive, lltype.Number):
    _mu_numbertypes = {}

    @staticmethod
    def build_number(name, type_cls, value_type_cls, *args):   # modification of lltype.build_number
        """
        Build a Mu number type
        :param name: type name
        :param type_cls: subclass of MuNumber that the new type class should belong to (MuIntType/MuFloatType)
        :param value_type_cls: rffi/rarithmetic value type class
        :param args: additional argument passed to type_class.__init__
        """
        try:
            return MuNumber._mu_numbertypes[(type_cls, value_type_cls)]
        except KeyError:
            pass
        if name is None:
            raise ValueError('No matching mu type for %r with super class %r' % (value_type_cls, type_cls))
        num_type = type_cls(name, value_type_cls, *args)
        MuNumber._mu_numbertypes[(type_cls, value_type_cls)] = num_type
        return num_type

    def get_value_type(self):
        return self._val_t


class MuIntType(MuNumber):
    def __init__(self, name, value_type_cls):
        lltype.Number.__init__(self, name, value_type_cls)
        self.BITS = value_type_cls.BITS
        self._val_t = value_type_cls


class MuFloatType(MuNumber):
    def __init__(self, name, value_type_cls, bits):
        lltype.Primitive.__init__(self, name, value_type_cls(0.0))
        self.BITS = bits
        self._val_t = value_type_cls


r_int1 = rarithmetic.build_int('r_int1', False, 1, True)
MU_INT1 = MuIntType("MU_INT1", r_int1)
MU_INT8 = MuIntType("MU_INT8", rffi.r_uchar)
MU_INT16 = MuIntType("MU_INT16", rffi.r_ushort)
MU_INT32 = MuIntType("MU_INT32", rffi.r_uint)
MU_INT64 = MuIntType("MU_INT64", rffi.r_ulong)

MU_FLOAT = MuFloatType("MU_FLOAT", rffi.r_singlefloat, 32)
MU_DOUBLE = MuFloatType("MU_DOUBLE", rarithmetic.r_longfloat, 64)

MU_VOID = MuPrimitive("MU_VOID", None)


class MuBigIntType(MuIntType):
    def __init__(self, name, bits):
        val_cls = rarithmetic.build_int('r_uint%d' % bits, False, bits, True)
        # TODO: Fix, dynamically add this method in the val_cls
        def get_uint64s(self):
            """
            Convert the number into a list of uint64s (see rmu.MuCtx.handle_from_uint64s)
            :return: [rffi.r_ulong]
            """
            lst = []
            val = long(self)
            int64_t = MU_INT64.get_value_type()
            while(val != 0):
                lst.append(int64_t(val & 0xFFFFFFFFFFFFFFFF))
                val >>= 64
            return lst

        val_cls.__dict__['get_uint64s'] = get_uint64s
        MuIntType.__init__(self, name, val_cls)

MU_INT128 = MuBigIntType("MU_INT128", 128)


# ----------------------------------------------------------
# Container types
class MuContainerType(MuType, lltype.ContainerType):
    _gckind = None  # all


class MuForwardReference(MuContainerType, lltype.ForwardReference):
    def become(self, realcontainertype):
        if not isinstance(realcontainertype, MuContainerType):
            raise TypeError("MuForwardReference can only be to a MuContainer, "
                            "not %r" % (realcontainertype,))
        lltype.ForwardReference.become(self, realcontainertype)


def _setup_consistent_methods(cls):
    for tmpcls, mtd in cls._template:
        setattr(cls, mtd, tmpcls.__dict__[mtd])


class MuStruct(MuContainerType):
    _template = (lltype.Struct, (
        '_first_struct',
        '__getattr__',
        '_nofield',
        '_str_fields',
        '__str__',
        '_short_name',
        '_immutable_field',
    ))

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

            names.append(name)
            flds[name] = typ

        # check field type inlining
        first = True
        for name, typ in fields[:-1]:
            typ._note_inlined_into(self, first=first, last=False)
            first = False
        name, typ = fields[-1]
        typ._note_inlined_into(self, first=first, last=True)

        self._flds = lltype.frozendict(flds)
        self._names = tuple(names)

        self._install_extras(**kwds)

    def _is_varsize(self):
        return False    # struct in Mu is always fixed size

    def __getitem__(self, idx):     # support indexing into a struct
        return self._flds[self._names[idx]]

    def _allocate(self, initialization='raw', parent=None, parentindex=None):
        return _mustruct(self, initialization=initialization,
                       parent=parent, parentindex=parentindex)

    def _container_example(self):
        return _mustruct(self)

    def _note_inlined_into(self, parent, first, last):
        pass


class _mustruct(lltype._parentable):
    _kind = "structure"
    _template = (lltype._struct, (
        '__repr__',
        '_str_fields',
        '__str__'
        '_getattr',
    ))

    __slots__ = ('_hash_cache_', '_compilation_info')

    def __new__(self, TYPE, initialization=None, parent=None, parentindex=None):
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

    def __init__(self, TYPE, initialization=None, parent=None, parentindex=None):
        lltype._parentable.__init__(self, TYPE)
        for fld, typ in TYPE._flds.items():
            value = typ._allocate(initialization=initialization,
                                  parent=self, parentindex=fld)
            setattr(self, fld, value)

        if parent is not None:
            self._setparentstructure(parent, parentindex)

    def __getitem__(self, idx):     # support indexing into fields
        return getattr(self, self._TYPE._names[idx])

_setup_consistent_methods(MuStruct)
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

    def _note_inlined_into(self, parent, first, last):
        if not isinstance(parent, MuHybrid):
            raise TypeError("_MuMemArray can only be inlined into MuHybrid")

        if not last:
            raise TypeError("_MuMemArray can only be the last field of MuHybrid")

class _mumemarray(lltype._parentable):
    __slots__ = ('items',)

    _template = (lltype._array, (
        '__init__',
        '__repr__',
        '_check_range',
        '__str__',
        'getlength',
        'shrinklength',
        'getbounds',
        'getitem',
        'setitem'
    ))

    def setitem(self, index, value):
        assert mutypeOf(value) == self._TYPE.OF
        self.items[index] = value

_setup_consistent_methods(_MuMemArray)
_setup_consistent_methods(_mumemarray)


class MuHybrid(MuContainerType):
    _template = (lltype.Struct, (
        '_first_struct',
        '__getattr__',
        '_nofield',
        '_str_fields',
        '__str__',
        '_short_name',
        '_immutable_field',
    ))

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

        for name, typ in fields:
            if name.startswith('_'):
                raise NameError("%s: field name %r should not start with "
                                "an underscore" % (self._name, name,))
            if typ is MU_VOID:
                raise TypeError("%s: void field '%s" % (self._name, name))

            if name in flds:
                raise TypeError("%s: repeated field name" % self._name)

            names.append(name)
            flds[name] = typ

        name, var_t = fields[-1]
        self._arrayfld = name
        self._varfld = self._arrayfld
        self._vartype = _MuMemArray(var_t)      # wrap with _MuMemArray

        self._flds = lltype.frozendict(flds)
        self._names = tuple(names)

        self._install_extras(**kwds)

    def _is_varsize(self):
        return True  # hybrid in Mu is always fixed size

    def __getitem__(self, idx):  # support indexing into the fixed part only
        return self._flds[self._names[:-1][idx]]

    def _container_example(self):
        return _muhybrid(self, 1)

    def _note_inlined_into(self, parent, first, last):
        raise TypeError("MuHybrid can not be inlined")


class _muhybrid(lltype._parentable):
    _kind = "hybrid"
    _template = (lltype._struct, (
        '__repr__',
        '_str_fields',
        '__str__',
        '_getattr',
    ))

    __slots__ = ('_hash_cache_', '_compilation_info')

    def __new__(self, TYPE, n, initialization=None, parent=None, parentindex=None):
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

    def __init__(self, TYPE, n, initialization=None, parent=None, parentindex=None):
        lltype._parentable.__init__(self, TYPE)
        for fld, typ in TYPE._flds.items():
            if fld == TYPE._varfld:
                value = _mumemarray(typ, n, initialization=initialization,
                                    parent=self, parentindex=fld)
            else:
                value = typ._allocate(initialization=initialization,
                                      parent=self, parentindex=fld)
            setattr(self, fld, value)

        if parent is not None:
            self._setparentstructure(parent, parentindex)

_setup_consistent_methods(MuHybrid)
_setup_consistent_methods(_muhybrid)


class MuArray(MuContainerType):
    _template = (lltype.FixedSizeArray, (
        '_str_fields',
        '__str__',
        '_short_name',
        '_first_struct'
    ))

    def __init__(self, OF, length, **kwds):
        self.OF = OF
        self.length = length

    def _is_varsize(self):
        return False    # arrays in Mu have fixed size

    def _allocate(self, initialization='raw', parent=None, parentindex=None):
        return _muarray(self, initialization=initialization,
                        parent=parent, parentindex=parentindex)

    def _note_inlined_into(self, parent, first, last):
        pass


class _muarray(lltype._parentable):
    _template = (lltype._fixedsizearray, (
        'getlength',
        'getbounds',
        'getitem',
        'setitem',
    ))

    def __init__(self, TYPE, initialization=None, parent=None,
                 parentindex=None):
        lltype._parentable.__init__(self, TYPE)

        typ = TYPE.OF
        storage = []
        for i, fld in enumerate(TYPE._names):
            value = typ._allocate(initialization=initialization,
                                  parent=self, parentindex=fld)
            storage.append(value)
        self._items = storage
        if parent is not None:
            self._setparentstructure(parent, parentindex)

    # support __get/setitem__ rather than __get/setattr__
    def __getitem__(self, idx):
        return self.getitem(idx)

    def __setitem__(self, idx, value):
        self.setitem(idx, value)

_setup_consistent_methods(MuArray)
_setup_consistent_methods(_muarray)


# ----------------------------------------------------------
_prim_val_type_map = {
        r_int1: MU_INT1,
        rffi.r_uchar: MU_INT8,
        rffi.r_ushort: MU_INT16,
        rffi.r_uint: MU_INT32,
        rffi.r_ulong: MU_INT64,
        MU_INT128.get_value_type(): MU_INT128,
        rffi.r_singlefloat: MU_FLOAT,
        rarithmetic.r_longfloat: MU_DOUBLE,
        NoneType: MU_VOID
    }


def mutypeOf(val):
    try:
        return val._TYPE
    except AttributeError:
        tp = type(val)
        if tp in _prim_val_type_map:
            return _prim_val_type_map[tp]

        raise TypeError("mutypeOf(%r object)" % (tp.__name__,))
