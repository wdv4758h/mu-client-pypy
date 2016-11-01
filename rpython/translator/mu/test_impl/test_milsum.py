from impl_test_util import impl_jit_test


def build_test_bundle(bldr, rmu):
    """
    Builds the following test bundle.
        .typedef @i64 = int<64>
        .const @0_i64 <@i64> = 0
        .const @1_i64 <@i64> = 1
        .funcsig @sig_i64_i64 = (@i64) -> (@i64)
        .funcdef @milsum VERSION @milsum.v1 <@sig_i64_i64> {
            @milsum.v1.blk0(<@i64> @milsum.v1.blk0.k):
                BRANCH @milsum.v1.blk1(@0_i64 @0_i64 @milsum.v1.blk0.k)

            @milsum.v1.blk1(<@i64> @milsum.v1.blk1.acc
                            <@i64> @milsum.v1.blk1.i
                            <@i64> @milsum.v1.blk1.end):
                @milsum.v1.blk1.cmpres = EQ <@i64> @milsum.v1.blk1.i @milsum.v1.blk1.end
                BRANCH2 @milsum.v1.blk1.cmpres
                    @milsum.v1.blk3(@milsum.v1.blk1.acc)
                    @milsum.v1.blk2(@milsum.v1.blk1.acc @milsum.v1.blk1.i @milsum.v1.blk1.end)

            @milsum.v1.blk2(<@i64> @milsum.v1.blk2.acc
                            <@i64> @milsum.v1.blk2.i
                            <@i64> @milsum.v1.blk2.end):
                @milsum.v1.blk2.i_res = ADD <@i64> @milsum.v1.blk2.i @1_64
                @milsum.v1.blk2.acc_res = ADD <@i64> @milsum.v1.blk2.acc @milsum.v1.blk2.i_res
                BRANCH @milsum.v1.blk1 (@milsum.v1.blk2.acc_res @milsum.v1.blk2.i_res @milsum.v1.blk2.end)

            @milsum.v1.blk3(<@i64> @milsum.v1.blk3.rtn):
                RET @milsum.v1.blk3.rtn
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

    sig_i64_i64 = bldr.gen_sym("@sig_i64_i64")
    bldr.new_funcsig(sig_i64_i64, [i64], [i64])

    milsum = bldr.gen_sym("@milsum")
    bldr.new_func(milsum, sig_i64_i64)

    # function body
    v1 = bldr.gen_sym("@milsum.v1")
    blk0 = bldr.gen_sym("@milsum.v1.blk0")
    blk1 = bldr.gen_sym("@milsum.v1.blk1")
    blk2 = bldr.gen_sym("@milsum.v1.blk2")
    blk3 = bldr.gen_sym("@milsum.v1.blk3")

    # blk0
    k = bldr.gen_sym("@milsum.v1.blk0.k")
    dst = bldr.gen_sym()
    bldr.new_dest_clause(dst, blk1, [c_0_i64, c_0_i64, k])
    op_branch = bldr.gen_sym()
    bldr.new_branch(op_branch, dst)
    bldr.new_bb(blk0, [k], [i64], rmu.MU_NO_ID, [op_branch])

    # blk1
    acc = bldr.gen_sym("@milsum.v1.blk1.acc")
    i = bldr.gen_sym("@milsum.v1.blk1.i")
    end = bldr.gen_sym("@milsum.v1.blk1.end")
    cmpres = bldr.gen_sym("@milsum.v1.blk1.cmpres")
    op_eq = bldr.gen_sym()
    bldr.new_cmp(op_eq, cmpres, rmu.MuCmpOptr.EQ, i64, i, end)
    op_br2 = bldr.gen_sym()
    dst_t = bldr.gen_sym()
    bldr.new_dest_clause(dst_t, blk3, [acc])
    dst_f = bldr.gen_sym()
    bldr.new_dest_clause(dst_f, blk2, [acc, i, end])
    bldr.new_branch2(op_br2, cmpres, dst_t, dst_f)
    bldr.new_bb(blk1, [acc, i, end], [i64, i64, i64], rmu.MU_NO_ID, [op_eq, op_br2])

    # blk2
    acc = bldr.gen_sym("@milsum.v1.blk2.acc")
    i = bldr.gen_sym("@milsum.v1.blk2.i")
    end = bldr.gen_sym("@milsum.v1.blk2.end")
    acc_res = bldr.gen_sym("@milsum.v1.blk2.acc_res")
    i_res = bldr.gen_sym("@milsum.v1.blk2.i_res")
    op_add_i = bldr.gen_sym()
    bldr.new_binop(op_add_i, i_res, rmu.MuBinOptr.ADD, i64, i, c_1_i64)
    op_add_acc = bldr.gen_sym()
    bldr.new_binop(op_add_acc, acc_res, rmu.MuBinOptr.ADD, i64, acc, i_res)
    dst = bldr.gen_sym()
    bldr.new_dest_clause(dst, blk1, [acc_res, i_res, end])
    op_br = bldr.gen_sym()
    bldr.new_branch(op_br, dst)
    bldr.new_bb(blk2, [acc, i, end], [i64, i64, i64], rmu.MU_NO_ID, [op_add_i, op_add_acc, op_br])


    # blk3
    rtn = bldr.gen_sym("@milsum.v1.blk3.rtn")
    op_ret = bldr.gen_sym()
    bldr.new_ret(op_ret, [rtn])
    bldr.new_bb(blk3, [rtn], [i64], rmu.MU_NO_ID, [op_ret])

    bldr.new_func_ver(v1, milsum, [blk0, blk1, blk2, blk3])

    return {
        "@i64": i64,
        "test_fnc_sig": sig_i64_i64,
        "test_fnc": milsum,
        "result_type": i64
    }


def extend_with_entrypoint(bldr, id_dict, rmu):
    """
        Extend the bundle with:
            .typedef @i32 = int<32>
            .typedef @i8 = int<8>
            .typedef @pi8 = uptr<@i8>
            .typedef @ppi8 = uptr<@pi8>
            .const @1000000_i64 = 1000000
            .global @result <@i8>
            .funcsig @sig_i8ppi8_ = (@i8 @ppi8) -> ()
            .funcdef @entry VERSION @entry_v1 <@sig_i8ppi8_> {
                .blk0 (<@i8> argc <@ppi8> argv):
                    %res = CALL @milsum (@1000000_i64)
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
    c_1000000_i64 = bldr.gen_sym("@1000000_i64")
    bldr.new_const_int(c_1000000_i64, i64, 1000000)
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
    bldr.new_call(op_call, [res], test_fnc_sig, test_fnc, [c_1000000_i64])
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
    arg_vmargs = parser.add_argument('--vmargs', type=str, default=None,
                                     help='MuVM arguments to be passed, only works with --impl ref.')
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
    if opts.vmargs:
        if not (opts.impl == 'ref'):
            raise argparse.ArgumentError(arg_vmargs,
                                         "must be specified with '--impl ref'.")

    impl_jit_test(opts, build_test_bundle, extend_with_entrypoint)