from impl_test_util import impl_jit_test

def test_eq_int(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i64 = int<64>
            .const @0x8d9f9c1d58324b55_i64 <@i64> = 0x8d9f9c1d58324b55
            .const @0xd5a8f2deb00debb4_i64 <@i64> = 0xd5a8f2deb00debb4
            .funcsig @sig__i64 = () -> (@i64)
            .funcdecl @fnc <@fnrsig__i64>
            .funcdef @fnc VERSION @fnc_v1 <@sig__i64> {
                @fnc_v1.blk0():
                    @fnc_v1.blk0.cmp_res = EQ <@i64> @0x8d9f9c1d58324b55 @0xd5a8f2deb00debb4_i64
                    @fnc_v1.blk0.res = ZEXT <@i1 @64> @fnc_v1.blk0.cmp_res
                    RET @fnc_v1.blk0.res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        i1 = bldr.gen_sym("@i1")
        bldr.new_type_int(i1, 1)
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
        cmp_res = bldr.gen_sym("@test_fnc_v1.blk0.cmp_res")
        res = bldr.gen_sym("@test_fnc_v1.blk0.res")
        op_cmpop = bldr.gen_sym()
        bldr.new_cmp(op_cmpop, cmp_res, rmu.MuCmpOptr.EQ, i64, c_0x8d9f9c1d58324b55_i64, c_0xd5a8f2deb00debb4_i64)
        op_convop = bldr.gen_sym()
        bldr.new_conv(op_convop, res, rmu.MuConvOptr.ZEXT, i1, i64, cmp_res)
        op_ret = bldr.gen_sym()
        bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_cmpop, op_convop, op_ret])
        bldr.new_func_ver(v1, test_fnc, [blk0])

        return {
            "@i64": i64,
            "test_fnc_sig": sig__i64,
            "test_fnc": test_fnc,
            "result_type": i64
        }

    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert res == 0

def test_eq_ref(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i64 = int<64>
            .typedef @refi64 = ref<@i64>
            .const @NULL_refi64 <@refi64> = NULL
            .funcsig @sig__i64 = () -> (@i64)
            .funcdecl @fnc <@fnrsig__i64>
            .funcdef @fnc VERSION @fnc_v1 <@sig__i64> {
                @fnc_v1.blk0():
                    @fnc_v1.blk0.r = NEW <@i64>
                    @fnc_v1.blk0.cmp_res = EQ <@refi64> @fnc_v1.blk0.r @NULL_refi64
                    @fnc_v1.blk0.res = ZEXT <@i1 @64> @fnc_v1.blk0.cmp_res
                    RET @fnc_v1.blk0.res
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

        # function body
        v1 = bldr.gen_sym("@test_fnc_v1")
        blk0 = bldr.gen_sym("@test_fnc_v1.blk0")
        r = bldr.gen_sym("@test_fnc_v1.blk0.r")
        cmp_res = bldr.gen_sym("@test_fnc_v1.blk0.cmp_res")
        res = bldr.gen_sym("@test_fnc_v1.blk0.res")
        op_new = bldr.gen_sym()
        bldr.new_new(op_new, r, i64)
        op_cmpop = bldr.gen_sym()
        bldr.new_cmp(op_cmpop, cmp_res, rmu.MuCmpOptr.EQ, refi64, r, NULL_refi64)
        op_convop = bldr.gen_sym()
        bldr.new_conv(op_convop, res, rmu.MuConvOptr.ZEXT, i1, i64, cmp_res)
        op_ret = bldr.gen_sym()
        bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_new, op_cmpop, op_convop, op_ret])
        bldr.new_func_ver(v1, test_fnc, [blk0])

        return {
            "@i64": i64,
            "test_fnc_sig": sig__i64,
            "test_fnc": test_fnc,
            "result_type": i64
        }

    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert res == 0

