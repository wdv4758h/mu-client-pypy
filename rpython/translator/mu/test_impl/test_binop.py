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

def test_sub(cmdopt):
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
                    @test_fnc_v1.blk0.res = SUB <@i8> @0x0a_i8 @0xff_i8
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
        bldr.new_binop(op_add, res, rmu.MuBinOptr.SUB, i8, c_0x0a_i8, c_0xff_i8)
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
    assert res == 11

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
    assert res == 0xf6

def test_sdiv(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i8 = int<8>
            .const @0x80_i8 <@i8> = 0x80
            .const @0x0a_i8 <@i8> = 0x0a
            .funcsig @sig__i8 = () -> (@i8)
            .funcdecl @test_fnc <@fnrsig__i8>
            .funcdef @test_fnc VERSION @test_fnc_v1 <@sig__i8> {
                @test_fnc_v1.blk0():
                    @test_fnc_v1.blk0.res = SDIV <@i8> @0x80_i8 @0x0a_i8
                    RET @test_fnc_v1.blk0.res
            }
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        i8 = bldr.gen_sym("@i8")
        bldr.new_type_int(i8, 8)

        c_0x80_i8 = bldr.gen_sym("@0x80_i8")
        bldr.new_const_int(c_0x80_i8, i8, 0x80)
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
        bldr.new_binop(op_add, res, rmu.MuBinOptr.SDIV, i8, c_0x80_i8, c_0x0a_i8)
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
    assert res == 0xf4

def test_urem(cmdopt):
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
                    @test_fnc_v1.blk0.res = UREM <@i8> @0xff_i8 @0x0a_i8
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
        bldr.new_binop(op_add, res, rmu.MuBinOptr.UREM, i8, c_0xff_i8, c_0x0a_i8)
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
    assert res == 5

def test_shl(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i64 = int<64>
            .const @0x6d9f9c1d58324b55_i64 <@i64> = 0x6d9f9c1d58324b55
            .const @0x0a_i64 <@i64> = 0x0a
            .funcsig @sig__i64 = () -> (@i64)
            .funcdecl @fnc <@fnrsig__i64>
            .funcdef @fnc VERSION @fnc_v1 <@sig__i64> {
                @fnc_v1.blk0():
                    @fnc_v1.blk0.res = SHL <@i64> @0x6d9f9c1d58324b55 @0x0a_i64
                    RET @fnc_v1.blk0.res
            }
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        i64 = bldr.gen_sym("@i64")
        bldr.new_type_int(i64, 64)

        c_0x6d9f9c1d58324b55_i64 = bldr.gen_sym("@0x6d9f9c1d58324b55_i64")
        bldr.new_const_int(c_0x6d9f9c1d58324b55_i64, i64, 0x6d9f9c1d58324b55)
        c_0x0a_i64 = bldr.gen_sym("@0x0a_i64")
        bldr.new_const_int(c_0x0a_i64, i64, 0x0a)

        sig__i64 = bldr.gen_sym("@sig__i64")
        bldr.new_funcsig(sig__i64, [], [i64])

        test_fnc = bldr.gen_sym("@test_fnc")
        bldr.new_func(test_fnc, sig__i64)

        # function body
        v1 = bldr.gen_sym("@test_fnc_v1")
        blk0 = bldr.gen_sym("@test_fnc_v1.blk0")
        res = bldr.gen_sym("@test_fnc_v1.blk0.res")
        op_add = bldr.gen_sym()
        bldr.new_binop(op_add, res, rmu.MuBinOptr.SHL, i64, c_0x6d9f9c1d58324b55_i64, c_0x0a_i64)
        op_ret = bldr.gen_sym()
        bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_add, op_ret])
        bldr.new_func_ver(v1, test_fnc, [blk0])

        return {
            "@i64": i64,
            "test_fnc_sig": sig__i64,
            "test_fnc": test_fnc,
            "result_type": i64
        }

    res = impl_jit_test(cmdopt, build_test_bundle)
    assert res == 0x7e707560c92d5400

def test_lshr(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i64 = int<64>
            .const @0x6d9f9c1d58324b55_i64 <@i64> = 0x6d9f9c1d58324b55
            .const @0x0a_i64 <@i64> = 0x0a
            .funcsig @sig__i64 = () -> (@i64)
            .funcdecl @fnc <@fnrsig__i64>
            .funcdef @fnc VERSION @fnc_v1 <@sig__i64> {
                @fnc_v1.blk0():
                    @fnc_v1.blk0.res = SHL <@i64> @0x6d9f9c1d58324b55 @0x0a_i64
                    RET @fnc_v1.blk0.res
            }
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        i64 = bldr.gen_sym("@i64")
        bldr.new_type_int(i64, 64)

        c_0x8d9f9c1d58324b55_i64 = bldr.gen_sym("@0x8d9f9c1d58324b55_i64")
        bldr.new_const_int(c_0x8d9f9c1d58324b55_i64, i64, 0x8d9f9c1d58324b55)
        c_0x0a_i64 = bldr.gen_sym("@0x0a_i64")
        bldr.new_const_int(c_0x0a_i64, i64, 0x0a)

        sig__i64 = bldr.gen_sym("@sig__i64")
        bldr.new_funcsig(sig__i64, [], [i64])

        test_fnc = bldr.gen_sym("@test_fnc")
        bldr.new_func(test_fnc, sig__i64)

        # function body
        v1 = bldr.gen_sym("@test_fnc_v1")
        blk0 = bldr.gen_sym("@test_fnc_v1.blk0")
        res = bldr.gen_sym("@test_fnc_v1.blk0.res")
        op_add = bldr.gen_sym()
        bldr.new_binop(op_add, res, rmu.MuBinOptr.LSHR, i64, c_0x8d9f9c1d58324b55_i64, c_0x0a_i64)
        op_ret = bldr.gen_sym()
        bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_add, op_ret])
        bldr.new_func_ver(v1, test_fnc, [blk0])

        return {
            "@i64": i64,
            "test_fnc_sig": sig__i64,
            "test_fnc": test_fnc,
            "result_type": i64
        }

    res = impl_jit_test(cmdopt, build_test_bundle)
    assert res == 0x2367e707560c92

