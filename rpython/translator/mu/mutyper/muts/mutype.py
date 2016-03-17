"""
Define Mu Type System in similar fashion of Low Level Type System.
"""
import weakref
from types import NoneType

from rpython.rlib.objectmodel import Symbolic
from rpython.rtyper.lltypesystem.lltype import LowLevelType, saferecursive, WeakValueDictionary, frozendict
from .muentity import MuEntity, MuName


class MuType(LowLevelType, MuEntity):
    def __init__(self, str_name):
        MuEntity.__init__(self, MuName(str_name))   # All types have global scope

    @property
    def mu_constructor(self):
        raise NotImplementedError

    @property
    def _mu_constructor_expanded(self):
        raise NotImplementedError

    def __repr__(self):
        return self._mu_constructor_expanded


# ----------------------------------------------------------
class MuPrimitive(MuType):
    def __init__(self, type_name, abbrv, constr, default):
        """
        :param abbrv: abbreviation string
        :param constr: constructor string
        :param default: default value of primitive type
        :return:
        """
        MuType.__init__(self, abbrv)
        self._default = default
        self._constr = constr
        self._type_name = type_name

    def __str__(self):
        return self._type_name

    def _defl(self, parent=None, parentindex=None):
        return self._default

    def _allocate(self, initialization=None, parent=None, parentindex=None):
        return self._default

    def _is_atomic(self):
        return True

    def _example(self, parent=None, parentindex=None):
        return self._default
    
    @property
    def mu_constructor(self):
        return self._constr
    
    @property
    def _mu_constructor_expanded(self):
        return self.mu_constructor

    def __eq__(self, other):
        return isinstance(other, MuPrimitive) and self._constr == other._constr


def _mu_int_type(n):
    assert n in (1, 8, 16, 32, 64, 128), "Invalid integer length: %d" % n
    return MuPrimitive("int%d_t" % n, "i%d" % n, "int<%d>" % n, 0)


int1_t = _mu_int_type(1)
int8_t = _mu_int_type(8)
int16_t = _mu_int_type(16)
int32_t = _mu_int_type(32)
int64_t = _mu_int_type(64)
int128_t = _mu_int_type(128)

float_t = MuPrimitive("float_t", "flt", "float", 0.0)
double_t = MuPrimitive("double_t", "dbl", "double", 0.0)
void_t = MuPrimitive("void_t", "void", "void", None)

bool_t = int1_t
char_t = int8_t
unichar_t = int16_t


# ----------------------------------------------------------
class MuContainerType(MuType):
    def __getattr__(self, item):
        raise AttributeError('%s %s has no field %r' %
                             (self.__class__.__name__, self.mu_name, item))

    def _container_example(self):
        raise NotImplementedError


class _muobject(object):
    __slots__ = ()

    def __repr__(self):
        return "<%s>" % self


class _mucontainer(_muobject):
    __slots__ = ()

    def _parentstructure(self):
        return None

    def _getid(self):
        return id(self)


class _muparentable(_mucontainer):
    _kind = "?"

    __slots__ = ('_TYPE',
                 '_parent_type', '_parent_index', '_keepparent',
                 '_wrparent',
                 '__weakref__')

    def __init__(self, TYPE):
        self._wrparent = None
        self._TYPE = TYPE

    def _setparent(self, parent, parentindex):
        """
        Set the parent information.
        Args:
            parent: parent object
            parentindex: base offset or field name

        Returns: None
        """
        self._wrparent = weakref.ref(parent)
        self._parent_type = mu_typeOf(parent)
        self._parent_index = parentindex

    def _parent(self):
        if self._wrparent is not None:
            parent = self._wrparent()
            if parent is None:
                raise RuntimeError("accessing sub%s %r,\n"
                                   "but already garbage collected parent %r"
                                   % (self._kind, self, self._parent_type))
            return parent
        return None


