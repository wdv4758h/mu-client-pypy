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


class MuInt(MuPrimitive):
    _valid_bits = (1, 8, 16, 32, 64, 128)
    
    def __init__(self, bits):
        assert bits in MuInt._valid_bits, "Invalid integer length: %d" % bits
        MuPrimitive.__init__(self, "int%d_t" % bits, "i%d" % bits, "int<%d>" % bits, 0)
        self.bits = bits

    def __eq__(self, other):
        # TODO: VERY BAD HACK! NEEDS TO BE REVISED.
        return isinstance(other, MuInt)

int1_t = MuInt(1)
int8_t = MuInt(8)
int16_t = MuInt(16)
int32_t = MuInt(32)
int64_t = MuInt(64)
int128_t = MuInt(128)

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
    __slots__ = ("_TYPE")

    def __init__(self, TYPE):
        _mucontainer._TYPE.__set__(self, TYPE)

    def _getid(self):
        return id(self)


class _muparentable(object):        # parentable may not be _mucontainers (eg. list for array and hybrid)
    def __init__(self, parent, parentindex):
        self._setparent(parent, parentindex)

    def _setparent(self, parent, parentindex):
        """
        Set the parent information.
        Args:
            parent: parent object
            parentindex: base parentindex or field name

        Returns: None
        """
        self._parent = parent
        self._parentindex = parentindex


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
        if fields:
            self._setfields(fields)

    def _setfields(self, *fields):
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


class _mustruct(_muparentable, _mucontainer):
    _kind = "structure"

    __slots__ = ()

    def __new__(cls, TYPE, parent=None, parentindex=None):
        return object.__new__(_struct_with_slots(TYPE._names),
                              parent, parentindex)

    def __init__(self, TYPE, parent=None, parentindex=None):
        assert isinstance(TYPE, MuStruct)

        _mucontainer.__init__(self, TYPE)
        _muparentable.__init__(self, parent, parentindex)

        for fld, typ in TYPE._flds.items():
            value = typ._allocate(parent=self, parentindex=fld)
            setattr(self, fld, value)

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


class _muhybrid(_muparentable, _mucontainer):
    _kind = "hybrid"

    __slots__ = ('_hash_cache_', '_compilation_info')

    def __new__(cls, TYPE, n, parent=None, parentindex=None):
        return object.__new__(_hybrid_with_slots(TYPE._names),
                              parent, parentindex)

    def __init__(self, TYPE, n, parent=None, parentindex=None):
        assert isinstance(TYPE, MuHybrid)
        assert n >= 0

        _mucontainer.__init__(self, TYPE)
        _muparentable.__init__(self, parent, parentindex)

        for fld, typ in TYPE._flds.items():
            if fld == TYPE._varfld:
                # NOTE: use list for now.
                # TODO: review this when defining iref.
                value = _mumemarray(typ, n, self, fld)
            else:
                value = typ._allocate(parent=self, parentindex=fld)

            setattr(self, fld, value)

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


class _mumemarray(_muparentable):
    def __init__(self, OF, n, parent=None, parentindex=None):
        if isinstance(OF, MuHybrid):
            raise TypeError("Hybrid type %s cannot be element type of Mu memory array." % OF)

        _muparentable.__init__(self, parent, parentindex)
        self._OF = OF
        self.items = [OF._allocate(parent=self, parentindex=i) for i in range(n)]

    def _str_item(self, item):
        if isinstance(self._OF, MuStruct):
            of = self._OF
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

    def __len__(self):
        return len(self.items)

    def __getitem__(self, item):
        return self.items[item]

    def __setitem__(self, key, value):
        assert mu_typeOf(value) == self._OF
        self.items[key] = value

    def __iter__(self):
        self._iteridx = 0
        return self

    def __next__(self):
        if self._iteridx >= len(self):
            raise StopIteration
        obj = self[self._iteridx]
        self._iteridx += 1
        return obj


class _muarray(_mumemarray, _mucontainer):
    _kind = "array"

    def __init__(self, TYPE, parent=None, parentindex=None):
        assert isinstance(TYPE, MuArray)

        _mucontainer.__init__(self, TYPE)
        _mumemarray.__init__(self, TYPE.OF, TYPE.length, parent, parentindex)


# ----------------------------------------------------------
class MuRefType(MuType):
    def _defl(self, parent=None, parentindex=None):
        return NULL


class _mugenref(_muobject):  # value of general reference types
    # def __init__(self, T):
    #     self._T = T

    # def __eq__(self, other):
    #     if self._T is None and other._T is None:
    #         return True
    #
    #     if type(self) is not type(other):
    #         raise TypeError("comparing %s with %r object" % (
    #             type(self).__name__, type(other).__name__,))
    #
    #     if self._TYPE != other._TYPE:
    #         raise TypeError("comparing %r and %r" % (self._TYPE, other._TYPE))
    #
    #     return self._obj == other._obj

    def __hash__(self):
        raise TypeError("reference objects are not hashable")


NULL = _mugenref()    # NULL is a value of general reference type


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
    type_constr_name = "funcref"

    def __init__(self, Sig):
        MuType.__init__(self, self.__class__.type_prefix + Sig.mu_name._name)
        self.Sig = Sig

    def __str__(self):
        return "%s %s" % (self.__class__.__name__, self.Sig)

    @property
    def mu_constructor(self):
        return "%s<%s>" % (self.__class__.type_constr_name, self.Sig.mu_name)

    @property
    def _mu_constructor_expanded(self):
        def _inner():
            return "%s<%s>" % (self.__class__.type_constr_name, self.Sig._mu_constructor_expanded)
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


