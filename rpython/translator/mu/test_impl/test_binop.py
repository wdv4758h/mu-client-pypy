from impl_test_util import impl_jit_test

def test_add(cmdopt):
    def build_test_bundle(bldr, rmu):
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

        return {
            "@i8": i8,
            "test_fnc_sig": sig__i8,
            "test_fnc": test_fnc,
            "result_type": i8
        }

    res = impl_jit_test(cmdopt, build_test_bundle)
    assert res == 9

def test_mul(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i8 = int<8>
            .const @0xff_i8 <@i8> = 0xff
            .const @0x0a_i8 <@i8> = 0x0a
            .funcsig @sig__i8 = () -> (@i8)
            .funcdecl @test_fnc <@fnrsig__i8>
            .funcdef @test_fnc VERSION @test_fnc_v1 <@sig__i8> {
                @test_fnc_v1.blk0():
                    @test_fnc_v1.blk0.res = MUL <@i8> @0xff_i8 @0x0a_i8
                    RET @test_fnc_v1.blk0.res
            }
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
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
        bldr.new_binop(op_add, res, rmu.MuBinOptr.MUL, i8, c_0xff_i8, c_0x0a_i8)
        op_ret = bldr.gen_sym()
        bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_add, op_ret])
        bldr.new_func_ver(v1, test_fnc, [blk0])

        return {
            "@i8": i8,
            "test_fnc_sig": sig__i8,
            "test_fnc": test_fnc,
            "result_type": i8
        }

    res = impl_jit_test(cmdopt, build_test_bundle)
    assert res == -10   # -10 & 0xff == 0xff * 0x0a & 0xff
