from impl_test_util import impl_jit_test

def build_test_bundle(bldr, rmu):
    """
    Builds the following test bundle.
        .typedef @i64 = int<64>
        .const @0_i64 <@i64> = 0
        .const @1_i64 <@i64> = 1
        .const @2_i64 <@i64> = 2
        .const @20_i64 = 20
        .funcsig @sig_i64_i64 = (@i64) -> (@i64)
        .funcsig @sig__i64 = () -> (@i64)
        .funcdef @fib VERSION @fib_v1 <@sig_i64_i64> {
            @fib_v1.blk0(<@i64> @fib_v1.blk0.k):
                SWITCH <@i64> @fib_v1.blk0.k @fib_v1.blk2 (@fib_v1.blk0.k) {
                    @0_i64 @fib_v1.blk1 (@0_i64)
                    @1_i64 @fib_v1.blk1 (@1_i64)
                }
            @fib_v1.blk1(<@i64> @fib_v1.blk1.rtn):
                RET @fib_v1.blk1.rtn
            @fib_v1.blk2(<@i64> @fib_v1.blk1.k):
                @fib_v1.blk2.k_1 = SUB <@i64> @fib_v1.blk2.k @1_i64
                @fib_v1.blk2.res1 = CALL <@sig_i64_i64> @fib (@fib_v1.blk2.k_1)
                @fib_v1.blk2.k_2 = SUB <@i64> @fib_v1.blk2.k @2_i64
                @fib_v1.blk2.res2 = CALL <@sig_i64_i64> @fib (@fib_v1.blk2.k_2)
                @fib_v1.blk2.res = ADD <@i64> @fib_v1.blk2.res1 @fib_v1.blk2.res2
                RET @fib_v1.blk2.res2
        }
        .funcdef @entry VERSION @entry_v1 <@sig__i64> {
            @entry_v1.blk0 ():
                @entry_v1.blk0.res = CALL @fib (@20_i64)
                RET @entry_v1.blk0.res
        }

    :type bldr: rpython.rlib.rmu.MuIRBuilder
    :type rmu: rpython.rlib.rmu
    :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
    """
    i64 = bldr.gen_sym("@i64")
    bldr.new_type_int(i64, 64)

    c_0_i64 = bldr.gen_sym("@0_i64")
    bldr.new_const_int(c_0_i64, i64, 0)
    c_1_i64 = bldr.gen_sym("@1_i64")
    bldr.new_const_int(c_1_i64, i64, 1)
    c_2_i64 = bldr.gen_sym("@2_i64")
    bldr.new_const_int(c_2_i64, i64, 2)
    c_20_i64 = bldr.gen_sym("@20_i64")
    bldr.new_const_int(c_20_i64, i64, 20)

    sig_i64_i64 = bldr.gen_sym("@sig_i64_i64")
    bldr.new_funcsig(sig_i64_i64, [i64], [i64])
    sig__i64 = bldr.gen_sym("@sig__i64")
    bldr.new_funcsig(sig__i64, [], [i64])

    fib = bldr.gen_sym("@fib")
    bldr.new_func(fib, sig_i64_i64)

    # function body
    v1 = bldr.gen_sym("@fib_v1")
    blk0 = bldr.gen_sym("@fib_v1.blk0")
    blk1 = bldr.gen_sym("@fib_v1.blk1")
    blk2 = bldr.gen_sym("@fib_v1.blk2")

    # blk0
    blk0_k = bldr.gen_sym("@fib_v1.blk0.k")
    dest_defl = bldr.gen_sym()
    dest_0 = bldr.gen_sym()
    dest_1 = bldr.gen_sym()
    bldr.new_dest_clause(dest_defl, blk2, [blk0_k])
    bldr.new_dest_clause(dest_0, blk1, [c_0_i64])
    bldr.new_dest_clause(dest_1, blk1, [c_1_i64])
    op_switch = bldr.gen_sym()
    bldr.new_switch(op_switch, i64, blk0_k, dest_defl, [c_0_i64, c_1_i64], [dest_0, dest_1])
    bldr.new_bb(blk0, [blk0_k], [i64], rmu.MU_NO_ID, [op_switch])

    # blk1
    blk1_rtn = bldr.gen_sym("@fig_v1.blk1.rtn")
    blk1_op_ret = bldr.gen_sym()
    bldr.new_ret(blk1_op_ret, [blk1_rtn])
    bldr.new_bb(blk1, [blk1_rtn], [i64], rmu.MU_NO_ID, [blk1_op_ret])

    # blk2
    blk2_k = bldr.gen_sym("@fig_v1.blk2.k")
    blk2_k_1 = bldr.gen_sym("@fig_v1.blk2.k_1")
    blk2_k_2 = bldr.gen_sym("@fig_v1.blk2.k_2")
    blk2_res = bldr.gen_sym("@fig_v1.blk2.res")
    blk2_res1 = bldr.gen_sym("@fig_v1.blk2.res1")
    blk2_res2 = bldr.gen_sym("@fig_v1.blk2.res2")
    op_sub_1 = bldr.gen_sym()
    bldr.new_binop(op_sub_1, blk2_k_1, rmu.MuBinOptr.SUB, i64, blk2_k, c_1_i64)
    op_call_1 = bldr.gen_sym()
    bldr.new_call(op_call_1, [blk2_res1], sig_i64_i64, fib, [blk2_k_1])
    op_sub_2 = bldr.gen_sym()
    bldr.new_binop(op_sub_2, blk2_k_2, rmu.MuBinOptr.SUB, i64, blk2_k, c_2_i64)
    op_call_2 = bldr.gen_sym()
    bldr.new_call(op_call_2, [blk2_res2], sig_i64_i64, fib, [blk2_k_2])
    op_add = bldr.gen_sym()
    bldr.new_binop(op_add, blk2_res, rmu.MuBinOptr.ADD, i64, blk2_res1, blk2_res2)
    blk2_op_ret = bldr.gen_sym()
    bldr.new_ret(blk2_op_ret, [blk2_res])
    bldr.new_bb(blk2, [blk2_k], [i64], rmu.MU_NO_ID,
                [op_sub_1, op_call_1, op_sub_2, op_call_2, op_add, blk2_op_ret])
    bldr.new_func_ver(v1, fib, [blk0, blk1, blk2])

    entry = bldr.gen_sym("@entry")
    bldr.new_func(entry, sig__i64)
    entry_v1 = bldr.gen_sym("@entry_v1")

    entry_blk0 = bldr.gen_sym("@entry_v1.blk0")
    entry_blk0_res = bldr.gen_sym("@entry_v1.blk0.res")
    op_call = bldr.gen_sym()
    bldr.new_call(op_call, [entry_blk0_res], sig_i64_i64, fib, [c_20_i64])
    op_ret = bldr.gen_sym()
    bldr.new_ret(op_ret, [entry_blk0_res])
    bldr.new_bb(entry_blk0, [], [], rmu.MU_NO_ID, [op_call, op_ret])
    bldr.new_func_ver(entry_v1, entry, [entry_blk0])

    return {
        "@i64": i64,
        "test_fnc_sig": sig__i64,
        "test_fnc": entry,
        "fncs": [entry, fib],
        "result_type": i64
    }

if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument('--impl', type=str, choices=['ref', 'fast'], default='ref',
                        help='Compile script to C targeting the selected implementation of Mu.')
    parser.add_argument('--run', action='store_true',
                        help='Run the script under RPython FFI on Mu Scala reference implementation.')
    arg_testjit = parser.add_argument('--testjit', action='store_true',
                                      help='Renerate C source file that can be used to test the JIT.')
    parser.add_argument('-o', '--output', help='File name of the generated C source file.')
    argv = sys.argv[1:]
    opts = parser.parse_args(argv)
    if opts.testjit:
        if not (opts.impl == 'fast'):
            raise argparse.ArgumentError(arg_testjit,
                                         "must be specified with '--impl fast'.")

    impl_jit_test(opts, build_test_bundle)