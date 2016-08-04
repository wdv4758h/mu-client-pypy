"""
Build a simple factorial bundle using MuAPI and run it.

Run with:
    PYTHONPATH=$PYPY_MU:$PYTHONPATH LIBRARY_PATH=$MU/cbinding:$LIBRARY_PATH python target_rmu_bundlebuilding.py
OR:
    rpython target_rmu_bundlebuilding.py
    LD_LIBRARY_PATH=$MU/cbinding:$LD_LIBRARY_PATH ./target_rmu_bundlebuilding-c
"""
from rpython.rlib.rmu import *

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
    with Mu() as mu:
        ctx = mu.new_context()
        ctx.load_bundle(fac_bundle)
    
        # Get handle to @main function, and execute it
        main_id = ctx.id_of("@main")
        main_h = ctx.handle_from_func(main_id)
        stack_h = ctx.new_stack(main_h)
        thread_h = ctx.new_thread_nor(stack_h, lltype.nullptr(MuValue.TO), [])
        mu.execute()
    
        # Load result from global cell
        gbl_id = ctx.id_of("@gblresult")
        gbl_h = ctx.handle_from_global(gbl_id)
        res_h = ctx.load(MuMemOrd.NOT_ATOMIC, gbl_h)
        res = ctx.handle_to_sint64(res_h)
    
        print "fac(10) = %d" % res
    return 0

def main_build(argv):
    mu = Mu()
    ctx = mu.new_context()

    bdl = ctx.new_bundle()
    i64 = ctx.new_type_int(bdl, 64)
    ctx.set_name(bdl, i64, "@i64")
    i1 = ctx.new_type_int(bdl, 1)
    ctx.set_name(bdl, i1, "@i1")

    c_0_i64 = ctx.new_const_int(bdl, i64, 0)
    ctx.set_name(bdl, c_0_i64, "@0_i64")
    c_1_i64 = ctx.new_const_int(bdl, i64, 1)
    ctx.set_name(bdl, c_1_i64, "@1_i64")
    c_10_i64 = ctx.new_const_int(bdl, i64, 10)
    ctx.set_name(bdl, c_10_i64, "@10_i64")

    gblres = ctx.new_global_cell(bdl, i64)
    ctx.set_name(bdl, gblres, "@gblresult")

    # ----
    # fac
    sig_i64_i64 = ctx.new_funcsig(bdl, [i64], [i64])
    ctx.set_name(bdl, sig_i64_i64, "@sig_i64_i64")

    fac = ctx.new_func(bdl, sig_i64_i64)
    ctx.set_name(bdl, fac, "@fac")
    fac_v1 = ctx.new_func_ver(bdl, fac)

    # blk0
    blk0 = ctx.new_bb(fac_v1)
    n_0 = ctx.new_nor_param(blk0, i64)
    v5 = ctx.get_inst_res(ctx.new_cmp(blk0, MuCmpOptr.EQ, i64, n_0, c_0_i64), 0)
    v6 = ctx.get_inst_res(ctx.new_cmp(blk0, MuCmpOptr.EQ, i64, n_0, c_1_i64), 0)
    v7 = ctx.get_inst_res(ctx.new_binop(blk0, MuBinOptr.OR, i1, v5, v6), 0)
    br2 = ctx.new_branch2(blk0, v7)
    blk1 = ctx.new_bb(fac_v1)
    blk2 = ctx.new_bb(fac_v1)
    ctx.add_dest(br2, MuDestKind.TRUE, blk2, [c_1_i64])
    ctx.add_dest(br2, MuDestKind.FALSE, blk1, [n_0])

    # blk1
    n_1 = ctx.new_nor_param(blk1, i64)
    v8 = ctx.get_inst_res(ctx.new_binop(blk1, MuBinOptr.SUB, i64, n_1, c_1_i64), 0)
    v9 = ctx.get_inst_res(ctx.new_call(blk1, sig_i64_i64, fac, [v8]), 0)
    v10 = ctx.get_inst_res(ctx.new_binop(blk1, MuBinOptr.MUL, i64, n_1, v9), 0)
    br = ctx.new_branch(blk1)
    ctx.add_dest(br, MuDestKind.NORMAL, blk2, [v10])

    # blk2
    v11 = ctx.new_nor_param(blk2, i64)
    ctx.new_ret(blk2, [v11])

    # ----
    # main
    sig__ = ctx.new_funcsig(bdl, [], [])
    ctx.set_name(bdl, sig__, "@sig__")
    main = ctx.new_func(bdl, sig__)
    ctx.set_name(bdl, main, "@main")
    main_v1 = ctx.new_func_ver(bdl, main)

    # blk0
    blk0 = ctx.new_bb(main_v1)
    res = ctx.get_inst_res(ctx.new_call(blk0, sig_i64_i64, fac, [c_10_i64]), 0)
    ctx.new_store(blk0, False, MuMemOrd.NOT_ATOMIC, i64, gblres, res)
    ctx.new_comminst(blk0, MuCommInst.UVM_THREAD_EXIT, [], [], [], [])

    main_id = ctx.get_id(bdl, main)
    ctx.load_bundle_from_node(bdl)

    main_h = ctx.handle_from_func(main_id)
    stack_h = ctx.new_stack(main_h)
    thread_h = ctx.new_thread_nor(stack_h, lltype.nullptr(MuValue.TO), [])

    mu.execute()

    # Load result from global cell
    gbl_id = ctx.id_of("@gblresult")
    gbl_h = ctx.handle_from_global(gbl_id)
    res_h = ctx.load(MuMemOrd.NOT_ATOMIC, gbl_h)
    res = ctx.handle_to_sint64(res_h)

    print "fac(10) = %d" % res

    mu.close()    # Don't forget to close it
    return 0


# ----------------------------------------------------------------------------------------
main = main_build
def target(*args):
    return main, None
if __name__ == "__main__":
    import sys
    main(sys.argv)