from impl_test_util import impl_jit_test


def test_double_add(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @dbl = double
            .const @pi <@dbl> = 3.1415926
            .const @e <@dbl> = 2.71828
            .funcsig @sig__dbl = () -> (@dbl)
            .funcdef @test_fnc VERSION @test_fnc.v1 <@sig__dbl> {
                %blk0():
                    %res = FADD <@dbl> @pi @e
                    RET %res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        dbl = bldr.gen_sym("@dbl"); bldr.new_type_double(dbl)

        pi = bldr.gen_sym("@pi"); bldr.new_const_double(pi, dbl, 3.141593)
        e = bldr.gen_sym("@e"); bldr.new_const_double(e, dbl, 2.71828)

        sig__dbl = bldr.gen_sym("@sig__dbl"); bldr.new_funcsig(sig__dbl, [], [dbl])

        test_fnc = bldr.gen_sym("@test_fnc"); bldr.new_func(test_fnc, sig__dbl)

        test_fnc_v1 = bldr.gen_sym("@test_fnc.v1")
        blk0 = bldr.gen_sym("@test_fnc.v1.blk0")
        res = bldr.gen_sym("@test_fnc.v1.blk0.res")
        op_binop = bldr.gen_sym(); bldr.new_binop(op_binop, res, rmu.MuBinOptr.FADD, dbl, pi, e)
        op_ret = bldr.gen_sym(); bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_binop, op_ret])

        bldr.new_func_ver(test_fnc_v1, test_fnc, [blk0])

        return {
            "test_fnc": test_fnc,
            "test_fnc_sig": sig__dbl,
            "result_type": dbl,
            "handle_conv_dst_type": 'double',
        }
    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert res == 5.859873


def within_err(res, exp, err=1e15):
    return abs(res - exp) < err


def test_double_sub(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @dbl = double
            .const @pi <@dbl> = 3.1415926
            .const @e <@dbl> = 2.71828
            .funcsig @sig__dbl = () -> (@dbl)
            .funcdef @test_fnc VERSION @test_fnc.v1 <@sig__dbl> {
                %blk0():
                    %res = FSUB <@dbl> @pi @e
                    RET %res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        dbl = bldr.gen_sym("@dbl"); bldr.new_type_double(dbl)

        pi = bldr.gen_sym("@pi"); bldr.new_const_double(pi, dbl, 3.141593)
        e = bldr.gen_sym("@e"); bldr.new_const_double(e, dbl, 2.71828)

        sig__dbl = bldr.gen_sym("@sig__dbl"); bldr.new_funcsig(sig__dbl, [], [dbl])

        test_fnc = bldr.gen_sym("@test_fnc"); bldr.new_func(test_fnc, sig__dbl)

        test_fnc_v1 = bldr.gen_sym("@test_fnc.v1")
        blk0 = bldr.gen_sym("@test_fnc.v1.blk0")
        res = bldr.gen_sym("@test_fnc.v1.blk0.res")
        op_binop = bldr.gen_sym(); bldr.new_binop(op_binop, res, rmu.MuBinOptr.FSUB, dbl, pi, e)
        op_ret = bldr.gen_sym(); bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_binop, op_ret])

        bldr.new_func_ver(test_fnc_v1, test_fnc, [blk0])

        return {
            "test_fnc": test_fnc,
            "test_fnc_sig": sig__dbl,
            "result_type": dbl,
            "handle_conv_dst_type": 'double',
        }
    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert within_err(res, 0.423313)


def test_double_mul(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @dbl = double
            .const @pi <@dbl> = 3.1415926
            .const @e <@dbl> = 2.71828
            .funcsig @sig__dbl = () -> (@dbl)
            .funcdef @test_fnc VERSION @test_fnc.v1 <@sig__dbl> {
                %blk0():
                    %res = FMUL <@dbl> @pi @e
                    RET %res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        dbl = bldr.gen_sym("@dbl"); bldr.new_type_double(dbl)

        pi = bldr.gen_sym("@pi"); bldr.new_const_double(pi, dbl, 3.141593)
        e = bldr.gen_sym("@e"); bldr.new_const_double(e, dbl, 2.71828)

        sig__dbl = bldr.gen_sym("@sig__dbl"); bldr.new_funcsig(sig__dbl, [], [dbl])

        test_fnc = bldr.gen_sym("@test_fnc"); bldr.new_func(test_fnc, sig__dbl)

        test_fnc_v1 = bldr.gen_sym("@test_fnc.v1")
        blk0 = bldr.gen_sym("@test_fnc.v1.blk0")
        res = bldr.gen_sym("@test_fnc.v1.blk0.res")
        op_binop = bldr.gen_sym(); bldr.new_binop(op_binop, res, rmu.MuBinOptr.FMUL, dbl, pi, e)
        op_ret = bldr.gen_sym(); bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_binop, op_ret])

        bldr.new_func_ver(test_fnc_v1, test_fnc, [blk0])

        return {
            "test_fnc": test_fnc,
            "test_fnc_sig": sig__dbl,
            "result_type": dbl,
            "handle_conv_dst_type": 'double',
        }
    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert res == 8.53972942004


