"""
Build a simple factorial bundle using MuAPI and run it.
"""
from rpython.rlib.rmu import *
from rpython.rtyper.lltypesystem import rffi

fac_bundle = """
.typedef @i64 = int<64>
.typedef @i1 = int<1>

.const @0_i64 <@i64> = 0
.const @1_i64 <@i64> = 1

.const @10_i64 <@i64> = 10

.global @gblresult <@i64>

.funcsig @sig_i64_i64 = (@i64) -> (@i64)
.funcdef @fac VERSION %v1 <@sig_i64_i64> {
    %blk0(<@i64> %n_0):
        %v5 = EQ <@i64> %n_0 @0_i64
        %v6 = EQ <@i64> %n_0 @1_i64
        %v7 = OR <@i1> %v5 %v6
        BRANCH2 %v7 %blk2(@1_i64) %blk1(%n_0)
    %blk1(<@i64> %n_1):
        %v8 = SUB <@i64> %n_1 @1_i64
        %v9 = CALL <@sig_i64_i64> @fac (%v8)
        %v10 = MUL <@i64> %n_1 %v9
        BRANCH %blk2(%v10)
    %blk2(<@i64> %v11):
        RET (%v11)
}

.funcsig @sig__ = () -> ()
.funcdef @main VERSION %v1 <@sig__> {
    %blk0():
        %res = CALL <@sig_i64_i64> @fac (@10_i64)
        STORE <@i64> @gblresult %res
        COMMINST @uvm.thread_exit
}
"""


def main_load(argv):
    # Load the bundle and run, verify its correctness
    mu = mu_new()
    ctx = mu.c_new_context(mu)
    with rffi.scoped_nonmovingbuffer(fac_bundle) as buf:
        size = rffi.cast(MuArraySize, len(fac_bundle))
        ctx.c_load_bundle(ctx, buf, size)

    # Get handle to @main function, and execute it
    with rffi.scoped_nonmovingbuffer("@main") as buf:
        main_id = ctx.c_id_of(ctx, buf)
    main_h = ctx.c_handle_from_func(ctx, main_id)
    stack_h = ctx.c_new_stack(ctx, main_h)
    thread_h = ctx.c_new_thread_nor(ctx, stack_h,
                                    lltype.nullptr(MuValue.TO),
                                    lltype.nullptr(MuValuePtr.TO),
                                    rffi.cast(MuArraySize, 0))

    mu.c_execute(mu)

    # Load result from global cell
    with rffi.scoped_nonmovingbuffer("@gblresult") as buf:
        gbl_id = ctx.c_id_of(ctx, buf)
    gbl_h = ctx.c_handle_from_global(ctx, gbl_id)
    res_h = ctx.c_load(ctx, rffi.cast(MuMemOrd._lltype, MuMemOrd.NOT_ATOMIC), gbl_h)
    res = ctx.c_handle_to_sint64(ctx, res_h)

    print "fac(10) = %d" % res
    mu_close(mu)
    return 0

def main_build(argv):
    def set_name(ctx, bdl, nd, s_name):
        with rffi.scoped_nonmovingbuffer(s_name) as buf:
            ctx.c_set_name(ctx, bdl, nd, buf)

    mu = mu_new()
    ctx = mu.c_new_context(mu)

    bdl = ctx.c_new_bundle(ctx)
    i64 = ctx.c_new_type_int(ctx, bdl, rffi.cast(rffi.INT, 64))
    set_name(ctx, bdl, i64, "@i64")
    i1 = ctx.c_new_type_int(ctx, bdl, rffi.cast(rffi.INT, 1))
    set_name(ctx, bdl, i1, "@i1")

    c_0_i64 = ctx.c_new_const_int(ctx, bdl, i64, rffi.cast(rffi.ULONG, 0))
    set_name(ctx, bdl, c_0_i64, "@0_i64")
    c_1_i64 = ctx.c_new_const_int(ctx, bdl, i64, rffi.cast(rffi.ULONG, 1))
    set_name(ctx, bdl, c_1_i64, "@1_i64")
    c_10_i64 = ctx.c_new_const_int(ctx, bdl, i64, rffi.cast(rffi.ULONG, 10))
    set_name(ctx, bdl, c_10_i64, "@10_i64")

    gblres = ctx.c_new_global_cell(ctx, bdl, i64)
    set_name(ctx, bdl, gblres, "@gblresult")
    with lltype.scoped_alloc(rffi.CArray(MuTypeNode), 1) as arr:
        arr[0] = i64
        sig = ctx.c_new_funcsig(ctx, bdl,
                                arr, rffi.cast(MuArraySize, 1),
                                arr, rffi.cast(MuArraySize, 1))
    set_name(ctx, bdl, sig, "@sig_i64_i64")


    mu_close(mu)
    return 0


# ----------------------------------------------------------------------------------------
main = main_build
def target(*args):
    return main, None
if __name__ == "__main__":
    import sys
    main(sys.argv)