# ----------------------------------------------------------
class MuStruct(MuContainerType):
    """
    Structs are fixed sizes.
    """
    type_prefix = "stt"

    def __init__(self, name, *fields):
        """
        Args:
            name: the custom name of the struct.
            *fields: a list of (str, MuType) tuples.
            **kwds: for extras.
        """
        self._name = name
        MuType.__init__(self, MuStruct.type_prefix + name)

        flds = {}
        names = []
        for name, typ in fields:
            if name.startswith('_'):
                raise NameError("%s: field name %r should not start with "
                                "an underscore" % (self._name, name,))
            if name in flds:
                raise TypeError("%s: repeated field name" % self._name)

            names.append(name)
            flds[name] = typ

            if isinstance(typ, MuHybrid):
                raise TypeError("%s: cannot inline MuHybrid type %s" %
                                (self._name, typ))

        self._flds = frozendict(flds)
        self._names = tuple(names)

    def _is_atomic(self):
        for typ in self._flds.values():
            if not typ._is_atomic():
                return False
        return True

    def __getattr__(self, name):
        try:
            return self._flds[name]
        except KeyError:
            return MuContainerType.__getattr__(self, name)

    def _str_fields(self):
        return ', '.join(['%s: %s' % (name, self._flds[name])
                          for name in self._names])
    _str_fields = saferecursive(_str_fields, "...")

    def __str__(self):
        # -- long version --
        # return "%s %s { %s }" % (self.__class__.__name__,
        #                         self._name, self._str_fields())
        # -- short version --
        return "%s %s { %s }" % (self.__class__.__name__, self._name,
                                 ', '.join(self._names))

    @property
    def mu_constructor(self):
        return "struct<%s>" % ' '.join([str(self._flds[name].mu_name) for name in self._names])
    
    @property
    def _mu_constructor_expanded(self):
        def _inner():
            return "struct<%s>" % ' '.join([self._flds[name]._mu_constructor_expanded
                                            for name in self._names])
        return saferecursive(_inner, "...")()

    def _allocate(self, initialization=None, parent=None, parentindex=None):
        return _mustruct(self, parent=parent, parentindex=parentindex)

    def _container_example(self):
        return _mustruct(self)


def _struct_with_slots(flds):
    class _mustruct1(_mustruct):
        __slots__ = tuple(flds)
    return _mustruct1


class _mustruct(_muparentable):
    _kind = "structure"

    __slots__ = ()

    def __new__(cls, TYPE, parent=None, parentindex=None):
        return object.__new__(_struct_with_slots(TYPE._names),
                              parent, parentindex)

    def __init__(self, TYPE, parent=None, parentindex=None):
        assert isinstance(TYPE, MuStruct)

        _muparentable.__init__(self, TYPE)
        for fld, typ in TYPE._flds.items():
            value = typ._allocate(parent=self, parentindex=fld)
            setattr(self, fld, value)
        if parent is not None:
            self._setparent(parent, parentindex)

    def _str_fields(self):
        fields = []
        names = self._TYPE._names
        if len(names) > 10:
            names = names[:5] + names[-1:]
            skipped_after = 5
        else:
            skipped_after = None
        for name in names:
            T = self._TYPE._flds[name]
            if isinstance(T, MuPrimitive):
                reprvalue = repr(getattr(self, name))
            else:
                reprvalue = '...'
            fields.append('%s=%s' % (name, reprvalue))
        if skipped_after:
            fields.insert(skipped_after, '(...)')
        return ', '.join(fields)

    def __str__(self):
        return 'stt %s { %s }' % (self._TYPE._name, self._str_fields())

    def _getattr(self, field_name):
        return getattr(self, field_name)


# ----------------------------------------------------------
class MuHybrid(MuContainerType):
    """
    MuHybrid is the only variable sized type.
    """
    type_prefix = "hyb"

    def __init__(self, name, *fields):
        """
        Args:
            name: custom name of the hybrid.
            *fields: a list of (str, MuType) pairs of more than one values;
                     the last field is the variable field.
            **kwds: for extras
        """
        if len(fields) == 0:
            raise TypeError("Variable part cannot be empty")

        self._name = name
        MuType.__init__(self, MuHybrid.type_prefix + name)

        flds = {}
        names = []
        for name, typ in fields:
            if name.startswith('_'):
                raise NameError("%s: field name %r should not start with "
                                "an underscore" % (self._name, name,))
            if name in flds:
                raise TypeError("%s: repeated field name" % self._name)

            names.append(name)
            flds[name] = typ

            if isinstance(typ, MuHybrid):
                raise TypeError("%s: cannot inline MuHybrid type %s" %
                                (self._name, typ))

        self._flds = frozendict(flds)
        self._names = tuple(names)
        self._varfld = names[-1]
        if self._flds[self._varfld] == void_t:
            raise TypeError("%s: variable part cannot by Void type" %
                            self._name)

    def _is_atomic(self):
        for typ in self._flds.values():
            if not typ._is_atomic():
                return False
        return True

    def __getattr__(self, name):
        try:
            return self._flds[name]
        except KeyError:
            return MuContainerType.__getattr__(self, name)

    def _str_fields(self):
        fix_part = ', '.join(['%s: %s' % (name, self._flds[name])
                              for name in self._names[:-1]])
        var_part = '%s: %s' % (self._varfld, self._flds[self._varfld])
        return fix_part + ' | ' + var_part
    _str_fields = saferecursive(_str_fields, "...")

    def __str__(self):
        # -- long version --
        # return "%s %s { %s }" % (self.__class__.__name__,
        #                         self._name, self._str_fields())
        # -- short version --
        return "%s %s { %s | %s }" % (self.__class__.__name__, self._name,
                                      ', '.join(self._names[:-1]),
                                      self._varfld)
    @property
    def mu_constructor(self):
        return "hybrid<%s>" % ' '.join([str(self._flds[name].mu_name) for name in self._names])

    @property
    def _mu_constructor_expanded(self):
        def _inner():
            return "hybrid<%s>" % ' '.join([self._flds[name]._mu_constructor_expanded
                                            for name in self._names])
        return saferecursive(_inner, '...')()

    def _container_example(self):
        return _muhybrid(self, 5)