class _muref(_mugenref, _mucontainer):
    __slots__ = ("_T", "_obj0")

    def __init__(self, TYPE, obj):
        _mucontainer.__init__(self, TYPE)
        self._T = TYPE.TO
        self._obj0 = obj

    @property       # read only!
    def _obj(self):
        return self._getiref()

    def _getiref(self):
        return _muiref(MuIRef(self._T), self._obj0, self, None)

    def _pin(self):
        return _muuptr(MuUPtr(self._T), self._obj0, self, None)

    def __str__(self):
        return "@ %s" % (self._obj0)

    def __eq__(self, other):
        return self._TYPE == other._TYPE and id(self._obj0) == id(other._obj0)


class MuIRef(MuRef):
    type_prefix = "irf"
    type_str_sym = "~"
    type_constr_name = "iref"


class _muiref(_muref, _muparentable):
    def __init__(self, TYPE, obj, parent, parentindex):
        assert isinstance(parent, _muref) or isinstance(parent, _muparentable), "parent must be _muref/_muparentable type."

        _muref.__init__(self, TYPE, obj)
        _muparentable.__init__(self, parent, parentindex)

    def __str__(self):
        return "~ %s" % self._obj0

    def __nonzero__(self):
        raise RuntimeError("do not test an interior pointer for nullity")

    def _expose(self, parentindex, val):
        """
        Expose the internal reference to a field/item of the referenced container type.

        :param parentindex: field name (str) or item index (int)
        :param val:
        :return:
        """
        T = mu_typeOf(val)
        return _muiref(MuIRef(T), val, self._obj0, parentindex)

    def _store(self, val):
        # Simulating STORE to this iref
        ob = self._parent
        o = self._parentindex
        T = mu_typeOf(val)
        if T != self._T:
            raise TypeError("Storing %r type to %r" % (T, self._T))

        if isinstance(ob, _mumemarray):
            ob[o] = val
        else:
            TYPE_PARENT = self._parent._TYPE
            if isinstance(TYPE_PARENT, MuStruct) or isinstance(TYPE_PARENT, MuHybrid):
                setattr(ob, o, val)

    def _load(self):
        return self._obj0

    _obj = property(_load, _store)

    def __getattr__(self, field_name):  # similar to GETFIELDIREF/GETVARPARTIREF
        if field_name[0] == '_':
            return self.__dict__[field_name]
        if isinstance(self._T, MuHybrid):
            if field_name == self._T._varfld:
                memarr = getattr(self._obj0, field_name)
                o = memarr[0]
                return _muiref(MuIRef(memarr._OF), o, memarr, 0)
        if isinstance(self._T, MuStruct) or isinstance(self._T, MuHybrid):
            if field_name in self._T._flds:
                o = self._obj0._getattr(field_name)
                return self._expose(field_name, o)
        raise AttributeError("%r instance has no field %r" % (self._T, field_name))

    def __setattr__(self, field_name, val):     # simiar to STORE to an IRef
        if field_name == '_obj':
            self._store(val)
            return
        if field_name[0] == '_':
            self.__dict__[field_name] = val
            return
        else:
            raise AttributeError("Cannot set field %s of %r; use _store() or _obj instead." % (field_name, self))

    def __getitem__(self, i):   # similar to GETELEMIREF
        if isinstance(self._parent, _mumemarray):
            return self + i

        if isinstance(self._obj0, _mumemarray):
            if not i < len(self._obj0):
                if isinstance(i, slice):
                    raise TypeError("array slicing not supported")
                raise IndexError("array index out of bounds")
            o = self._obj0[i]
            return self._expose(i, o)
        raise TypeError("%r instance is not an array" % (self._T,))

    def __setitem__(self, i, val):
        raise AttributeError("cannot set item to %r; use _store() or _obj instead." % self)

    def __add__(self, other):
        assert isinstance(other, int)
        obj = self._parent
        idx = self._parentindex
        assert isinstance(obj, _mumemarray), \
            "can only shift irefs that points to an internal element of an continuous array memory."
        if not 0 <= (idx + other) < len(obj):
            raise IndexError("memory array index out of bounds")
        return _muiref(self._TYPE, obj[idx + other], obj, idx + other)


class MuUPtr(MuIRef):
    type_prefix = "ptr"
    type_str_sym = "*"
    type_constr_name = "uptr"


class _muuptr(_muiref):
    def __str__(self):
        return "* %s" % self._obj0

    def _expose(self, parentindex, val):
        T = mu_typeOf(val)
        return _muuptr(MuUPtr(T), val, self._obj0, parentindex)

    def __getattr__(self, field_name):  # similar to GETFIELDIREF/GETVARPARTIREF
        if field_name[0] == '_':
            return self.__dict__[field_name]
        if isinstance(self._T, MuHybrid):
            if field_name == self._T._varfld:
                memarr = getattr(self._obj0, field_name)
                o = memarr[0]
                return _muuptr(MuUPtr(memarr._OF), o, memarr, 0)
        if isinstance(self._T, MuStruct) or isinstance(self._T, MuHybrid):
            if field_name in self._T._flds:
                o = self._obj0._getattr(field_name)
                return self._expose(field_name, o)
        raise AttributeError("%r instance has no field %r" % (self._T, field_name))


class MuUFuncPtr(MuFuncRef):
    type_prefix = "fnp"
    # TODO: Not a perfect definition


class _muufuncptr(_mufuncref):
    pass


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


def new(T):
    if isinstance(T, MuStruct):
        obj = _mustruct(T)
    elif isinstance(T, MuArray):
        obj = _muarray(T)
    elif isinstance(T, MuPrimitive):
        obj = T._allocate()
    else:
        raise TypeError("Unable to allocate memory for %r" % T)
    return _muref(MuRef(T), obj)


def newhybrid(T, n):
    assert isinstance(T, MuHybrid)
    return _muref(MuRef(T), _muhybrid(T, n))
