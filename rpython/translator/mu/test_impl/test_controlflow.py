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
            .const @c_fnc <@fnpsig_i64_i64> = EXTERN "fnc"
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

    impl_jit_test(cmdopt, build_test_bundle, extend_with_entrypoint, ["suite/test_ccall_fnc.c"])


def test_extern_func(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i32 = int<32>
            .typedef @i64 = int<64>
            .typedef @void = void
            .typedef @voidp = uptr<@void>
            .const @fd_stdout <@i32> = 1
            .funcsig @sig_voidpi64_i64 = (@voidp @i64) -> ()
            .funcsig @sig_i32voidpi64_i64 = (@i32 @voidp @i64) -> (@i64)
            .typedef @fnpsig_i32voidpi64_i64 = ufuncptr<@sig_i32voidpi64_i64>
            .const c_write <@fnpsig_voidpi64_i64> = EXTERN "write"
            .funcdef @test_write VERSION @test_write_v1 <@sig_voidpi64_i64> {
                %blk0(<@voidp> %buf <@i64> %sz):
                    %res = CCALL <@sig_i32voidpi64_i64> @c_write (@fd_stdout %buf %sz)
                    RET %res
            }

        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        i32 = bldr.gen_sym("@i32"); bldr.new_type_int(i32, 32)
        i64 = bldr.gen_sym("@i64"); bldr.new_type_int(i64, 64)
        void = bldr.gen_sym("@void"); bldr.new_type_void(void)
        voidp = bldr.gen_sym("@voidp"); bldr.new_type_uptr(voidp, void)

        fd_stdout = bldr.gen_sym("@fd_stdout"); bldr.new_const_int(fd_stdout, i32, 1)
        sig_voidpi64_i64 = bldr.gen_sym("@sig_voidpi64_i64"); bldr.new_funcsig(sig_voidpi64_i64, [voidp, i64], [i64])
        sig_i32voidpi64_i64 = bldr.gen_sym("@sig_i32voidpi64_i64"); bldr.new_funcsig(sig_i32voidpi64_i64, [i32, voidp, i64], [i64])

        fnpsig_i32voidpi64_i64 = bldr.gen_sym("@fnpsig_i32voidpi64_i64"); bldr.new_type_ufuncptr(fnpsig_i32voidpi64_i64, sig_i32voidpi64_i64)

        c_write = bldr.gen_sym("@c_write"); bldr.new_const_extern(c_write, fnpsig_i32voidpi64_i64, "write")

        test_write = bldr.gen_sym("@test_write"); bldr.new_func(test_write, sig_voidpi64_i64)

        # function body
        v1 = bldr.gen_sym("@test_write_v1")
        blk0 = bldr.gen_sym("@test_write_v1.blk0")

        # blk0
        buf = bldr.gen_sym("@test_write_v1.blk0.buf")
        sz = bldr.gen_sym("@test_write_v1.blk0.sz")
        res = bldr.gen_sym("@test_write_v1.blk0.res")
        op_ccall = bldr.gen_sym(); bldr.new_ccall(op_ccall, [res], rmu.MuCallConv.DEFAULT, fnpsig_i32voidpi64_i64, sig_i32voidpi64_i64, c_write,
                                                  [fd_stdout, buf, sz])
        op_ret = bldr.gen_sym(); bldr.new_ret(op_ret, [res])
        bldr.new_bb(blk0, [buf, sz], [voidp, i64], rmu.MU_NO_ID, [op_ccall, op_ret])
        bldr.new_func_ver(v1, test_write, [blk0])

        return {
            "@i32": i32,
            "@i64": i64,
            "test_fnc_sig": sig_voidpi64_i64,
            "test_fnc": test_write,
            "fncs": [test_write],
            "result_type": i64
        }
    impl_jit_test(cmdopt, build_test_bundle)


def test_throw(cmdopt):
    def build_test_bundle(bldr, rmu):
        """
        Builds the following test bundle.
            .typedef @i64 = int<64>
            .typedef @void = void
            .typedef @refi64 = ref<@i64>
            .typedef @refvoid = ref<@void>
            .const @c_10 <@i64> = 10
            .const @c_20 <@i64> = 20
            .const @c_42 <@i64> = 42
            .funcsig @sig_i64_i64 = (@i64) -> (@i64)
            .funcdef @throw_fnc VERSION @throw_fnc.v1 <@sig_i64_i64> {
                %blk0(<@i64> %num):
                    %cmpres = SLT <@i64> %num @c_42
                    BRANCH2 %cmpres %blk1() %blk2()
                %blk1():
                    %excobj = NEW <@i64>
                    %iref_obj = GETIREF <@i64> %excobj
                    STORE <@i64> %iref_obj @c_20
                    THROW %excobj
                %blk2():
                    RET (@c_10)
            }
            .funcdef @test_fnc VERSION @test_fnc.v1 <@sig_i64_i64> {
                %blk0(<@i64> %num):
                    %res = CALL <@sig_i64_i64> @throw_fnc (%num) EXC(%blk1(%res) %blk2())
                %blk1(<@i64> %rtn):
                    RET %rtn
                %blk2()[%excobj]:
                    %ri64 = REFCAST <@refvoid @refi64> %excobj
                    %iri64 = GETIREF <@i64> %excobj
                    %obj = LOAD <@i64> %iri64
                    BRANCH %blk1(%obj)
            }
        :type bldr: rpython.rlib.rmu.MuIRBuilder
        :type rmu: rpython.rlib.rmu
        :return: (rmu.MuVM(), rmu.MuCtx, rmu.MuIRBuilder, MuID, MuID)
        """
        void = bldr.gen_sym("@void"); bldr.new_type_void(void)
        i64 = bldr.gen_sym("@i64"); bldr.new_type_int(i64, 64)
        refi64 = bldr.gen_sym("@refi64"); bldr.new_type_ref(refi64, i64)
        refvoid = bldr.gen_sym("@refvoid"); bldr.new_type_ref(refvoid, void)

        c_10 = bldr.gen_sym("@c_10"); bldr.new_const_int(c_10, i64, 10)
        c_20 = bldr.gen_sym("@c_20"); bldr.new_const_int(c_20, i64, 20)
        c_42 = bldr.gen_sym("@c_42"); bldr.new_const_int(c_42, i64, 42)

        sig_i64_i64 = bldr.gen_sym("@sig_i64_i64"); bldr.new_funcsig(sig_i64_i64, [i64], [i64])

        test_fnc = bldr.gen_sym("@test_fnc"); bldr.new_func(test_fnc, sig_i64_i64)
        throw_fnc = bldr.gen_sym("@throw_fnc"); bldr.new_func(throw_fnc, sig_i64_i64)

        throw_fnc_v1 = bldr.gen_sym("@throw_fnc.v1")
        blk0 = bldr.gen_sym("@throw_fnc.v1.blk0")
        blk1 = bldr.gen_sym("@throw_fnc.v1.blk1")
        blk2 = bldr.gen_sym("@throw_fnc.v1.blk2")

        # blk0
        num = bldr.gen_sym("@throw_fnc.v1.blk0.num")
        cmpres = bldr.gen_sym("@throw_fnc.v1.blk0.cmpres")
        op_slt = bldr.gen_sym(); bldr.new_cmp(op_slt, cmpres, rmu.MuCmpOptr.SLT, i64, num, c_42)
        dst_t = bldr.gen_sym(); bldr.new_dest_clause(dst_t, blk1, [])
        dst_f = bldr.gen_sym(); bldr.new_dest_clause(dst_f, blk2, [])
        op_br2 = bldr.gen_sym(); bldr.new_branch2(op_br2, cmpres, dst_t, dst_f)
        bldr.new_bb(blk0, [num], [i64], rmu.MU_NO_ID, [op_slt, op_br2])

        # blk1
        excobj = bldr.gen_sym("@throw_fnc.v1.blk1.excobj")
        iref_obj = bldr.gen_sym("@throw_fnc.v1.blk1.iref_obj")
        op_new = bldr.gen_sym(); bldr.new_new(op_new, excobj, i64)
        op_getiref = bldr.gen_sym(); bldr.new_getiref(op_getiref, iref_obj, i64, excobj)
        op_store = bldr.gen_sym(); bldr.new_store(op_store, False, rmu.MuMemOrd.NOT_ATOMIC, i64, iref_obj, c_20)
        op_throw = bldr.gen_sym(); bldr.new_throw(op_throw, excobj)
        bldr.new_bb(blk1, [], [], rmu.MU_NO_ID, [op_new, op_getiref, op_store, op_throw])

        # blk2
        op_ret = bldr.gen_sym(); bldr.new_ret(op_ret, [c_10])
        bldr.new_bb(blk2, [], [], rmu.MU_NO_ID, [op_ret])

        bldr.new_func_ver(throw_fnc_v1, throw_fnc, [blk0, blk1, blk2])

        test_fnc_v1 = bldr.gen_sym("@test_fnc.v1")
        blk0 = bldr.gen_sym("@test_fnc.v1.blk0")
        blk1 = bldr.gen_sym("@test_fnc.v1.blk1")
        blk2 = bldr.gen_sym("@test_fnc.v1.blk2")

        # blk0
        num = bldr.gen_sym("@test_fnc.v1.blk0.num")
        res = bldr.gen_sym("@test_fnc.v1.blk0.res")
        dst_nor = bldr.gen_sym(); bldr.new_dest_clause(dst_nor, blk1, [res])
        dst_exc = bldr.gen_sym(); bldr.new_dest_clause(dst_exc, blk2, [])
        exc = bldr.gen_sym(); bldr.new_exc_clause(exc, dst_nor, dst_exc)
        op_call = bldr.gen_sym(); bldr.new_call(op_call, [res], sig_i64_i64, throw_fnc, [num], exc)
        bldr.new_bb(blk0, [num], [i64], rmu.MU_NO_ID, [op_call])

        # blk1
        rtn = bldr.gen_sym("@test_fnc.v1.blk1.rtn")
        op_ret = bldr.gen_sym(); bldr.new_ret(op_ret, [rtn])
        bldr.new_bb(blk1, [rtn], [i64], rmu.MU_NO_ID, [op_ret])

        # blk2
        excobj = bldr.gen_sym("@test_fnc.v1.blk2.excobj")
        ri64 = bldr.gen_sym("@test_fnc.v1.blk2.ri64")
        iri64 = bldr.gen_sym("@test_fnc.v1.blk2.iri64")
        obj = bldr.gen_sym("@test_fnc.v1.blk2.obj")
        op_refcast = bldr.gen_sym(); bldr.new_conv(op_refcast, ri64, rmu.MuConvOptr.REFCAST, refvoid, refi64, excobj)
        op_getiref = bldr.gen_sym(); bldr.new_getiref(op_getiref, iri64, i64, ri64)
        op_load = bldr.gen_sym(); bldr.new_load(op_load, obj, False, rmu.MuMemOrd.NOT_ATOMIC, i64, iri64)
        dst = bldr.gen_sym(); bldr.new_dest_clause(dst, blk1, [obj])
        op_br = bldr.gen_sym(); bldr.new_branch(op_br, dst)
        bldr.new_bb(blk2, [], [], excobj, [op_refcast, op_getiref, op_load, op_br])

        bldr.new_func_ver(test_fnc_v1, test_fnc, [blk0, blk1, blk2])

        return {
            "test_fnc": test_fnc,
            "test_fnc_sig": sig_i64_i64,
            "result_type": i64,
            "@i64": i64,
            "@refi64": refi64
        }

    def extend_with_entrypoint(bldr, id_dict, rmu):
        """
            Extend the bundle with:
                .typedef @i32 = int<32>
                .const @c_0 <@i64> = 0
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
        c_0 = bldr.gen_sym("@c_0")
        bldr.new_const_int(c_0, i64, 0)
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
        bldr.new_call(op_call, [res], test_fnc_sig, test_fnc, [c_0])
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
