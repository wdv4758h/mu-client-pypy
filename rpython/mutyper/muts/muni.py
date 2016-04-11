"""
Some native interface stuff.
"""
from .mutype import *
from .muentity import MuGlobalCell
from rpython.translator.mu.mem import mu_sizeOf

__voidptr_t = MuUPtr(void_t)
__ptr_int_t = MuInt(mu_sizeOf(__voidptr_t) * 8)     # the corresponding int type for pointers.


class MuExternalFunc(MuGlobalCell):
    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)

    def __init__(self, c_name, arg_ts, rtn_t, c_libs=()):
        MuGlobalCell.__init__(self, MuUFuncPtr(MuFuncSig(arg_ts, (rtn_t, ) if rtn_t is not void_t else ())))
        self.mu_name = MuName(MuUFuncPtr.type_prefix + c_name)
        self.c_name = c_name
        self.c_libs = c_libs

    def __str__(self):
        return "muexternfnc %s <%s> @ %s" % (self.c_name, self.mu_type.Sig, self.mu_name)


c_malloc = MuExternalFunc('malloc', (int64_t, ), __voidptr_t, ('stdlib.h',))
c_free = MuExternalFunc('free', (__voidptr_t, ), void_t, ('stdlib.h',))
c_memset = MuExternalFunc('memset', (__voidptr_t, int64_t, int64_t), __voidptr_t, ('string.h',))
c_memcpy = MuExternalFunc('memcpy', (__voidptr_t, __voidptr_t, int64_t), __voidptr_t, ('string.h',))
c_memcopy = c_memcpy
c_memmove = MuExternalFunc('memmove', (__voidptr_t, __voidptr_t, int64_t), __voidptr_t, ('string.h',))
