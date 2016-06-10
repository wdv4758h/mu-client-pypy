"""
Extracted parts from muapi.h that are relevant using muapiparser.py

This file is RPython
"""


# --------------------------------
# Flags
class MuTrapHandlerResult:
    MU_THREAD_EXIT = 0x00
    MU_REBIND_PASS_VALUES = 0x01
    MU_REBIND_THROW_EXC = 0x02
class MuDestKind:
    MU_DEST_NORMAL = 0x01
    MU_DEST_EXCEPT = 0x02
    MU_DEST_TRUE = 0x03
    MU_DEST_FALSE = 0x04
    MU_DEST_DEFAULT = 0x05
    MU_DEST_DISABLED = 0x06
    MU_DEST_ENABLED = 0x07
class MuBinOptr:
    MU_BINOP_ADD = 0x01
    MU_BINOP_SUB = 0x02
    MU_BINOP_MUL = 0x03
    MU_BINOP_SDIV = 0x04
    MU_BINOP_SREM = 0x05
    MU_BINOP_UDIV = 0x06
    MU_BINOP_UREM = 0x07
    MU_BINOP_SHL = 0x08
    MU_BINOP_LSHR = 0x09
    MU_BINOP_ASHR = 0x0A
    MU_BINOP_AND = 0x0B
    MU_BINOP_OR = 0x0C
    MU_BINOP_XOR = 0x0D
    MU_BINOP_FADD = 0xB0
    MU_BINOP_FSUB = 0xB1
    MU_BINOP_FMUL = 0xB2
    MU_BINOP_FDIV = 0xB3
    MU_BINOP_FREM = 0xB4
class MuCmpOptr:
    MU_CMP_EQ = 0x20
    MU_CMP_NE = 0x21
    MU_CMP_SGE = 0x22
    MU_CMP_SGT = 0x23
    MU_CMP_SLE = 0x24
    MU_CMP_SLT = 0x25
    MU_CMP_UGE = 0x26
    MU_CMP_UGT = 0x27
    MU_CMP_ULE = 0x28
    MU_CMP_ULT = 0x29
    MU_CMP_FFALSE = 0xC0
    MU_CMP_FTRUE = 0xC1
    MU_CMP_FUNO = 0xC2
    MU_CMP_FUEQ = 0xC3
    MU_CMP_FUNE = 0xC4
    MU_CMP_FUGT = 0xC5
    MU_CMP_FUGE = 0xC6
    MU_CMP_FULT = 0xC7
    MU_CMP_FULE = 0xC8
    MU_CMP_FORD = 0xC9
    MU_CMP_FOEQ = 0xCA
    MU_CMP_FONE = 0xCB
    MU_CMP_FOGT = 0xCC
    MU_CMP_FOGE = 0xCD
    MU_CMP_FOLT = 0xCE
    MU_CMP_FOLE = 0xCF
class MuConvOptr:
    MU_CONV_TRUNC = 0x30
    MU_CONV_ZEXT = 0x31
    MU_CONV_SEXT = 0x32
    MU_CONV_FPTRUNC = 0x33
    MU_CONV_FPEXT = 0x34
    MU_CONV_FPTOUI = 0x35
    MU_CONV_FPTOSI = 0x36
    MU_CONV_UITOFP = 0x37
    MU_CONV_SITOFP = 0x38
    MU_CONV_BITCAST = 0x39
    MU_CONV_REFCAST = 0x3A
    MU_CONV_PTRCAST = 0x3B
class MuMemOrd:
    MU_ORD_NOT_ATOMIC = 0x00
    MU_ORD_RELAXED = 0x01
    MU_ORD_CONSUME = 0x02
    MU_ORD_ACQUIRE = 0x03
    MU_ORD_RELEASE = 0x04
    MU_ORD_ACQ_REL = 0x05
    MU_ORD_SEQ_CST = 0x06
class MuAtomicRMWOp:
    MU_ARMW_XCHG = 0x00
    MU_ARMW_ADD = 0x01
    MU_ARMW_SUB = 0x02
    MU_ARMW_AND = 0x03
    MU_ARMW_NAND = 0x04
    MU_ARMW_OR = 0x05
    MU_ARMW_XOR = 0x06
    MU_ARMW_MAX = 0x07
    MU_ARMW_MIN = 0x08
    MU_ARMW_UMAX = 0x09
    MU_ARMW_UMIN = 0x0A
