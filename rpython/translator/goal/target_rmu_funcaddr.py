"""
Hello world program
Touches on how to load a C function address.

Run with:
    PYTHONPATH=$PYPY_MU:$PYTHONPATH LIBRARY_PATH=$MU/cbinding:$LIBRARY_PATH python target_rmu_funcaddr.py
OR:
    rpython target_rmu_funcaddr.py
    LD_LIBRARY_PATH=$MU/cbinding:$LD_LIBRARY_PATH ./target_rmu_funcaddr-c
"""
from rpython.rlib.rmu import *
from rpython.rlib import rposix
from rpython.rlib.objectmodel import we_are_translated

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


def main(argv):
    mu = MuVM("vmLog=ERROR")
    ctx = mu.new_context()

    ctx.load_bundle(prelude)
    ctx.load_bundle(hello_world_uir)
    ctx.load_hail(hello_world_hail)
    write_g_id = ctx.id_of("@write.g")
    write_g_hdle = ctx.handle_from_global(write_g_id)
    write_fp_id = ctx.id_of("@write.fp")
    ll_fncptr = rposix.c_write._ptr
    if we_are_translated():
        addr = ll_fncptr
    else:
        import ctypes
        from rpython.rtyper.lltypesystem.ll2ctypes import get_ctypes_callable, ctypes2lltype
        from rpython.rtyper.lltypesystem import llmemory
        c_fncptr = get_ctypes_callable(ll_fncptr, ll_fncptr._obj.calling_conv)
        addr = ctypes2lltype(llmemory.Address, ctypes.cast(c_fncptr, ctypes.c_void_p).value)
    write_addr = rffi.cast(MuCFP, addr)
    write_addr_hdle = ctx.handle_from_fp(write_fp_id, write_addr)
    ctx.store(MuMemOrd.NOT_ATOMIC, write_g_hdle, write_addr_hdle)
    _start_id = ctx.id_of("@_start")
    _start_hdle = ctx.handle_from_func(_start_id)
    stack_hdle = ctx.new_stack(_start_hdle)
    thread_hdle = ctx.new_thread_nor(stack_hdle, rffi.cast(MuRefValue, 0), [])
    mu.execute()

    mu.close()
    return 0


def target(*args):
    return main, None


if __name__ == '__main__':
    import sys
    main(sys.argv)