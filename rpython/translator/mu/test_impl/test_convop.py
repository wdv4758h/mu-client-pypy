from impl_test_util import impl_jit_test

def test_trunc(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i64 = int<64>
            .typedef @i32 = int<32>
            .const @0x6d9f9c1d58324b55_i64 <@i64> = 0x6d9f9c1d58324b55
            .funcsig @sig__i32 = () -> (@i32)
            .funcdef @test_fnc VERSION @test_fnc_v1 <@sig__i32> {
                @test_fnc_v1.blk0():
                    @test_fnc_v1.blk0.res = TRUNC <@i64 @i32> @0x6d9f9c1d58324b55_i64
                    RET @test_fnc_v1.blk0.res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        i32 = bldr.gen_sym("@i32")
        bldr.new_type_int(i32, 32)
        i64 = bldr.gen_sym("@i64")
        bldr.new_type_int(i64, 64)

        c_0x6d9f9c1d58324b55_i64 = bldr.gen_sym("@0x6d9f9c1d58324b55_i64")
        bldr.new_const_int(c_0x6d9f9c1d58324b55_i64, i64, 0x6d9f9c1d58324b55)

        sig__i32 = bldr.gen_sym("@sig__i32")
        bldr.new_funcsig(sig__i32, [], [i32])

        test_fnc = bldr.gen_sym("@test_fnc")
        bldr.new_func(test_fnc, sig__i32)

        # function body
        v1 = bldr.gen_sym("@test_fnc_v1")
        blk0 = bldr.gen_sym("@test_fnc_v1.blk0")
        res = bldr.gen_sym("@test_fnc_v1.blk0.res")
        op_convop = bldr.gen_sym()
        bldr.new_conv(op_convop, res, rmu.MuConvOptr.TRUNC, i64, i32, c_0x6d9f9c1d58324b55_i64)
        op_ret = bldr.gen_sym()
        bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_convop, op_ret])
        bldr.new_func_ver(v1, test_fnc, [blk0])

        return {
            "@i32": i32,
            "@i64": i64,
            "test_fnc_sig": sig__i32,
            "test_fnc": test_fnc,
            "result_type": i32
        }

    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert res == 0x58324b55  

def test_sext(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i32 = int<32>
            .typedef @i64 = int<64>
            .const @0xa8324b55_i32 <@i32> = 0xa8324b55
            .funcsig @sig__i64 = () -> (@i64)
            .funcdef @test_fnc VERSION @test_fnc_v1 <@sig__i64> {
                @test_fnc_v1.blk0():
                    @test_fnc_v1.blk0.res = SEXT <@i32 @i64> @0xa8324b55_i64
                    RET @test_fnc_v1.blk0.res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        i32 = bldr.gen_sym("@i32")
        bldr.new_type_int(i32, 32)
        i64 = bldr.gen_sym("@i64")
        bldr.new_type_int(i64, 64)

        c_0xa8324b55_i32 = bldr.gen_sym("@0xa8324b55_i32")
        bldr.new_const_int(c_0xa8324b55_i32, i64, 0xa8324b55)

        sig__i64 = bldr.gen_sym("@sig__i64")
        bldr.new_funcsig(sig__i64, [], [i64])

        test_fnc = bldr.gen_sym("@test_fnc")
        bldr.new_func(test_fnc, sig__i64)

        # function body
        v1 = bldr.gen_sym("@test_fnc_v1")
        blk0 = bldr.gen_sym("@test_fnc_v1.blk0")
        res = bldr.gen_sym("@test_fnc_v1.blk0.res")
        op_convop = bldr.gen_sym()
        bldr.new_conv(op_convop, res, rmu.MuConvOptr.SEXT, i32, i64, c_0xa8324b55_i32)
        op_ret = bldr.gen_sym()
        bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_convop, op_ret])
        bldr.new_func_ver(v1, test_fnc, [blk0])

        return {
            "@i32": i32,
            "@i64": i64,
            "test_fnc_sig": sig__i64,
            "test_fnc": test_fnc,
            "result_type": i64
        }

    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert res == 0xffffffffa8324b55

def test_zext(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i32 = int<32>
            .typedef @i64 = int<64>
            .const @0xa8324b55_i32 <@i32> = 0xa8324b55
            .funcsig @sig__i64 = () -> (@i64)
            .funcdef @test_fnc VERSION @test_fnc_v1 <@sig__i64> {
                @test_fnc_v1.blk0():
                    @test_fnc_v1.blk0.res = ZEXT <@i32 @i64> @0xa8324b55_i64
                    RET @test_fnc_v1.blk0.res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        i32 = bldr.gen_sym("@i32")
        bldr.new_type_int(i32, 32)
        i64 = bldr.gen_sym("@i64")
        bldr.new_type_int(i64, 64)

        c_0xa8324b55_i32 = bldr.gen_sym("@0xa8324b55_i32")
        bldr.new_const_int(c_0xa8324b55_i32, i64, 0xa8324b55)

        sig__i64 = bldr.gen_sym("@sig__i64")
        bldr.new_funcsig(sig__i64, [], [i64])

        test_fnc = bldr.gen_sym("@test_fnc")
        bldr.new_func(test_fnc, sig__i64)

        # function body
        v1 = bldr.gen_sym("@test_fnc_v1")
        blk0 = bldr.gen_sym("@test_fnc_v1.blk0")
        res = bldr.gen_sym("@test_fnc_v1.blk0.res")
        op_convop = bldr.gen_sym()
        bldr.new_conv(op_convop, res, rmu.MuConvOptr.ZEXT, i32, i64, c_0xa8324b55_i32)
        op_ret = bldr.gen_sym()
        bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_convop, op_ret])
        bldr.new_func_ver(v1, test_fnc, [blk0])

        return {
            "@i32": i32,
            "@i64": i64,
            "test_fnc_sig": sig__i64,
            "test_fnc": test_fnc,
            "result_type": i64
        }

    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert res == 0x00000000a8324b55