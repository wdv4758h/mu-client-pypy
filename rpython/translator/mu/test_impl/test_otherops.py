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