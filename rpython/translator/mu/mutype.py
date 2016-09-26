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


class MuBigIntType(MuIntType):
    def __init__(self, name, bits):
        val_cls = rarithmetic.build_int('r_uint%d' % bits, False, bits, True)
        # TODO: Fix, dynamically add this method in the val_cls
        class __extend__(val_cls):
            def get_uint64_array(self):
                """
                Convert the number into array of uint64s (see rmu.MuCtx.handle_from_uint64s)
                :return: _mu_memarray(rffi.r_ulong)
                """
                raise NotImplementedError
        MuIntType.__init__(self, name, val_cls)


MU_INT1 = MuIntType("MU_INT1", rarithmetic.build_int('r_int1', False, 1, True))
MU_INT8 = MuIntType("MU_INT8", rffi.r_uchar)
MU_INT16 = MuIntType("MU_INT16", rffi.r_ushort)
MU_INT32 = MuIntType("MU_INT32", rffi.r_uint)
MU_INT64 = MuIntType("MU_INT64", rffi.r_ulong)
MU_INT128 = MuBigIntType("MU_INT128", 128)

MU_FLOAT = MuFloatType("MU_FLOAT", rffi.r_singlefloat, 32)
MU_DOUBLE = MuFloatType("MU_DOUBLE", rarithmetic.r_longfloat, 64)

MU_VOID = MuPrimitive("MU_VOID", None)


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


class MuStruct(MuContainerType):
    # methods that are consistent with lltype.Struct
    _consistent_methods = [
        '_first_struct',
        '__getattr__',
        '_nofield',
        '_str_fields',
        '__str__',
        '_short_name',
        '_immutable_field',
    ]

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

            names.append(name)
            if name in flds:
                raise TypeError("%s: repeated field name" % self._name)
            flds[name] = typ

        self._flds = lltype.frozendict(flds)
        self._names = tuple(names)

        self._install_extras(**kwds)

    def _is_atomic(self):
        # Mu memory order does not depend on data structure
        raise NotImplementedError

    def _is_varsize(self):
        return False    # struct in Mu is always fixed size

    def __getitem__(self, idx):     # support indexing into a struct
        return self._flds[self._names[idx]]

    def _allocate(self, initialization='raw', parent=None, parentindex=None):
        # return _mustruct(self, initialization=initialization,
        #                parent=parent, parentindex=parentindex)
        raise NotImplementedError

    def _container_example(self):
        # return _mustruct(self)
        raise NotImplementedError

for mtd in MuStruct._consistent_methods:
    setattr(MuStruct, mtd, lltype.Struct.__dict__[mtd])

# TODO: write tests