def test_ne_int(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i64 = int<64>
            .const @0x8d9f9c1d58324b55_i64 <@i64> = 0x8d9f9c1d58324b55
            .const @0xd5a8f2deb00debb4_i64 <@i64> = 0xd5a8f2deb00debb4
            .funcsig @sig__i64 = () -> (@i64)
            .funcdecl @fnc <@fnrsig__i64>
            .funcdef @fnc VERSION @fnc_v1 <@sig__i64> {
                @fnc_v1.blk0():
                    @fnc_v1.blk0.cmp_res = EQ <@i64> @0x8d9f9c1d58324b55 @0xd5a8f2deb00debb4_i64
                    @fnc_v1.blk0.res = ZEXT <@i1 @64> @fnc_v1.blk0.cmp_res
                    RET @fnc_v1.blk0.res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        i1 = bldr.gen_sym("@i1")
        bldr.new_type_int(i1, 1)
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
        cmp_res = bldr.gen_sym("@test_fnc_v1.blk0.cmp_res")
        res = bldr.gen_sym("@test_fnc_v1.blk0.res")
        op_cmpop = bldr.gen_sym()
        bldr.new_cmp(op_cmpop, cmp_res, rmu.MuCmpOptr.NE, i64, c_0x8d9f9c1d58324b55_i64, c_0xd5a8f2deb00debb4_i64)
        op_convop = bldr.gen_sym()
        bldr.new_conv(op_convop, res, rmu.MuConvOptr.ZEXT, i1, i64, cmp_res)
        op_ret = bldr.gen_sym()
        bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_cmpop, op_convop, op_ret])
        bldr.new_func_ver(v1, test_fnc, [blk0])

        return {
            "@i64": i64,
            "test_fnc_sig": sig__i64,
            "test_fnc": test_fnc,
            "result_type": i64
        }

    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert res == 1

def test_ne_ref(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i64 = int<64>
            .typedef @refi64 = ref<@i64>
            .const @NULL_refi64 <@refi64> = NULL
            .funcsig @sig__i64 = () -> (@i64)
            .funcdecl @fnc <@fnrsig__i64>
            .funcdef @fnc VERSION @fnc_v1 <@sig__i64> {
                @fnc_v1.blk0():
                    @fnc_v1.blk0.r = NEW <@i64>
                    @fnc_v1.blk0.cmp_res = EQ <@refi64> @fnc_v1.blk0.r @NULL_refi64
                    @fnc_v1.blk0.res = ZEXT <@i1 @i64> @fnc_v1.blk0.cmp_res
                    RET @fnc_v1.blk0.res
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

        # function body
        v1 = bldr.gen_sym("@test_fnc_v1")
        blk0 = bldr.gen_sym("@test_fnc_v1.blk0")
        r = bldr.gen_sym("@test_fnc_v1.blk0.r")
        cmp_res = bldr.gen_sym("@test_fnc_v1.blk0.cmp_res")
        res = bldr.gen_sym("@test_fnc_v1.blk0.res")
        op_new = bldr.gen_sym()
        bldr.new_new(op_new, r, i64)
        op_cmpop = bldr.gen_sym()
        bldr.new_cmp(op_cmpop, cmp_res, rmu.MuCmpOptr.NE, refi64, r, NULL_refi64)
        op_convop = bldr.gen_sym()
        bldr.new_conv(op_convop, res, rmu.MuConvOptr.ZEXT, i1, i64, cmp_res)
        op_ret = bldr.gen_sym()
        bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_new, op_cmpop, op_convop, op_ret])
        bldr.new_func_ver(v1, test_fnc, [blk0])

        return {
            "@i64": i64,
            "test_fnc_sig": sig__i64,
            "test_fnc": test_fnc,
            "result_type": i64
        }

    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert res == 1

