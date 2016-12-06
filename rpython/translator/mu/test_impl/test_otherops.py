from impl_test_util import impl_jit_test

def test_select(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i8 = int<8>
            .typedef @i64 = int<64>
            .const @10_i64 <@i64> = 10
            .const @20_i64 <@i64> = 20
            .const @TRUE <@i8> = 1
            .funcsig @sig_i8_i64 = (@i8) -> (@i64)
            .funcdef @test_fnc VERSION @test_fnc.v1 <@sig_i8_i64> {
                %blk0(<@i8> flag):
                    %cmpres = EQ <@i8> flag @TRUE
                    %res = SELECT <@i64> %cmpres @10_i64 @20_i64
                    RET %res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        i1 = bldr.gen_sym("@i1"); bldr.new_type_int(i1, 1)
        i8 = bldr.gen_sym("@i8"); bldr.new_type_int(i8, 8)
        i64 = bldr.gen_sym("@i64"); bldr.new_type_int(i64, 64)

        c_10_i64 = bldr.gen_sym("@10_i64"); bldr.new_const_int(c_10_i64, i64, 10)
        c_20_i64 = bldr.gen_sym("@20_i64"); bldr.new_const_int(c_20_i64, i64, 20)
        TRUE = bldr.gen_sym("@TRUE"); bldr.new_const_int(TRUE, i8, 1)

        sig_i8_i64 = bldr.gen_sym("@sig_i8_i64"); bldr.new_funcsig(sig_i8_i64, [i8], [i64])

        test_fnc = bldr.gen_sym("@test_fnc"); bldr.new_func(test_fnc, sig_i8_i64)

        test_fnc_v1 = bldr.gen_sym("@test_fnc.v1")
        blk0 = bldr.gen_sym("@test_fnc.v1.blk0")
        flag = bldr.gen_sym("@test_fnc.v1.blk0.flag")
        cmpres = bldr.gen_sym("@test_fnc.v1.blk0.cmpres")
        res = bldr.gen_sym("@test_fnc.v1.blk0.res")
        op_eq = bldr.gen_sym(); bldr.new_cmp(op_eq, cmpres, rmu.MuCmpOptr.EQ, i64, flag, TRUE)
        op_select = bldr.gen_sym(); bldr.new_select(op_select, res, i1, i64, cmpres, c_10_i64, c_20_i64)
        op_ret = bldr.gen_sym(); bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [flag], [i8], rmu.MU_NO_ID, [op_eq, op_select, op_ret])

        bldr.new_func_ver(test_fnc_v1, test_fnc, [blk0])

        return {
            "test_fnc": test_fnc,
            "test_fnc_sig": sig_i8_i64,
            "result_type": i64,
            "@i8": i8,
            "@i64": i64
        }

    def extend_with_entrypoint(bldr, id_dict, rmu):
        """
            Extend the bundle with:
                .typedef @i32 = int<32>
                .typedef @i8 = int<8>
                .typedef @pi8 = uptr<@i8>
                .typedef @ppi8 = uptr<@pi8>
                .const @FALSE <@i8> = 0
                .global @result <@i8>
                .funcsig @sig_i8ppi8_ = (@i8 @ppi8) -> ()
                .funcdef @entry VERSION @entry_v1 <@sig_i8ppi8_> {
                    .blk0 (<@i8> argc <@ppi8> argv):
                        %res = CALL @test_fnc (@FALSE)
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
        FALSE = bldr.gen_sym("@FALSE")
        bldr.new_const_int(FALSE, i8, 0)
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
        bldr.new_call(op_call, [res], test_fnc_sig, test_fnc, [FALSE])
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

    res = impl_jit_test(cmdopt, build_test_bundle, extend_with_entrypoint)
    if cmdopt.run:
        assert res == 20

def test_commoninst_pin(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i8 = int<8>
            .typedef @i32 = int<32>
            .typedef @i64 = int<64>
            .typedef @void = void
            .typedef @voidp = uptr<@void>
            .typedef @hyb = hybrid<@i8>
            .typedef @rhyb = ref<@hyb>
            .typedef @phyb = uptr<@hyb>
            .const @fd_stdout <@i32> = 1
            .const @c_h <@i8> = 104
            .const @c_e <@i8> = 101
            .const @c_l <@i8> = 108
            .const @c_o <@i8> = 111
            .const @c_0 <@i8> = 0
            .const @c_1 <@i64> = 1
            .const @c_len <@i64> = 5
            .const @c_bufsz <@i64> = 6
            .funcsig @sig__i64 = (@voidp @i64) -> ()
            .funcsig @sig_i32voidpi64_i64 = (@i32 @voidp @i64) -> (@i64)
            .typedef @fnpsig_i32voidpi64_i64 = ufuncptr<@sig_i32voidpi64_i64>
            .const c_write <@fnpsig_voidpi64_i64> = EXTERN "write"
            .funcdef @test_pin VERSION @test_write_v1 <@sig__i64> {
                %blk0():
                    %rs = NEWHYBRID <@hyb @i64> @c_bufsz
                    %irs = GETIREF <@hyb> %rs
                    %irelm_0 = GETVARPARTIREF <@hyb> %irs
                    STORE <@i8> %irelm_0 @c_h
                    %irelm_1 = SHIFTIREF <@i8 @i64> %irelm_0 @c_1
                    STORE <@i8> %irelm_1 @c_e
                    %irelm_2 = SHIFTIREF <@i8 @i64> %irelm_1 @c_1
                    STORE <@i8> %irelm_2 @c_l
                    %irelm_3 = SHIFTIREF <@i8 @i64> %irelm_2 @c_1
                    STORE <@i8> %irelm_3 @c_l
                    %irelm_4 = SHIFTIREF <@i8 @i64> %irelm_3 @c_1
                    STORE <@i8> %irelm_4 @c_o
                    %irelm_5 = SHIFTIREF <@i8 @i64> %irelm_4 @c_1
                    STORE <@i8> %irelm_5 @c_0

                    %ps = COMMINST @uvm.native.pin <@rhyb> %rs
                    %buf = PTRCAST <@phyb @voidp> %ps
                    %res = CCALL <@sig_i32voidpi64_i64> @c_write (@fd_stdout %buf %sz)
                    COMMINST @uvm.native.unpin <@rhyb> %rs

                    RET %res
            }

        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        i8 = bldr.gen_sym("@i8"); bldr.new_type_int(i8, 8)
        i32 = bldr.gen_sym("@i32"); bldr.new_type_int(i32, 32)
        i64 = bldr.gen_sym("@i64"); bldr.new_type_int(i64, 64)
        void = bldr.gen_sym("@void"); bldr.new_type_void(void)
        voidp = bldr.gen_sym("@voidp"); bldr.new_type_uptr(voidp, void)
        hyb = bldr.gen_sym("@hyb"); bldr.new_type_hybrid(hyb, [], i8)
        rhyb = bldr.gen_sym("@rhyb"); bldr.new_type_ref(rhyb, hyb)
        phyb = bldr.gen_sym("@phyb"); bldr.new_type_uptr(phyb, hyb)

        fd_stdout = bldr.gen_sym("@fd_stdout"); bldr.new_const_int(fd_stdout, i32, 1)

        c_h = bldr.gen_sym("@c_h"); bldr.new_const_int(c_h, i8, ord('h'))
        c_e = bldr.gen_sym("@c_e"); bldr.new_const_int(c_e, i8, ord('e'))
        c_l = bldr.gen_sym("@c_l"); bldr.new_const_int(c_l, i8, ord('l'))
        c_o = bldr.gen_sym("@c_o"); bldr.new_const_int(c_o, i8, ord('o'))
        c_0 = bldr.gen_sym("@c_0"); bldr.new_const_int(c_0, i64, 0)
        c_1 = bldr.gen_sym("@c_1"); bldr.new_const_int(c_1, i64, 1)
        c_len = bldr.gen_sym("@c_len"); bldr.new_const_int(c_len, i64, 5)
        c_bufsz = bldr.gen_sym("@c_bufsz"); bldr.new_const_int(c_bufsz, i64, 6)

        sig__i64 = bldr.gen_sym("@sig__i64"); bldr.new_funcsig(sig__i64, [voidp, i64], [i64])
        sig_i32voidpi64_i64 = bldr.gen_sym("@sig_i32voidpi64_i64"); bldr.new_funcsig(sig_i32voidpi64_i64, [i32, voidp, i64], [i64])

        fnpsig_i32voidpi64_i64 = bldr.gen_sym("@fnpsig_i32voidpi64_i64"); bldr.new_type_ufuncptr(fnpsig_i32voidpi64_i64, sig_i32voidpi64_i64)

        c_write = bldr.gen_sym("@c_write"); bldr.new_const_extern(c_write, fnpsig_i32voidpi64_i64, "write")

        test_pin = bldr.gen_sym("@test_pin"); bldr.new_func(test_pin, sig__i64)

        # function body
        v1 = bldr.gen_sym("@test_write_v1")
        blk0 = bldr.gen_sym("@test_write_v1.blk0")

        # blk0
        rs = bldr.gen_sym("@test_pin.v1.blk0.rs")
        irs = bldr.gen_sym("@test_pin.v1.blk0.irs")
        irelm_0 = bldr.gen_sym("@test_pin.v1.blk0.irelm_0")
        irelm_1 = bldr.gen_sym("@test_pin.v1.blk0.irelm_1")
        irelm_2 = bldr.gen_sym("@test_pin.v1.blk0.irelm_2")
        irelm_3 = bldr.gen_sym("@test_pin.v1.blk0.irelm_3")
        irelm_4 = bldr.gen_sym("@test_pin.v1.blk0.irelm_4")
        irelm_5 = bldr.gen_sym("@test_pin.v1.blk0.irelm_5")
        ps = bldr.gen_sym("@test_pin.v1.blk0.ps")
        buf = bldr.gen_sym("@test_pin.v1.blk0.buf")
        res = bldr.gen_sym("@test_pin.v1.blk0.res")
        op_newhybrid = bldr.gen_sym(); bldr.new_newhybrid(op_newhybrid, rs, hyb, i64, c_bufsz)
        op_getiref = bldr.gen_sym(); bldr.new_getiref(op_getiref, irs, hyb, rs)
        op_getvarpartiref = bldr.gen_sym(); bldr.new_getvarpartiref(op_getvarpartiref, irelm_0, False, hyb, irs)
        op_store1 = bldr.gen_sym(); bldr.new_store(op_store1, False, rmu.MuMemOrd.NOT_ATOMIC, i8, irelm_0, c_h)
        op_shiftiref1 = bldr.gen_sym(); bldr.new_shiftiref(op_shiftiref1, irelm_1, False, i8, i64, irelm_0, c_1)
        op_store2 = bldr.gen_sym(); bldr.new_store(op_store2, False, rmu.MuMemOrd.NOT_ATOMIC, i8, irelm_1, c_e)
        op_shiftiref2 = bldr.gen_sym(); bldr.new_shiftiref(op_shiftiref2, irelm_2, False, i8, i64, irelm_1, c_1)
        op_store3 = bldr.gen_sym(); bldr.new_store(op_store3, False, rmu.MuMemOrd.NOT_ATOMIC, i8, irelm_2, c_l)
        op_shiftiref3 = bldr.gen_sym(); bldr.new_shiftiref(op_shiftiref3, irelm_3, False, i8, i64, irelm_2, c_1)
        op_store4 = bldr.gen_sym(); bldr.new_store(op_store4, False, rmu.MuMemOrd.NOT_ATOMIC, i8, irelm_3, c_l)
        op_shiftiref4 = bldr.gen_sym(); bldr.new_shiftiref(op_shiftiref4, irelm_4, False, i8, i64, irelm_3, c_1)
        op_store5 = bldr.gen_sym(); bldr.new_store(op_store5, False, rmu.MuMemOrd.NOT_ATOMIC, i8, irelm_4, c_o)
        op_shiftiref5 = bldr.gen_sym(); bldr.new_shiftiref(op_shiftiref5, irelm_5, False, i8, i64, irelm_4, c_1)
        op_store6 = bldr.gen_sym(); bldr.new_store(op_store6, False, rmu.MuMemOrd.NOT_ATOMIC, i8, irelm_5, c_0)
        op_pin = bldr.gen_sym(); bldr.new_comminst(op_pin, [ps], rmu.MuCommInst.NATIVE_PIN, [], [rhyb], [], [rs])
        op_ptrcast = bldr.gen_sym(); bldr.new_conv(op_ptrcast, buf, rmu.MuConvOptr.PTRCAST, phyb, voidp, ps)
        op_ccall = bldr.gen_sym(); bldr.new_ccall(op_ccall, [res], rmu.MuCallConv.DEFAULT, fnpsig_i32voidpi64_i64, sig_i32voidpi64_i64, c_write,
                                                  [fd_stdout, buf, c_bufsz])
        op_unpin = bldr.gen_sym(); bldr.new_comminst(op_unpin, [], rmu.MuCommInst.NATIVE_UNPIN, [], [rhyb], [], [rs])
        op_ret = bldr.gen_sym(); bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [
            op_newhybrid,
            op_getiref,
            op_getvarpartiref,
            op_store1,
            op_shiftiref1,
            op_store2,
            op_shiftiref2,
            op_store3,
            op_shiftiref3,
            op_store4,
            op_shiftiref4,
            op_store5,
            op_shiftiref5,
            op_store6,
            op_pin,
            op_ptrcast,
            op_ccall,
            op_unpin,
            op_ret])
        bldr.new_func_ver(v1, test_pin, [blk0])

        return {
            "@i8": i8,
            "@i32": i32,
            "@i64": i64,
            "test_fnc_sig": sig__i64,
            "test_fnc": test_pin,
            "fncs": [test_pin],
            "result_type": i64
        }
    impl_jit_test(cmdopt, build_test_bundle)