def test_and(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i64 = int<64>
            .const @0x6d9f9c1d58324b55_i64 <@i64> = 0x6d9f9c1d58324b55
            .const @0xd5a8f2deb00debb4_i64 <@i64> = 0xd5a8f2deb00debb4
            .funcsig @sig__i64 = () -> (@i64)
            .funcdecl @fnc <@fnrsig__i64>
            .funcdef @fnc VERSION @fnc_v1 <@sig__i64> {
                @fnc_v1.blk0():
                    @fnc_v1.blk0.res = AND <@i64> @0x6d9f9c1d58324b55 @0xd5a8f2deb00debb4_i64
                    RET @fnc_v1.blk0.res
            }
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        i64 = bldr.gen_sym("@i64")
        bldr.new_type_int(i64, 64)

        c_0x8d9f9c1d58324b55_i64 = bldr.gen_sym("@0x8d9f9c1d58324b55_i64")
        bldr.new_const_int(c_0x8d9f9c1d58324b55_i64, i64, 0x8d9f9c1d58324b55)
        c_0xd5a8f2deb00debb4_i64 = bldr.gen_sym("@0xd5a8f2deb00debb4_i64")
        bldr.new_const_int(c_0xd5a8f2deb00debb4_i64, i64, 0xd5a8f2deb00debb4)

        sig__i64 = bldr.gen_sym("@sig__i64")
        bldr.new_funcsig(sig__i64, [], [i64])

        test_fnc = bldr.gen_sym("@test_fnc")
        bldr.new_func(test_fnc, sig__i64)

        # function body
        v1 = bldr.gen_sym("@test_fnc_v1")
        blk0 = bldr.gen_sym("@test_fnc_v1.blk0")
        res = bldr.gen_sym("@test_fnc_v1.blk0.res")
        op_add = bldr.gen_sym()
        bldr.new_binop(op_add, res, rmu.MuBinOptr.AND, i64, c_0x8d9f9c1d58324b55_i64, c_0xd5a8f2deb00debb4_i64)
        op_ret = bldr.gen_sym()
        bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_add, op_ret])
        bldr.new_func_ver(v1, test_fnc, [blk0])

        return {
            "@i64": i64,
            "test_fnc_sig": sig__i64,
            "test_fnc": test_fnc,
            "result_type": i64
        }

    res = impl_jit_test(cmdopt, build_test_bundle)
    assert res == 0x8588901c10004b14

def test_xor(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i64 = int<64>
            .const @0x6d9f9c1d58324b55_i64 <@i64> = 0x6d9f9c1d58324b55
            .const @0xd5a8f2deb00debb4_i64 <@i64> = 0xd5a8f2deb00debb4
            .funcsig @sig__i64 = () -> (@i64)
            .funcdecl @fnc <@fnrsig__i64>
            .funcdef @fnc VERSION @fnc_v1 <@sig__i64> {
                @fnc_v1.blk0():
                    @fnc_v1.blk0.res = AND <@i64> @0x6d9f9c1d58324b55 @0xd5a8f2deb00debb4_i64
                    RET @fnc_v1.blk0.res
            }
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        i64 = bldr.gen_sym("@i64")
        bldr.new_type_int(i64, 64)

        c_0x8d9f9c1d58324b55_i64 = bldr.gen_sym("@0x8d9f9c1d58324b55_i64")
        bldr.new_const_int(c_0x8d9f9c1d58324b55_i64, i64, 0x8d9f9c1d58324b55)
        c_0xd5a8f2deb00debb4_i64 = bldr.gen_sym("@0xd5a8f2deb00debb4_i64")
        bldr.new_const_int(c_0xd5a8f2deb00debb4_i64, i64, 0xd5a8f2deb00debb4)

        sig__i64 = bldr.gen_sym("@sig__i64")
        bldr.new_funcsig(sig__i64, [], [i64])

        test_fnc = bldr.gen_sym("@test_fnc")
        bldr.new_func(test_fnc, sig__i64)

        # function body
        v1 = bldr.gen_sym("@test_fnc_v1")
        blk0 = bldr.gen_sym("@test_fnc_v1.blk0")
        res = bldr.gen_sym("@test_fnc_v1.blk0.res")
        op_add = bldr.gen_sym()
        bldr.new_binop(op_add, res, rmu.MuBinOptr.XOR, i64, c_0x8d9f9c1d58324b55_i64, c_0xd5a8f2deb00debb4_i64)
        op_ret = bldr.gen_sym()
        bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_add, op_ret])
        bldr.new_func_ver(v1, test_fnc, [blk0])

        return {
            "@i64": i64,
            "test_fnc_sig": sig__i64,
            "test_fnc": test_fnc,
            "result_type": i64
        }

    res = impl_jit_test(cmdopt, build_test_bundle)
    assert res == 0x58376ec3e83fa0e1