def test_double_div(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @dbl = double
            .const @pi <@dbl> = 3.1415926
            .const @e <@dbl> = 2.71828
            .funcsig @sig__dbl = () -> (@dbl)
            .funcdef @test_fnc VERSION @test_fnc.v1 <@sig__dbl> {
                %blk0():
                    %res = FDIV <@dbl> @pi @e
                    RET %res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        dbl = bldr.gen_sym("@dbl"); bldr.new_type_double(dbl)

        pi = bldr.gen_sym("@pi"); bldr.new_const_double(pi, dbl, 3.141593)
        e = bldr.gen_sym("@e"); bldr.new_const_double(e, dbl, 2.71828)

        sig__dbl = bldr.gen_sym("@sig__dbl"); bldr.new_funcsig(sig__dbl, [], [dbl])

        test_fnc = bldr.gen_sym("@test_fnc"); bldr.new_func(test_fnc, sig__dbl)

        test_fnc_v1 = bldr.gen_sym("@test_fnc.v1")
        blk0 = bldr.gen_sym("@test_fnc.v1.blk0")
        res = bldr.gen_sym("@test_fnc.v1.blk0.res")
        op_binop = bldr.gen_sym(); bldr.new_binop(op_binop, res, rmu.MuBinOptr.FDIV, dbl, pi, e)
        op_ret = bldr.gen_sym(); bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_binop, op_ret])

        bldr.new_func_ver(test_fnc_v1, test_fnc, [blk0])

        return {
            "test_fnc": test_fnc,
            "test_fnc_sig": sig__dbl,
            "result_type": dbl,
            "handle_conv_dst_type": 'double',
        }
    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert within_err(res, 1.1557282546316052)


def test_double_ordered_eq(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @dbl = double
            .typedef @i1 = int<1>
            .typedef @i64 = int<64>
            .const @pi <@dbl> = 3.1415926
            .const @e <@dbl> = 2.71828
            .funcsig @sig__i64 = () -> (@dbl)
            .funcdef @test_fnc VERSION @test_fnc.v1 <@sig__i64> {
                %blk0():
                    %cmpres = FOEQ <@dbl> @pi @e
                    %res = ZEXT <@i1 @i64> %cmpres
                    RET %res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        dbl = bldr.gen_sym("@dbl"); bldr.new_type_double(dbl)
        i1 = bldr.gen_sym("@i1"); bldr.new_type_int(i1, 1)
        i64 = bldr.gen_sym("@i64"); bldr.new_type_int(i64, 64)

        pi = bldr.gen_sym("@pi"); bldr.new_const_double(pi, dbl, 3.141593)
        e = bldr.gen_sym("@e"); bldr.new_const_double(e, dbl, 2.71828)

        sig__i64 = bldr.gen_sym("@sig__i64"); bldr.new_funcsig(sig__i64, [], [i64])

        test_fnc = bldr.gen_sym("@test_fnc"); bldr.new_func(test_fnc, sig__i64)

        test_fnc_v1 = bldr.gen_sym("@test_fnc.v1")
        blk0 = bldr.gen_sym("@test_fnc.v1.blk0")
        cmpres = bldr.gen_sym("@test_fnc.v1.blk0.cmpres")
        res = bldr.gen_sym("@test_fnc.v1.blk0.res")
        op_cmpop = bldr.gen_sym(); bldr.new_cmp(op_cmpop, cmpres, rmu.MuCmpOptr.FOEQ, dbl, pi, e)
        op_zext = bldr.gen_sym(); bldr.new_conv(op_zext, res, rmu.MuConvOptr.ZEXT, i1, i64, cmpres)
        op_ret = bldr.gen_sym(); bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_cmpop, op_zext, op_ret])

        bldr.new_func_ver(test_fnc_v1, test_fnc, [blk0])

        return {
            "test_fnc": test_fnc,
            "test_fnc_sig": sig__i64,
            "result_type": i64,
            "handle_conv_dst_type": 'uint64',
        }
    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert res == 0


