"""
Some native interface stuff.
"""
from .mutype import *
from .muentity import MuGlobalCell


__voidptr_t = MuUPtr(void_t)
__ptr_int_t = MuInt(mu_sizeOf(__voidptr_t) * 8)     # the corresponding int type for pointers.


class MuExternalFunc(MuUFuncPtr):
    def __init__(self, c_name, arg_ts, rtn_t, c_libs=()):
        sig = MuFuncSig(arg_ts, (rtn_t, ) if rtn_t is not void_t else ())
        MuFuncRef.__init__(self, sig)
        self.c_name = c_name
        self.gcl_adr = MuGlobalCell(globals()['__ptr_int_t'])
        self.c_libs = c_libs

    def __str__(self):
        return "muexternfnc %s <%s> @ %s" % (self.c_name, self.Sig, self.gcl_adr)


c_malloc = MuExternalFunc('malloc', (int64_t, ), __voidptr_t, ('stdlib.h',))
c_free = MuExternalFunc('free', (__voidptr_t, ), void_t, ('stdlib.h',))
c_memset = MuExternalFunc('memset', (__voidptr_t, int64_t, int64_t), __voidptr_t, ('string.h',))
c_memcpy = MuExternalFunc('memcpy', (__voidptr_t, __voidptr_t, int64_t), __voidptr_t, ('string.h',))
c_memcopy = c_memcpy
c_memmove = MuExternalFunc('memmove', (__voidptr_t, __voidptr_t, int64_t), __voidptr_t, ('string.h',))
