from impl_test_util import impl_jit_test


def build_test_bundle(bldr, rmu):
    """
    Builds the following test bundle.
        .typedef @i32 = int<32>
        .const @0_i32 <@i32> = 0
        .funcsig @sig__i32 = () -> (@i32)
        .funcdecl @test_fnc <@fnrsig__i32>
        .funcdef @test_fnc VERSION @test_fnc_v1 <@sig__i32> {
            @test_fnc_v1.blk0():
                RET @0_i32
        }
    :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
    """
    i32 = bldr.gen_sym("@i32")
    bldr.new_type_int(i32, 8)

    c_0_i32 = bldr.gen_sym("@0_i32")
    bldr.new_const_int(c_0_i32, i32, 0)

    sig__i32 = bldr.gen_sym("@sig__i32")
    bldr.new_funcsig(sig__i32, [], [i32])

    test_fnc = bldr.gen_sym("@test_fnc")
    bldr.new_func(test_fnc, sig__i32)

    # function body
    v1 = bldr.gen_sym("@test_fnc_v1")
    blk0 = bldr.gen_sym("@test_fnc_v1.blk0")
    res = bldr.gen_sym("@test_fnc_v1.blk0.res")
    op_ret = bldr.gen_sym()
    bldr.new_ret(op_ret, [c_0_i32])
    bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_ret])
    bldr.new_func_ver(v1, test_fnc, [blk0])

    return {
        "@i32": i32,
        "test_fnc_sig": sig__i32,
        "test_fnc": test_fnc,
        "result_type": i32
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