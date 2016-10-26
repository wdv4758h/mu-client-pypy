from impl_test_util import impl_jit_test


def build_test_bundle(bldr, rmu):
    """
    Builds the following test bundle.
        .typedef @i64 = int<64>
        .const @0_i64 <@i64> = 0
        .const @1_i64 <@i64> = 1
        .const @2_i64 <@i64> = 2
        .funcsig @sig_i64_i64 = (@i64) -> (@i64)
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

    sig_i64_i64 = bldr.gen_sym("@sig_i64_i64")
    bldr.new_funcsig(sig_i64_i64, [i64], [i64])

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

    return {
        "@i64": i64,
        "test_fnc_sig": sig_i64_i64,
        "test_fnc": fib,
        "result_type": i64
    }


def extend_with_entrypoint(bldr, id_dict, rmu):
    """
        Extend the bundle with:
            .typedef @i32 = int<32>
            .typedef @i8 = int<8>
            .typedef @pi8 = uptr<@i8>
            .typedef @ppi8 = uptr<@pi8>
            .const @20_i64 = 20
            .global @result <@i8>
            .funcsig @sig_i8ppi8_ = (@i8 @ppi8) -> ()
            .funcdef @entry VERSION @entry_v1 <@sig_i8ppi8_> {
                .blk0 (<@i8> argc <@ppi8> argv):
                    %res = CALL @fib (@20_i64)
                    STORE <i8> @result %res
                    COMMINST @uvm.thread_exit
            }
    :type bldr: rpython.rlib.rmu.MuIRBuilder
    :type rmu: rpython.rlib.rmu
    """
    if '@i8' in id_dict:
        i8 = id_dict['@i8']
    else:
        i8 = bldr.gen_sym('@i8')
        bldr.new_type_int(i8, 8)

    test_fnc_sig = id_dict['test_fnc_sig']
    test_fnc = id_dict['test_fnc']
    result_type = id_dict['result_type']

    if '@i32' in id_dict:
        i32 = id_dict['@i32']
    else:
        i32 = bldr.gen_sym('@i32')
        bldr.new_type_int(i32, 32)
    i64 = id_dict['@i64']

    pi8 = bldr.gen_sym("@pi8")
    bldr.new_type_uptr(pi8, i8)
    ppi8 = bldr.gen_sym("@ppi8")
    bldr.new_type_uptr(ppi8, pi8)
    c_20_i64 = bldr.gen_sym("@20_i64")
    bldr.new_const_int(c_20_i64, i64, 20)
    result = bldr.gen_sym("@result")
    bldr.new_global_cell(result, result_type)
    sig_i32ppi8_ = bldr.gen_sym("@sig_i32ppi8_")
    bldr.new_funcsig(sig_i32ppi8_, [i32, ppi8], [])
    entry = bldr.gen_sym("@entry")
    bldr.new_func(entry, sig_i32ppi8_)
    # function body
    v1 = bldr.gen_sym("@entry_v1")
    blk0 = bldr.gen_sym()
    argc = bldr.gen_sym()
    argv = bldr.gen_sym()
    res = bldr.gen_sym()
    op_call = bldr.gen_sym()
    bldr.new_call(op_call, [res], test_fnc_sig, test_fnc, [c_20_i64])
    op_store = bldr.gen_sym()
    bldr.new_store(op_store, False, rmu.MuMemOrd.NOT_ATOMIC, result_type, result, res)
    op_exit = bldr.gen_sym()
    bldr.new_comminst(op_exit, [], rmu.MuCommInst.THREAD_EXIT, [], [], [], [])
    bldr.new_bb(blk0, [argc, argv], [i32, ppi8], rmu.MU_NO_ID, [op_call, op_store, op_exit])
    bldr.new_func_ver(v1, entry, [blk0])

    id_dict.update({
        '@entry': entry,
        '@i32': i32,
        '@ppi8': ppi8,
        '@result': result
    })


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

    impl_jit_test(opts, build_test_bundle, extend_with_entrypoint)