"""
Define Mu Type System in similar fashion of Low Level Type System.
"""
from rpython.rtyper.lltypesystem.lltype import LowLevelType, safe_equal, saferecursive
from .muentity import MuEntity, MuName


class MuType(LowLevelType, MuEntity):
    def mu_constructor_short(self):
        raise NotImplementedError

    def mu_constructor_long(self):
        raise NotImplementedError

    @property
    def mu_constructor(self):
        return self.mu_constructor_short()

    def __repr__(self):
        return self.mu_constructor


class MuPrimitive(MuType):
    def __init__(self, mu_name, default):
        """
        :param mu_name: MuName instance
        :param default: default value of primitive type
        :return:
        """
        MuEntity.__init__(self, mu_name)
        self._default = default

    def _defl(self, parent=None, parentindex=None):
        return self._default

    def _allocate(self, initialization=None, parent=None, parentindex=None):
        return self._default

    def _is_atomic(self):
        return True

    def _example(self, parent=None, parentindex=None):
        return self._default


class MuInt(MuPrimitive):
    _valid_lengths = (1, 8, 16, 32, 64, 128)

    def __init__(self, length):
        """
        :param length: valid length of an integer
        :raises: ValueError (invalid integer length)
        """
        assert length in self._valid_lengths, "Invalid integer length %d!" % length

        MuPrimitive.__init__(self, MuName("i%d" % length), 0)
        self.bits = length

    def mu_constructor_short(self):
        return "int<%d>" % self.bits

    mu_constructor_long = mu_constructor_short

    def __eq__(self, other):
        return isinstance(other, MuInt) and self.bits == other.bits

int1_t = MuInt(1)
int8_t = MuInt(8)
int16_t = MuInt(16)
int32_t = MuInt(32)
int64_t = MuInt(64)