def test_sge(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i8 = int<64>
            .const @0xff_i8 <@i8> = 0xff
            .const @0x0a_i8 <@i8> = 0x0a
            .funcsig @sig__i8 = () -> (@i8)
            .funcdecl @fnc <@fnrsig__i8>
            .funcdef @fnc VERSION @fnc_v1 <@sig__i8> {
                @fnc_v1.blk0():
                    @fnc_v1.blk0.cmp_res_1 = SGE <@i8> @0xff_i8 @0x0a_i8
                    @fnc_v1.blk0.cmp_res_2 = SGE <@i8> @0xff_i8 @0xff_i8
                    @fnc_v1.blk0.bin_res = XOR <@i1> @fnc_v1.blk0.cmp_res_1 @fnc_v1.blk0.cmp_res_2
                    @fnc_v1.blk0.res = ZEXT <@i1 @i8> @fnc_v1.blk0.bin_res
                    RET @fnc_v1.blk0.res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        i1 = bldr.gen_sym("@i1")
        bldr.new_type_int(i1, 1)
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
        cmp_res_1 = bldr.gen_sym("@test_fnc_v1.blk0.cmp_res_1")
        cmp_res_2 = bldr.gen_sym("@test_fnc_v1.blk0.cmp_res_2")
        bin_res = bldr.gen_sym("@test_fnc_v1.blk0.bin_res")
        res = bldr.gen_sym("@test_fnc_v1.blk0.res")
        op_cmpop_1 = bldr.gen_sym()
        bldr.new_cmp(op_cmpop_1, cmp_res_1, rmu.MuCmpOptr.SGE, i8, c_0xff_i8, c_0x0a_i8)
        op_cmpop_2 = bldr.gen_sym()
        bldr.new_cmp(op_cmpop_2, cmp_res_2, rmu.MuCmpOptr.SGE, i8, c_0xff_i8, c_0xff_i8)
        op_binop = bldr.gen_sym()
        bldr.new_binop(op_binop, bin_res, rmu.MuBinOptr.XOR, i1, cmp_res_1, cmp_res_2)
        op_convop = bldr.gen_sym()
        bldr.new_conv(op_convop, res, rmu.MuConvOptr.ZEXT, i1, i8, bin_res)
        op_ret = bldr.gen_sym()
        bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_cmpop_1, op_cmpop_2, op_binop, op_convop, op_ret])
        bldr.new_func_ver(v1, test_fnc, [blk0])

        return {
            "@i8": i8,
            "test_fnc_sig": sig__i8,
            "test_fnc": test_fnc,
            "result_type": i8
        }

    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert res == 1

def test_sgt(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i8 = int<64>
            .const @0xff_i8 <@i8> = 0xff
            .const @0x0a_i8 <@i8> = 0x0a
            .funcsig @sig__i8 = () -> (@i8)
            .funcdecl @fnc <@fnrsig__i8>
            .funcdef @fnc VERSION @fnc_v1 <@sig__i8> {
                @fnc_v1.blk0():
                    @fnc_v1.blk0.cmp_res_1 = SGT <@i8> @0xff_i8 @0x0a_i8
                    @fnc_v1.blk0.cmp_res_2 = SGT <@i8> @0xff_i8 @0xff_i8
                    @fnc_v1.blk0.bin_res = OR <@i1> @fnc_v1.blk0.cmp_res_1 @fnc_v1.blk0.cmp_res_2
                    @fnc_v1.blk0.res = ZEXT <@i1 @i8> @fnc_v1.blk0.bin_res
                    RET @fnc_v1.blk0.res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        i1 = bldr.gen_sym("@i1")
        bldr.new_type_int(i1, 1)
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
        cmp_res_1 = bldr.gen_sym("@test_fnc_v1.blk0.cmp_res_1")
        cmp_res_2 = bldr.gen_sym("@test_fnc_v1.blk0.cmp_res_2")
        bin_res = bldr.gen_sym("@test_fnc_v1.blk0.bin_res")
        res = bldr.gen_sym("@test_fnc_v1.blk0.res")
        op_cmpop_1 = bldr.gen_sym()
        bldr.new_cmp(op_cmpop_1, cmp_res_1, rmu.MuCmpOptr.SGT, i8, c_0xff_i8, c_0x0a_i8)
        op_cmpop_2 = bldr.gen_sym()
        bldr.new_cmp(op_cmpop_2, cmp_res_2, rmu.MuCmpOptr.SGT, i8, c_0xff_i8, c_0xff_i8)
        op_binop = bldr.gen_sym()
        bldr.new_binop(op_binop, bin_res, rmu.MuBinOptr.OR, i1, cmp_res_1, cmp_res_2)
        op_convop = bldr.gen_sym()
        bldr.new_conv(op_convop, res, rmu.MuConvOptr.ZEXT, i1, i8, bin_res)
        op_ret = bldr.gen_sym()
        bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_cmpop_1, op_cmpop_2, op_binop, op_convop, op_ret])
        bldr.new_func_ver(v1, test_fnc, [blk0])

        return {
            "@i8": i8,
            "test_fnc_sig": sig__i8,
            "test_fnc": test_fnc,
            "result_type": i8
        }

    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert res == 0

