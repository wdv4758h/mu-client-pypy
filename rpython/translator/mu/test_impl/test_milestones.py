from impl_test_util import impl_jit_test

def test_constfunc(cmdopt):
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

    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert res == 0


def test_fib(cmdopt):
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

    res = impl_jit_test(cmdopt, build_test_bundle, extend_with_entrypoint)
    if cmdopt.run:
        assert res == 6765


def test_fac(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i64 = int<64>
            .const @0_i64 <@i64> = 0
            .const @1_i64 <@i64> = 1
            .funcsig @sig_i64_i64 = (@i64) -> (@i64)
            .funcdef @fac VERSION @fac.v1 <@sig_i64_i64> {
                @fac.v1.blk0(<@i64> @fac.v1.blk0.k):
                    BRANCH @fac.v1.blk1(@1_i64 @0_i64 @fac.v1.blk0.k)

                @fac.v1.blk1(<@i64> @fac.v1.blk1.prod
                                <@i64> @fac.v1.blk1.i
                                <@i64> @fac.v1.blk1.end):
                    @fac.v1.blk1.cmpres = EQ <@i64> @fac.v1.blk1.i @fac.v1.blk1.end
                    BRANCH2 @fac.v1.blk1.cmpres
                        @fac.v1.blk3(@fac.v1.blk1.prod)
                        @fac.v1.blk2(@fac.v1.blk1.prod @fac.v1.blk1.i @fac.v1.blk1.end)

                @fac.v1.blk2(<@i64> @fac.v1.blk2.prod
                                <@i64> @fac.v1.blk2.i
                                <@i64> @fac.v1.blk2.end):
                    @fac.v1.blk2.i_res = ADD <@i64> @fac.v1.blk2.i @1_64
                    @fac.v1.blk2.prod_res = MUL <@i64> @fac.v1.blk2.prod @fac.v1.blk2.i_res
                    BRANCH @fac.v1.blk1 (@fac.v1.blk2.prod_res @fac.v1.blk2.i_res @fac.v1.blk2.end)

                @fac.v1.blk3(<@i64> @fac.v1.blk3.rtn):
                    RET @fac.v1.blk3.rtn
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

        fac = bldr.gen_sym("@fac")
        bldr.new_func(fac, sig_i64_i64)

        # function body
        v1 = bldr.gen_sym("@fac.v1")
        blk0 = bldr.gen_sym("@fac.v1.blk0")
        blk1 = bldr.gen_sym("@fac.v1.blk1")
        blk2 = bldr.gen_sym("@fac.v1.blk2")
        blk3 = bldr.gen_sym("@fac.v1.blk3")

        # blk0
        k = bldr.gen_sym("@fac.v1.blk0.k")
        dst = bldr.gen_sym()
        bldr.new_dest_clause(dst, blk1, [c_1_i64, c_0_i64, k])
        op_branch = bldr.gen_sym()
        bldr.new_branch(op_branch, dst)
        bldr.new_bb(blk0, [k], [i64], rmu.MU_NO_ID, [op_branch])

        # blk1
        prod = bldr.gen_sym("@fac.v1.blk1.prod")
        i = bldr.gen_sym("@fac.v1.blk1.i")
        end = bldr.gen_sym("@fac.v1.blk1.end")
        cmpres = bldr.gen_sym("@fac.v1.blk1.cmpres")
        op_eq = bldr.gen_sym()
        bldr.new_cmp(op_eq, cmpres, rmu.MuCmpOptr.EQ, i64, i, end)
        op_br2 = bldr.gen_sym()
        dst_t = bldr.gen_sym()
        bldr.new_dest_clause(dst_t, blk3, [prod])
        dst_f = bldr.gen_sym()
        bldr.new_dest_clause(dst_f, blk2, [prod, i, end])
        bldr.new_branch2(op_br2, cmpres, dst_t, dst_f)
        bldr.new_bb(blk1, [prod, i, end], [i64, i64, i64], rmu.MU_NO_ID, [op_eq, op_br2])

        # blk2
        prod = bldr.gen_sym("@fac.v1.blk2.prod")
        i = bldr.gen_sym("@fac.v1.blk2.i")
        end = bldr.gen_sym("@fac.v1.blk2.end")
        prod_res = bldr.gen_sym("@fac.v1.blk2.prod_res")
        i_res = bldr.gen_sym("@fac.v1.blk2.i_res")
        op_add = bldr.gen_sym()
        bldr.new_binop(op_add, i_res, rmu.MuBinOptr.ADD, i64, i, c_1_i64)
        op_mul = bldr.gen_sym()
        bldr.new_binop(op_mul, prod_res, rmu.MuBinOptr.MUL, i64, prod, i_res)
        dst = bldr.gen_sym()
        bldr.new_dest_clause(dst, blk1, [prod_res, i_res, end])
        op_br = bldr.gen_sym()
        bldr.new_branch(op_br, dst)
        bldr.new_bb(blk2, [prod, i, end], [i64, i64, i64], rmu.MU_NO_ID, [op_add, op_mul, op_br])

        # blk3
        rtn = bldr.gen_sym("@fac.v1.blk3.rtn")
        op_ret = bldr.gen_sym()
        bldr.new_ret(op_ret, [rtn])
        bldr.new_bb(blk3, [rtn], [i64], rmu.MU_NO_ID, [op_ret])

        bldr.new_func_ver(v1, fac, [blk0, blk1, blk2, blk3])

        return {
            "@i64": i64,
            "test_fnc_sig": sig_i64_i64,
            "test_fnc": fac,
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

    res = impl_jit_test(cmdopt, build_test_bundle, extend_with_entrypoint)
    if cmdopt.run:
        assert res == 2432902008176640000

def test_milsum(cmdopt):
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

    res = impl_jit_test(cmdopt, build_test_bundle, extend_with_entrypoint)
    if cmdopt.run:
        assert res == 500000500000