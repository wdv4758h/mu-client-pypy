from __future__ import with_statement

from rpython.jit.backend.arm import conditions as c
from rpython.jit.backend.arm.arch import (JITFRAME_FIXED_SIZE)
from rpython.jit.backend.arm.regalloc import (Regalloc)
from rpython.jit.backend.llsupport import jitframe
from rpython.jit.backend.llsupport.assembler import BaseAssembler, GuardToken
from rpython.jit.backend.llsupport.gcmap import allocate_gcmap
from rpython.jit.backend.model import CompiledLoopToken
from rpython.jit.backend.muvm import conditions as c
from rpython.jit.backend.muvm.arch import JITFRAME_FIXED_SIZE
from rpython.jit.backend.muvm.regalloc import Regalloc
from rpython.jit.metainterp.resoperation import rop
from rpython.rlib.debug import debug_print, debug_start, debug_stop
from rpython.rlib.jit import AsmInfo
from rpython.rlib.objectmodel import we_are_translated
from rpython.rlib.rarithmetic import r_uint
from rpython.rlib.rmu import MuBinOptr, MuCmpOptr, MuConvOptr, MuVM, \
    MuBinOpStatus
from rpython.rtyper.lltypesystem import rffi


class MuGuardToken(GuardToken):
    def __init__(self, cpu, gcmap, descr, failargs, faillocs, guard_opnum,
                 frame_depth, faildescrindex, fcond=c.cond_none):
        GuardToken.__init__(self, cpu, gcmap, descr, failargs, faillocs,
                            guard_opnum, frame_depth, faildescrindex)
        self.fcond = fcond


def gen_emit_int_op(optr):
    def f(self, op, arglocs, regalloc):
        self.do_emit_int_op(arglocs, optr)
    return f


def gen_emit_int_op_with_flags(optr, flags):
    def f(self, op, arglocs, regalloc):
        self.do_emit_int_op_with_flags(arglocs, optr, flags)
    return f


def gen_emit_cmp_op(condition):
    def f(self, op, arglocs, regalloc):
        self.do_emit_cmp_op(arglocs, condition)
    return f


def gen_emit_float_op(optr):
    def f(self, op, arglocs, regalloc):
        self.do_emit_int_op(arglocs, optr)
    return f


def gen_emit_fp_cmp_op(condition):
    def f(self, op, arglocs, regalloc):
        self.do_emit_fp_cmp_op(arglocs, condition)
    return f