class MuFlag:
    MU_CC_DEFAULT = 0x00


# --------------------------------
# Classes
class MuVM:
    def new_context(self):
        # type: (MuVM) -> MuCtx
        pass

    def id_of(self, name):
        # type: (MuVM, MuName) -> MuID
        pass

    def name_of(self, id):
        # type: (MuVM, MuID) -> MuName
        pass

    def set_trap_handler(self, trap_handler, userdata):
        # type: (MuVM, MuTrapHandler, MuCPtr) -> void
        pass

    def execute(self):
        # type: (MuVM) -> void
        pass

    def get_mu_error_ptr(self):
        # type: (MuVM) -> int
        pass

class MuCtx:
    def id_of(self, name):
        # type: (MuCtx, MuName) -> MuID
        pass

    def name_of(self, id):
        # type: (MuCtx, MuID) -> MuName
        pass

    def close_context(self):
        # type: (MuCtx) -> void
        pass

    def load_bundle(self, buf, sz):
        # type: (MuCtx, char, int) -> void
        pass

    def load_hail(self, buf, sz):
        # type: (MuCtx, char, int) -> void
        pass

    def handle_from_sint8(self, num, len):
        # type: (MuCtx, int8_t, int) -> MuIntValue
        pass

    def handle_from_uint8(self, num, len):
        # type: (MuCtx, uint8_t, int) -> MuIntValue
        pass

    def handle_from_sint16(self, num, len):
        # type: (MuCtx, int16_t, int) -> MuIntValue
        pass

    def handle_from_uint16(self, num, len):
        # type: (MuCtx, uint16_t, int) -> MuIntValue
        pass

    def handle_from_sint32(self, num, len):
        # type: (MuCtx, int32_t, int) -> MuIntValue
        pass

    def handle_from_uint32(self, num, len):
        # type: (MuCtx, uint32_t, int) -> MuIntValue
        pass

    def handle_from_sint64(self, num, len):
        # type: (MuCtx, int64_t, int) -> MuIntValue
        pass

    def handle_from_uint64(self, num, len):
        # type: (MuCtx, uint64_t, int) -> MuIntValue
        pass

    def handle_from_float(self, num):
        # type: (MuCtx, float) -> MuFloatValue
        pass

    def handle_from_double(self, num):
        # type: (MuCtx, double) -> MuDoubleValue
        pass

    def handle_from_ptr(self, mu_type, ptr):
        # type: (MuCtx, MuID, MuCPtr) -> MuUPtrValue
        pass

    def handle_from_fp(self, mu_type, fp):
        # type: (MuCtx, MuID, MuCFP) -> MuUFPValue
        pass

    def handle_to_sint8(self, opnd):
        # type: (MuCtx, MuIntValue) -> int8_t
        pass

    def handle_to_uint8(self, opnd):
        # type: (MuCtx, MuIntValue) -> uint8_t
        pass

    def handle_to_sint16(self, opnd):
        # type: (MuCtx, MuIntValue) -> int16_t
        pass

    def handle_to_uint16(self, opnd):
        # type: (MuCtx, MuIntValue) -> uint16_t
        pass

    def handle_to_sint32(self, opnd):
        # type: (MuCtx, MuIntValue) -> int32_t
        pass

    def handle_to_uint32(self, opnd):
        # type: (MuCtx, MuIntValue) -> uint32_t
        pass

    def handle_to_sint64(self, opnd):
        # type: (MuCtx, MuIntValue) -> int64_t
        pass

    def handle_to_uint64(self, opnd):
        # type: (MuCtx, MuIntValue) -> uint64_t
        pass

    def handle_to_float(self, opnd):
        # type: (MuCtx, MuFloatValue) -> float
        pass

    def handle_to_double(self, opnd):
        # type: (MuCtx, MuDoubleValue) -> double
        pass

    def handle_to_ptr(self, opnd):
        # type: (MuCtx, MuUPtrValue) -> MuCPtr
        pass

    def handle_to_fp(self, opnd):
        # type: (MuCtx, MuUFPValue) -> MuCFP
        pass

    def handle_from_const(self, id):
        # type: (MuCtx, MuID) -> MuValue
        pass

    def handle_from_global(self, id):
        # type: (MuCtx, MuID) -> MuIRefValue
        pass

    def handle_from_func(self, id):
        # type: (MuCtx, MuID) -> MuFuncRefValue
        pass

    def handle_from_expose(self, id):
        # type: (MuCtx, MuID) -> MuValue
        pass

    def delete_value(self, opnd):
        # type: (MuCtx, MuValue) -> void
        pass

    def ref_eq(self, lhs, rhs):
        # type: (MuCtx, MuGenRefValue, MuGenRefValue) -> int
        pass

    def ref_ult(self, lhs, rhs):
        # type: (MuCtx, MuIRefValue, MuIRefValue) -> int
        pass

    def extract_value(self, str, index):
        # type: (MuCtx, MuStructValue, int) -> MuValue
        pass

    def insert_value(self, str, index, newval):
        # type: (MuCtx, MuStructValue, int, MuValue) -> MuStructValue
        pass

    def extract_element(self, str, index):
        # type: (MuCtx, MuSeqValue, MuIntValue) -> MuValue
        pass

    def insert_element(self, str, index, newval):
        # type: (MuCtx, MuSeqValue, MuIntValue, MuValue) -> MuSeqValue
        pass

    def new_fixed(self, mu_type):
        # type: (MuCtx, MuID) -> MuRefValue
        pass

    def new_hybrid(self, mu_type, length):
        # type: (MuCtx, MuID, MuIntValue) -> MuRefValue
        pass

    def refcast(self, opnd, new_type):
        # type: (MuCtx, MuGenRefValue, MuID) -> MuGenRefValue
        pass

    def get_iref(self, opnd):
        # type: (MuCtx, MuRefValue) -> MuIRefValue
        pass

    def get_field_iref(self, opnd, field):
        # type: (MuCtx, MuIRefValue, int) -> MuIRefValue
        pass

    def get_elem_iref(self, opnd, index):
        # type: (MuCtx, MuIRefValue, MuIntValue) -> MuIRefValue
        pass

    def shift_iref(self, opnd, offset):
        # type: (MuCtx, MuIRefValue, MuIntValue) -> MuIRefValue
        pass

    def get_var_part_iref(self, opnd):
        # type: (MuCtx, MuIRefValue) -> MuIRefValue
        pass

    def load(self, ord, loc):
        # type: (MuCtx, MuMemOrd, MuIRefValue) -> MuValue
        pass

    def store(self, ord, loc, newval):
        # type: (MuCtx, MuMemOrd, MuIRefValue, MuValue) -> void
        pass

    def cmpxchg(self, ord_succ, ord_fail, weak, loc, expected, desired, is_succ):
        # type: (MuCtx, MuMemOrd, MuMemOrd, int, MuIRefValue, MuValue, MuValue, int) -> MuValue
        pass

    def atomicrmw(self, ord, op, loc, opnd):
        # type: (MuCtx, MuMemOrd, MuAtomicRMWOp, MuIRefValue, MuValue) -> MuValue
        pass

    def fence(self, ord):
        # type: (MuCtx, MuMemOrd) -> void
        pass

    def new_stack(self, func):
        # type: (MuCtx, MuFuncRefValue) -> MuStackRefValue
        pass

    def new_thread_nor(self, stack, threadlocal, vals):
        # type: (MuCtx, MuStackRefValue, MuRefValue, [MuValue]) -> MuThreadRefValue
        pass

    def new_thread_exc(self, stack, threadlocal, exc):
        # type: (MuCtx, MuStackRefValue, MuRefValue, MuRefValue) -> MuThreadRefValue
        pass

    def kill_stack(self, stack):
        # type: (MuCtx, MuStackRefValue) -> void
        pass

    def set_threadlocal(self, thread, threadlocal):
        # type: (MuCtx, MuThreadRefValue, MuRefValue) -> void
        pass

    def get_threadlocal(self, thread):
        # type: (MuCtx, MuThreadRefValue) -> MuRefValue
        pass

    def new_cursor(self, stack):
        # type: (MuCtx, MuStackRefValue) -> MuFCRefValue
        pass

    def next_frame(self, cursor):
        # type: (MuCtx, MuFCRefValue) -> void
        pass

    def copy_cursor(self, cursor):
        # type: (MuCtx, MuFCRefValue) -> MuFCRefValue
        pass

    def close_cursor(self, cursor):
        # type: (MuCtx, MuFCRefValue) -> void
        pass

    def cur_func(self, cursor):
        # type: (MuCtx, MuFCRefValue) -> MuID
        pass

    def cur_func_ver(self, cursor):
        # type: (MuCtx, MuFCRefValue) -> MuID
        pass

    def cur_inst(self, cursor):
        # type: (MuCtx, MuFCRefValue) -> MuID
        pass

    def dump_keepalives(self, cursor, results):
        # type: (MuCtx, MuFCRefValue, MuValue) -> void
        pass

    def pop_frames_to(self, cursor):
        # type: (MuCtx, MuFCRefValue) -> void
        pass

    def push_frame(self, stack, func):
        # type: (MuCtx, MuStackRefValue, MuFuncRefValue) -> void
        pass

    def tr64_is_fp(self, value):
        # type: (MuCtx, MuTagRef64Value) -> int
        pass

    def tr64_is_int(self, value):
        # type: (MuCtx, MuTagRef64Value) -> int
        pass

    def tr64_is_ref(self, value):
        # type: (MuCtx, MuTagRef64Value) -> int
        pass

    def tr64_to_fp(self, value):
        # type: (MuCtx, MuTagRef64Value) -> MuDoubleValue
        pass

    def tr64_to_int(self, value):
        # type: (MuCtx, MuTagRef64Value) -> MuIntValue
        pass

    def tr64_to_ref(self, value):
        # type: (MuCtx, MuTagRef64Value) -> MuRefValue
        pass

    def tr64_to_tag(self, value):
        # type: (MuCtx, MuTagRef64Value) -> MuIntValue
        pass

    def tr64_from_fp(self, value):
        # type: (MuCtx, MuDoubleValue) -> MuTagRef64Value
        pass

    def tr64_from_int(self, value):
        # type: (MuCtx, MuIntValue) -> MuTagRef64Value
        pass

    def tr64_from_ref(self, ref, tag):
        # type: (MuCtx, MuRefValue, MuIntValue) -> MuTagRef64Value
        pass

    def enable_watchpoint(self, wpid):
        # type: (MuCtx, MuWPID) -> void
        pass

    def disable_watchpoint(self, wpid):
        # type: (MuCtx, MuWPID) -> void
        pass

    def pin(self, loc):
        # type: (MuCtx, MuValue) -> MuUPtrValue
        pass

    def unpin(self, loc):
        # type: (MuCtx, MuValue) -> void
        pass

    def expose(self, func, call_conv, cookie):
        # type: (MuCtx, MuFuncRefValue, MuCallConv, MuIntValue) -> MuValue
        pass

    def unexpose(self, call_conv, value):
        # type: (MuCtx, MuCallConv, MuValue) -> void
        pass

    # --------------------------------
    # Bundle building APIs
    def new_bundle(self):
        # type: (MuCtx) -> MuBundleNode
        pass

    def load_bundle_from_node(self, b):
        # type: (MuCtx, MuBundleNode) -> void
        pass

    def abort_bundle_node(self, b):
        # type: (MuCtx, MuBundleNode) -> void
        pass

    def get_node(self, b, id):
        # type: (MuCtx, MuBundleNode, MuID) -> MuChildNode
        pass

    def get_id(self, b, node):
        # type: (MuCtx, MuBundleNode, MuChildNode) -> MuID
        pass

    def set_name(self, b, node, name):
        # type: (MuCtx, MuBundleNode, MuChildNode, MuName) -> void
        pass

    def new_type_int(self, b, len):
        # type: (MuCtx, MuBundleNode, int) -> MuTypeNode
        pass

    def new_type_float(self, b):
        # type: (MuCtx, MuBundleNode) -> MuTypeNode
        pass

    def new_type_double(self, b):
        # type: (MuCtx, MuBundleNode) -> MuTypeNode
        pass

    def new_type_uptr(self, b):
        # type: (MuCtx, MuBundleNode) -> MuTypeNode
        pass

    def set_type_uptr(self, uptr, ty):
        # type: (MuCtx, MuTypeNode, MuTypeNode) -> void
        pass

    def new_type_ufuncptr(self, b):
        # type: (MuCtx, MuBundleNode) -> MuTypeNode
        pass

    def set_type_ufuncptr(self, ufuncptr, sig):
        # type: (MuCtx, MuTypeNode, MuFuncSigNode) -> void
        pass

    def new_type_struct(self, b, fieldtys):
        # type: (MuCtx, MuBundleNode, [MuTypeNode]) -> MuTypeNode
        pass

    def new_type_hybrid(self, b, fixedtys, varty):
        # type: (MuCtx, MuBundleNode, [MuTypeNode], MuTypeNode) -> MuTypeNode
        pass

    def new_type_array(self, b, elemty, len):
        # type: (MuCtx, MuBundleNode, MuTypeNode, uint64_t) -> MuTypeNode
        pass

    def new_type_vector(self, b, elemty, len):
        # type: (MuCtx, MuBundleNode, MuTypeNode, uint64_t) -> MuTypeNode
        pass

    def new_type_void(self, b):
        # type: (MuCtx, MuBundleNode) -> MuTypeNode
        pass

    def new_type_ref(self, b):
        # type: (MuCtx, MuBundleNode) -> MuTypeNode
        pass

    def set_type_ref(self, ref, ty):
        # type: (MuCtx, MuTypeNode, MuTypeNode) -> void
        pass

    def new_type_iref(self, b):
        # type: (MuCtx, MuBundleNode) -> MuTypeNode
        pass

    def set_type_iref(self, iref, ty):
        # type: (MuCtx, MuTypeNode, MuTypeNode) -> void
        pass

    def new_type_weakref(self, b):
        # type: (MuCtx, MuBundleNode) -> MuTypeNode
        pass

    def set_type_weakref(self, weakref, ty):
        # type: (MuCtx, MuTypeNode, MuTypeNode) -> void
        pass

    def new_type_funcref(self, b):
        # type: (MuCtx, MuBundleNode) -> MuTypeNode
        pass

    def set_type_funcref(self, funcref, sig):
        # type: (MuCtx, MuTypeNode, MuFuncSigNode) -> void
        pass

    def new_type_tagref64(self, b):
        # type: (MuCtx, MuBundleNode) -> MuTypeNode
        pass

    def new_type_threadref(self, b):
        # type: (MuCtx, MuBundleNode) -> MuTypeNode
        pass

    def new_type_stackref(self, b):
        # type: (MuCtx, MuBundleNode) -> MuTypeNode
        pass

    def new_type_framecursorref(self, b):
        # type: (MuCtx, MuBundleNode) -> MuTypeNode
        pass

    def new_type_irnoderef(self, b):
        # type: (MuCtx, MuBundleNode) -> MuTypeNode
        pass

    def new_funcsig(self, b, paramtys, rettys):
        # type: (MuCtx, MuBundleNode, [MuTypeNode], [MuTypeNode]) -> MuFuncSigNode
        pass

    def new_const_int(self, b, ty, value):
        # type: (MuCtx, MuBundleNode, MuTypeNode, uint64_t) -> MuConstNode
        pass

    def new_const_int_ex(self, b, ty, values):
        # type: (MuCtx, MuBundleNode, MuTypeNode, [uint64_t]) -> MuConstNode
        pass

    def new_const_float(self, b, ty, value):
        # type: (MuCtx, MuBundleNode, MuTypeNode, float) -> MuConstNode
        pass

    def new_const_double(self, b, ty, value):
        # type: (MuCtx, MuBundleNode, MuTypeNode, double) -> MuConstNode
        pass

    def new_const_null(self, b, ty):
        # type: (MuCtx, MuBundleNode, MuTypeNode) -> MuConstNode
        pass

    def new_const_seq(self, b, ty, elems):
        # type: (MuCtx, MuBundleNode, MuTypeNode, [MuConstNode]) -> MuConstNode
        pass

    def new_global_cell(self, b, ty):
        # type: (MuCtx, MuBundleNode, MuTypeNode) -> MuGlobalNode
        pass

    def new_func(self, b, sig):
        # type: (MuCtx, MuBundleNode, MuFuncSigNode) -> MuFuncNode
        pass

    def new_func_ver(self, b, func):
        # type: (MuCtx, MuBundleNode, MuFuncNode) -> MuFuncVerNode
        pass

    def new_exp_func(self, b, func, callconv, cookie):
        # type: (MuCtx, MuBundleNode, MuFuncNode, MuCallConv, MuConstNode) -> MuExpFuncNode
        pass

    def new_bb(self, fv):
        # type: (MuCtx, MuFuncVerNode) -> MuBBNode
        pass

    def new_nor_param(self, bb, ty):
        # type: (MuCtx, MuBBNode, MuTypeNode) -> MuNorParamNode
        pass

    def new_exc_param(self, bb):
        # type: (MuCtx, MuBBNode) -> MuExcParamNode
        pass

    def new_inst_res(self, inst):
        # type: (MuCtx, MuInstNode) -> MuInstResNode
        pass

    def add_dest(self, inst, kind, dest, vars):
        # type: (MuCtx, MuInstNode, MuDestKind, MuBBNode, [MuVarNode]) -> void
        pass

    def add_keepalives(self, inst, vars):
        # type: (MuCtx, MuInstNode, [MuLocalVarNode]) -> void
        pass

    def new_binop(self, bb, optr, ty, opnd1, opnd2):
        # type: (MuCtx, MuBBNode, MuBinOptr, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_cmp(self, bb, optr, ty, opnd1, opnd2):
        # type: (MuCtx, MuBBNode, MuCmpOptr, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_conv(self, bb, optr, from_ty, to_ty, opnd):
        # type: (MuCtx, MuBBNode, MuConvOptr, MuTypeNode, MuTypeNode, MuVarNode) -> MuInstNode
        pass

    def new_select(self, bb, cond_ty, opnd_ty, cond, if_true, if_false):
        # type: (MuCtx, MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_branch(self, bb):
        # type: (MuCtx, MuBBNode) -> MuInstNode
        pass

    def new_branch2(self, bb, cond):
        # type: (MuCtx, MuBBNode, MuVarNode) -> MuInstNode
        pass

    def new_switch(self, bb, opnd_ty, opnd):
        # type: (MuCtx, MuBBNode, MuTypeNode, MuVarNode) -> MuInstNode
        pass

    def add_switch_dest(self, sw, key, dest, vars):
        # type: (MuCtx, MuInstNode, MuConstNode, MuBBNode, [MuVarNode]) -> void
        pass

    def new_call(self, bb, sig, callee, args):
        # type: (MuCtx, MuBBNode, MuFuncSigNode, MuVarNode, [MuVarNode]) -> MuInstNode
        pass

    def new_tailcall(self, bb, sig, callee, args):
        # type: (MuCtx, MuBBNode, MuFuncSigNode, MuVarNode, [MuVarNode]) -> MuInstNode
        pass

    def new_ret(self, bb, rvs):
        # type: (MuCtx, MuBBNode, [MuVarNode]) -> MuInstNode
        pass

    def new_throw(self, bb, exc):
        # type: (MuCtx, MuBBNode, MuVarNode) -> MuInstNode
        pass

    def new_extractvalue(self, bb, strty, index, opnd):
        # type: (MuCtx, MuBBNode, MuTypeNode, int, MuVarNode) -> MuInstNode
        pass

    def new_insertvalue(self, bb, strty, index, opnd, newval):
        # type: (MuCtx, MuBBNode, MuTypeNode, int, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_extractelement(self, bb, seqty, indty, opnd, index):
        # type: (MuCtx, MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_insertelement(self, bb, seqty, indty, opnd, index, newval):
        # type: (MuCtx, MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_shufflevector(self, bb, vecty, maskty, vec1, vec2, mask):
        # type: (MuCtx, MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_new(self, bb, allocty):
        # type: (MuCtx, MuBBNode, MuTypeNode) -> MuInstNode
        pass

    def new_newhybrid(self, bb, allocty, lenty, length):
        # type: (MuCtx, MuBBNode, MuTypeNode, MuTypeNode, MuVarNode) -> MuInstNode
        pass

    def new_alloca(self, bb, allocty):
        # type: (MuCtx, MuBBNode, MuTypeNode) -> MuInstNode
        pass

    def new_allocahybrid(self, bb, allocty, lenty, length):
        # type: (MuCtx, MuBBNode, MuTypeNode, MuTypeNode, MuVarNode) -> MuInstNode
        pass

    def new_getiref(self, bb, refty, opnd):
        # type: (MuCtx, MuBBNode, MuTypeNode, MuVarNode) -> MuInstNode
        pass

    def new_getfieldiref(self, bb, is_ptr, refty, index, opnd):
        # type: (MuCtx, MuBBNode, int, MuTypeNode, int, MuVarNode) -> MuInstNode
        pass

    def new_getelemiref(self, bb, is_ptr, refty, indty, opnd, index):
        # type: (MuCtx, MuBBNode, int, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_shiftiref(self, bb, is_ptr, refty, offty, opnd, offset):
        # type: (MuCtx, MuBBNode, int, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_getvarpartiref(self, bb, is_ptr, refty, opnd):
        # type: (MuCtx, MuBBNode, int, MuTypeNode, MuVarNode) -> MuInstNode
        pass

    def new_load(self, bb, is_ptr, ord, refty, loc):
        # type: (MuCtx, MuBBNode, int, MuMemOrd, MuTypeNode, MuVarNode) -> MuInstNode
        pass

    def new_store(self, bb, is_ptr, ord, refty, loc, newval):
        # type: (MuCtx, MuBBNode, int, MuMemOrd, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_cmpxchg(self, bb, is_ptr, is_weak, ord_succ, ord_fail, refty, loc, expected, desired):
        # type: (MuCtx, MuBBNode, int, int, MuMemOrd, MuMemOrd, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_atomicrmw(self, bb, is_ptr, ord, optr, refTy, loc, opnd):
        # type: (MuCtx, MuBBNode, int, MuMemOrd, MuAtomicRMWOp, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_fence(self, bb, ord):
        # type: (MuCtx, MuBBNode, MuMemOrd) -> MuInstNode
        pass

    def new_trap(self, bb, rettys):
        # type: (MuCtx, MuBBNode, [MuTypeNode]) -> MuInstNode
        pass

    def new_watchpoint(self, bb, wpid, rettys):
        # type: (MuCtx, MuBBNode, MuWPID, [MuTypeNode]) -> MuInstNode
        pass

    def new_wpbranch(self, bb, wpid):
        # type: (MuCtx, MuBBNode, MuWPID) -> MuInstNode
        pass

    def new_ccall(self, bb, callconv, callee_ty, sig, callee, args):
        # type: (MuCtx, MuBBNode, MuCallConv, MuTypeNode, MuFuncSigNode, MuVarNode, [MuVarNode]) -> MuInstNode
        pass

    def new_newthread(self, bb, stack, threadlocal):
        # type: (MuCtx, MuBBNode, MuVarNode, MuVarNode) -> MuInstNode
        pass

    def new_swapstack_ret(self, bb, swappee, ret_tys):
        # type: (MuCtx, MuBBNode, MuVarNode, [MuTypeNode]) -> MuInstNode
        pass

    def new_swapstack_kill(self, bb, swappee):
        # type: (MuCtx, MuBBNode, MuVarNode) -> MuInstNode
        pass

    def set_newstack_pass_values(self, inst, tys, vars):
        # type: (MuCtx, MuInstNode, MuTypeNode, [MuVarNode]) -> void
        pass

    def set_newstack_throw_exc(self, inst, exc):
        # type: (MuCtx, MuInstNode, MuVarNode) -> void
        pass

    def new_comminst(self, bb, opcode, flags, tys, sigs, args):
        # type: (MuCtx, MuBBNode, MuCommInst, [MuFlag], [MuTypeNode], [MuFuncSigNode], [MuVarNode]) -> MuInstNode
        pass

