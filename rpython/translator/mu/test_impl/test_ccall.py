from impl_test_util import impl_jit_test

def build_test_bundle(bldr, rmu):
    """
    Builds the following test bundle.
        .typedef @i64 = int<64>
        .funcsig @sig_i64_i64 = (@i64) -> (@i64)
        .typedef @fnpsig_i64_i64 = ufuncptr<@sig_i64_i64>
        .const @c_fnc = "fnc"
        .funcdef @test_ccall VERSION @test_ccall_v1 <@sig_i64_i64> {
            @test_ccall_v1.blk0(<@i64> @test_ccall_v1.blk0.k):
                @test_ccall_v1.blk0.res = CCALL <@sig_i64_i64> @c_fnc (@test_ccall_v1.blk0.k)
                RET @test_ccall_v1.blk0.res
        }

    :type bldr: rpython.rlib.rmu.MuIRBuilder
    :type rmu: rpython.rlib.rmu
    :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
    """
    i64 = bldr.gen_sym("@i64")
    bldr.new_type_int(i64, 64)

    sig_i64_i64 = bldr.gen_sym("@sig_i64_i64")
    bldr.new_funcsig(sig_i64_i64, [i64], [i64])

    fnpsig_i64_i64 = bldr.gen_sym("@fnpsig_i64_i64")
    bldr.new_type_ufuncptr(fnpsig_i64_i64, sig_i64_i64)

    c_fnc = bldr.gen_sym("@c_fnc")
    bldr.new_const_extern(c_fnc, fnpsig_i64_i64, "fnc")

    test_ccall = bldr.gen_sym("@test_ccall")
    bldr.new_func(test_ccall, sig_i64_i64)

    # function body
    v1 = bldr.gen_sym("@test_ccall_v1")
    blk0 = bldr.gen_sym("@test_ccall_v1.blk0")

    # blk0
    blk0_k = bldr.gen_sym("@test_ccall_v1.blk0.k")
    blk0_res = bldr.gen_sym("@test_ccall_v1.blk0.res")
    op_ccall = bldr.gen_sym()
    bldr.new_ccall(op_ccall, [blk0_res], rmu.MuCallConv.DEFAULT, fnpsig_i64_i64, sig_i64_i64, c_fnc, [blk0_k])
    op_ret = bldr.gen_sym()
    bldr.new_ret(op_ret, [blk0_res])
    bldr.new_bb(blk0, [blk0_k], [i64], rmu.MU_NO_ID, [op_ccall, op_ret])

    bldr.new_func_ver(v1, test_ccall, [blk0])

    return {
        "@i64": i64,
        "test_fnc_sig": sig_i64_i64,
        "test_fnc": test_ccall,
        "fncs": [test_ccall],
        "result_type": i64
    }

def extend_with_entrypoint(bldr, id_dict, rmu):
    """
        Extend the bundle with:
            .typedef @i32 = int<32>
            .const @0x8d9f9c1d58324b55_i64 <@i64> = 0x8d9f9c1d58324b55
            .typedef @i8 = int<8>
            .typedef @pi8 = uptr<@i8>
            .typedef @ppi8 = uptr<@pi8>
            .global @result <@i8>
            .funcsig @sig_i8ppi8_ = (@i8 @ppi8) -> ()
            .funcdef @entry VERSION @entry_v1 <@sig_i8ppi8_> {
                .blk0 (<@i8> argc <@ppi8> argv):
                    %res = CALL @test_fnc (@0x8d9f9c1d58324b55_i64)
                    STORE <i8> @result %res
                    COMMINST @uvm.thread_exit
            }
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
    pi8 = bldr.gen_sym("@pi8")
    bldr.new_type_uptr(pi8, i8)
    ppi8 = bldr.gen_sym("@ppi8")
    bldr.new_type_uptr(ppi8, pi8)
    i64 = id_dict['@i64']
    c_0x8d9f9c1d58324b55_i64 = bldr.gen_sym("@0x8d9f9c1d58324b55_i64")
    bldr.new_const_int(c_0x8d9f9c1d58324b55_i64, i64, 0x8d9f9c1d58324b55)
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
    bldr.new_call(op_call, [res], test_fnc_sig, test_fnc, [c_0x8d9f9c1d58324b55_i64])
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
    arg_vmargs = parser.add_argument('--vmargs', type=str,
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

    impl_jit_test(opts, build_test_bundle, extend_with_entrypoint, ["test_ccall_fnc.c"])