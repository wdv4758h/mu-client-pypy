"""
Build a simple factorial bundle using MuAPI and run it.

Run with:
    PYTHONPATH=$PYPY_MU:$PYTHONPATH LIBRARY_PATH=$MU/cbinding:$LIBRARY_PATH python target_rmu_bundlebuilding.py
OR:
    rpython target_rmu_bundlebuilding.py
    LD_LIBRARY_PATH=$MU/cbinding:$LD_LIBRARY_PATH ./target_rmu_bundlebuilding-c
"""
from rpython.rlib.rmu_genc import *

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
    mu = MuVM("vmLog=ERROR")
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
    mu = MuVM("vmLog=ERROR")
    ctx = mu.new_context()
    bldr = ctx.new_ir_builder()

    i64 = bldr.gen_sym("@i64")
    bldr.new_type_int(i64, 64)
    i1 = bldr.gen_sym("@i1")
    bldr.new_type_int(i1, 1)

    c_0_i64 = bldr.gen_sym("@0_i64")
    bldr.new_const_int(c_0_i64, i64, 0)
    c_1_i64 = bldr.gen_sym("@1_i64")
    bldr.new_const_int(c_1_i64, i64, 1)
    c_10_i64 = bldr.gen_sym("@10_64")
    bldr.new_const_int(c_10_i64, i64, 10)

    gblres = bldr.gen_sym("@gblresult")
    bldr.new_global_cell(gblres, i64)

    # ----
    # fac

    sig_i64_i64 = bldr.gen_sym("@sig_i64_i64")
    bldr.new_funcsig(sig_i64_i64, [i64], [i64])

    fac = bldr.gen_sym("@fac")
    bldr.new_func(fac, sig_i64_i64)
    fac_v1 = bldr.gen_sym()
    blk0 = bldr.gen_sym()
    blk1 = bldr.gen_sym()
    blk2 = bldr.gen_sym()
    fac_v1 = bldr.new_func_ver(fac_v1, fac, [blk0, blk1, blk2])

    # blk0
    n_0 = bldr.gen_sym()
    v5 = bldr.gen_sym()
    v6 = bldr.gen_sym()
    v7 = bldr.gen_sym()
    blk0_cmp0 = bldr.gen_sym()
    blk0_cmp1 = bldr.gen_sym()
    blk0_or = bldr.gen_sym()
    blk0_br2 = bldr.gen_sym()
    blk0_br2_t = bldr.gen_sym()
    blk0_br2_f = bldr.gen_sym()
    bldr.new_bb(blk0, [n_0], [i64], MU_NO_ID, [blk0_cmp0, blk0_cmp1, blk0_or, blk0_br2])
    bldr.new_cmp(blk0_cmp0, v5, MuCmpOptr.EQ, i64, n_0, c_0_i64)
    bldr.new_cmp(blk0_cmp1, v6, MuCmpOptr.EQ, i64, n_0, c_1_i64)
    bldr.new_binop(blk0_or, v7, MuBinOptr.OR, i1, v5, v6)
    bldr.new_dest_clause(blk0_br2_t, blk2, [c_1_i64])
    bldr.new_dest_clause(blk0_br2_f, blk1, [n_0])
    bldr.new_branch2(blk0_br2, v7, blk0_br2_t, blk0_br2_f)

    # blk1
    n_1 = bldr.gen_sym()
    v8 = bldr.gen_sym()
    v9 = bldr.gen_sym()
    v10 = bldr.gen_sym()
    blk1_sub = bldr.gen_sym()
    blk1_call = bldr.gen_sym()
    blk1_mul = bldr.gen_sym()
    blk1_br = bldr.gen_sym()
    blk1_br_d = bldr.gen_sym()
    bldr.new_bb(blk1, [n_1], [i64], MU_NO_ID, [blk1_sub, blk1_call, blk1_mul, blk1_br])
    bldr.new_binop(blk1_sub, v8, MuBinOptr.SUB, i64, n_1, c_1_i64)
    bldr.new_call(blk1_call, [v9], sig_i64_i64, fac, [v8])
    bldr.new_binop(blk1_mul, v10, MuBinOptr.MUL, i64, n_1, v9)
    bldr.new_dest_clause(blk1_br_d, blk2, [v10])
    bldr.new_branch(blk1_br, blk1_br_d)

    # blk2
    v11 = bldr.gen_sym()
    blk2_ret = bldr.gen_sym()
    bldr.new_bb(blk2, [v11], [i64], MU_NO_ID, [blk2_ret])
    bldr.new_ret(blk2_ret, [v11])

    # ----
    # main
    sig__ = bldr.gen_sym("@sig__")
    main = bldr.gen_sym("@main")
    main_v1 = bldr.gen_sym("@main_v1")
    bldr.new_funcsig(sig__, [], [])
    bldr.new_func(main, sig__)
    blk0 = bldr.gen_sym()
    bldr.new_func_ver(main_v1, main, [blk0])


    # blk0
    res = bldr.gen_sym()
    blk0_call = bldr.gen_sym()
    blk0_store = bldr.gen_sym()
    blk0_comminst = bldr.gen_sym()
    bldr.new_bb(blk0, [], [], MU_NO_ID, [blk0_call, blk0_store, blk0_comminst])
    bldr.new_call(blk0_call, [res], sig_i64_i64, fac, [c_10_i64])
    bldr.new_store(blk0_store, False, MuMemOrd.NOT_ATOMIC, i64, gblres, res)
    bldr.new_comminst(blk0_comminst, [], MuCommInst.THREAD_EXIT, [], [], [], [])

    bldr.load()

    main_h = ctx.handle_from_func(main)
    stack_h = ctx.new_stack(main_h)
    thread_h = ctx.new_thread_nor(stack_h, lltype.nullptr(MuValue.TO), [])

    mu.execute()

    # Load result from global cell
    gbl_h = ctx.handle_from_global(gblres)
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