def test_double_ordered_ne(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @dbl = double
            .typedef @i1 = int<1>
            .typedef @i64 = int<64>
            .const @1_dbl <@dbl> = 1.0
            .const @3_dbl <@dbl> = 3.0
            .const @zp3 <@dbl> = 0.3
            .funcsig @sig__i64 = () -> (@dbl)
            .funcdef @test_fnc VERSION @test_fnc.v1 <@sig__i64> {
                %blk0():
                    %k = FDIV <@dbl> @1_dbl @3_dbl
                    %cmpres = FONE %k %zp3
                    %res = ZEXT <@i1 @i64> %cmpres
                    RET %res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        dbl = bldr.gen_sym("@dbl"); bldr.new_type_double(dbl)
        i1 = bldr.gen_sym("@i1"); bldr.new_type_int(i1, 1)
        i64 = bldr.gen_sym("@i64"); bldr.new_type_int(i64, 64)

        c_1_dbl = bldr.gen_sym("@1_dbl"); bldr.new_const_double(c_1_dbl, dbl, 1.0)
        c_3_dbl = bldr.gen_sym("@3_dbl"); bldr.new_const_double(c_3_dbl, dbl, 3.0)
        zp3 = bldr.gen_sym("@zp3"); bldr.new_const_double(zp3, dbl, 0.3)

        sig__i64 = bldr.gen_sym("@sig__i64"); bldr.new_funcsig(sig__i64, [], [i64])

        test_fnc = bldr.gen_sym("@test_fnc"); bldr.new_func(test_fnc, sig__i64)

        test_fnc_v1 = bldr.gen_sym("@test_fnc.v1")
        blk0 = bldr.gen_sym("@test_fnc.v1.blk0")
        k = bldr.gen_sym("@test_fnc.v1.blk0.k")
        cmpres = bldr.gen_sym("@test_fnc.v1.blk0.cmpres")
        res = bldr.gen_sym("@test_fnc.v1.blk0.res")
        op_binop = bldr.gen_sym(); bldr.new_binop(op_binop, k, rmu.MuBinOptr.FDIV, dbl, c_1_dbl, c_3_dbl)
        op_cmpop = bldr.gen_sym(); bldr.new_cmp(op_cmpop, cmpres, rmu.MuCmpOptr.FONE, dbl, k, zp3)
        op_zext = bldr.gen_sym(); bldr.new_conv(op_zext, res, rmu.MuConvOptr.ZEXT, i1, i64, cmpres)
        op_ret = bldr.gen_sym(); bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_binop, op_cmpop, op_zext, op_ret])

        bldr.new_func_ver(test_fnc_v1, test_fnc, [blk0])

        return {
            "test_fnc": test_fnc,
            "test_fnc_sig": sig__i64,
            "result_type": i64,
            "handle_conv_dst_type": 'uint64',
        }
    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert res == 1


def test_double_ordered_lt(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @dbl = double
            .typedef @i1 = int<1>
            .typedef @i64 = int<64>
            .const @pi <@dbl> = 3.1415926
            .const @e <@dbl> = 2.71828
            .funcsig @sig__i64 = () -> (@dbl)
            .funcdef @test_fnc VERSION @test_fnc.v1 <@sig__i64> {
                %blk0():
                    %cmpres = FOLT <@dbl> @e @pi
                    %res = ZEXT <@i1 @i64> %cmpres
                    RET %res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        dbl = bldr.gen_sym("@dbl"); bldr.new_type_double(dbl)
        i1 = bldr.gen_sym("@i1"); bldr.new_type_int(i1, 1)
        i64 = bldr.gen_sym("@i64"); bldr.new_type_int(i64, 64)

        pi = bldr.gen_sym("@pi"); bldr.new_const_double(pi, dbl, 3.141593)
        e = bldr.gen_sym("@e"); bldr.new_const_double(e, dbl, 2.71828)

        sig__i64 = bldr.gen_sym("@sig__i64"); bldr.new_funcsig(sig__i64, [], [i64])

        test_fnc = bldr.gen_sym("@test_fnc"); bldr.new_func(test_fnc, sig__i64)

        test_fnc_v1 = bldr.gen_sym("@test_fnc.v1")
        blk0 = bldr.gen_sym("@test_fnc.v1.blk0")
        cmpres = bldr.gen_sym("@test_fnc.v1.blk0.cmpres")
        res = bldr.gen_sym("@test_fnc.v1.blk0.res")
        op_cmpop = bldr.gen_sym(); bldr.new_cmp(op_cmpop, cmpres, rmu.MuCmpOptr.FOLT, dbl, e, pi)
        op_zext = bldr.gen_sym(); bldr.new_conv(op_zext, res, rmu.MuConvOptr.ZEXT, i1, i64, cmpres)
        op_ret = bldr.gen_sym(); bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_cmpop, op_zext, op_ret])

        bldr.new_func_ver(test_fnc_v1, test_fnc, [blk0])

        return {
            "test_fnc": test_fnc,
            "test_fnc_sig": sig__i64,
            "result_type": i64,
            "handle_conv_dst_type": 'uint64',
        }
    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert res == 1


