from impl_test_util import impl_jit_test


def test_new(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i64 = int<64>
            .typedef @refi64 = ref<@i64>
            .const @NULL_refi64 <@refi64> = NULL
            .funcsig @sig__i64 = () -> (@i64)
            .funcdef @test_fnc VERSION @test_fnc.v1 <@sig__i64> {
                @test_fnc.v1.blk0():
                    @test_fnc.v1.blk0.r = NEW <@i64>
                    @test_fnc.v1.blk0.cmpres = EQ <@refi64> @test_fnc.v1.blk0.r @NULL_refi64
                    @@test_fnc.v1.blk0.res = ZEXT <@i1 @i64> @test_fnc.v1.blk0.cmpres
                    RET @test_fnc.v1.blk0.res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        i1 = bldr.gen_sym("@i1")
        bldr.new_type_int(i1, 1)
        i64 = bldr.gen_sym("@i64")
        bldr.new_type_int(i64, 64)
        refi64 = bldr.gen_sym("@refi64")
        bldr.new_type_ref(refi64, i64)
        
        NULL_refi64 = bldr.gen_sym("@NULL_refi64")
        bldr.new_const_null(NULL_refi64, refi64)
        
        sig__i64 = bldr.gen_sym("@sig__i64")
        bldr.new_funcsig(sig__i64, [], [i64])
        
        test_fnc = bldr.gen_sym("@test_fnc")
        bldr.new_func(test_fnc, sig__i64)

        test_fnc_v1 = bldr.gen_sym("@test_fnc.v1")
        blk0 = bldr.gen_sym("@test_fnc.v1.blk0")
        r = bldr.gen_sym("@test_fnc.v1.blk0.r")
        cmpres = bldr.gen_sym("@test_fnc.v1.blk0.cmpres")
        res = bldr.gen_sym("@test_fnc.v1.blk0.res")
        op_new = bldr.gen_sym()
        bldr.new_new(op_new, r, i64)
        op_eq = bldr.gen_sym()
        bldr.new_cmp(op_eq, cmpres, rmu.MuCmpOptr.EQ, refi64, r, NULL_refi64)
        op_zext = bldr.gen_sym()
        bldr.new_conv(op_zext, res, rmu.MuConvOptr.ZEXT, i1, i64, cmpres)
        op_ret = bldr.gen_sym()
        bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_new, op_eq, op_zext, op_ret])

        bldr.new_func_ver(test_fnc_v1, test_fnc, [blk0])

        return {
            "test_fnc": test_fnc,
            "test_fnc_sig": sig__i64,
            "result_type": i64,
            "@i64": i64
        }

    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert res == 0