def _hybrid_with_slots(flds):
    class _hybrid1(_muhybrid):
        __slots__ = tuple(flds)
    return _hybrid1


class _muhybrid(_muparentable):
    _kind = "hybrid"

    __slots__ = ('_hash_cache_', '_compilation_info')

    def __new__(cls, TYPE, n, parent=None, parentindex=None):
        return object.__new__(_hybrid_with_slots(TYPE._names),
                              parent, parentindex)

    def __init__(self, TYPE, n, parent=None, parentindex=None):
        assert isinstance(TYPE, MuHybrid)
        assert n >= 0

        _muparentable.__init__(self, TYPE)
        for fld, typ in TYPE._flds.items():
            if fld == TYPE._varfld:
                # NOTE: use list for now.
                # TODO: review this when defining iref.
                value = [typ._allocate(parent=self, parentindex=i)
                         for i in range(n)]
            else:
                value = typ._allocate(parent=self, parentindex=fld)

            setattr(self, fld, value)

        if parent is not None:
            self._setparent(parent, parentindex)

    def _str_item(self, item):
        if isinstance(self._TYPE.OF, MuStruct):
            of = self._TYPE.OF
            if self._TYPE._anonym_struct:
                return "{%s}" % item._str_fields()
            else:
                return "%s {%s}" % (of._name, item._str_fields())
        else:
            return repr(item)

    def _str_fields(self):
        fields = []
        names = self._TYPE._names[:-1]
        if len(names) > 10:
            names = names[:5] + names[-1:]
            skipped_after = 5
        else:
            skipped_after = None
        for name in names:
            T = self._TYPE._flds[name]
            if isinstance(T, MuPrimitive):
                reprvalue = repr(getattr(self, name))
            else:
                reprvalue = '...'
            fields.append('%s=%s' % (name, reprvalue))
        if skipped_after:
            fields.insert(skipped_after, '(...)')
        fix_part = ', '.join(fields)

        items = self._TYPE._varfld
        if len(items) > 20:
            items = items[:12] + items[-5:]
            skipped_at = 12
        else:
            skipped_at = None
        items = [self._str_item(item) for item in items]
        if skipped_at:
            items.insert(skipped_at, '(...)')
        var_part = '[ %s ]' % (', '.join(items),)

        return '%s | %s' % (fix_part, var_part)

    def __str__(self):
        return 'hyb %s { %s }' % (self._TYPE._name, self._str_fields())

    def _getattr(self, field_name):
        return getattr(self, field_name)


# ----------------------------------------------------------
class MuArray(MuContainerType):
    """
    Fixed size array type.
    """
    type_prefix = "arr"

    def __init__(self, OF, length):
        if isinstance(OF, MuHybrid):
            raise TypeError("cannot create an array of hybrids")
        if length < 0:
            raise ValueError("negative array length")

        MuType.__init__(self, (MuArray.type_prefix + "%d%s") % (length, OF.mu_name._name))

        self.OF = OF
        self.length = length

    def _str_fields(self):
        return str(self.OF)
    _str_fields = saferecursive(_str_fields, '...')

    def __str__(self):
        return "%s of %d %s" % (self.__class__.__name__,
                                 self.length,
                                 self._str_fields(),)

    def _container_example(self):
        return _muarray(self)

    @property
    def mu_constructor(self):
        return "array<%s %d>" % (self.OF.mu_name, self.length)

    @property
    def _mu_constructor_expanded(self):
        def _inner():
            return "array<%s %d>" % (self.OF._mu_constructor_expanded, self.length)
        return saferecursive(_inner, "...")()


