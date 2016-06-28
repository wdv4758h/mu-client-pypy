"""
Run with:
    PYTHONPATH=$PYPY_MU LIBRARY_PATH=$MU/cbinding:$LIBRARY_PATH python target_test_mu.py
OR:
    rpython target_test_mu.py
    LD_LIBRARY_PATH=$MU/cbinding:$LD_LIBRARY_PATH ./target_test_mu-c
"""
from rpython.rlib.rmuapi import *
from rpython.rlib import rposix
from rpython.rlib import rdynload

import os
print os.getpid()

prelude = """
.typedef @i1        = int<1>
.typedef @i6        = int<6>
.typedef @i8        = int<8>
.typedef @i16       = int<16>
.typedef @i32       = int<32>
.typedef @i52       = int<52>
.typedef @i64       = int<64>
.typedef @float     = float
.typedef @double    = double

.typedef @void      = void

.typedef @thread    = threadref
.typedef @stack     = stackref
.typedef @tagref64  = tagref64

.typedef @refi8     = ref<@i8>
.typedef @refi16    = ref<@i16>
.typedef @refi32    = ref<@i32>
.typedef @refi64    = ref<@i64>
.typedef @reffloat  = ref<@float>
.typedef @refdouble = ref<@double>

.typedef @irefi8    = iref<@i8>
.typedef @irefi16   = iref<@i16>
.typedef @irefi32   = iref<@i32>
.typedef @irefi64   = iref<@i64>
.typedef @ireffloat = iref<@float>
.typedef @irefdouble= iref<@double>

.typedef @ptrvoid    = uptr<@void>
.typedef @ptri8      = uptr<@i8>
.typedef @ptri16     = uptr<@i16>
.typedef @ptri32     = uptr<@i32>
.typedef @ptri64     = uptr<@i64>
.typedef @ptrfloat   = uptr<@float>
.typedef @ptrdouble  = uptr<@double>
.typedef @ptrptrvoid = uptr<@ptrvoid>

.typedef @weakrefi64    = weakref<@i64>

.typedef @refvoid       = ref<@void>
.typedef @irefvoid      = iref<@void>
.typedef @weakrefvoid   = weakref<@void>

.const @I32_0 <@i32> = 0
.const @I32_1 <@i32> = 1
.const @I64_0 <@i64> = 0
.const @I64_1 <@i64> = 1

.funcsig @v_v = () -> ()
.typedef @frv_v = funcref<@v_v>

.const @NULLREF     <@refvoid>  = NULL
.const @NULLIREF    <@irefvoid> = NULL
.const @NULLFUNC    <@frv_v>    = NULL
.const @NULLSTACK   <@stack>    = NULL

.const @NULLREF_I64  <@refi64>  = NULL
.const @NULLIREF_I64 <@irefi64> = NULL
"""

hello_world_uir = """
.typedef @string = hybrid<
                    @i64    // hash
                    @i64    // length
                    @i8     // bytes
                    >
.typedef @ref_string = ref<@string>

.global @hello_world.g <@ref_string>
.global @newline.g <@ref_string>

.typedef @array_ref_string = hybrid<
                                @i64        // length
                                @ref_string // elements
                                >
.typedef @ref_array_ref_string = ref<@array_ref_string>
.typedef @iref_ref_string = iref<@ref_string>

.funcsig @_start.sig = () -> ()
.funcdef @_start VERSION %v1 <@_start.sig> {
    %entry():
        %rv = CALL <@main.sig> @main ()

        COMMINST @uvm.thread_exit
}

.funcsig @main.sig = () -> (@i32)
.funcdef @main VERSION %v1 <@main.sig> {
    %entry():
        %hw = LOAD <@ref_string> @hello_world.g
        CALL <@puts.sig> @puts (%hw)

        RET @I32_0
}

.typedef @size_t = int<64>
.funcsig @write.sig = (@i32 @ptrvoid @size_t) -> (@size_t)
.typedef @write.fp  = ufuncptr<@write.sig>
.global @write.g <@write.fp>

.funcsig @puts.sig = (@ref_string) -> ()
.funcdef @puts VERSION %v1 <@puts.sig> {
    %entry(<@ref_string> %str_r):
        CALL <@puts.sig> @print (%str_r)
        %nl = LOAD <@ref_string> @newline.g
        CALL <@puts.sig> @print (%nl)
        RET ()
}

.funcsig @print.sig = (@ref_string) -> ()
.funcdef @print VERSION %v1 <@print.sig> {
    %entry(<@ref_string> %str_r):
        %str_ir = GETIREF <@string> %str_r
        %len_ir = GETFIELDIREF <@string 1> %str_ir
        %len = LOAD <@i64> %len_ir
        %content_ir = GETVARPARTIREF <@string> %str_ir
        %content_ptr = COMMINST @uvm.native.pin <@irefi8> (%content_ir)
        %content_ptr_v = PTRCAST <@ptri8 @ptrvoid> %content_ptr

        %write = LOAD <@write.fp> @write.g
        %rv = CCALL #DEFAULT <@write.fp @write.sig> %write (@I32_1 %content_ptr_v %len)
        COMMINST @uvm.native.unpin <@irefi8> (%content_ir)

        RET ()
}
"""