def test_new_bytestore_load(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i8 = int<8>
            .typedef @i32 = int<32>
            .typedef @refi8 = ref<@i8>
            .typedef @irefi8 = iref<@i8>
            .typedef @refi32 = ref<@i32>
            .const @1_i8 <@i8> = 1
            .const @0x8d_i8 <@i8> = 0x8d
            .const @0x9f_i8 <@i8> = 0x9f
            .const @0x9c_i8 <@i8> = 0x9c
            .const @0x1d_i8 <@i8> = 0x1d
            .funcsig @sig__i32 = () -> (@i32)
            .funcdef @test_fnc VERSION @test_fnc.v1 <@sig__i32> {
                @test_fnc.v1.blk0():
                    @test_fnc.v1.blk0.r32x = NEW <@i32>
                    @test_fnc.v1.blk0.r8x = REFCAST <@refi32 @refi8> @test_fnc.v1.blk0.r32x
                    @test_fnc.v1.blk0.ir8x_0 = GETIREF <@i8> @test_fnc.v1.blk0.r8x
                    STORE <@i8> @test_fnc.v1.blk0.ir8x_0 @0x1d_i8
                    @test_fnc.v1.blk0.ir8x_1 = SHIFTIREF <@i8 @i8> @test_fnc.v1.blk0.ir8x_0 @1_i8
                    STORE <@i8> @test_fnc.v1.blk0.ir8x_1 @0x9c_i8
                    @test_fnc.v1.blk0.ir8x_2 = SHIFTIREF <@i8 @i8> @test_fnc.v1.blk0.ir8x_1 @1_i8
                    STORE <@i8> @test_fnc.v1.blk0.ir8x_2 @0x9f_i8
                    @test_fnc.v1.blk0.ir8x_3 = SHIFTIREF <@i8 @i8> @test_fnc.v1.blk0.ir8x_2 @1_i8
                    STORE <@i8> @test_fnc.v1.blk0.ir8x_3 @0x8d_i8
                    @test_fnc.v1.blk0.ir32x = GETIREF <@i32> @test_fnc.v1.blk0.r32x
                    @test_fnc.v1.blk0.res = LOAD <@i32> @test_fnc.v1.blk0.ir32x
                    RET @test_fnc.v1.blk0.res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        i8 = bldr.gen_sym("@i8")
        bldr.new_type_int(i8, 8)
        i32 = bldr.gen_sym("@i32")
        bldr.new_type_int(i32, 32)
        refi8 = bldr.gen_sym("@refi8")
        bldr.new_type_ref(refi8, i8)
        irefi8 = bldr.gen_sym("@irefi8")
        bldr.new_type_iref(irefi8, i8)
        refi32 = bldr.gen_sym("@refi32")
        bldr.new_type_ref(refi32, i32)
        iref32 = bldr.gen_sym("@iref32")
        bldr.new_type_iref(iref32, i32)

        c_1_i8 = bldr.gen_sym("@1_i8")
        bldr.new_const_int(c_1_i8, i8, 1)
        c_0x8d_i8 = bldr.gen_sym("@0x8d_i8")
        bldr.new_const_int(c_0x8d_i8, i8, 0x8d)
        c_0x9f_i8 = bldr.gen_sym("@0x9f_i8")
        bldr.new_const_int(c_0x9f_i8, i8, 0x9f)
        c_0x9c_i8 = bldr.gen_sym("@0x9c_i8")
        bldr.new_const_int(c_0x9c_i8, i8, 0x9c)
        c_0x1d_i8 = bldr.gen_sym("@0x1d_i8")
        bldr.new_const_int(c_0x1d_i8, i8, 0x1d)

        sig__i32 = bldr.gen_sym("@sig__i32")
        bldr.new_funcsig(sig__i32, [], [i32])

        test_fnc = bldr.gen_sym("@test_fnc")
        bldr.new_func(test_fnc, sig__i32)

        test_fnc_v1 = bldr.gen_sym("@test_fnc.v1")
        blk0 = bldr.gen_sym("@test_fnc.v1.blk0")
        r32x = bldr.gen_sym("@test_fnc.v1.blk0.r32x")
        r8x = bldr.gen_sym("@test_fnc.v1.blk0.r8x")
        ir8x_0 = bldr.gen_sym("@test_fnc.v1.blk0.ir8x_0")
        ir8x_1 = bldr.gen_sym("@test_fnc.v1.blk0.ir8x_1")
        ir8x_2 = bldr.gen_sym("@test_fnc.v1.blk0.ir8x_2")
        ir8x_3 = bldr.gen_sym("@test_fnc.v1.blk0.ir8x_3")
        ir32x = bldr.gen_sym("@test_fnc.v1.blk0.ir32x")
        res = bldr.gen_sym("@test_fnc.v1.blk0.res")
        op_new = bldr.gen_sym()
        bldr.new_new(op_new, r32x, i32)
        op_cast = bldr.gen_sym()
        bldr.new_conv(op_cast, r8x, rmu.MuConvOptr.REFCAST, refi32, refi8, r32x)
        op_getiref_0 = bldr.gen_sym()
        bldr.new_getiref(op_getiref_0, ir8x_0, i8, r8x)
        op_store_0 = bldr.gen_sym()
        bldr.new_store(op_store_0, False, rmu.MuMemOrd.NOT_ATOMIC, i8, ir8x_0, c_0x1d_i8)
        op_shift_1 = bldr.gen_sym()
        bldr.new_shiftiref(op_shift_1, ir8x_1, False, i8, i8, ir8x_0, c_1_i8)
        op_store_1 = bldr.gen_sym()
        bldr.new_store(op_store_1, False, rmu.MuMemOrd.NOT_ATOMIC, i8, ir8x_1, c_0x9c_i8)
        op_shift_2 = bldr.gen_sym()
        bldr.new_shiftiref(op_shift_2, ir8x_2, False, i8, i8, ir8x_1, c_1_i8)
        op_store_2 = bldr.gen_sym()
        bldr.new_store(op_store_2, False, rmu.MuMemOrd.NOT_ATOMIC, i8, ir8x_2, c_0x9f_i8)
        op_shift_3 = bldr.gen_sym()
        bldr.new_shiftiref(op_shift_3, ir8x_3, False, i8, i8, ir8x_2, c_1_i8)
        op_store_3 = bldr.gen_sym()
        bldr.new_store(op_store_3, False, rmu.MuMemOrd.NOT_ATOMIC, i8, ir8x_3, c_0x8d_i8)
        op_getiref_1 = bldr.gen_sym()
        bldr.new_getiref(op_getiref_1, ir32x, i32, r32x)
        op_load = bldr.gen_sym()
        bldr.new_load(op_load, res, False, rmu.MuMemOrd.NOT_ATOMIC, i32, ir32x)
        op_ret = bldr.gen_sym()
        bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_new, op_cast, op_getiref_0, op_store_0,
                                                 op_shift_1, op_store_1,
                                                 op_shift_2, op_store_2,
                                                 op_shift_3, op_store_3,
                                                 op_getiref_1, op_load, op_ret])

        bldr.new_func_ver(test_fnc_v1, test_fnc, [blk0])

        return {
            "test_fnc": test_fnc,
            "test_fnc_sig": sig__i32,
            "result_type": i32,
            "@i8": i8,
            "@i32": i32
        }

    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert res == 0x8d9f9c1d

