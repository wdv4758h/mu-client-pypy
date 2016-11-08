from impl_test_util import impl_jit_test

def test_branch(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i64 = int<64>
            .const @10_i64 <@i64> = 10
            .const @20_i64 <@i64> = 10
            .funcsig @sig__i64 = (@i64) -> (@i64)
            .funcdef @test_fnc VERSION @test_fnc.v1 <@sig__i64> {
                @test_fnc.v1.blk0():
                    BRANCH @test_fnc.v1.blk1(@10_i64 @20_i64)
        
                @test_fnc.v1.blk1(<@i64> @test_fnc.v1.blk1.a <@i64> @test_fnc.v1.blk1.b):
                    @test_fnc.v1.blk1.res = ADD <@i64> @test_fnc.v1.blk1.a @test_fnc.v1.blk1.b
                    RET @test_fnc.v1.blk1.res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """

        i64 = bldr.gen_sym("@i64")
        bldr.new_type_int(i64, 64)

        c_10_i64 = bldr.gen_sym("@10_i64")
        bldr.new_const_int(c_10_i64, i64, 10)
        c_20_i64 = bldr.gen_sym("@20_i64")
        bldr.new_const_int(c_20_i64, i64, 20)

        sig__i64 = bldr.gen_sym("@sig__i64")
        bldr.new_funcsig(sig__i64, [], [i64])

        test_fnc = bldr.gen_sym("@test_fnc")
        bldr.new_func(test_fnc, sig__i64)
        test_fnc_v1 = bldr.gen_sym("@test_fnc.v1")

        blk0 = bldr.gen_sym("@test_fnc.v1.blk0")
        blk1 = bldr.gen_sym("@test_fnc.v1.blk1")
        op_br = bldr.gen_sym()
        dst = bldr.gen_sym()
        bldr.new_dest_clause(dst, blk1, [c_10_i64, c_20_i64])
        bldr.new_branch(op_br, dst)
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_br])

        a = bldr.gen_sym("@test_fnc.v1.blk1.a")
        b = bldr.gen_sym("@test_fnc.v1.blk1.b")
        res = bldr.gen_sym("@test_fnc.v1.blk1.res")
        op_add = bldr.gen_sym()
        bldr.new_binop(op_add, res, rmu.MuBinOptr.ADD, i64, a, b)
        op_ret = bldr.gen_sym()
        bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk1, [a, b], [i64, i64], rmu.MU_NO_ID, [op_add, op_ret])

        bldr.new_func_ver(test_fnc_v1, test_fnc, [blk0, blk1])

        return {
            "test_fnc": test_fnc,
            "test_fnc_sig": sig__i64,
            "result_type": i64,
            "@i64": i64
        }

    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert res == 30


def test_branch2(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i8
            .typedef @i64 = int<64>
            .const @TRUE <@i8> = 1
            .const @10_i64 <@i64> = 10
            .const @20_i64 <@i64> = 10
            .funcsig @sig_i8_i64 = (@i64) -> (@i64)
            .funcdef @test_fnc VERSION @test_fnc.v1 <@sig_i8_i64> {
                @test_fnc.v1.blk0(<@i8> @test_fnc.v1.blk0.sel):
                    @test_fnc.v1.blk0.flag = EQ @test_fnc.v1.blk0.sel @TRUE
                    BRANCH2 @test_fnc.v1.blk0.flag @test_fnc.v1.blk1(@10_i64 @20_i64)

                @test_fnc.v1.blk1(<@i64> @test_fnc.v1.blk1.a <@i64> @test_fnc.v1.blk1.b):
                    @test_fnc.v1.blk1.res = ADD <@i64> @test_fnc.v1.blk1.a @test_fnc.v1.blk1.b
                    RET @test_fnc.v1.blk1.res

                @test_fnc.v1.blk2(<@i64> @test_fnc.v1.blk2.a <@i64> @test_fnc.v1.blk2.b):
                    @test_fnc.v1.blk2.res = MUL <@i64> @test_fnc.v1.blk2.a @test_fnc.v1.blk2.b
                    RET @test_fnc.v1.blk2.res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        i8 = bldr.gen_sym("@i8")
        bldr.new_type_int(i8, 8)
        i64 = bldr.gen_sym("@i64")
        bldr.new_type_int(i64, 64)

        TRUE = bldr.gen_sym("@TRUE")
        bldr.new_const_int(TRUE, i8, 1)
        c_10_i64 = bldr.gen_sym("@10_i64")
        bldr.new_const_int(c_10_i64, i64, 10)
        c_20_i64 = bldr.gen_sym("@20_i64")
        bldr.new_const_int(c_20_i64, i64, 20)

        sig_i8_i64 = bldr.gen_sym("@sig_i8_i64")
        bldr.new_funcsig(sig_i8_i64, [i8], [i64])

        test_fnc = bldr.gen_sym("@test_fnc")
        bldr.new_func(test_fnc, sig_i8_i64)
        test_fnc_v1 = bldr.gen_sym("@test_fnc.v1")

        blk0 = bldr.gen_sym("@test_fnc.v1.blk0")
        blk1 = bldr.gen_sym("@test_fnc.v1.blk1")
        blk2 = bldr.gen_sym("@test_fnc.v1.blk2")

        sel = bldr.gen_sym("@test_fnc.v1.blk0.sel")
        flag = bldr.gen_sym("@test_fnc.v1.blk0.flag")
        op_eq = bldr.gen_sym()
        bldr.new_cmp(op_eq, flag, rmu.MuCmpOptr.EQ, i8, sel, TRUE)
        op_br2 = bldr.gen_sym()
        dst_t = bldr.gen_sym()
        bldr.new_dest_clause(dst_t, blk1, [c_10_i64, c_20_i64])
        dst_f = bldr.gen_sym()
        bldr.new_dest_clause(dst_f, blk2, [c_10_i64, c_20_i64])
        bldr.new_branch2(op_br2, flag, dst_t, dst_f)
        bldr.new_bb(blk0, [sel], [i8], rmu.MU_NO_ID, [op_eq, op_br2])

        a = bldr.gen_sym("@test_fnc.v1.blk1.a")
        b = bldr.gen_sym("@test_fnc.v1.blk1.b")
        res = bldr.gen_sym("@test_fnc.v1.blk1.res")
        op_add = bldr.gen_sym()
        bldr.new_binop(op_add, res, rmu.MuBinOptr.ADD, i64, a, b)
        op_ret = bldr.gen_sym()
        bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk1, [a, b], [i64, i64], rmu.MU_NO_ID, [op_add, op_ret])

        a = bldr.gen_sym("@test_fnc.v1.blk2.a")
        b = bldr.gen_sym("@test_fnc.v1.blk2.b")
        res = bldr.gen_sym("@test_fnc.v1.blk2.res")
        op_add = bldr.gen_sym()
        bldr.new_binop(op_add, res, rmu.MuBinOptr.MUL, i64, a, b)
        op_ret = bldr.gen_sym()
        bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk2, [a, b], [i64, i64], rmu.MU_NO_ID, [op_add, op_ret])
        
        bldr.new_func_ver(test_fnc_v1, test_fnc, [blk0, blk1, blk2])

        return {
            "test_fnc": test_fnc,
            "test_fnc_sig": sig_i8_i64,
            "result_type": i64,
            "@i64": i64,
            "@i8": i8,
            "@TRUE": TRUE
        }

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
        TRUE = id_dict['@TRUE']
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

    res = impl_jit_test(cmdopt, build_test_bundle, extend_fnc=extend_with_entrypoint)
    if cmdopt.run:
        assert res == 200

def test_ccall(cmdopt):
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

    impl_jit_test(cmdopt, build_test_bundle, extend_with_entrypoint, ["../suite/test_ccall_fnc.c"])