def test_double_ordered_le(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @dbl = double
            .typedef @i1 = int<1>
            .typedef @i64 = int<64>
            .const @pi <@dbl> = 3.1415926
            .const @e <@dbl> = 2.71828
            .funcsig @sig__i64 = () -> (@dbl)
            .funcdef @test_fnc VERSION @test_fnc.v1 <@sig__i64> {
                %blk0():
                    %cmpres = FOLE <@dbl> @pi @e
                    %res = ZEXT <@i1 @i64> %cmpres
                    RET %res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        dbl = bldr.gen_sym("@dbl"); bldr.new_type_double(dbl)
        i1 = bldr.gen_sym("@i1"); bldr.new_type_int(i1, 1)
        i64 = bldr.gen_sym("@i64"); bldr.new_type_int(i64, 64)

        pi = bldr.gen_sym("@pi"); bldr.new_const_double(pi, dbl, 3.141593)

        sig__i64 = bldr.gen_sym("@sig__i64"); bldr.new_funcsig(sig__i64, [], [i64])

        test_fnc = bldr.gen_sym("@test_fnc"); bldr.new_func(test_fnc, sig__i64)

        test_fnc_v1 = bldr.gen_sym("@test_fnc.v1")
        blk0 = bldr.gen_sym("@test_fnc.v1.blk0")
        cmpres = bldr.gen_sym("@test_fnc.v1.blk0.cmpres")
        res = bldr.gen_sym("@test_fnc.v1.blk0.res")
        op_cmpop = bldr.gen_sym(); bldr.new_cmp(op_cmpop, cmpres, rmu.MuCmpOptr.FOLE, dbl, pi, pi)
        op_zext = bldr.gen_sym(); bldr.new_conv(op_zext, res, rmu.MuConvOptr.ZEXT, i1, i64, cmpres)
        op_ret = bldr.gen_sym(); bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_cmpop, op_zext, op_ret])

        bldr.new_func_ver(test_fnc_v1, test_fnc, [blk0])

        return {
            "test_fnc": test_fnc,
            "test_fnc_sig": sig__i64,
            "result_type": i64,
            "handle_conv_dst_type": 'uint64',
        }
    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert res == 1


def test_double_ordered_ge(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @dbl = double
            .typedef @i1 = int<1>
            .typedef @i64 = int<64>
            .const @pi <@dbl> = 3.1415926
            .const @e <@dbl> = 2.71828
            .funcsig @sig__i64 = () -> (@dbl)
            .funcdef @test_fnc VERSION @test_fnc.v1 <@sig__i64> {
                %blk0():
                    %cmpres = FOGE <@dbl> @pi @e
                    %res = ZEXT <@i1 @i64> %cmpres
                    RET %res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        dbl = bldr.gen_sym("@dbl"); bldr.new_type_double(dbl)
        i1 = bldr.gen_sym("@i1"); bldr.new_type_int(i1, 1)
        i64 = bldr.gen_sym("@i64"); bldr.new_type_int(i64, 64)

        e = bldr.gen_sym("@e"); bldr.new_const_double(e, dbl, 2.71828)

        sig__i64 = bldr.gen_sym("@sig__i64"); bldr.new_funcsig(sig__i64, [], [i64])

        test_fnc = bldr.gen_sym("@test_fnc"); bldr.new_func(test_fnc, sig__i64)

        test_fnc_v1 = bldr.gen_sym("@test_fnc.v1")
        blk0 = bldr.gen_sym("@test_fnc.v1.blk0")
        cmpres = bldr.gen_sym("@test_fnc.v1.blk0.cmpres")
        res = bldr.gen_sym("@test_fnc.v1.blk0.res")
        op_cmpop = bldr.gen_sym(); bldr.new_cmp(op_cmpop, cmpres, rmu.MuCmpOptr.FOGE, dbl, e, e)
        op_zext = bldr.gen_sym(); bldr.new_conv(op_zext, res, rmu.MuConvOptr.ZEXT, i1, i64, cmpres)
        op_ret = bldr.gen_sym(); bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_cmpop, op_zext, op_ret])

        bldr.new_func_ver(test_fnc_v1, test_fnc, [blk0])

        return {
            "test_fnc": test_fnc,
            "test_fnc_sig": sig__i64,
            "result_type": i64,
            "handle_conv_dst_type": 'uint64',
        }
    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert res == 1