hello_world_hail = """
.newhybrid $hw <@string> 12
.init $hw = {
    0
    12
    { 0x48 0x65 0x6c 0x6c 0x6f 0x20 0x77 0x6f 0x72 0x6c 0x64 0x21 }
    }

.newhybrid $nl <@string> 1
.init $nl = { 0 1 { 0x0a } }

.init @hello_world.g = $hw
.init @newline.g = $nl
"""

def load(ctx, bdl):
    size = rffi.cast(MuArraySize, len(bdl))
    with rffi.scoped_nonmovingbuffer(bdl) as buf:
        ctx.c_load_bundle(ctx, buf, size)

def main(argv):
    mu = mu_new()
    ctx = mu.c_new_context(mu)
    ctx_ptr = ctx

    load(ctx, prelude)
    load(ctx, hello_world_uir)

    size = rffi.cast(MuArraySize, len(hello_world_hail))
    with rffi.scoped_nonmovingbuffer(hello_world_hail) as buf:
        ctx.c_load_hail(ctx, buf, size)

    with rffi.scoped_nonmovingbuffer("@write.g\0") as buf:
        write_g_id = ctx.c_id_of(ctx_ptr, buf)

    write_g_hdle = ctx.c_handle_from_global(ctx, rffi.cast(MuID, write_g_id))

    with rffi.scoped_nonmovingbuffer("@write.fp\0") as buf:
        write_fp_id = ctx.c_id_of(ctx_ptr, buf)
    with rffi.scoped_nonmovingbuffer("/lib/x86_64-linux-gnu/libc-2.23.so\0") as buf:
        dlc = rdynload.dlopen(buf, rdynload.RTLD_LAZY)
    with rffi.scoped_nonmovingbuffer("write\0") as buf:
        addr = rdynload.dlsym(dlc, buf)

    write_addr = rffi.cast(MuCFP, addr)
    write_addr_hdle = ctx.c_handle_from_fp(ctx_ptr, write_fp_id, write_addr)
    ctx.c_store(ctx_ptr, rffi.cast(MuMemOrd._lltype, MuMemOrd.NOT_ATOMIC),
              write_g_hdle, write_addr_hdle)

    with rffi.scoped_nonmovingbuffer("@_start\0") as buf:
        _start_id = ctx.c_id_of(ctx_ptr, buf)
    _start_hdle = ctx.c_handle_from_func(ctx_ptr, _start_id)
    stack_hdle = ctx.c_new_stack(ctx_ptr, _start_hdle)
    thread_hdle = ctx.c_new_thread_nor(ctx_ptr, stack_hdle,
                                       rffi.cast(MuValue, 0),
                                       rffi.cast(MuValuePtr, 0),
                                       rffi.cast(MuArraySize, 0))

    mu.c_execute(mu)

    mu_close(mu)
    return 0


def target(*args):
    return main, None


if __name__ == '__main__':
    import sys
    main(sys.argv)