"""
Node type hierarchy:

MuIRNode
 +-- MuBundleNode
 +-- MuChildNode
     +-- MuFuncSigNode
     +-- MuInstNode
     +-- MuVarNode
     |   +-- MuLocalVarNode
     |   |   +-- MuInstResNode
     |   |   +-- MuNorParamNode
     |   |   +-- MuExcParamNode
     |   +-- MuGlobalVarNode
     |       +-- MuExpFuncNode
     |       +-- MuConstNode
     |       +-- MuFuncNode
     |       +-- MuGlobalNode
     +-- MuTypeNode
     +-- MuFuncVerNode
     +-- MuBBNode

"""

class MuIRNode(object):                 pass
class MuBundleNode(MuIRNode):           pass
class MuChildNode(MuIRNode):            pass
class MuTypeNode(MuChildNode):          pass
class MuFuncSigNode(MuChildNode):       pass
class MuVarNode(MuChildNode):           pass
class MuGlobalVarNode(MuVarNode):       pass
class MuConstNode(MuGlobalVarNode):     pass
class MuGlobalNode(MuGlobalVarNode):    pass
class MuFuncNode(MuGlobalVarNode):      pass
class MuExpFuncNode(MuGlobalVarNode):   pass
class MuLocalVarNode(MuVarNode):        pass
class MuNorParamNode(MuLocalVarNode):   pass
class MuExcParamNode(MuLocalVarNode):   pass
class MuInstResNode(MuLocalVarNode):    pass
class MuFuncVerNode(MuChildNode):       pass
class MuBBNode(MuChildNode):            pass
class MuInstNode(MuChildNode):          pass


class MuID(int):                        pass
class MuName(str):                      pass