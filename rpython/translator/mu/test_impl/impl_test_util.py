import sys

def extend_with_entrypoint(bldr, id_dict, rmu):
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
    bldr.new_call(op_call, [res], test_fnc_sig, test_fnc, [])
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


def impl_jit_test(opts, test_bundle_building_fn, extend_fnc=extend_with_entrypoint, extra_srcs=[]):
    if opts.run:
        if opts.impl == 'ref':
            from rpython.rlib import rmu
        else:
            from rpython.rlib import rmu_fast as rmu
    else:
        if opts.impl == 'ref':
            from rpython.rlib import rmu_genc as rmu
        else:
            from rpython.rlib import rmu_genc_fast as rmu
        rmu.get_global_apilogger().clear()

    if opts.impl == 'ref':
        vmargs = 'vmLog=ERROR'
    else:
        vmargs = '--log-level=none --aot-emit-dir=emit'
    mu = rmu.MuVM(vmargs)
    ctx = mu.new_context()
    bldr = ctx.new_ir_builder()

    id_dict = test_bundle_building_fn(bldr, rmu)

    if opts.testjit:
        bldr.load()
        if sys.platform.startswith('linux'):
            libext = '.so'
        elif sys.platform.startswith('darwin'):
            libext = '.dylib'
        else:
            libext = '.dll'
        lib_path = opts.output[:-2] + libext
        mu.compile_to_sharedlib(lib_path, extra_srcs)
        symbol = "test_fnc"
        if opts.run:
            print "compiled shared library:", lib_path
            import ctypes
            lib = ctypes.CDLL(lib_path)
            fn = getattr(lib, symbol)
            res = fn()
            print "fn() =", res
        else:
            log = rmu.get_global_apilogger()
            # lib = rmu.CVar("void*", "lib")
            # log.logcall("dlopen", [lib_path, "RTLD_LAZY"], lib, context=None)
            # fn = rmu.CFuncPtr([], "int", "fn")
            # log.logcall("dlsym", [lib, rmu.CStr(symbol)], fn, context=None)
            # res = rmu.CVar("int", "res")
            # log.logcall("fn", [], res, context=None)
            # log.logcall("dlclose", [lib], None, context=None)

            # just print out the compiled library name
            log.logcall("printf", [rmu.CStr("%s\\n"), rmu.CStr(lib_path)], None, context=None)
            with open(opts.output, 'w') as fp:
                log.genc(fp)

        # # NOTE: below is just a mock up
        # lib_path = "libfnc.dylib"
        # symbol = "fnc"
        # if opts.run:
        #     import ctypes
        #     lib = ctypes.CDLL(lib_path)
        #     fn = getattr(lib, symbol)
        #     print "fn() =", fn()
        # else:
        #     log = rmu.get_global_apilogger()
        #     lib = rmu.CVar("void*", "lib")
        #     log.logcall("dlopen", [rmu.CStr(lib_path), "RTLD_LAZY"], lib, context=None)
        #     fn = rmu.CFuncPtr([], "int", "fn")
        #     log.logcall("dlsym", [lib, rmu.CStr(symbol)], fn, context=None)
        #     res = rmu.CVar("int", "res")
        #     log.logcall("fn", [], res, context=None)
        #     log.logcall("printf", [rmu.CStr("fn() = %d\\n"), res], None, context=None)
        #     log.logcall("dlclose", [lib], None, context=None)
        #     with open(opts.output, 'w') as fp:
        #         log.genc(fp)
    else:
        extend_fnc(bldr, id_dict, rmu)
        entry = id_dict['@entry']
        result = id_dict['@result']
        i32 = id_dict['@i32']
        ppi8 = id_dict['@ppi8']

        bldr.load()

        # execute and get result
        hdl = ctx.handle_from_func(entry)
        stk = ctx.new_stack(hdl)
        hargc = ctx.handle_from_sint32(1, i32)
        if opts.run:
            from rpython.rtyper.lltypesystem import rffi
            c_argv = rffi.liststr2charpp(["entry"])
            hargv = ctx.handle_from_ptr(ppi8, rffi.cast(rffi.VOIDP, c_argv))
        else:  # HACK
            hargv = ctx.handle_from_ptr(ppi8, '(char **){&"entry"}')
        thd = ctx.new_thread_nor(stk, rmu.null(rmu.MuThreadRefValue), [hargc, hargv])
        if opts.impl == 'ref':
            mu.execute()

        hres = ctx.load(rmu.MuMemOrd.NOT_ATOMIC, ctx.handle_from_global(result))
        if opts.run:
            res_val = getattr(ctx, 'handle_to_' + id_dict.get('handle_conv_dst_type', 'uint64'))(hres)
            print "result =", res_val

            rffi.free_charpp(c_argv)    # clean up
        else:  # HACK again
            log = rmu.get_global_apilogger()
            res_val = ctx.handle_to_uint64(hres)
            if opts.impl == 'ref':
                log.logcall("printf", [rmu.CStr("result = %d\\n"), res_val], None, context=None, check_err=False)
            else:
                log.logcall("printf", [rmu.CStr("result = %d\\n"), res_val], None, context=None)
            with open(opts.output, 'w') as fp:
                log.genc(fp, exitcode=res_val)

    # return
    if opts.run:
        return res_val