class _muarray(_muparentable):
    _kind = "array"

    __slots__ = ('items')

    def __init__(self, TYPE, parent=None, parentindex=None):
        assert isinstance(TYPE, MuArray)

        _muparentable.__init__(self, TYPE)
        n = TYPE.length
        self.items = [TYPE.OF._allocate(parent=self, parentindex=j)
                      for j in range(n)]
        if parent is not None:
            self._setparent(parent, parentindex)

    def _str_item(self, item):
        if isinstance(self._TYPE.OF, MuStruct):
            of = self._TYPE.OF
            return "%s {%s}" % (of._name, item._str_fields())
        else:
            return repr(item)

    def __str__(self):
        items = self.items
        if len(items) > 20:
            items = items[:12] + items[-5:]
            skipped_at = 12
        else:
            skipped_at = None
        items = [self._str_item(item) for item in items]
        if skipped_at:
            items.insert(skipped_at, '(...)')
        return 'arr [ %s ]' % (', '.join(items),)

    def getlength(self):
        return self._TYPE.length

    def getbounds(self):
        stop = self.getlength()
        return 0, stop

    def getitem(self, index):
        return self.items[index]

    def setitem(self, index, value):
        assert mu_typeOf(value) == self._TYPE.OF
        self.items[index] = value


# ----------------------------------------------------------
class MuRefType(MuType):
    def _defl(self, parent=None, parentindex=None):
        return NULL


class _mugenref(object):  # value of general reference types
    __slots__ = ("_T", "_TYPE")

    def __init__(self, T):
        self.__class__._T.__set__(self, T)

    def __eq__(self, other):
        if type(self) is not type(other):
            raise TypeError("comparing pointer with %r object" % (
                type(other).__name__,))
        if self._TYPE != other._TYPE:
            raise TypeError("comparing %r and %r" % (self._TYPE, other._TYPE))

        return self._obj == other._obj

    def __hash__(self):
        raise TypeError("reference objects are not hashable")


NULL = _mugenref(void_t)    # NULL is a value of general reference type


# ----------------------------------------------------------
class MuFuncSig(MuType):
    type_prefix = "sig"

    def __init__(self, arg_ts, rtn_ts):
        """
        Args:
            arg_ts: parameter types
            rtn_ts: return types
        """
        name = "sig_"
        for arg in arg_ts:
            assert isinstance(arg, MuType)
            name += arg.mu_name._name
        name += "_"
        for rtn in rtn_ts:
            assert isinstance(rtn, MuType)
            if isinstance(rtn, MuHybrid):
                raise TypeError("function result cannot be MuHybrid type")
            name += rtn.mu_name._name

        MuType.__init__(self, name)
        self.ARGS = tuple(arg_ts)
        self.RTNS = tuple(rtn_ts)

    @property
    def mu_constructor(self):
        args = ', '.join(map(lambda a: repr(a.mu_name), self.ARGS))
        if len(self.RTNS) == 1:
            rtns = repr(self.RTNS[0].mu_name)
        else:
            rtns = '(%s)' % ', '.join(map(lambda a: repr(a.mu_name), self.RTNS))
        return "(%s) -> %s" % (args, rtns)

    @property
    def _mu_constructor_expanded(self):
        def _inner():
            args = ', '.join(map(lambda a: a._mu_constructor_expanded, self.ARGS))
            if len(self.RTNS) == 1:
                rtns = self.RTNS[0]._mu_constructor_expanded
            else:
                rtns = '( %s )' % ', '.join(map(lambda a: a._mu_constructor_expanded, self.RTNS))
            return "( %s ) -> %s" % (args, rtns)
        return saferecursive(_inner, '...')()

    def __str__(self):
        args = ', '.join(map(str, self.ARGS))
        if len(self.RTNS) == 1:
            rtns = '%s' % self.RTNS[0]
        else:
            rtns = '( %s )' % ', '.join(map(str, self.RTNS))
        return "( %s ) -> %s" % (args, rtns)
    __str__ = saferecursive(__str__, '...')

    def _short_name(self):
        args = ', '.join([ARG._short_name() for ARG in self.ARGS])
        if len(self.RTNS) == 1:
            rtns = '%s' % self.RTNS[0]._short_name()
        else:
            rtns = '(%s)' % ', '.join([rtn._short_name() for rtn in self.RTNS])
        return "(%s)->%s" % (args, rtns)
    _short_name = saferecursive(_short_name, '...')

    def _trueargs(self):
        return [arg for arg in self.ARGS if arg is not void_t]