def test_uptr_bytestore_load(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i8 = int<8>
            .typedef @i32 = int<32>
            .typedef @pi8 = uptr<@i8>
            .typedef @pi32 = uptr<@i32>
            .const @1_i8 <@i8> = 1
            .const @0x8d_i8 <@i8> = 0x8d
            .const @0x9f_i8 <@i8> = 0x9f
            .const @0x9c_i8 <@i8> = 0x9c
            .const @0x1d_i8 <@i8> = 0x1d
            .funcsig @sig_pi32_i32 = (@pi32) -> (@i32)
            .funcdef @test_fnc VERSION @test_fnc.v1 <@sig_pi32_i32> {
                %blk0(<@pi32> %pi32x):
                    %pi8x_0 = PTRCAST <@pi32 @pi8> %pi32x
                    STORE PTR <@i8> %pi8x_0 @0x1d_i8
                    %pi8x_1 = SHIFTIREF PTR <@i8 @i8> %pi8x_0 @1_i8
                    STORE PTR <@i8> %pi8x_1 @0x9c_i8
                    %pi8x_2 = SHIFTIREF PTR <@i8 @i8> %pi8x_1 @1_i8
                    STORE PTR <@i8> %pi8x_2 @0x9f_i8
                    %pi8x_3 = SHIFTIREF PTR <@i8 @i8> %pi8x_2 @1_i8
                    STORE PTR <@i8> %pi8x_3 @0x8d_i8
                    %res = LOAD PTR <@i32> %pi32x
                    RET %res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        i8 = bldr.gen_sym("@i8"); bldr.new_type_int(i8, 8)
        i32 = bldr.gen_sym("@i32"); bldr.new_type_int(i32, 32)
        pi8 = bldr.gen_sym("@pi8"); bldr.new_type_uptr(pi8, 8)
        pi32 = bldr.gen_sym("@pi32"); bldr.new_type_uptr(pi32, 32)

        c_1_i8 = bldr.gen_sym("@1_i8"); bldr.new_const_int(c_1_i8, i8, 1)
        c_0x8d_i8 = bldr.gen_sym("@0x8d_i8"); bldr.new_const_int(c_0x8d_i8, i8, 0x8d)
        c_0x9f_i8 = bldr.gen_sym("@0x9f_i8"); bldr.new_const_int(c_0x9f_i8, i8, 0x9f)
        c_0x9c_i8 = bldr.gen_sym("@0x9c_i8"); bldr.new_const_int(c_0x9c_i8, i8, 0x9c)
        c_0x1d_i8 = bldr.gen_sym("@0x1d_i8"); bldr.new_const_int(c_0x1d_i8, i8, 0x1d)

        sig_pi32_i32 = bldr.gen_sym("@sig_pi32_i32"); bldr.new_funcsig(sig_pi32_i32, [pi32], [i32])

        test_fnc = bldr.gen_sym("@test_fnc"); bldr.new_func(test_fnc, sig_pi32_i32)

        test_fnc_v1 = bldr.gen_sym("@test_fnc.v1")
        blk0 = bldr.gen_sym("@test_fnc.v1.blk0")
        pi32x = bldr.gen_sym("@test_fnc.v1.blk0.pi32x")
        pi8x_0 = bldr.gen_sym("@test_fnc.v1.blk0.pi8x_0")
        pi8x_1 = bldr.gen_sym("@test_fnc.v1.blk0.pi8x_1")
        pi8x_2 = bldr.gen_sym("@test_fnc.v1.blk0.pi8x_2")
        pi8x_3 = bldr.gen_sym("@test_fnc.v1.blk0.pi8x_3")
        res = bldr.gen_sym("@test_fnc.v1.blk0.res")
        op_cast = bldr.gen_sym(); bldr.new_conv(op_cast, pi8x_0, rmu.MuConvOptr.PTRCAST, pi32, pi8, pi32x)        
        op_store_0 = bldr.gen_sym(); bldr.new_store(op_store_0, True, rmu.MuMemOrd.NOT_ATOMIC, i8, pi8x_0, c_0x1d_i8)
        op_shift_1 = bldr.gen_sym(); bldr.new_shiftiref(op_shift_1, pi8x_1, True, i8, i8, pi8x_0, c_1_i8)
        op_store_1 = bldr.gen_sym(); bldr.new_store(op_store_1, True, rmu.MuMemOrd.NOT_ATOMIC, i8, pi8x_1, c_0x9c_i8)
        op_shift_2 = bldr.gen_sym(); bldr.new_shiftiref(op_shift_2, pi8x_2, True, i8, i8, pi8x_1, c_1_i8)
        op_store_2 = bldr.gen_sym(); bldr.new_store(op_store_2, True, rmu.MuMemOrd.NOT_ATOMIC, i8, pi8x_2, c_0x9f_i8)
        op_shift_3 = bldr.gen_sym(); bldr.new_shiftiref(op_shift_3, pi8x_3, True, i8, i8, pi8x_2, c_1_i8)
        op_store_3 = bldr.gen_sym(); bldr.new_store(op_store_3, True, rmu.MuMemOrd.NOT_ATOMIC, i8, pi8x_3, c_0x8d_i8)
        op_load = bldr.gen_sym(); bldr.new_load(op_load, res, True, rmu.MuMemOrd.NOT_ATOMIC, i32, pi32x)
        op_ret = bldr.gen_sym(); bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [pi32x], [pi32], rmu.MU_NO_ID, [op_cast, op_store_0,
                                                          op_shift_1, op_store_1,
                                                          op_shift_2, op_store_2,
                                                          op_shift_3, op_store_3,
                                                          op_load, op_ret])

        bldr.new_func_ver(test_fnc_v1, test_fnc, [blk0])

        return {
            "test_fnc": test_fnc,
            "test_fnc_sig": sig_pi32_i32,
            "result_type": i32,
            "@i8": i8,
            "@pi8": pi8,
            "@i32": i32,
            "@pi32": pi32
        }

    res = impl_jit_test(cmdopt, build_test_bundle, extra_srcs=['entry_test_uptr_bytestore_load.c'])
    if cmdopt.run:
        assert res == 0x8d9f9c1d