class AssemblerMu(BaseAssembler):
    def __init__(self, cpu, translate_support_code=False):
        BaseAssembler.__init__(self, cpu, translate_support_code)
        self.current_clt = None
        self.pending_guard_tokens = None
        self.pending_guard_tokens_recovered = 0
        self.target_tokens_currently_compiling = None
        self.frame_depth_to_patch = None
        self.pending_guards = None
        self.ctx = MuVM().new_context()
        self.mc = None
        self.bndl = None
        self.vars = None
        self.type_i32 = None
        self.type_i64 = None
        self.type_float = None
        self.type_double = None

        # temporary constant declarations
        self.const_i0 = None
        self.const_f0 = None
        self.const_ineg1 = None

        self.loop_run_counters = []

    def setup_once(self):
        BaseAssembler.setup_once(self)
        self.mc = self.ctx.new_ir_builder()
        self.type_i32 = self.mc.gen_sym('@i32')
        self.mc.new_type_int(self.type_i32, 32)
        self.type_i64 = self.mc.gen_sym('@i64')
        self.mc.new_type_int(self.type_i64, 64)
        self.type_float = self.mc.gen_sym('@float')
        self.mc.new_type_float(self.type_float)
        self.type_double = self.mc.gen_sym('@double')
        self.mc.new_type_double(self.type_double)
        self.const_i0 = self.mc.gen_sym('@i0')
        self.mc.new_const_int(self.const_i0, self.type_i32, 0)
        self.const_f0 = self.mc.gen_sym('@f0')
        self.mc.new_const_float(self.const_f0, self.type_float, 0.0)
        self.const_ineg1 = self.mc.gen_sym('@i_neg1')
        self.mc.new_const_int(self.const_ineg1, self.type_i32, -1)
        self.mc.load()

    def setup(self, looptoken):
        BaseAssembler.setup(self, looptoken)
        self.current_clt = looptoken.compiled_loop_token
        self.pending_guard_tokens = []
        self.pending_guard_tokens_recovered = 0
        self.target_tokens_currently_compiling = {}
        self.frame_depth_to_patch = []
        self.mc = self.ctx.new_ir_builder()

    def teardown(self):
        self.current_clt = None
        self.mc = None
        self.pending_guards = None

    # TODO: I think for each of these I need to create a basic block that
    # implements the functionality
    def _build_cond_call_slowpath(self, supports_floats, callee_only):
        print '_build_cond_call_slowpath called'
        pass

    def _build_failure_recovery(self, exc, withfloats=False):
        print '_build_failure_recovery called'
        pass

    def _build_malloc_slowpath(self, kind):
        print '_build_malloc_slowpath called'
        pass

    def _build_propagate_exception_path(self):
        print '_build_propagate_exception_path called'
        pass

    def _build_stack_check_slowpath(self):
        print '_build_stack_check_slowpath called'
        pass

    def _build_wb_slowpath(self, withcards, withfloats=False, for_frame=False):
        print '_build_wb_slowpath called'
        pass

    def build_frame_realloc_slowpath(self):
        print 'build_frame_realloc_slowpath called'
        pass

    def get_asmmemmgr_blocks(self, looptoken):
        clt = looptoken.compiled_loop_token
        if clt.asmmemmgr_blocks is None:
            clt.asmmemmgr_blocks = []
        return clt.asmmemmgr_blocks

    # at the end we need to store dirty vars to a frame (or something) in the
    # heap
    def assemble_loop(self, jd_id, unique_id, logger, loopname, inputargs,
                      operations, looptoken, log):
        # TODO: this is copied from arm
        clt = CompiledLoopToken(self.cpu, looptoken.number)
        looptoken.compiled_loop_token = clt
        clt._debug_nbargs = len(inputargs)

        if not we_are_translated():
            # Arguments should be unique
            assert len(set(inputargs)) == len(inputargs)

        self.setup(looptoken)

        clt.frame_info = jitframe.NULLFRAMEINFO
        # TODO: figure out how to directly create a jitframe.JITFRAMEINFO() or
        # an object that can cast to it
        # clt.frame_info = jitframe.JITFRAMEINFO()
        # set clt.frame_info to a newly allocated jitframe.JITFRAMEINFOPTR
        # frame_info = self.datablockwrapper.malloc_aligned(
        #         jitframe.JITFRAMEINFO_SIZE)
        # clt.frame_info = rffi.cast(jitframe.JITFRAMEINFOPTR, frame_info)
        # clt.frame_info.clear()  # for now

        if log:
            operations = self._inject_debugging_code(looptoken, operations,
                                                     'e', looptoken.number)

        regalloc = Regalloc(assembler=self)
        allgcrefs = []
        operations = regalloc.prepare_loop(inputargs, operations, looptoken,
                                           allgcrefs)
        # functionpos = self.mc.get_relative_pos()

        # self._call_header_with_stack_check()
        # self._check_frame_depth_debug(self.mc)

        # loop_head = self.mc.get_relative_pos()
        # looptoken._ll_loop_code = loop_head

        # frame_depth is probably frame size
        # frame_depth_no_fixed_size = self._assemble(regalloc, inputargs,
        #                                            operations)
        # self.update_frame_depth(frame_depth_no_fixed_size + JITFRAME_FIXED_SIZE)
        #
        # size_excluding_failure_stuff = self.mc.get_relative_pos()

        # self.write_pending_failure_recoveries()

        # full_size = self.mc.get_relative_pos()
        # TODO: this is where we actually toss the bundle into Mu
        # rawstart = self.materialize_loop(looptoken)
        self.mc.load()
        looptoken._ll_function_addr = 0
        # looptoken._ll_function_addr = rawstart + functionpos

        # TODO: Remove all of this. No Pypy GC + naming stuff
        # self.patch_gcref_table(looptoken, rawstart)
        # self.process_pending_guards(rawstart)
        # self.fixup_target_tokens(rawstart)

        # if log and not we_are_translated():
        #     self.mc._dump_trace(rawstart, 'loop.mu')

        # ops_offset = self.mc.ops_offset
        # if logger is not None:
        #     logger.log_loop(inputargs, operations, 0, "rewritten",
        #                     name=loopname, ops_offset=ops_offset)
        self.teardown()

        debug_start("jit-backend-addr")
        # debug_print("Loop %d (%s) has address 0x%x to 0x%x (bootstrap 0x%x)" % (
        #     looptoken.number, loopname,
        #     r_uint(rawstart + loop_head),
        #     r_uint(rawstart + size_excluding_failure_stuff),
        #     r_uint(rawstart + functionpos)))
        # debug_print("       gc table: 0x%x" % r_uint(rawstart))
        # debug_print("       function: 0x%x" % r_uint(rawstart + functionpos))
        # debug_print("         resops: 0x%x" % r_uint(rawstart + loop_head))
        # debug_print("       failures: 0x%x" % r_uint(rawstart +
        #                                              size_excluding_failure_stuff))
        # debug_print("            end: 0x%x" % r_uint(rawstart + full_size))
        debug_stop("jit-backend-addr")

        # return AsmInfo(ops_offset, rawstart + loop_head,
        #                size_excluding_failure_stuff - loop_head)

    def _assemble(self, regalloc, inputargs, operations):
        # TODO: copied from ARM
        self.guard_success_cc = c.cond_none
        regalloc.compute_hint_frame_locations(operations)
        # self._walk_operations(inputargs, operations, regalloc)
        assert self.guard_success_cc == c.cond_none
        frame_depth = regalloc.get_final_frame_depth()
        jump_target_descr = regalloc.jump_target_descr
        if jump_target_descr is not None:
            tgt_depth = jump_target_descr._arm_clt.frame_info.jfi_frame_depth
            target_frame_depth = tgt_depth - JITFRAME_FIXED_SIZE
            frame_depth = max(frame_depth, target_frame_depth)
        return frame_depth

    def assemble_bridge(self, faildescr, inputargs, operations,
                        original_loop_token, log, logger):
        # TODO
        pass

    # TODO: change new_binop -> new form (id, result_id, status_result_ids,
    # optr, status_flags, ty, opnd1, opnd2)
    def do_emit_int_op(self, arglocs, optr):
        l0, l1, res = arglocs
        v0 = self.get_int(l0)
        v1 = self.get_int(l1)
        inst = self.mc.new_binop(self.bb, optr, self.type_i32, v0, v1)
        inst_res = self.mc.get_inst_res(inst, 0)
        self.mc.set_name(self.bndl, inst_res, res.__repr__())
        self.vars[res] = inst_res

    def do_emit_int_op_with_flags(self, arglocs, optr, flags):
        l0, l1, res = arglocs
        v0 = self.get_int(l0)
        v1 = self.get_int(l1)
        inst = self.mc.new_binop_with_status(self.bb, optr, self.type_i32, v0,
                                             v1)
        inst_res = self.mc.get_inst_res(inst, 0)
        self.mc.set_name(self.bndl, inst_res, res.__repr__())
        self.vars[res] = inst_res

    emit_op_int_add = gen_emit_int_op(MuBinOptr.ADD)
    emit_op_int_sub = gen_emit_int_op(MuBinOptr.SUB)
    emit_op_int_mul = gen_emit_int_op(MuBinOptr.MUL)
    emit_op_int_add_ovf = gen_emit_int_op_with_flags(MuBinOptr.ADD,
                                                     [MuBinOpStatus.BOS_V])
    emit_op_int_sub_ovf = gen_emit_int_op_with_flags(MuBinOptr.SUB,
                                                     [MuBinOpStatus.BOS_V])
    emit_op_int_mul_ovf = gen_emit_int_op_with_flags(MuBinOptr.MUL,
                                                     [MuBinOpStatus.BOS_V])
    emit_op_int_floordiv = gen_emit_int_op(MuBinOptr.SDIV)
    emit_op_uint_floordiv = gen_emit_int_op(MuBinOptr.UDIV)
    emit_op_int_mod = gen_emit_int_op(MuBinOptr.SREM)

    emit_op_int_and = gen_emit_int_op(MuBinOptr.AND)
    emit_op_int_or = gen_emit_int_op(MuBinOptr.OR)
    emit_op_int_xor = gen_emit_int_op(MuBinOptr.XOR)
    emit_op_int_lshift = gen_emit_int_op(MuBinOptr.SHL)
    emit_op_int_rshift = gen_emit_int_op(MuBinOptr.ASHR)
    emit_op_uint_rshift = gen_emit_int_op(MuBinOptr.LSHR)

    emit_op_nursery_ptr_increment = emit_op_int_add  # unsure what this does

    def do_emit_cmp_op(self, arglocs, condition):
        l0, l1, res = arglocs
        v0 = self.get_int(l0)
        v1 = self.get_int(l1)
        inst = self.mc.new_cmp(self.bb, condition, self.type_i32, v0, v1)
        inst_res = self.mc.get_inst_res(inst, 0)
        self.mc.set_name(self.bndl, inst_res, res.__repr__())
        self.vars[res] = inst_res

    emit_op_int_le = gen_emit_cmp_op(MuCmpOptr.SLE)
    emit_op_int_lt = gen_emit_cmp_op(MuCmpOptr.SLT)
    emit_op_int_gt = gen_emit_cmp_op(MuCmpOptr.SGT)
    emit_op_int_ge = gen_emit_cmp_op(MuCmpOptr.SGE)
    emit_op_int_eq = gen_emit_cmp_op(MuCmpOptr.EQ)
    emit_op_int_ne = gen_emit_cmp_op(MuCmpOptr.NE)

    emit_op_uint_lt = gen_emit_cmp_op(MuCmpOptr.ULT)
    emit_op_uint_le = gen_emit_cmp_op(MuCmpOptr.ULE)
    emit_op_uint_gt = gen_emit_cmp_op(MuCmpOptr.UGT)
    emit_op_uint_ge = gen_emit_cmp_op(MuCmpOptr.UGE)

    emit_op_int_is_zero = emit_op_int_eq  # EQ to 0
    emit_op_int_is_true = emit_op_int_ne  # NE to 0

    emit_op_ptr_eq = emit_op_int_eq
    emit_op_ptr_ne = emit_op_int_ne

    emit_op_instance_ptr_eq = emit_op_ptr_eq
    emit_op_instance_ptr_ne = emit_op_ptr_ne

    def emit_op_int_neg(self, op, arglocs, regalloc):
        l0, res = arglocs
        i = self.get_int(l0)
        inst = self.mc.new_binop(self.bb, MuBinOptr.SUB, self.type_i32,
                                 self.const_i0, i)
        inst_res = self.mc.get_inst_res(inst, 0)
        self.mc.set_name(self.bndl, inst_res, res.__repr__())
        self.vars[res] = inst_res

    def emit_op_int_invert(self, op, arglocs, regalloc):
        pass
        l0, res = arglocs
        v0 = self.get_int(l0)
        inst = self.mc.new_binop(self.bb, MuBinOptr.SUB, self.type_i32,
                                 self.const_ineg1, v0)
        inst_res = self.mc.get_inst_res(inst, 0)
        self.mc.set_name(self.bndl, inst_res, res.__repr__())
        self.vars[res] = inst_res

    def emit_op_int_signext(self, op, arglocs, regalloc):
        pass
        l0, res = arglocs
        v0 = self.get_int(l0)
        inst = self.mc.new_conv(self.bb, MuConvOptr.SEXT, self.type_i32,
                                self.type_i64, v0)
        inst_res = self.mc.get_inst_res(inst, 0)
        self.mc.set_name(self.bndl, inst_res, res.__repr__())
        self.vars[res] = inst_res

    def emit_op_int_force_ge_zero(self, op, arglocs, regalloc):
        pass
        """
        arg, res = arglocs
        with scratch_reg(self.mc):
            self.mc.nor(r.SCRATCH.value, arg.value, arg.value)
            if IS_PPC_32:
                self.mc.srawi(r.SCRATCH.value, r.SCRATCH.value, 31)
            else:
                # sradi (scratch, scratch, 63)
                self.mc.sradi(r.SCRATCH.value, r.SCRATCH.value, 1, 31)
            self.mc.and_(res.value, arg.value, r.SCRATCH.value)
        """

    def do_emit_float_op(self, arglocs, optr):
        l0, l1, res = arglocs
        v0 = self.get_float(l0)
        v1 = self.get_float(l1)
        inst = self.mc.new_binop(self.bb, optr, self.type_float, v0, v1)
        inst_res = self.mc.get_inst_res(inst, 0)
        self.mc.set_name(self.bndl, inst_res, res.__repr__())
        self.vars[res] = inst_res

    emit_op_float_add = gen_emit_float_op(MuBinOptr.FADD)
    emit_op_float_sub = gen_emit_float_op(MuBinOptr.FSUB)
    emit_op_float_mul = gen_emit_float_op(MuBinOptr.FMUL)
    emit_op_float_truediv = gen_emit_float_op(MuBinOptr.FDIV)

    def emit_op_float_neg(self, op, arglocs, regalloc):
        pass
        l0, res = arglocs
        v0 = self.get_float(l0)
        inst = self.mc.new_binop(self.bb, MuBinOptr.SUB, self.type_float,
                                 self.const_f0, v0)
        inst_res = self.mc.get_inst_res(inst, 0)
        self.mc.set_name(self.bndl, inst_res, res.__repr__())
        self.vars[res] = inst_res

    def emit_op_float_abs(self, op, arglocs, regalloc):
        pass
        """
        l0, res = arglocs
        self.mc.fabs(res.value, l0.value)
        """

    def _emit_math_sqrt(self, op, arglocs, regalloc):
        pass
        """
        l0, res = arglocs
        self.mc.fsqrt(res.value, l0.value)
        """

    def _emit_threadlocalref_get(self, op, arglocs, regalloc):
        pass
        """
        [resloc] = arglocs
        offset = op.getarg(1).getint()   # getarg(0) == 'threadlocalref_get'
        calldescr = op.getdescr()
        size = calldescr.get_result_size()
        sign = calldescr.is_result_signed()
        #
        # This loads the stack location THREADLOCAL_OFS into a
        # register, and then read the word at the given offset.
        # It is only supported if 'translate_support_code' is
        # true; otherwise, the execute_token() was done with a
        # dummy value for the stack location THREADLOCAL_OFS
        #
        assert self.cpu.translate_support_code
        assert resloc.is_reg()
        assert _check_imm_arg(offset)
        self.mc.ld(resloc.value, r.SP.value, THREADLOCAL_ADDR_OFFSET)
        self._load_from_mem(resloc, resloc, imm(offset), imm(size), imm(sign))
        """

    def do_emit_fp_cmp_op(self, arglocs, condition):
        l0, l1, res = arglocs
        v0 = self.get_float(l0)
        v1 = self.get_float(l1)
        inst = self.mc.new_cmp(self.bb, condition, self.type_float, v0, v1)
        inst_res = self.mc.get_inst_res(inst, 0)
        self.mc.set_name(self.bndl, inst_res, res.__repr__())
        self.vars[res] = inst_res

    emit_op_float_le = gen_emit_fp_cmp_op(MuCmpOptr.FOLE)
    emit_op_float_lt = gen_emit_fp_cmp_op(MuCmpOptr.FOLT)
    emit_op_float_gt = gen_emit_fp_cmp_op(MuCmpOptr.FOGT)
    emit_op_float_ge = gen_emit_fp_cmp_op(MuCmpOptr.FOGE)
    emit_op_float_eq = gen_emit_fp_cmp_op(MuCmpOptr.FOEQ)
    emit_op_float_ne = gen_emit_fp_cmp_op(MuCmpOptr.FONE)

    def emit_op_cast_float_to_int(self, op, arglocs, regalloc):
        pass
        l0, res = arglocs
        v0 = self.get_float(l0)
        inst = self.mc.new_conv(self.bb, MuConvOptr.FPTOSI, self.type_float,
                                self.type_i32, v0)
        inst_res = self.mc.get_inst_res(inst, 0)
        self.mc.set_name(self.bndl, inst_res, res.__repr__())
        self.vars[res] = inst_res

    def emit_op_cast_int_to_float(self, op, arglocs, regalloc):
        pass
        l0, res = arglocs
        v0 = self.get_int(l0)
        inst = self.mc.new_conv(self.bb, MuConvOptr.SITOFP, self.type_i32,
                                self.type_float, v0)
        inst_res = self.mc.get_inst_res(inst, 0)
        self.mc.set_name(self.bndl, inst_res, res.__repr__())
        self.vars[res] = inst_res

    def emit_op_convert_float_bytes_to_longlong(self, op, arglocs, regalloc):
        pass
        l0, res = arglocs
        v0 = self.get_float(l0)
        inst = self.mc.new_conv(self.bb, MuConvOptr.FPTOSI, self.type_float,
                                self.type_i64, v0)
        inst_res = self.mc.get_inst_res(inst, 0)
        self.mc.set_name(self.bndl, inst_res, res.__repr__())
        self.vars[res] = inst_res

    def emit_op_convert_longlong_bytes_to_float(self, op, arglocs, regalloc):
        pass
        l0, res = arglocs
        v0 = self.get_int(l0)
        inst = self.mc.new_conv(self.bb, MuConvOptr.SITOFP, self.type_i64,
                                self.type_float, v0)
        inst_res = self.mc.get_inst_res(inst, 0)
        self.mc.set_name(self.bndl, inst_res, res.__repr__())
        self.vars[res] = inst_res

    def _emit_guard(self, op, arglocs, is_guard_not_invalidated=False):
        pass
        if is_guard_not_invalidated:
            fcond = c.cond_none
        else:
            fcond = self.guard_success_cc
            self.guard_success_cc = c.cond_none
            assert fcond != c.cond_none
        token = self.build_guard_token(op, arglocs[0].value, arglocs[1:], fcond)
        assert token.guard_not_invalidated() == is_guard_not_invalidated
        if not is_guard_not_invalidated:
            inst = self.mc.new_branch2(self.bb, fcond)
            branch2 = self.mc.get_inst_res(inst, 0)
            norm_path = self.mc.new_bb(self.fv)
            guard_block = self.mc.new_bb(
                    self.fv)  # TODO: Generate code for guard block, remove need
            # for guard tokens
            # TODO: this was outdated
            # self.mc.add_dest(branch2, MuDestKind.TRUE, norm_path,
            # regalloc.get_live_vars()).add_dest(branch2, MuDestKind.FALSE,
            # guard_block, guard_args)
            self.bb = norm_path
        else:
            pass
            # TODO: create a wpbranch
        self.pending_guard_tokens.append(token)

    def build_guard_token(self, op, frame_depth, arglocs, fcond):
        pass
        descr = op.getdescr()
        gcmap = allocate_gcmap(self, frame_depth, JITFRAME_FIXED_SIZE)
        faildescrindex = self.get_gcref_from_faildescr(descr)
        token = MuGuardToken(self.cpu, gcmap, descr, op.getfailargs(),
                             arglocs, op.getopnum(), frame_depth,
                             faildescrindex,
                             fcond)
        return token

    def emit_op_guard_true(self, op, arglocs, regalloc):
        pass
        """
        self._emit_guard(op, arglocs)
        """

    def emit_op_guard_false(self, op, arglocs, regalloc):
        pass
        """
        self.guard_success_cc = c.invert(self.guard_success_cc)
        self._emit_guard(op, arglocs)
        """

    def emit_op_guard_overflow(self, op, arglocs, regalloc):
        pass
        """
        self.guard_success_cc = c.SO
        self._emit_guard(op, arglocs)
        """

    def emit_op_guard_no_overflow(self, op, arglocs, regalloc):
        pass
        """
        self.guard_success_cc = c.NS
        self._emit_guard(op, arglocs)
        """

    def emit_op_guard_value(self, op, arglocs, regalloc):
        pass
        l0 = arglocs[0]
        l1 = arglocs[1]
        failargs = arglocs[2:]
        if l0.is_int():
            v0 = self.get_int(l0)
            v1 = self.get_int(l1)
            inst = self.mc.new_cmp(self.bb, MuCmpOptr.EQ, self.type_i32, v0, v1)
        else:
            v0 = self.get_float(l0)
            v1 = self.get_float(l1)
            inst = self.mc.new_cmp(self.bb, MuCmpOptr.FOEQ, self.type_float, v0,
                                   v1)
        inst_res = self.mc.get_inst_res(inst, 0)
        self.guard_success_cc = c.MuCondition(inst_res)
        self._emit_guard(op, failargs)
        """
        l0 = arglocs[0]
        l1 = arglocs[1]
        failargs = arglocs[2:]

        if l0.is_reg():
            if l1.is_imm():
                self.mc.cmp_op(0, l0.value, l1.getint(), imm=True)
            else:
                self.mc.cmp_op(0, l0.value, l1.value)
        elif l0.is_fp_reg():
            assert l1.is_fp_reg()
            self.mc.cmp_op(0, l0.value, l1.value, fp=True)
        self.guard_success_cc = c.EQ
        self._emit_guard(op, failargs)
        """

    emit_op_guard_nonnull = emit_op_guard_true
    emit_op_guard_isnull = emit_op_guard_false

    def emit_op_guard_class(self, op, arglocs, regalloc):
        pass
        """
        self._cmp_guard_class(op, arglocs, regalloc)
        self.guard_success_cc = c.EQ
        self._emit_guard(op, arglocs[2:])
        """

    def emit_op_guard_nonnull_class(self, op, arglocs, regalloc):
        pass
        """
        self.mc.cmp_op(0, arglocs[0].value, 1, imm=True, signed=False)
        patch_pos = self.mc.currpos()
        self.mc.trap()
        self._cmp_guard_class(op, arglocs, regalloc)
        pmc = OverwritingBuilder(self.mc, patch_pos, 1)
        pmc.blt(self.mc.currpos() - patch_pos)
        pmc.overwrite()
        self.guard_success_cc = c.EQ
        self._emit_guard(op, arglocs[2:])
        """

    def _cmp_guard_class(self, op, locs, regalloc):
        pass
        """
        offset = self.cpu.vtable_offset
        if offset is not None:
            # could be one instruction shorter, but don't care because
            # it's not this case that is commonly translated
            self.mc.load(r.SCRATCH.value, locs[0].value, offset)
            self.mc.load_imm(r.SCRATCH2, locs[1].value)
            self.mc.cmp_op(0, r.SCRATCH.value, r.SCRATCH2.value)
        else:
            expected_typeid = (self.cpu.gc_ll_descr
                    .get_typeid_from_classptr_if_gcremovetypeptr(locs[1].value))
            self._cmp_guard_gc_type(locs[0], expected_typeid)
        """

    def _read_typeid(self, targetreg, loc_ptr):
        pass
        """
        # Note that the typeid half-word is at offset 0 on a little-endian
        # machine; it is at offset 2 or 4 on a big-endian machine.
        assert self.cpu.supports_guard_gc_type
        if IS_PPC_32:
            self.mc.lhz(targetreg.value, loc_ptr.value, 2 * IS_BIG_ENDIAN)
        else:
            self.mc.lwz(targetreg.value, loc_ptr.value, 4 * IS_BIG_ENDIAN)
        """

    def _cmp_guard_gc_type(self, loc_ptr, expected_typeid):
        pass
        """
        self._read_typeid(r.SCRATCH2, loc_ptr)
        assert 0 <= expected_typeid <= 0x7fffffff   # 4 bytes are always enough
        if expected_typeid > 0xffff:     # if 2 bytes are not enough
            self.mc.subis(r.SCRATCH2.value, r.SCRATCH2.value,
                          expected_typeid >> 16)
            expected_typeid = expected_typeid & 0xffff
        self.mc.cmp_op(0, r.SCRATCH2.value, expected_typeid,
                       imm=True, signed=False)
        """

    def emit_op_guard_gc_type(self, op, arglocs, regalloc):
        pass
        """
        self._cmp_guard_gc_type(arglocs[0], arglocs[1].value)
        self.guard_success_cc = c.EQ
        self._emit_guard(op, arglocs[2:])
        """

    def emit_op_guard_is_object(self, op, arglocs, regalloc):
        pass
        """
        assert self.cpu.supports_guard_gc_type
        loc_object = arglocs[0]
        # idea: read the typeid, fetch one byte of the field 'infobits' from
        # the big typeinfo table, and check the flag 'T_IS_RPYTHON_INSTANCE'.
        base_type_info, shift_by, sizeof_ti = (
            self.cpu.gc_ll_descr.get_translated_info_for_typeinfo())
        infobits_offset, IS_OBJECT_FLAG = (
            self.cpu.gc_ll_descr.get_translated_info_for_guard_is_object())

        self._read_typeid(r.SCRATCH2, loc_object)
        self.mc.load_imm(r.SCRATCH, base_type_info + infobits_offset)
        assert shift_by == 0     # on PPC64; fixme for PPC32
        self.mc.lbzx(r.SCRATCH2.value, r.SCRATCH2.value, r.SCRATCH.value)
        self.mc.andix(r.SCRATCH2.value, r.SCRATCH2.value, IS_OBJECT_FLAG & 0xff)
        self.guard_success_cc = c.NE
        self._emit_guard(op, arglocs[1:])
        """

    def emit_op_guard_subclass(self, op, arglocs, regalloc):
        pass
        """
        assert self.cpu.supports_guard_gc_type
        loc_object = arglocs[0]
        loc_check_against_class = arglocs[1]
        offset = self.cpu.vtable_offset
        offset2 = self.cpu.subclassrange_min_offset
        if offset is not None:
            # read this field to get the vtable pointer
            self.mc.load(r.SCRATCH2.value, loc_object.value, offset)
            # read the vtable's subclassrange_min field
            assert _check_imm_arg(offset2)
            self.mc.ld(r.SCRATCH2.value, r.SCRATCH2.value, offset2)
        else:
            # read the typeid
            self._read_typeid(r.SCRATCH, loc_object)
            # read the vtable's subclassrange_min field, as a single
            # step with the correct offset
            base_type_info, shift_by, sizeof_ti = (
                self.cpu.gc_ll_descr.get_translated_info_for_typeinfo())
            self.mc.load_imm(r.SCRATCH2, base_type_info + sizeof_ti + offset2)
            assert shift_by == 0     # on PPC64; fixme for PPC32
            self.mc.ldx(r.SCRATCH2.value, r.SCRATCH2.value, r.SCRATCH.value)
        # get the two bounds to check against
        vtable_ptr = loc_check_against_class.getint()
        vtable_ptr = rffi.cast(rclass.CLASSTYPE, vtable_ptr)
        check_min = vtable_ptr.subclassrange_min
        check_max = vtable_ptr.subclassrange_max
        assert check_max > check_min
        check_diff = check_max - check_min - 1
        # right now, a full PyPy uses less than 6000 numbers,
        # so we'll assert here that it always fit inside 15 bits
        assert 0 <= check_min <= 0x7fff
        assert 0 <= check_diff <= 0xffff
        # check by doing the unsigned comparison (tmp - min) < (max - min)
        self.mc.subi(r.SCRATCH2.value, r.SCRATCH2.value, check_min)
        self.mc.cmp_op(0, r.SCRATCH2.value, check_diff, imm=True, signed=False)
        # the guard passes if we get a result of "below or equal"
        self.guard_success_cc = c.LE
        self._emit_guard(op, arglocs[2:])
        """

    def emit_op_guard_not_invalidated(self, op, arglocs, regalloc):
        pass
        """
        self._emit_guard(op, arglocs, is_guard_not_invalidated=True)
        """

    def emit_op_guard_not_forced(self, op, arglocs, regalloc):
        pass
        """
        ofs = self.cpu.get_ofs_of_frame_field('jf_descr')
        self.mc.ld(r.SCRATCH.value, r.SPP.value, ofs)
        self.mc.cmp_op(0, r.SCRATCH.value, 0, imm=True)
        self.guard_success_cc = c.EQ
        self._emit_guard(op, arglocs)
        """

    def emit_op_guard_not_forced_2(self, op, arglocs, regalloc):
        pass
        """
        guard_token = self.build_guard_token(op, arglocs[0].value, arglocs[1:],
                                             c.cond_none)
        self._finish_gcmap = guard_token.gcmap
        self._store_force_index(op)
        self.store_info_on_descr(0, guard_token)
        """

    def emit_op_label(self, op, arglocs, regalloc):
        pass

    def emit_op_increment_debug_counter(self, op, arglocs, regalloc):
        pass
        """
        [addr_loc, value_loc] = arglocs
        self.mc.load(value_loc.value, addr_loc.value, 0)
        self.mc.addi(value_loc.value, value_loc.value, 1)   # can't use r0!
        self.mc.store(value_loc.value, addr_loc.value, 0)
        """

    def emit_op_finish(self, op, arglocs, regalloc):
        pass
        """
        base_ofs = self.cpu.get_baseofs_of_frame_field()
        if len(arglocs) > 0:
            [return_val] = arglocs
            if op.getarg(0).type == FLOAT:
                self.mc.stfd(return_val.value, r.SPP.value, base_ofs)
            else:
                self.mc.std(return_val.value, r.SPP.value, base_ofs)

        ofs = self.cpu.get_ofs_of_frame_field('jf_descr')
        ofs2 = self.cpu.get_ofs_of_frame_field('jf_gcmap')

        descr = op.getdescr()
        faildescrindex = self.get_gcref_from_faildescr(descr)
        self._load_from_gc_table(r.r5, r.r5, faildescrindex)

        # gcmap logic here:
        arglist = op.getarglist()
        if arglist and arglist[0].type == REF:
            if self._finish_gcmap:
                # we're returning with a guard_not_forced_2, and
                # additionally we need to say that the result contains
                # a reference too:
                self._finish_gcmap[0] |= r_uint(1)
                gcmap = self._finish_gcmap
            else:
                gcmap = self.gcmap_for_finish
        elif self._finish_gcmap:
            # we're returning with a guard_not_forced_2
            gcmap = self._finish_gcmap
        else:
            gcmap = lltype.nullptr(jitframe.GCMAP)
        self.load_gcmap(self.mc, r.r2, gcmap)

        self.mc.std(r.r5.value, r.SPP.value, ofs)
        self.mc.store(r.r2.value, r.SPP.value, ofs2)

        # exit function
        self._call_footer()
        """

    def emit_op_jump(self, op, arglocs, regalloc):
        pass
        """
        # The backend's logic assumes that the target code is in a piece of
        # assembler that was also called with the same number of arguments,
        # so that the locations [ebp+8..] of the input arguments are valid
        # stack locations both before and after the jump.
        #
        descr = op.getdescr()
        assert isinstance(descr, TargetToken)
        my_nbargs = self.current_clt._debug_nbargs
        target_nbargs = descr._ppc_clt._debug_nbargs
        assert my_nbargs == target_nbargs

        if descr in self.target_tokens_currently_compiling:
            self.mc.b_offset(descr._ll_loop_code)
        else:
            self.mc.b_abs(descr._ll_loop_code)
        """

    def _genop_same_as(self, op, arglocs, regalloc):
        pass
        """
        argloc, resloc = arglocs
        if argloc is not resloc:
            self.regalloc_mov(argloc, resloc)
        """

    emit_op_same_as_i = _genop_same_as
    emit_op_same_as_r = _genop_same_as
    emit_op_same_as_f = _genop_same_as
    emit_op_cast_ptr_to_int = _genop_same_as
    emit_op_cast_int_to_ptr = _genop_same_as

    def emit_op_guard_no_exception(self, op, arglocs, regalloc):
        pass
        """
        self.mc.load_from_addr(r.SCRATCH2, r.SCRATCH2, self.cpu.pos_exception())
        self.mc.cmp_op(0, r.SCRATCH2.value, 0, imm=True)
        self.guard_success_cc = c.EQ
        self._emit_guard(op, arglocs)
        # If the previous operation was a COND_CALL, overwrite its conditional
        # jump to jump over this GUARD_NO_EXCEPTION as well, if we can
        if self._find_nearby_operation(regalloc,-1).getopnum() == rop.COND_CALL:
            jmp_adr, BI, BO = self.previous_cond_call_jcond
            relative_target = self.mc.currpos() - jmp_adr
            pmc = OverwritingBuilder(self.mc, jmp_adr, 1)
            pmc.bc(BO, BI, relative_target)
            pmc.overwrite()
        """

    def emit_op_save_exc_class(self, op, arglocs, regalloc):
        pass
        """
        [resloc] = arglocs
        diff = self.mc.load_imm_plus(r.r2, self.cpu.pos_exception())
        self.mc.load(resloc.value, r.r2.value, diff)
        """

    def emit_op_save_exception(self, op, arglocs, regalloc):
        pass
        """
        [resloc] = arglocs
        self._store_and_reset_exception(self.mc, resloc)
        """

    def emit_op_restore_exception(self, op, arglocs, regalloc):
        pass
        """
        self._restore_exception(self.mc, arglocs[1], arglocs[0])
        """

    def emit_op_guard_exception(self, op, arglocs, regalloc):
        pass
        """
        loc, resloc = arglocs[:2]
        failargs = arglocs[2:]

        mc = self.mc
        mc.load_imm(r.SCRATCH2, self.cpu.pos_exc_value())
        diff = self.cpu.pos_exception() - self.cpu.pos_exc_value()
        assert _check_imm_arg(diff)

        mc.load(r.SCRATCH.value, r.SCRATCH2.value, diff)
        mc.cmp_op(0, r.SCRATCH.value, loc.value)
        self.guard_success_cc = c.EQ
        self._emit_guard(op, failargs)

        if resloc:
            mc.load(resloc.value, r.SCRATCH2.value, 0)
        mc.load_imm(r.SCRATCH, 0)
        mc.store(r.SCRATCH.value, r.SCRATCH2.value, 0)
        mc.store(r.SCRATCH.value, r.SCRATCH2.value, diff)
        """

    def _load_from_gc_table(self, rD, rT, index):
        pass
        """
        # rT is a temporary, may be equal to rD, must be != r0
        addr = self.gc_table_addr + index * WORD
        self.mc.load_from_addr(rD, rT, addr)
        """

    def emit_op_load_from_gc_table(self, op, arglocs, regalloc):
        pass
        """
        index = op.getarg(0).getint()
        [resloc] = arglocs
        assert resloc.is_reg()
        self._load_from_gc_table(resloc, resloc, index)
        """

    def _emit_call(self, op, arglocs, is_call_release_gil=False):
        pass
        """
        resloc = arglocs[0]
        func_index = 1 + is_call_release_gil
        adr = arglocs[func_index]
        arglist = arglocs[func_index+1:]

        cb = callbuilder.CallBuilder(self, adr, arglist, resloc)

        descr = op.getdescr()
        assert isinstance(descr, CallDescr)
        cb.argtypes = descr.get_arg_types()
        cb.restype  = descr.get_result_type()

        if is_call_release_gil:
            saveerrloc = arglocs[1]
            assert saveerrloc.is_imm()
            cb.emit_call_release_gil(saveerrloc.value)
        else:
            cb.emit()
        """

    def _genop_call(self, op, arglocs, regalloc):
        pass
        """
        oopspecindex = regalloc.get_oopspecindex(op)
        if oopspecindex == EffectInfo.OS_MATH_SQRT:
            return self._emit_math_sqrt(op, arglocs, regalloc)
        if oopspecindex == EffectInfo.OS_THREADLOCALREF_GET:
            return self._emit_threadlocalref_get(op, arglocs, regalloc)
        self._emit_call(op, arglocs)
        """

    emit_op_call_i = _genop_call
    emit_op_call_r = _genop_call
    emit_op_call_f = _genop_call
    emit_op_call_n = _genop_call

    def _genop_call_may_force(self, op, arglocs, regalloc):
        pass
        """
        self._store_force_index(self._find_nearby_operation(regalloc, +1))
        self._emit_call(op, arglocs)
        """

    emit_op_call_may_force_i = _genop_call_may_force
    emit_op_call_may_force_r = _genop_call_may_force
    emit_op_call_may_force_f = _genop_call_may_force
    emit_op_call_may_force_n = _genop_call_may_force

    def _genop_call_release_gil(self, op, arglocs, regalloc):
        pass
        """
        self._store_force_index(self._find_nearby_operation(regalloc, +1))
        self._emit_call(op, arglocs, is_call_release_gil=True)
        """

    emit_op_call_release_gil_i = _genop_call_release_gil
    emit_op_call_release_gil_f = _genop_call_release_gil
    emit_op_call_release_gil_n = _genop_call_release_gil

    def _store_force_index(self, guard_op):
        pass
        """
        assert (guard_op.getopnum() == rop.GUARD_NOT_FORCED or
                guard_op.getopnum() == rop.GUARD_NOT_FORCED_2)
        faildescr = guard_op.getdescr()
        ofs = self.cpu.get_ofs_of_frame_field('jf_force_descr')
        faildescrindex = self.get_gcref_from_faildescr(faildescr)
        self._load_from_gc_table(r.r2, r.r2, faildescrindex)
        self.mc.store(r.r2.value, r.SPP.value, ofs)
        """

    def _find_nearby_operation(self, regalloc, delta):
        pass
        """
        return regalloc.operations[regalloc.rm.position + delta]
        """

    def emit_op_cond_call(self, op, arglocs, regalloc):
        pass
        """
        fcond = self.guard_success_cc
        self.guard_success_cc = c.cond_none
        assert fcond != c.cond_none
        fcond = c.negate(fcond)

        jmp_adr = self.mc.get_relative_pos()
        self.mc.trap()        # patched later to a 'bc'

        self.load_gcmap(self.mc, r.r2, regalloc.get_gcmap())

        # save away r3, r4, r5, r6, r12 into the jitframe
        should_be_saved = [
            reg for reg in self._regalloc.rm.reg_bindings.itervalues()
                if reg in self._COND_CALL_SAVE_REGS]
        self._push_core_regs_to_jitframe(self.mc, should_be_saved)
        #
        # load the 0-to-4 arguments into these registers, with the address of
        # the function to call into r12
        remap_frame_layout(self, arglocs,
                           [r.r12, r.r3, r.r4, r.r5, r.r6][:len(arglocs)],
                           r.SCRATCH)
        #
        # figure out which variant of cond_call_slowpath to call, and call it
        callee_only = False
        floats = False
        for reg in regalloc.rm.reg_bindings.values():
            if reg not in regalloc.rm.save_around_call_regs:
                break
        else:
            callee_only = True
        if regalloc.fprm.reg_bindings:
            floats = True
        cond_call_adr = self.cond_call_slowpath[floats * 2 + callee_only]
        self.mc.bl_abs(cond_call_adr)
        # restoring the registers saved above, and doing pop_gcmap(), is left
        # to the cond_call_slowpath helper.  We never have any result value.
        relative_target = self.mc.currpos() - jmp_adr
        pmc = OverwritingBuilder(self.mc, jmp_adr, 1)
        BI, BO = c.encoding[fcond]
        pmc.bc(BO, BI, relative_target)
        pmc.overwrite()
        # might be overridden again to skip over the following
        # guard_no_exception too
        self.previous_cond_call_jcond = jmp_adr, BI, BO
        """

    def _write_to_mem(self, value_loc, base_loc, ofs, size_loc):
        pass
        """
        assert size_loc.is_imm()
        size = size_loc.value
        if size == 8:
            if value_loc.is_fp_reg():
                if ofs.is_imm():
                    self.mc.stfd(value_loc.value, base_loc.value, ofs.value)
                else:
                    self.mc.stfdx(value_loc.value, base_loc.value, ofs.value)
            else:
                if ofs.is_imm():
                    self.mc.std(value_loc.value, base_loc.value, ofs.value)
                else:
                    self.mc.stdx(value_loc.value, base_loc.value, ofs.value)
        elif size == 4:
            if ofs.is_imm():
                self.mc.stw(value_loc.value, base_loc.value, ofs.value)
            else:
                self.mc.stwx(value_loc.value, base_loc.value, ofs.value)
        elif size == 2:
            if ofs.is_imm():
                self.mc.sth(value_loc.value, base_loc.value, ofs.value)
            else:
                self.mc.sthx(value_loc.value, base_loc.value, ofs.value)
        elif size == 1:
            if ofs.is_imm():
                self.mc.stb(value_loc.value, base_loc.value, ofs.value)
            else:
                self.mc.stbx(value_loc.value, base_loc.value, ofs.value)
        else:
            assert 0, "size not supported"
        """

    def emit_op_gc_store(self, op, arglocs, regalloc):
        pass
        """
        value_loc, base_loc, ofs_loc, size_loc = arglocs
        self._write_to_mem(value_loc, base_loc, ofs_loc, size_loc)
        """

    def _apply_offset(self, index_loc, ofs_loc):
        pass
        """
        # If offset != 0 then we have to add it here.  Note that
        # mc.addi() would not be valid with operand r0.
        assert ofs_loc.is_imm()                # must be an immediate...
        assert _check_imm_arg(ofs_loc.getint())   # ...that fits 16 bits
        assert index_loc is not r.SCRATCH2
        # (simplified version of _apply_scale())
        if ofs_loc.value > 0:
            self.mc.addi(r.SCRATCH2.value, index_loc.value, ofs_loc.value)
            index_loc = r.SCRATCH2
        return index_loc
        """

    def emit_op_gc_store_indexed(self, op, arglocs, regalloc):
        pass
        """
        base_loc, index_loc, value_loc, ofs_loc, size_loc = arglocs
        index_loc = self._apply_offset(index_loc, ofs_loc)
        self._write_to_mem(value_loc, base_loc, index_loc, size_loc)
        """

    def _load_from_mem(self, res, base_loc, ofs, size_loc, sign_loc):
        pass
        """
        # res, base_loc, ofs, size and signed are all locations
        assert base_loc is not r.SCRATCH
        assert size_loc.is_imm()
        size = size_loc.value
        assert sign_loc.is_imm()
        sign = sign_loc.value
        if size == 8:
            if res.is_fp_reg():
                if ofs.is_imm():
                    self.mc.lfd(res.value, base_loc.value, ofs.value)
                else:
                    self.mc.lfdx(res.value, base_loc.value, ofs.value)
            else:
                if ofs.is_imm():
                    self.mc.ld(res.value, base_loc.value, ofs.value)
                else:
                    self.mc.ldx(res.value, base_loc.value, ofs.value)
        elif size == 4:
            if IS_PPC_64 and sign:
                if ofs.is_imm():
                    self.mc.lwa(res.value, base_loc.value, ofs.value)
                else:
                    self.mc.lwax(res.value, base_loc.value, ofs.value)
            else:
                if ofs.is_imm():
                    self.mc.lwz(res.value, base_loc.value, ofs.value)
                else:
                    self.mc.lwzx(res.value, base_loc.value, ofs.value)
        elif size == 2:
            if sign:
                if ofs.is_imm():
                    self.mc.lha(res.value, base_loc.value, ofs.value)
                else:
                    self.mc.lhax(res.value, base_loc.value, ofs.value)
            else:
                if ofs.is_imm():
                    self.mc.lhz(res.value, base_loc.value, ofs.value)
                else:
                    self.mc.lhzx(res.value, base_loc.value, ofs.value)
        elif size == 1:
            if ofs.is_imm():
                self.mc.lbz(res.value, base_loc.value, ofs.value)
            else:
                self.mc.lbzx(res.value, base_loc.value, ofs.value)
            if sign:
                self.mc.extsb(res.value, res.value)
        else:
            assert 0, "size not supported"
        """

    def _genop_gc_load(self, op, arglocs, regalloc):
        pass
        """
        base_loc, ofs_loc, res_loc, size_loc, sign_loc = arglocs
        self._load_from_mem(res_loc, base_loc, ofs_loc, size_loc, sign_loc)
        """

    emit_op_gc_load_i = _genop_gc_load
    emit_op_gc_load_r = _genop_gc_load
    emit_op_gc_load_f = _genop_gc_load

    def _genop_gc_load_indexed(self, op, arglocs, regalloc):
        pass
        """
        base_loc, index_loc, res_loc, ofs_loc, size_loc, sign_loc = arglocs
        index_loc = self._apply_offset(index_loc, ofs_loc)
        self._load_from_mem(res_loc, base_loc, index_loc, size_loc, sign_loc)
        """

    emit_op_gc_load_indexed_i = _genop_gc_load_indexed
    emit_op_gc_load_indexed_r = _genop_gc_load_indexed
    emit_op_gc_load_indexed_f = _genop_gc_load_indexed

    SIZE2SCALE = dict([(1 << _i, _i) for _i in range(32)])

    def _multiply_by_constant(self, loc, multiply_by, scratch_loc):
        pass
        """
        # XXX should die together with _apply_scale() but can't because
        # of emit_op_zero_array() and malloc_cond_varsize() at the moment
        assert loc.is_reg()
        if multiply_by == 1:
            return loc
        try:
            scale = self.SIZE2SCALE[multiply_by]
        except KeyError:
            if _check_imm_arg(multiply_by):
                self.mc.mulli(scratch_loc.value, loc.value, multiply_by)
            else:
                self.mc.load_imm(scratch_loc, multiply_by)
                if IS_PPC_32:
                    self.mc.mullw(scratch_loc.value, loc.value,
                                  scratch_loc.value)
                else:
                    self.mc.mulld(scratch_loc.value, loc.value,
                                  scratch_loc.value)
        else:
            self.mc.sldi(scratch_loc.value, loc.value, scale)
        return scratch_loc
        """

    def _copy_in_scratch2(self, loc):
        pass
        """
        if loc.is_imm():
            self.mc.li(r.SCRATCH2.value, loc.value)
        elif loc is not r.SCRATCH2:
            self.mc.mr(r.SCRATCH2.value, loc.value)
        return r.SCRATCH2
        """

    # RPythonic workaround for emit_op_zero_array()
    def eza_stXux(self, a, b, c, itemsize):
        pass
        """
        if itemsize & 1:                  self.mc.stbux(a, b, c)
        elif itemsize & 2:                self.mc.sthux(a, b, c)
        elif (itemsize & 4) or IS_PPC_32: self.mc.stwux(a, b, c)
        else:                             self.mc.stdux(a, b, c)
        """

    def eza_stXu(self, a, b, c, itemsize):
        pass
        """
        if itemsize & 1:                  self.mc.stbu(a, b, c)
        elif itemsize & 2:                self.mc.sthu(a, b, c)
        elif (itemsize & 4) or IS_PPC_32: self.mc.stwu(a, b, c)
        else:                             self.mc.stdu(a, b, c)
        """

    def emit_op_zero_array(self, op, arglocs, regalloc):
        pass
        """
        base_loc, startindex_loc, length_loc, ofs_loc = arglocs

        stepsize = 8
        shift_by = 3
        if IS_PPC_32:
            stepsize = 4
            shift_by = 2

        if length_loc.is_imm():
            if length_loc.value <= 0:
                return     # nothing to do

        if startindex_loc.is_imm():
            self.mc.load_imm(r.SCRATCH2, startindex_loc.value)
            startindex_loc = r.SCRATCH2
        if ofs_loc.is_imm():
            self.mc.addi(r.SCRATCH2.value, startindex_loc.value, ofs_loc.value)
        else:
            self.mc.add(r.SCRATCH2.value, startindex_loc.value, ofs_loc.value)
        ofs_loc = r.SCRATCH2
        assert base_loc.is_core_reg()
        self.mc.add(ofs_loc.value, ofs_loc.value, base_loc.value)
        # ofs_loc is now the real address pointing to the first
        # byte to be zeroed

        prev_length_loc = length_loc
        if length_loc.is_imm():
            self.mc.load_imm(r.SCRATCH, length_loc.value)
            length_loc = r.SCRATCH

        self.mc.cmp_op(0, length_loc.value, stepsize, imm=True)
        jlt_location = self.mc.currpos()
        self.mc.trap()

        self.mc.sradi(r.SCRATCH.value, length_loc.value, 0, shift_by)
        self.mc.mtctr(r.SCRATCH.value) # store the length in count register

        self.mc.li(r.SCRATCH.value, 0)

        # NOTE the following assumes that bytes have been passed to both
        startindex
        # and length. Thus we zero 4/8 bytes in a loop in 1) and every remaining
        # byte is zeroed in another loop in 2)

        self.mc.subi(ofs_loc.value, ofs_loc.value, stepsize)

        # first store of case 1)
        # 1) The next loop copies WORDS into the memory chunk starting at
        startindex
        # ending at startindex + length. These are bytes
        loop_location = self.mc.currpos()
        self.eza_stXu(r.SCRATCH.value, ofs_loc.value, stepsize, stepsize)
        self.mc.bdnz(loop_location - self.mc.currpos())

        self.mc.addi(ofs_loc.value, ofs_loc.value, stepsize)

        pmc = OverwritingBuilder(self.mc, jlt_location, 1)
        pmc.blt(self.mc.currpos() - jlt_location)    # jump if length < WORD
        pmc.overwrite()

        # 2) There might be some bytes left to be written.
        # following scenario: length_loc == 3 bytes, stepsize == 4!
        # need to write the last bytes.

        # move the last bytes to the count register
        length_loc = prev_length_loc
        if length_loc.is_imm():
            self.mc.load_imm(r.SCRATCH, length_loc.value & (stepsize-1))
        else:
            self.mc.andix(r.SCRATCH.value, length_loc.value, (stepsize-1) &
            0xff)

        self.mc.cmp_op(0, r.SCRATCH.value, 0, imm=True)
        jle_location = self.mc.currpos()
        self.mc.trap()

        self.mc.mtctr(r.SCRATCH.value)
        self.mc.li(r.SCRATCH.value, 0)

        self.mc.subi(ofs_loc.value, ofs_loc.value, 1)

        loop_location = self.mc.currpos()
        self.eza_stXu(r.SCRATCH.value, ofs_loc.value, 1, 1)
        self.mc.bdnz(loop_location - self.mc.currpos())

        pmc = OverwritingBuilder(self.mc, jle_location, 1)
        pmc.ble(self.mc.currpos() - jle_location)    # !GT
        pmc.overwrite()
        """

    def emit_op_copystrcontent(self, op, arglocs, regalloc):
        pass
        """
        self._emit_copycontent(arglocs, is_unicode=False)
        """

    def emit_op_copyunicodecontent(self, op, arglocs, regalloc):
        pass
        """
        self._emit_copycontent(arglocs, is_unicode=True)
        """

    def _emit_load_for_copycontent(self, dst, src_ptr, src_ofs, scale):
        pass
        """
        if src_ofs.is_imm():
            value = src_ofs.value << scale
            if value < 32768:
                self.mc.addi(dst.value, src_ptr.value, value)
            else:
                self.mc.load_imm(dst, value)
                self.mc.add(dst.value, src_ptr.value, dst.value)
        elif scale == 0:
            self.mc.add(dst.value, src_ptr.value, src_ofs.value)
        else:
            self.mc.sldi(dst.value, src_ofs.value, scale)
            self.mc.add(dst.value, src_ptr.value, dst.value)
        """

    def _emit_copycontent(self, arglocs, is_unicode):
        pass
        """
        [src_ptr_loc, dst_ptr_loc,
         src_ofs_loc, dst_ofs_loc, length_loc] = arglocs

        if is_unicode:
            basesize, itemsize, _ = symbolic.get_array_token(rstr.UNICODE,
                                        self.cpu.translate_support_code)
            if   itemsize == 2: scale = 1
            elif itemsize == 4: scale = 2
            else: raise AssertionError
        else:
            basesize, itemsize, _ = symbolic.get_array_token(rstr.STR,
                                        self.cpu.translate_support_code)
            assert itemsize == 1
            scale = 0

        self._emit_load_for_copycontent(r.r0, src_ptr_loc, src_ofs_loc, scale)
        self._emit_load_for_copycontent(r.r2, dst_ptr_loc, dst_ofs_loc, scale)

        if length_loc.is_imm():
            length = length_loc.getint()
            self.mc.load_imm(r.r5, length << scale)
        else:
            if scale > 0:
                self.mc.sldi(r.r5.value, length_loc.value, scale)
            elif length_loc is not r.r5:
                self.mc.mr(r.r5.value, length_loc.value)

        self.mc.mr(r.r4.value, r.r0.value)
        self.mc.addi(r.r4.value, r.r4.value, basesize)
        self.mc.addi(r.r3.value, r.r2.value, basesize)

        self.mc.load_imm(self.mc.RAW_CALL_REG, self.memcpy_addr)
        self.mc.raw_call()
        """

    def emit_op_call_malloc_gc(self, op, arglocs, regalloc):
        pass
        """
        self._emit_call(op, arglocs)
        self.propagate_memoryerror_if_r3_is_null()
        """

    def emit_op_call_malloc_nursery(self, op, arglocs, regalloc):
        pass
        """
        # registers r.RES and r.RSZ are allocated for this call
        size_box = op.getarg(0)
        assert isinstance(size_box, ConstInt)
        size = size_box.getint()
        gc_ll_descr = self.cpu.gc_ll_descr
        gcmap = regalloc.get_gcmap([r.RES, r.RSZ])
        self.malloc_cond(
            gc_ll_descr.get_nursery_free_addr(),
            gc_ll_descr.get_nursery_top_addr(),
            size, gcmap)
        """

    def emit_op_call_malloc_nursery_varsize_frame(self, op, arglocs, regalloc):
        pass
        """
        # registers r.RES and r.RSZ are allocated for this call
        [sizeloc] = arglocs
        gc_ll_descr = self.cpu.gc_ll_descr
        gcmap = regalloc.get_gcmap([r.RES, r.RSZ])
        self.malloc_cond_varsize_frame(
            gc_ll_descr.get_nursery_free_addr(),
            gc_ll_descr.get_nursery_top_addr(),
            sizeloc, gcmap)
        """

    def emit_op_call_malloc_nursery_varsize(self, op, arglocs, regalloc):
        pass
        """
        # registers r.RES and r.RSZ are allocated for this call
        gc_ll_descr = self.cpu.gc_ll_descr
        if not hasattr(gc_ll_descr, 'max_size_of_young_obj'):
            raise Exception("unreachable code")
            # for boehm, this function should never be called
        [lengthloc] = arglocs
        arraydescr = op.getdescr()
        itemsize = op.getarg(1).getint()
        maxlength = (gc_ll_descr.max_size_of_young_obj - WORD * 2) / itemsize
        gcmap = regalloc.get_gcmap([r.RES, r.RSZ])
        self.malloc_cond_varsize(
            op.getarg(0).getint(),
            gc_ll_descr.get_nursery_free_addr(),
            gc_ll_descr.get_nursery_top_addr(),
            lengthloc, itemsize, maxlength, gcmap, arraydescr)
        """

    def emit_op_debug_merge_point(self, op, arglocs, regalloc):
        pass

    emit_op_jit_debug = emit_op_debug_merge_point
    emit_op_keepalive = emit_op_debug_merge_point

    def emit_op_enter_portal_frame(self, op, arglocs, regalloc):
        pass
        """
        self.enter_portal_frame(op)
        """

    def emit_op_leave_portal_frame(self, op, arglocs, regalloc):
        pass
        """
        self.leave_portal_frame(op)
        """

    def _write_barrier_fastpath(self, mc, descr, arglocs, regalloc, array=False,
                                is_frame=False):
        pass
        """
        # Write code equivalent to write_barrier() in the GC: it checks
        # a flag in the object at arglocs[0], and if set, it calls a
        # helper piece of assembler.  The latter saves registers as needed
        # and call the function remember_young_pointer() from the GC.
        if we_are_translated():
            cls = self.cpu.gc_ll_descr.has_write_barrier_class()
            assert cls is not None and isinstance(descr, cls)
        #
        card_marking_mask = 0
        mask = descr.jit_wb_if_flag_singlebyte
        if array and descr.jit_wb_cards_set != 0:
            # assumptions the rest of the function depends on:
            assert (descr.jit_wb_cards_set_byteofs ==
                    descr.jit_wb_if_flag_byteofs)
            card_marking_mask = descr.jit_wb_cards_set_singlebyte
        #
        loc_base = arglocs[0]
        assert loc_base.is_reg()
        if is_frame:
            assert loc_base is r.SPP
        assert _check_imm_arg(descr.jit_wb_if_flag_byteofs)
        mc.lbz(r.SCRATCH2.value, loc_base.value, descr.jit_wb_if_flag_byteofs)
        mc.andix(r.SCRATCH.value, r.SCRATCH2.value, mask & 0xFF)

        jz_location = mc.get_relative_pos()
        mc.trap()        # patched later with 'beq'

        # for cond_call_gc_wb_array, also add another fast path:
        # if GCFLAG_CARDS_SET, then we can just set one bit and be done
        if card_marking_mask:
            # GCFLAG_CARDS_SET is in the same byte, loaded in r2 already
            mc.andix(r.SCRATCH.value, r.SCRATCH2.value,
                     card_marking_mask & 0xFF)
            js_location = mc.get_relative_pos()
            mc.trap()        # patched later with 'bne'
        else:
            js_location = 0

        # Write only a CALL to the helper prepared in advance, passing it as
        # argument the address of the structure we are writing into
        # (the first argument to COND_CALL_GC_WB).
        helper_num = (card_marking_mask != 0)
        if is_frame:
            helper_num = 4
        elif regalloc.fprm.reg_bindings:
            helper_num += 2
        if self.wb_slowpath[helper_num] == 0:    # tests only
            assert not we_are_translated()
            assert not is_frame
            self.cpu.gc_ll_descr.write_barrier_descr = descr
            self._build_wb_slowpath(card_marking_mask != 0,
                                    bool(regalloc.fprm.reg_bindings))
            assert self.wb_slowpath[helper_num] != 0
        #
        if not is_frame:
            mc.mr(r.r0.value, loc_base.value)    # unusual argument location
        mc.load_imm(r.SCRATCH2, self.wb_slowpath[helper_num])
        mc.mtctr(r.SCRATCH2.value)
        mc.bctrl()

        if card_marking_mask:
            # The helper ends again with a check of the flag in the object.
            # So here, we can simply write again a beq, which will be
            # taken if GCFLAG_CARDS_SET is still not set.
            jns_location = mc.get_relative_pos()
            mc.trap()
            #
            # patch the 'bne' above
            currpos = mc.currpos()
            pmc = OverwritingBuilder(mc, js_location, 1)
            pmc.bne(currpos - js_location)
            pmc.overwrite()
            #
            # case GCFLAG_CARDS_SET: emit_op a few instructions to do
            # directly the card flag setting
            loc_index = arglocs[1]
            if loc_index.is_reg():

                tmp_loc = arglocs[2]
                n = descr.jit_wb_card_page_shift

                # compute in tmp_loc the byte offset:
                #     ~(index >> (card_page_shift + 3))   ('~' is 'not_' below)
                mc.srli_op(tmp_loc.value, loc_index.value, n + 3)

                # compute in r2 the index of the bit inside the byte:
                #     (index >> card_page_shift) & 7
                mc.rldicl(r.SCRATCH2.value, loc_index.value, 64 - n, 61)
                mc.li(r.SCRATCH.value, 1)
                mc.not_(tmp_loc.value, tmp_loc.value)

                # set r2 to 1 << r2
                mc.sl_op(r.SCRATCH2.value, r.SCRATCH.value, r.SCRATCH2.value)

                # set this bit inside the byte of interest
                mc.lbzx(r.SCRATCH.value, loc_base.value, tmp_loc.value)
                mc.or_(r.SCRATCH.value, r.SCRATCH.value, r.SCRATCH2.value)
                mc.stbx(r.SCRATCH.value, loc_base.value, tmp_loc.value)
                # done

            else:
                byte_index = loc_index.value >> descr.jit_wb_card_page_shift
                byte_ofs = ~(byte_index >> 3)
                byte_val = 1 << (byte_index & 7)
                assert _check_imm_arg(byte_ofs)

                mc.lbz(r.SCRATCH.value, loc_base.value, byte_ofs)
                mc.ori(r.SCRATCH.value, r.SCRATCH.value, byte_val)
                mc.stb(r.SCRATCH.value, loc_base.value, byte_ofs)
            #
            # patch the beq just above
            currpos = mc.currpos()
            pmc = OverwritingBuilder(mc, jns_location, 1)
            pmc.beq(currpos - jns_location)
            pmc.overwrite()

        # patch the JZ above
        currpos = mc.currpos()
        pmc = OverwritingBuilder(mc, jz_location, 1)
        pmc.beq(currpos - jz_location)
        pmc.overwrite()
        """

    def emit_op_cond_call_gc_wb(self, op, arglocs, regalloc):
        pass
        """
        self._write_barrier_fastpath(self.mc, op.getdescr(), arglocs, regalloc)
        """

    def emit_op_cond_call_gc_wb_array(self, op, arglocs, regalloc):
        pass
        """
        self._write_barrier_fastpath(self.mc, op.getdescr(), arglocs, regalloc,
                                     array=True)
        """

    def emit_op_force_token(self, op, arglocs, regalloc):
        pass
        """
        res_loc = arglocs[0]
        self.mc.mr(res_loc.value, r.SPP.value)
        """

    def _genop_call_assembler(self, op, arglocs, regalloc):
        pass
        """
        if len(arglocs) == 3:
            [result_loc, argloc, vloc] = arglocs
        else:
            [result_loc, argloc] = arglocs
            vloc = imm(0)
        self._store_force_index(self._find_nearby_operation(regalloc, +1))
        # 'result_loc' is either r3 or f1, or None
        self.call_assembler(op, argloc, vloc, result_loc, r.r3)
        """

    emit_op_call_assembler_i = _genop_call_assembler
    emit_op_call_assembler_r = _genop_call_assembler
    emit_op_call_assembler_f = _genop_call_assembler
    emit_op_call_assembler_n = _genop_call_assembler

    # imm = staticmethod(imm)   # for call_assembler()

    def _call_assembler_emit_call(self, addr, argloc, _):
        pass
        """
        self.regalloc_mov(argloc, r.r3)
        self.mc.ld(r.r4.value, r.SP.value, THREADLOCAL_ADDR_OFFSET)

        cb = callbuilder.CallBuilder(self, addr, [r.r3, r.r4], r.r3)
        cb.emit()
        """

    def _call_assembler_emit_helper_call(self, addr, arglocs, result_loc):
        pass
        """
        cb = callbuilder.CallBuilder(self, addr, arglocs, result_loc)
        cb.emit()
        """

    def _call_assembler_check_descr(self, value, tmploc):
        pass
        """
        ofs = self.cpu.get_ofs_of_frame_field('jf_descr')
        self.mc.ld(r.r5.value, r.r3.value, ofs)
        if _check_imm_arg(value):
            self.mc.cmp_op(0, r.r5.value, value, imm=True)
        else:
            self.mc.load_imm(r.r4, value)
            self.mc.cmp_op(0, r.r5.value, r.r4.value, imm=False)
        jump_if_eq = self.mc.currpos()
        self.mc.trap()      # patched later
        return jump_if_eq
        """

    def _call_assembler_patch_je(self, result_loc, je_location):
        pass
        """
        jump_to_done = self.mc.currpos()
        self.mc.trap()      # patched later
        #
        currpos = self.mc.currpos()
        pmc = OverwritingBuilder(self.mc, je_location, 1)
        pmc.beq(currpos - je_location)
        pmc.overwrite()
        #
        return jump_to_done
        """

    def _call_assembler_load_result(self, op, result_loc):
        pass
        """
        if op.type != VOID:
            # load the return value from the dead frame's value index 0
            kind = op.type
            descr = self.cpu.getarraydescr_for_frame(kind)
            ofs = self.cpu.unpack_arraydescr(descr)
            if kind == FLOAT:
                assert result_loc is r.f1
                self.mc.lfd(r.f1.value, r.r3.value, ofs)
            else:
                assert result_loc is r.r3
                self.mc.ld(r.r3.value, r.r3.value, ofs)
        """

    def _call_assembler_patch_jmp(self, jmp_location):
        pass
        """
        currpos = self.mc.currpos()
        pmc = OverwritingBuilder(self.mc, jmp_location, 1)
        pmc.b(currpos - jmp_location)
        pmc.overwrite()
        """

    def redirect_call_assembler(self, oldlooptoken, newlooptoken):
        pass
        """
        # some minimal sanity checking
        old_nbargs = oldlooptoken.compiled_loop_token._debug_nbargs
        new_nbargs = newlooptoken.compiled_loop_token._debug_nbargs
        assert old_nbargs == new_nbargs
        oldadr = oldlooptoken._ll_function_addr
        target = newlooptoken._ll_function_addr
        # copy frame-info data
        baseofs = self.cpu.get_baseofs_of_frame_field()
        newlooptoken.compiled_loop_token.update_frame_info(
            oldlooptoken.compiled_loop_token, baseofs)
        if IS_PPC_64 and IS_BIG_ENDIAN:
            # PPC64 big-endian trampolines are data so overwrite the code
            # address in the function descriptor at the old address.
            # Copy the whole 3-word trampoline, even though the other
            # words are always zero so far.  That's not enough in all
            # cases: if the "target" trampoline is itself redirected
            # later, then the "old" trampoline won't be updated; so
            # we still need the jump below to be safe.
            odata = rffi.cast(rffi.CArrayPtr(lltype.Signed), oldadr)
            tdata = rffi.cast(rffi.CArrayPtr(lltype.Signed), target)
            odata[0] = tdata[0]
            odata[1] = tdata[1]
            odata[2] = tdata[2]
            oldadr += 3 * WORD
            target += 3 * WORD
        # we overwrite the instructions at the old _ll_function_addr
        # to start with a JMP to the new _ll_function_addr.
        mc = PPCBuilder()
        mc.b_abs(target)
        mc.copy_to_raw_memory(oldadr)
        """

    def get_int(self, arg):
        if arg in self.vars:
            var = self.vars[arg]
        else:
            var = self.mc.new_const_int(self.bndl, self.type_i32, arg.value)
            self.vars[arg] = var
        return var

    def get_float(self, arg):
        if arg in self.vars:
            var = self.vars[arg]
        else:
            var = self.mc.new_const_float(self.bndl, self.type_float, arg.value)
            self.vars[arg] = var
        return var

    def nop(self):
        pass


def notimplemented_op(self, op, arglocs, regalloc, fcond):
    print "[MU/vm] %s not implemented" % op.getopname()
    raise NotImplementedError(op)

asm_operations = [notimplemented_op] * (rop._LAST + 1)

for name, value in AssemblerMu.__dict__.iteritems():
    if name.startswith('emit_op_'):
        opname = name[len('emit_op_'):]
        num = getattr(rop, opname.upper())
        asm_operations[num] = value