class MuFuncRef(MuRefType):
    type_prefix = "fnr"

    def __init__(self, Sig):
        MuType.__init__(self, MuFuncRef.type_prefix + Sig.mu_name._name)
        self.Sig = Sig

    def __str__(self):
        return "MuFuncRef %s" % self.Sig

    @property
    def mu_constructor(self):
        return "funcref<%s>" % self.Sig.mu_name

    @property
    def _mu_constructor_expanded(self):
        def _inner():
            return "funcref<%s>" % self.Sig._mu_constructor_expanded
        return saferecursive(_inner, "...")()


class _mufuncref(_mugenref):
    # TODO: This needs to be reviewed.
    def __init__(self, TYPE, **attrs):
        """
        An actual function reference
        :param TYPE: MuFuncRef
        """
        self._TYPE = TYPE
        for attr in attrs:
            setattr(self, attr, attrs[attr])


class MuRef(MuRefType):
    type_prefix = "ref"
    type_str_sym = "@"
    type_constr_name = "ref"

    def __init__(self, TO):
        MuType.__init__(self, self.__class__.type_prefix + TO.mu_name._name)
        self.TO = TO

    def __str__(self):
        return "%s %s" % (self.__class__.type_str_sym, self.TO)

    @property
    def mu_constructor(self):
        return "%s<%s>" % (self.__class__.type_constr_name, self.TO.mu_name)

    @property
    def _mu_constructor_expanded(self):
        def _inner():
            return "%s<%s>" % (self.__class__.type_constr_name, self.TO._mu_constructor_expanded)
        return saferecursive(_inner, "...")()


class _muref(_mugenref):
    __slots__ = ("_obj",)

    def __init__(self, TYPE, obj):
        _muref._TYPE.__set__(TYPE)
        _mugenref.__init__(self, TYPE.TO)
        _muref._obj.__set__(obj)

    def _getiref(self):
        return _muiref(MuIRef(self._T), self._obj)


class MuIRef(MuRef):
    type_prefix = "irf"
    type_str_sym = "~"
    type_constr_name = "iref"


class _muiref(_muref, _muparentable):
    def __init__(self, TYPE, obj, parent, parentindex):
        _muref.__init__(self, TYPE, obj)

        self._setparent(parent, parentindex)

    def __getattr__(self, field_name):
        if isinstance(self._T, MuStruct) or isinstance(self._T, MuHybrid):
            if field_name in self._T._flds:
                o = self._obj._getattr(field_name)
                return self._expose(field_name, o)
        raise AttributeError("%s instance has no field %s" % (self._T, field_name))

    def __setattr__(self, field_name, val):
        if isinstance(self._T, MuStruct) or isinstance(self._T, MuHybrid):
            if field_name in self._T._flds:
                T1 = self._T._flds[field_name]
                T2 = typeOf(val)
                if T1 == T2:
                    setattr(self._obj, field_name, val)
                else:
                    raise TypeError(
                        "%r instance field %r:\nexpects %r\n    got %r" %
                        (self._T, field_name, T1, T2))
                return
        raise AttributeError("%r instance has no field %r" %
                             (self._T, field_name))

    def __getitem__(self, i): # ! can only return basic or ptr !
        if isinstance(self._T, (Array, FixedSizeArray)):
            start, stop = self._obj.getbounds()
            if not (start <= i < stop):
                if isinstance(i, slice):
                    raise TypeError("array slicing not supported")
                raise IndexError("array index out of bounds")
            o = self._obj.getitem(i)
            return self._expose(i, o)
        raise TypeError("%r instance is not an array" % (self._T,))

    def __setitem__(self, i, val):
        if isinstance(self._T, (Array, FixedSizeArray)):
            T1 = self._T.OF
            if isinstance(T1, ContainerType):
                raise TypeError("cannot directly assign to container array "
                                "items")
            T2 = typeOf(val)
            if T2 != T1:
                from rpython.rtyper.lltypesystem import rffi
                if T1 is rffi.VOIDP and isinstance(T2, Ptr):
                    # Any pointer is convertible to void*
                    val = rffi.cast(rffi.VOIDP, val)
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


# ----------------------------------------------------------
def mu_typeOf(val):
    try:
        return val._TYPE
    except AttributeError:
        tp = type(val)
        if tp is NoneType:
            return void_t   # maybe
        if tp is int:
            return int64_t
        if tp is long:
            return int128_t
        if tp is bool:
            return bool_t
        if tp is float:
            return double_t
        if tp is str:
            assert len(val) == 1
            return char_t
        if tp is unicode:
            assert len(val) == 1
            return unichar_t
        if issubclass(tp, Symbolic):
            return val.lltype()
        # if you get a TypeError: mu_typeOf('_interior_ptr' object)
        # here, it is very likely that you are accessing an interior pointer
        # in an illegal way!
        raise TypeError("mu_typeOf(%r object)" % (tp.__name__,))