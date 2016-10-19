"""
Generate C source file that builds a bundle to
test the binary operations

Run on reference implementation with:
    $ PYTHONPATH=$PYPY_MU:$MU/tools python gen_test_binops.py
Compile to C, then compile with clang, then run:
    $ PYTHONPATH=$PYPY_MU:$MU/tools python gen_test_binops.py -c gen_test_binops.c
    $ clang -std=c99 -I$MU/cbinding -L$MU/cbinding -lmurefimpl2start -o test_binops gen_test_binops.c
    $ ./test_binops
"""

def build_test_bundle(rmu):
    """
    Builds the following test bundle.
        .typedef @i8 = int<8>
        .const @0xff_i8 <@i8> = 0xff
        .const @0x0a_i8 <@i8> = 0x0a
        .funcsig @sig__i8 = () -> (@i8)
        .funcdecl @test_fnc <@fnrsig__i8>
        .funcdef @test_fnc VERSION @test_fnc_v1 <@sig__i8> {
            @test_fnc_v1.blk0():
                @test_fnc_v1.blk0.res = ADD <@i8> @0xff_i8 @0x0a_i8
                RET @test_fnc_v1.blk0.res
        }
    :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
    """
    mu = rmu.MuVM()
    ctx = mu.new_context()
    bldr = ctx.new_ir_builder()

    i8 = bldr.gen_sym("@i8")
    bldr.new_type_int(i8, 8)

    c_0xff_i8 = bldr.gen_sym("@0xff_i8")
    bldr.new_const_int(c_0xff_i8, i8, 0xff)
    c_0x0a_i8 = bldr.gen_sym("@0x0a_i8")
    bldr.new_const_int(c_0x0a_i8, i8, 0x0a)

    sig__i8 = bldr.gen_sym("@sig__i8")
    bldr.new_funcsig(sig__i8, [], [i8])

    test_fnc = bldr.gen_sym("@test_fnc")
    bldr.new_func(test_fnc, sig__i8)

    # function body
    v1 = bldr.gen_sym("@test_fnc_v1")
    blk0 = bldr.gen_sym("@test_fnc_v1.blk0")
    res = bldr.gen_sym("@test_fnc_v1.blk0.res")
    op_add = bldr.gen_sym()
    bldr.new_binop(op_add, res, rmu.MuBinOptr.ADD, i8, c_0xff_i8, c_0x0a_i8)
    op_ret = bldr.gen_sym()
    bldr.new_ret(op_ret, [res])
    bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_add, op_ret])
    bldr.new_func_ver(v1, test_fnc, [blk0])

    return mu, ctx, bldr, {
        "@i8": i8,
        "@0xff_i8": c_0xff_i8,
        "@0x0a_i8": c_0x0a_i8,
        "@sig__i8": sig__i8,
        "@test_fnc": test_fnc,
    }

def main(opts):
    if opts.run:
        from rpython.rlib import rmu
    else:
        from rpython.rlib import rmu_genc as rmu

    mu, ctx, bldr, id_dict = build_test_bundle(rmu)

    if opts.impl == 'rust':
        raise NotImplementedError
    else:   # on Scala reference implementation
        """
        Extend the bundle with:
            .typedef @i32 = int<32>
            .typedef @i8 = int<8>
            .typedef @pi8 = uptr<@i8>
            .typedef @ppi8 = uptr<@pi8>
            .global @result <@i8>
            .funcsig @sig_i8ppi8_ = (@i8 @ppi8) -> ()
            .funcdef @entry VERSION @entry_v1 <@sig_i8ppi8_> {
                .blk0 (<@i8> argc <@ppi8> argv):
                    %res = CALL @test_fnc ()
                    STORE <i8> @result %res
                    COMMINST @uvm.thread_exit
            }
        """
        i8 = id_dict['@i8']
        sig__i8 = id_dict['@sig__i8']
        test_fnc = id_dict['@test_fnc']

        i32 = bldr.gen_sym("@i32")
        bldr.new_type_int(i32, 32)
        pi8 = bldr.gen_sym("@pi8")
        bldr.new_type_uptr(pi8, i8)
        ppi8 = bldr.gen_sym("@ppi8")
        bldr.new_type_uptr(ppi8, pi8)

        result = bldr.gen_sym("@result")
        bldr.new_global_cell(result, i8)

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
        bldr.new_call(op_call, [res], sig__i8, test_fnc, [])
        op_store = bldr.gen_sym()
        bldr.new_store(op_store, False, rmu.MuMemOrd.NOT_ATOMIC, i8, result, res)
        op_exit = bldr.gen_sym()
        bldr.new_comminst(op_exit, [], rmu.MuCommInst.THREAD_EXIT, [], [], [], [])
        bldr.new_bb(blk0, [argc, argv], [i32, ppi8], rmu.MU_NO_ID, [op_call, op_store, op_exit])
        bldr.new_func_ver(v1, entry, [blk0])

        bldr.load()

        # execute and get result
        hdl = ctx.handle_from_func(entry)
        stk = ctx.new_stack(hdl)
        hargc = ctx.handle_from_sint32(1, i32)
        if opts.run:
            from rpython.rtyper.lltypesystem import rffi
            hargv = ctx.handle_from_ptr(ppi8, rffi.cast(rffi.VOIDP, rffi.liststr2charpp(["entry"])))
        else:   # HACK
            hargv = ctx.handle_from_ptr(ppi8, '(char **){&"entry"}')
        thd = ctx.new_thread_nor(stk, rmu.null(rmu.MuThreadRefValue), [hargc, hargv])
        mu.execute()

        hres = ctx.load(rmu.MuMemOrd.NOT_ATOMIC, ctx.handle_from_global(result))
        if opts.run:
            res_val = ctx.handle_to_sint32(hres)
            print "result =", res_val
            assert res_val == 9
        else:   # HACK again
            log = rmu.get_global_apilogger()
            res_val = rmu.CVar('int', 'res_val')
            log.logcall("handle_to_sint32", [ctx._ctx, hres], res_val, ctx._ctx)
            log.logcall("printf", [rmu.CStr("result = %d\\n"), res_val], None, context=None, check_err=False)
            with open(opts.output, 'w') as fp:
                log.genc(fp, exitcode=res_val)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--impl', type=str, choices=['scala', 'rust'], default='scala',
                        help='Compile script to C targeting the selected implementation of Mu.')
    parser.add_argument('--run', action='store_true',
                        help='Run the script under RPython FFI on Mu Scala reference implementation.')
    parser.add_argument('-o', '--output', help='file name of the generated C source file.')
    opts = parser.parse_args()
    main(opts)