def test_sle(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i8 = int<64>
            .const @0xff_i8 <@i8> = 0xff
            .const @0x0a_i8 <@i8> = 0x0a
            .funcsig @sig__i8 = () -> (@i8)
            .funcdecl @fnc <@fnrsig__i8>
            .funcdef @fnc VERSION @fnc_v1 <@sig__i8> {
                @fnc_v1.blk0():
                    @fnc_v1.blk0.cmp_res_1 = SLE <@i8> @0x0a_i8 @0xff_i8
                    @fnc_v1.blk0.cmp_res_2 = SLE <@i8> @0xff_i8 @0xff_i8
                    @fnc_v1.blk0.bin_res = XOR <@i1> @fnc_v1.blk0.cmp_res_1 @fnc_v1.blk0.cmp_res_2
                    @fnc_v1.blk0.res = ZEXT <@i1 @i8> @fnc_v1.blk0.bin_res
                    RET @fnc_v1.blk0.res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        i1 = bldr.gen_sym("@i1")
        bldr.new_type_int(i1, 1)
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
        cmp_res_1 = bldr.gen_sym("@test_fnc_v1.blk0.cmp_res_1")
        cmp_res_2 = bldr.gen_sym("@test_fnc_v1.blk0.cmp_res_2")
        bin_res = bldr.gen_sym("@test_fnc_v1.blk0.bin_res")
        res = bldr.gen_sym("@test_fnc_v1.blk0.res")
        op_cmpop_1 = bldr.gen_sym()
        bldr.new_cmp(op_cmpop_1, cmp_res_1, rmu.MuCmpOptr.SLE, i8, c_0x0a_i8, c_0xff_i8)
        op_cmpop_2 = bldr.gen_sym()
        bldr.new_cmp(op_cmpop_2, cmp_res_2, rmu.MuCmpOptr.SLE, i8, c_0xff_i8, c_0xff_i8)
        op_binop = bldr.gen_sym()
        bldr.new_binop(op_binop, bin_res, rmu.MuBinOptr.XOR, i1, cmp_res_1, cmp_res_2)
        op_convop = bldr.gen_sym()
        bldr.new_conv(op_convop, res, rmu.MuConvOptr.ZEXT, i1, i8, bin_res)
        op_ret = bldr.gen_sym()
        bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_cmpop_1, op_cmpop_2, op_binop, op_convop, op_ret])
        bldr.new_func_ver(v1, test_fnc, [blk0])

        return {
            "@i8": i8,
            "test_fnc_sig": sig__i8,
            "test_fnc": test_fnc,
            "result_type": i8
        }

    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert res == 1