def test_double_ordered_gt(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @dbl = double
            .typedef @i1 = int<1>
            .typedef @i64 = int<64>
            .const @pi <@dbl> = 3.1415926
            .const @e <@dbl> = 2.71828
            .funcsig @sig__i64 = () -> (@dbl)
            .funcdef @test_fnc VERSION @test_fnc.v1 <@sig__i64> {
                %blk0():
                    %cmpres = FOGT <@dbl> @pi @e
                    %res = ZEXT <@i1 @i64> %cmpres
                    RET %res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVsM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        dbl = bldr.gen_sym("@dbl"); bldr.new_type_double(dbl)
        i1 = bldr.gen_sym("@i1"); bldr.new_type_int(i1, 1)
        i64 = bldr.gen_sym("@i64"); bldr.new_type_int(i64, 64)

        pi = bldr.gen_sym("@pi"); bldr.new_const_double(pi, dbl, 3.141593)
        e = bldr.gen_sym("@e"); bldr.new_const_double(e, dbl, 2.71828)

        sig__i64 = bldr.gen_sym("@sig__i64"); bldr.new_funcsig(sig__i64, [], [i64])

        test_fnc = bldr.gen_sym("@test_fnc"); bldr.new_func(test_fnc, sig__i64)

        test_fnc_v1 = bldr.gen_sym("@test_fnc.v1")
        blk0 = bldr.gen_sym("@test_fnc.v1.blk0")
        cmpres = bldr.gen_sym("@test_fnc.v1.blk0.cmpres")
        res = bldr.gen_sym("@test_fnc.v1.blk0.res")
        op_cmpop = bldr.gen_sym(); bldr.new_cmp(op_cmpop, cmpres, rmu.MuCmpOptr.FOGT, dbl, pi, e)
        op_zext = bldr.gen_sym(); bldr.new_conv(op_zext, res, rmu.MuConvOptr.ZEXT, i1, i64, cmpres)
        op_ret = bldr.gen_sym(); bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [], [], rmu.MU_NO_ID, [op_cmpop, op_zext, op_ret])

        bldr.new_func_ver(test_fnc_v1, test_fnc, [blk0])

        return {
            "test_fnc": test_fnc,
            "test_fnc_sig": sig__i64,
            "result_type": i64,
            "handle_conv_dst_type": 'uint64',
        }
    res = impl_jit_test(cmdopt, build_test_bundle)
    if cmdopt.run:
        assert res == 1


def test_double_arg_pass(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @dbl = double
            .funcsig @sig_dbldbl_dbl = (@dbl @dbl) -> (@dbl)
            .funcdef @test_fnc VERSION @test_fnc.v1 <@sig_dbldbl_dbl> {
                %blk0(<@dbl> %a <@dbl> %b):
                    %res = FADD <@dbl> %a %b
                    RET %res
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVsM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        dbl = bldr.gen_sym("@dbl"); bldr.new_type_double(dbl)

        sig_dbldbl_dbl = bldr.gen_sym("@sig_dbldbl_dbl"); bldr.new_funcsig(sig_dbldbl_dbl, [dbl, dbl], [dbl])

        test_fnc = bldr.gen_sym("@test_fnc"); bldr.new_func(test_fnc, sig_dbldbl_dbl)

        test_fnc_v1 = bldr.gen_sym("@test_fnc.v1")
        blk0 = bldr.gen_sym("@test_fnc.v1.blk0")
        a = bldr.gen_sym("@test_fnc.v1.blk0.a")
        b = bldr.gen_sym("@test_fnc.v1.blk0.b")
        res = bldr.gen_sym("@test_fnc.v1.blk0.res")
        op_binop = bldr.gen_sym(); bldr.new_binop(op_binop, res, rmu.MuBinOptr.FADD, dbl, a, b)
        op_ret = bldr.gen_sym(); bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [a, b], [dbl, dbl], rmu.MU_NO_ID, [op_binop, op_ret])

        bldr.new_func_ver(test_fnc_v1, test_fnc, [blk0])

        return {
            "test_fnc": test_fnc,
            "test_fnc_sig": sig_dbldbl_dbl,
            "result_type": dbl,
            "handle_conv_dst_type": 'double',
        }
    res = impl_jit_test(cmdopt, build_test_bundle)