def test_slt(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i8 = int<64>
            .const @0xff_i8 <@i8> = 0xff
            .const @0x0a_i8 <@i8> = 0x0a
            .funcsig @sig__i8 = () -> (@i8)
            .funcdecl @fnc <@fnrsig__i8>
            .funcdef @fnc VERSION @fnc_v1 <@sig__i8> {
                @fnc_v1.blk0():
                    @fnc_v1.blk0.cmp_res_1 = SLT <@i8> @0x0a_i8s @0xff_i8
                    @fnc_v1.blk0.cmp_res_2 = SLT <@i8> @0xff_i8s @0xff_i8s
                    @fnc_v1.blk0.bin_res = OR <@i1> @fnc_v1.blk0.cmp_res_1 @fnc_v1.blk0.cmp_res_2
                    @fnc_v1.blk0.res = ZEXT <@i1 @i8> @fnc_v1.blk0.bin_res
                    RET @fnc_v1.blk0.res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        i1 = bldr.gen_sym("@i1")
        bldr.new_type_int(i1, 1)
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
        cmp_res_1 = bldr.gen_sym("@test_fnc_v1.blk0.cmp_res_1")
        cmp_res_2 = bldr.gen_sym("@test_fnc_v1.blk0.cmp_res_2")
        bin_res = bldr.gen_sym("@test_fnc_v1.blk0.bin_res")
        res = bldr.gen_sym("@test_fnc_v1.blk0.res")
        op_cmpop_1 = bldr.gen_sym()
        bldr.new_cmp(op_cmpop_1, cmp_res_1, rmu.MuCmpOptr.SLT, i8, c_0x0a_i8, c_0xff_i8)
        op_cmpop_2 = bldr.gen_sym()
        bldr.new_cmp(op_cmpop_2, cmp_res_2, rmu.MuCmpOptr.SLT, i8, c_0xff_i8, c_0xff_i8)
        op_binop = bldr.gen_sym()
        bldr.new_binop(op_binop, bin_res, rmu.MuBinOptr.OR, i1, cmp_res_1, cmp_res_2)
        op_convop = bldr.gen_sym()
        bldr.new_conv(op_convop, res, rmu.MuConvOptr.ZEXT, i1, i8, bin_res)
        op_ret = bldr.gen_sym()
        bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_cmpop_1, op_cmpop_2, op_binop, op_convop, op_ret])
        bldr.new_func_ver(v1, test_fnc, [blk0])

        return {
            "@i8": i8,
            "test_fnc_sig": sig__i8,
            "test_fnc": test_fnc,
            "result_type": i8
        }

    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert res == 0

def test_ult(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i8 = int<64>
            .const @0xff_i8 <@i8> = 0xff
            .const @0x0a_i8 <@i8> = 0x0a
            .funcsig @sig__i8 = () -> (@i8)
            .funcdecl @fnc <@fnrsig__i8>
            .funcdef @fnc VERSION @fnc_v1 <@sig__i8> {
                @fnc_v1.blk0():
                    @fnc_v1.blk0.cmp_res_1 = ULT <@i8> @0xff_i8s @0x0a_i8
                    @fnc_v1.blk0.cmp_res_2 = ULT <@i8> @0xff_i8s @0xff_i8s
                    @fnc_v1.blk0.bin_res = OR <@i1> @fnc_v1.blk0.cmp_res_1 @fnc_v1.blk0.cmp_res_2
                    @fnc_v1.blk0.res = ZEXT <@i1 @i8> @fnc_v1.blk0.bin_res
                    RET @fnc_v1.blk0.res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        i1 = bldr.gen_sym("@i1")
        bldr.new_type_int(i1, 1)
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
        cmp_res_1 = bldr.gen_sym("@test_fnc_v1.blk0.cmp_res_1")
        cmp_res_2 = bldr.gen_sym("@test_fnc_v1.blk0.cmp_res_2")
        bin_res = bldr.gen_sym("@test_fnc_v1.blk0.bin_res")
        res = bldr.gen_sym("@test_fnc_v1.blk0.res")
        op_cmpop_1 = bldr.gen_sym()
        bldr.new_cmp(op_cmpop_1, cmp_res_1, rmu.MuCmpOptr.ULT, i8, c_0xff_i8, c_0x0a_i8)
        op_cmpop_2 = bldr.gen_sym()
        bldr.new_cmp(op_cmpop_2, cmp_res_2, rmu.MuCmpOptr.ULT, i8, c_0xff_i8, c_0xff_i8)
        op_binop = bldr.gen_sym()
        bldr.new_binop(op_binop, bin_res, rmu.MuBinOptr.OR, i1, cmp_res_1, cmp_res_2)
        op_convop = bldr.gen_sym()
        bldr.new_conv(op_convop, res, rmu.MuConvOptr.ZEXT, i1, i8, bin_res)
        op_ret = bldr.gen_sym()
        bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_cmpop_1, op_cmpop_2, op_binop, op_convop, op_ret])
        bldr.new_func_ver(v1, test_fnc, [blk0])

        return {
            "@i8": i8,
            "test_fnc_sig": sig__i8,
            "test_fnc": test_fnc,
            "result_type": i8
        }

    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert res == 0