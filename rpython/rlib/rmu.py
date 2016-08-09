"""
Mu API RPython binding.

Note: environment variable $MU needs to be defined to point to the reference implementation!
"""
from rpython.rtyper.lltypesystem import rffi
from rpython.rtyper.lltypesystem import lltype
from rpython.translator.tool.cbuild import ExternalCompilationInfo
import os

mu_dir = os.path.join(os.getenv('MU'), 'cbinding')
eci = ExternalCompilationInfo(includes=['refimpl2-start.h', 'muapi.h'],
                              include_dirs=[mu_dir],
                              libraries=['murefimpl2start'],
                              library_dirs=[mu_dir])


# -------------------------------------------------------------------------------------------------------
# OO wrappers
class Mu:
    def __init__(self, config_str=""):
        with rffi.scoped_str2charp(config_str) as buf:
            self._mu = mu_new_ex(buf)

    # scope support
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def new_context(self):
        # type: () -> MuContext
        return MuContext(self._mu.c_new_context(self._mu))

    def id_of(self, name):
        # type (str) -> MuID
        with rffi.scoped_str2charp(name) as buf:
            return self._mu.c_id_of(self._mu, buf)

    def name_of(self, id):
        # type (MuID) -> str
        c_charp = self._mu.c_name_of(self._mu, id)
        return rffi.charp2str(c_charp)

    def set_trap_handler(self, trap_handler, userdata):
        # type (MuTrapHandler, MuCPtr) -> None
        self._mu.c_set_trap_handler(self._mu, trap_handler, userdata)

    def make_boot_image(self, whitelist, output_file):
        # type ([MuID], str) -> None
        with scoped_lst2arr(MuID, whitelist) as (arr, sz):
            with rffi.scoped_str2charp(output_file) as buf:
                self._mu.c_make_boot_image(self._mu, arr, sz, buf)

    def execute(self):
        # type () -> None
        self._mu.c_execute(self._mu)

    def get_mu_error_ptr(self):
        # type () -> rffi.INTP
        return self._mu.c_get_mu_error_ptr(self._mu)

    def close(self):
        return mu_close(self._mu)


class MuContext:
    def __init__(self, rffi_ctx_ptr):
        self._ctx = rffi_ctx_ptr

    # scope support
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close_context()

    def id_of(self, name):
        # type: (str) -> MuID
        with rffi.scoped_str2charp(name) as buf:
            return self._ctx.c_id_of(self._ctx, buf)

    def name_of(self, id):
        # type: (MuID) -> str
        c_charp = self._ctx.c_name_of(self._ctx, id)
        return rffi.charp2str(c_charp)

    def close_context(self):
        # type: () -> None
        self._ctx.c_close_context(self._ctx)

    def load_bundle(self, bdl):
        # type: (str) -> None
        with rffi.scoped_str2charp(bdl) as buf:
            self._ctx.c_load_bundle(self._ctx, buf, rffi.cast(MuArraySize, len(bdl)))

    def load_hail(self, hail):
        # type: (str) -> None
        with rffi.scoped_str2charp(hail) as buf:
            self._ctx.c_load_hail(self._ctx, buf, rffi.cast(MuArraySize, len(hail)))

    def handle_from_sint8(self, num, length):
        # type: (int, int) -> MuIntValue
        num = rffi.cast(rffi.CHAR, num)
        length = rffi.cast(rffi.INT, length)
        return self._ctx.c_handle_from_sint8(self._ctx, num, length)

    def handle_from_uint8(self, num, length):
        # type: (int, int) -> MuIntValue
        num = rffi.cast(rffi.UCHAR, num)
        length = rffi.cast(rffi.INT, length)
        return self._ctx.c_handle_from_uint8(self._ctx, num, length)

    def handle_from_sint16(self, num, length):
        # type: (int, int) -> MuIntValue
        num = rffi.cast(rffi.SHORT, num)
        length = rffi.cast(rffi.INT, length)
        return self._ctx.c_handle_from_sint16(self._ctx, num, length)

    def handle_from_uint16(self, num, length):
        # type: (int, int) -> MuIntValue
        num = rffi.cast(rffi.USHORT, num)
        length = rffi.cast(rffi.INT, length)
        return self._ctx.c_handle_from_uint16(self._ctx, num, length)

    def handle_from_sint32(self, num, length):
        # type: (int, int) -> MuIntValue
        num = rffi.cast(rffi.INT, num)
        length = rffi.cast(rffi.INT, length)
        return self._ctx.c_handle_from_sint32(self._ctx, num, length)

    def handle_from_uint32(self, num, length):
        # type: (int, int) -> MuIntValue
        num = rffi.cast(rffi.UINT, num)
        length = rffi.cast(rffi.INT, length)
        return self._ctx.c_handle_from_uint32(self._ctx, num, length)

    def handle_from_sint64(self, num, length):
        # type: (int, int) -> MuIntValue
        num = rffi.cast(rffi.LONG, num)
        length = rffi.cast(rffi.INT, length)
        return self._ctx.c_handle_from_sint64(self._ctx, num, length)

    def handle_from_uint64(self, num, length):
        # type: (int, int) -> MuIntValue
        num = rffi.cast(rffi.ULONG, num)
        length = rffi.cast(rffi.INT, length)
        return self._ctx.c_handle_from_uint64(self._ctx, num, length)

    def handle_from_uint64s(self, nums, length):
        # type: ([int], int) -> MuIntValue
        with scoped_lst2arr(rffi.ULONG, nums) as (arr, sz):
            length = rffi.cast(rffi.INT, length)
            return self._ctx.c_handle_from_uint64s(self._ctx, arr, sz, length)

    def handle_from_float(self, num):
        # type: (float) -> MuFloatValue
        num = rffi.cast(rffi.FLOAT, num)
        return self._ctx.c_handle_from_float(self._ctx, num)

    def handle_from_double(self, num):
        # type: (float) -> MuDoubleValue
        num = rffi.cast(rffi.DOUBLE, num)
        return self._ctx.c_handle_from_double(self._ctx, num)

    def handle_from_ptr(self, mu_type, ptr):
        # type: (MuID, MuCPtr) -> MuUPtrValue
        ptr = rffi.cast(MuCPtr, ptr)
        return self._ctx.c_handle_from_ptr(self._ctx, mu_type, ptr)

    def handle_from_fp(self, mu_type, fp):
        # type: (MuID, MuCFP) -> MuUFPValue
        fp = rffi.cast(MuCFP, fp)
        return self._ctx.c_handle_from_fp(self._ctx, mu_type, fp)

    def handle_to_sint8(self, opnd):
        # type: (MuIntValue) -> int
        return int(self._ctx.c_handle_to_sint8(self._ctx, opnd))

    def handle_to_uint8(self, opnd):
        # type: (MuIntValue) -> int
        return int(self._ctx.c_handle_to_uint8(self._ctx, opnd))

    def handle_to_sint16(self, opnd):
        # type: (MuIntValue) -> int
        return int(self._ctx.c_handle_to_sint16(self._ctx, opnd))

    def handle_to_uint16(self, opnd):
        # type: (MuIntValue) -> int
        return int(self._ctx.c_handle_to_uint16(self._ctx, opnd))

    def handle_to_sint32(self, opnd):
        # type: (MuIntValue) -> int
        return int(self._ctx.c_handle_to_sint32(self._ctx, opnd))

    def handle_to_uint32(self, opnd):
        # type: (MuIntValue) -> int
        return int(self._ctx.c_handle_to_uint32(self._ctx, opnd))

    def handle_to_sint64(self, opnd):
        # type: (MuIntValue) -> int
        return int(self._ctx.c_handle_to_sint64(self._ctx, opnd))

    def handle_to_uint64(self, opnd):
        # type: (MuIntValue) -> int
        return int(self._ctx.c_handle_to_uint64(self._ctx, opnd))

    def handle_to_float(self, opnd):
        # type: (MuFloatValue) -> float
        return float(self._ctx.c_handle_to_float(self._ctx, opnd))

    def handle_to_double(self, opnd):
        # type: (MuDoubleValue) -> float
        return float(self._ctx.c_handle_to_double(self._ctx, opnd))

    def handle_to_ptr(self, opnd):
        # type: (MuUPtrValue) -> MuCPtr
        return self._ctx.c_handle_to_ptr(self._ctx, opnd)

    def handle_to_fp(self, opnd):
        # type: (MuUFPValue) -> MuCFP
        return self._ctx.c_handle_to_fp(self._ctx, opnd)

    def handle_from_const(self, id):
        # type: (MuID) -> MuValue
        return self._ctx.c_handle_from_const(self._ctx, id)

    def handle_from_global(self, id):
        # type: (MuID) -> MuIRefValue
        return self._ctx.c_handle_from_global(self._ctx, id)

    def handle_from_func(self, id):
        # type: (MuID) -> MuFuncRefValue
        return self._ctx.c_handle_from_func(self._ctx, id)

    def handle_from_expose(self, id):
        # type: (MuID) -> MuValue
        return self._ctx.c_handle_from_expose(self._ctx, id)

    def delete_value(self, opnd):
        # type: (MuValue) -> None
        return self._ctx.c_delete_value(self._ctx, opnd)

    def ref_eq(self, lhs, rhs):
        # type: (MuGenRefValue, MuGenRefValue) -> bool
        return bool(self._ctx.c_ref_eq(self._ctx, lhs, rhs))

    def ref_ult(self, lhs, rhs):
        # type: (MuIRefValue, MuIRefValue) -> bool
        return bool(self._ctx.c_ref_ult(self._ctx, lhs, rhs))

    def extract_value(self, str, index):
        # type: (MuStructValue, int) -> MuValue
        return self._ctx.c_extract_value(self._ctx, str, rffi.cast(rffi.INT, index))

    def insert_value(self, str, index, newval):
        # type: (MuStructValue, int, MuValue) -> MuStructValue
        return self._ctx.c_insert_value(self._ctx, str, rffi.cast(rffi.INT, index), newval)

    def extract_element(self, str, index):
        # type: (MuSeqValue, MuIntValue) -> MuValue
        return self._ctx.c_extract_element(self._ctx, str, index)

    def insert_element(self, str, index, newval):
        # type: (MuSeqValue, MuIntValue, MuValue) -> MuSeqValue
        return self._ctx.c_insert_element(self._ctx, str, index, newval)

    def new_fixed(self, mu_type):
        # type: (MuID) -> MuRefValue
        return self._ctx.c_new_fixed(self._ctx, mu_type)

    def new_hybrid(self, mu_type, length):
        # type: (MuID, MuIntValue) -> MuRefValue
        return self._ctx.c_new_hybrid(self._ctx, mu_type, length)

    def refcast(self, opnd, new_type):
        # type: (MuGenRefValue, MuID) -> MuGenRefValue
        return self._ctx.c_refcast(self._ctx, opnd, new_type)

    def get_iref(self, opnd):
        # type: (MuRefValue) -> MuIRefValue
        return self._ctx.c_get_iref(self._ctx, opnd)

    def get_field_iref(self, opnd, field):
        # type: (MuIRefValue, int) -> MuIRefValue
        return self._ctx.c_get_field_iref(self._ctx, opnd, rffi.cast(rffi.INT, field))

    def get_elem_iref(self, opnd, index):
        # type: (MuIRefValue, MuIntValue) -> MuIRefValue
        return self._ctx.c_get_elem_iref(self._ctx, opnd, index)

    def shift_iref(self, opnd, offset):
        # type: (MuIRefValue, MuIntValue) -> MuIRefValue
        return self._ctx.c_shift_iref(self._ctx, opnd, offset)

    def get_var_part_iref(self, opnd):
        # type: (MuIRefValue) -> MuIRefValue
        return self._ctx.c_get_var_part_iref(self._ctx, opnd)

    def load(self, ord, loc):
        # type: (MuMemOrd, MuIRefValue) -> MuValue
        return self._ctx.c_load(self._ctx, ord, loc)

    def store(self, ord, loc, newval):
        # type: (MuMemOrd, MuIRefValue, MuValue) -> None
        self._ctx.c_store(self._ctx, ord, loc, newval)

    def cmpxchg(self, ord_succ, ord_fail, weak, loc, expected, desired, is_succ):
        # type: (MuMemOrd, MuMemOrd, bool, MuIRefValue, MuValue, MuValue, bool) -> MuValue
        return self._ctx.c_cmpxchg(self._ctx, ord_succ, ord_fail, rffi.cast(MuBool, weak),
                                   loc, expected, desired, rffi.cast(MuBool, is_succ))

    def atomicrmw(self, ord, op, loc, opnd):
        # type: (MuMemOrd, MuAtomicRMWOptr, MuIRefValue, MuValue) -> MuValue
        return self._ctx.c_atomicrmw(self._ctx, ord, op, loc, opnd)

    def fence(self, ord):
        # type: (MuMemOrd) -> None
        self._ctx.c_fence(self._ctx, ord)

    def new_stack(self, func):
        # type: (MuFuncRefValue) -> MuStackRefValue
        return self._ctx.c_new_stack(self._ctx, func)

    def new_thread_nor(self, stack, threadlocal, vals):
        # type: (MuStackRefValue, MuRefValue, [MuValue]) -> MuThreadRefValue
        with scoped_lst2arr(MuValue, vals) as (arr, sz):
            return self._ctx.c_new_thread_nor(self._ctx, stack, threadlocal, arr, sz)

    def new_thread_exc(self, stack, threadlocal, exc):
        # type: (MuStackRefValue, MuRefValue, MuRefValue) -> MuThreadRefValue
        return self._ctx.c_new_thread_exc(self._ctx, stack, threadlocal, exc)

    def kill_stack(self, stack):
        # type: (MuStackRefValue) -> None
        self._ctx.c_kill_stack(self._ctx, stack)

    def set_threadlocal(self, thread, threadlocal):
        # type: (MuThreadRefValue, MuRefValue) -> None
        self._ctx.c_set_threadlocal(self._ctx, thread, threadlocal)

    def get_threadlocal(self, thread):
        # type: (MuThreadRefValue) -> MuRefValue
        return self._ctx.c_get_threadlocal(self._ctx, thread)

    def new_cursor(self, stack):
        # type: (MuStackRefValue) -> MuFCRefValue
        return self._ctx.c_new_cursor(self._ctx, stack)

    def next_frame(self, cursor):
        # type: (MuFCRefValue) -> None
        self._ctx.c_next_frame(self._ctx, cursor)

    def copy_cursor(self, cursor):
        # type: (MuFCRefValue) -> MuFCRefValue
        return self._ctx.c_copy_cursor(self._ctx, cursor)

    def close_cursor(self, cursor):
        # type: (MuFCRefValue) -> None
        self._ctx.c_close_cursor(self._ctx, cursor)

    def cur_func(self, cursor):
        # type: (MuFCRefValue) -> MuID
        return self._ctx.c_cur_func(self._ctx, cursor)

    def cur_func_ver(self, cursor):
        # type: (MuFCRefValue) -> MuID
        return self._ctx.c_cur_func_ver(self._ctx, cursor)

    def cur_inst(self, cursor):
        # type: (MuFCRefValue) -> MuID
        return self._ctx.c_cur_inst(self._ctx, cursor)

    def dump_keepalives(self, cursor, results):
        # type: (MuFCRefValue, MuValue) -> None
        self._ctx.c_dump_keepalives(self._ctx, cursor, results)

    def pop_frames_to(self, cursor):
        # type: (MuFCRefValue) -> None
        self._ctx.c_pop_frames_to(self._ctx, cursor)

    def push_frame(self, stack, func):
        # type: (MuStackRefValue, MuFuncRefValue) -> None
        self._ctx.c_push_frame(self._ctx, stack, func)

    def tr64_is_fp(self, value):
        # type: (MuTagRef64Value) -> bool
        return bool(self._ctx.c_tr64_is_fp(self._ctx, value))

    def tr64_is_int(self, value):
        # type: (MuTagRef64Value) -> bool
        return bool(self._ctx.c_tr64_is_int(self._ctx, value))

    def tr64_is_ref(self, value):
        # type: (MuTagRef64Value) -> bool
        return bool(self._ctx.c_tr64_is_ref(self._ctx, value))

    def tr64_to_fp(self, value):
        # type: (MuTagRef64Value) -> MuDoubleValue
        return self._ctx.c_tr64_to_fp(self._ctx, value)

    def tr64_to_int(self, value):
        # type: (MuTagRef64Value) -> MuIntValue
        return self._ctx.c_tr64_to_int(self._ctx, value)

    def tr64_to_ref(self, value):
        # type: (MuTagRef64Value) -> MuRefValue
        return self._ctx.c_tr64_to_ref(self._ctx, value)

    def tr64_to_tag(self, value):
        # type: (MuTagRef64Value) -> MuIntValue
        return self._ctx.c_tr64_to_tag(self._ctx, value)

    def tr64_from_fp(self, value):
        # type: (MuDoubleValue) -> MuTagRef64Value
        return self._ctx.c_tr64_from_fp(self._ctx, value)

    def tr64_from_int(self, value):
        # type: (MuIntValue) -> MuTagRef64Value
        return self._ctx.c_tr64_from_int(self._ctx, value)

    def tr64_from_ref(self, ref, tag):
        # type: (MuRefValue, MuIntValue) -> MuTagRef64Value
        return self._ctx.c_tr64_from_ref(self._ctx, ref, tag)

    def enable_watchpoint(self, wpid):
        # type: (MuWPID) -> None
        self._ctx.c_enable_watchpoint(self._ctx, wpid)

    def disable_watchpoint(self, wpid):
        # type: (MuWPID) -> None
        self._ctx.c_disable_watchpoint(self._ctx, wpid)

    def pin(self, loc):
        # type: (MuValue) -> MuUPtrValue
        return self._ctx.c_pin(self._ctx, loc)

    def unpin(self, loc):
        # type: (MuValue) -> None
        self._ctx.c_unpin(self._ctx, loc)

    def expose(self, func, call_conv, cookie):
        # type: (MuFuncRefValue, MuCallConv, MuIntValue) -> MuValue
        return self._ctx.c_expose(self._ctx, func, call_conv, cookie)

    def unexpose(self, call_conv, value):
        # type: (MuCallConv, MuValue) -> None
        self._ctx.c_unexpose(self._ctx, call_conv, value)

    def new_bundle(self):
        # type: () -> MuBundleNode
        return self._ctx.c_new_bundle(self._ctx)

    def load_bundle_from_node(self, b):
        # type: (MuBundleNode) -> None
        self._ctx.c_load_bundle_from_node(self._ctx, b)

    def abort_bundle_node(self, b):
        # type: (MuBundleNode) -> None
        self._ctx.c_abort_bundle_node(self._ctx, b)

    def get_node(self, b, id):
        # type: (MuBundleNode, MuID) -> MuChildNode
        return self._ctx.c_get_node(self._ctx, b, id)

    def get_id(self, b, node):
        # type: (MuBundleNode, MuChildNode) -> MuID
        return self._ctx.c_get_id(self._ctx, b, node)

    def set_name(self, b, node, name):
        # type: (MuBundleNode, MuChildNode, str) -> None
        with rffi.scoped_str2charp(name) as buf:
            return self._ctx.c_set_name(self._ctx, b, node, buf)

    def new_type_int(self, b, len):
        # type: (MuBundleNode, int) -> MuTypeNode
        return self._ctx.c_new_type_int(self._ctx, b, rffi.cast(rffi.INT, len))

    def new_type_float(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        return self._ctx.c_new_type_float(self._ctx, b)

    def new_type_double(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        return self._ctx.c_new_type_double(self._ctx, b)

    def new_type_uptr(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        return self._ctx.c_new_type_uptr(self._ctx, b)

    def set_type_uptr(self, uptr, ty):
        # type: (MuTypeNode, MuTypeNode) -> None
        self._ctx.c_set_type_uptr(self._ctx, uptr, ty)

    def new_type_ufuncptr(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        return self._ctx.c_new_type_ufuncptr(self._ctx, b)

    def set_type_ufuncptr(self, ufuncptr, sig):
        # type: (MuTypeNode, MuFuncSigNode) -> None
        self._ctx.c_set_type_ufuncptr(self._ctx, ufuncptr, sig)

    def new_type_struct(self, b, fieldtys):
        # type: (MuBundleNode, [MuTypeNode]) -> MuTypeNode
        with scoped_lst2arr(MuTypeNode, fieldtys) as (arr, sz):
            return self._ctx.c_new_type_struct(self._ctx, b, arr, sz)

    def new_type_hybrid(self, b, fixedtys, varty):
        # type: (MuBundleNode, [MuTypeNode], MuTypeNode) -> MuTypeNode
        with scoped_lst2arr(MuTypeNode, fixedtys) as (arr, sz):
            return self._ctx.c_new_type_hybrid(self._ctx, b, arr, sz, varty)

    def new_type_array(self, b, elemty, length):
        # type: (MuBundleNode, MuTypeNode, int) -> MuTypeNode
        return self._ctx.c_new_type_array(self._ctx, b, elemty, rffi.cast(rffi.INT, length))

    def new_type_vector(self, b, elemty, length):
        # type: (MuBundleNode, MuTypeNode, int) -> MuTypeNode
        return self._ctx.c_new_type_vector(self._ctx, b, elemty, rffi.cast(rffi.INT, length))

    def new_type_void(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        return self._ctx.c_new_type_void(self._ctx, b)

    def new_type_ref(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        return self._ctx.c_new_type_ref(self._ctx, b)

    def set_type_ref(self, ref, ty):
        # type: (MuTypeNode, MuTypeNode) -> None
        self._ctx.c_set_type_ref(self._ctx, ref, ty)

    def new_type_iref(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        return self._ctx.c_new_type_iref(self._ctx, b)

    def set_type_iref(self, iref, ty):
        # type: (MuTypeNode, MuTypeNode) -> None
        self._ctx.c_set_type_iref(self._ctx, iref, ty)

    def new_type_weakref(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        return self._ctx.c_new_type_weakref(self._ctx, b)

    def set_type_weakref(self, weakref, ty):
        # type: (MuTypeNode, MuTypeNode) -> None
        self._ctx.c_set_type_weakref(self._ctx, weakref, ty)

    def new_type_funcref(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        return self._ctx.c_new_type_funcref(self._ctx, b)

    def set_type_funcref(self, funcref, sig):
        # type: (MuTypeNode, MuFuncSigNode) -> None
        return self._ctx.c_set_type_funcref(self._ctx, funcref, sig)

    def new_type_tagref64(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        return self._ctx.c_new_type_tagref64(self._ctx, b)

    def new_type_threadref(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        return self._ctx.c_new_type_threadref(self._ctx, b)

    def new_type_stackref(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        return self._ctx.c_new_type_stackref(self._ctx, b)

    def new_type_framecursorref(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        return self._ctx.c_new_type_framecursorref(self._ctx, b)

    def new_type_irnoderef(self, b):
        # type: (MuBundleNode) -> MuTypeNode
        return self._ctx.c_new_type_irnoderef(self._ctx, b)

    def new_funcsig(self, b, paramtys, rettys):
        # type: (MuBundleNode, [MuTypeNode], [MuTypeNode]) -> MuFuncSigNode
        with scoped_lst2arr(MuTypeNode, paramtys) as (prm_ts, sz_prm_ts):
            with scoped_lst2arr(MuTypeNode, rettys) as (rtn_ts, sz_rtn_ts):
                return self._ctx.c_new_funcsig(self._ctx, b, prm_ts, sz_prm_ts, rtn_ts, sz_rtn_ts)

    def new_const_int(self, b, ty, value):
        # type: (MuBundleNode, MuTypeNode, int) -> MuConstNode
        return self._ctx.c_new_const_int(self._ctx, b, ty, rffi.cast(rffi.ULONG, value))

    def new_const_int_ex(self, b, ty, values):
        # type: (MuBundleNode, MuTypeNode, [int]) -> MuConstNode
        with scoped_lst2arr(rffi.ULONG, values, need_rffi_cast=True) as (arr, sz):
            return self._ctx.c_new_const_int_ex(self._ctx, b, ty, arr, sz)

    def new_const_float(self, b, ty, value):
        # type: (MuBundleNode, MuTypeNode, float) -> MuConstNode
        return self._ctx.c_new_const_float(self._ctx, b, ty, rffi.cast(rffi.FLOAT, value))

    def new_const_double(self, b, ty, value):
        # type: (MuBundleNode, MuTypeNode, float) -> MuConstNode
        return self._ctx.c_new_const_double(self._ctx, b, ty, rffi.cast(rffi.DOUBLE, value))

    def new_const_null(self, b, ty):
        # type: (MuBundleNode, MuTypeNode) -> MuConstNode
        return self._ctx.c_new_const_null(self._ctx, b, ty)

    def new_const_seq(self, b, ty, elems):
        # type: (MuBundleNode, MuTypeNode, [MuConstNode]) -> MuConstNode
        with scoped_lst2arr(MuConstNode, elems) as (arr, sz):
            return self._ctx.c_new_const_seq(self._ctx, b, ty, arr, sz)

    def new_const_extern(self, b, ty, symbol):
        # type: (MuBundleNode, MuTypeNode, str) -> MuConstNode
        with rffi.scoped_str2charp(symbol) as buf:
            return self._ctx.c_new_const_extern(self._ctx, b, ty, buf)

    def new_global_cell(self, b, ty):
        # type: (MuBundleNode, MuTypeNode) -> MuGlobalNode
        return self._ctx.c_new_global_cell(self._ctx, b, ty)

    def new_func(self, b, sig):
        # type: (MuBundleNode, MuFuncSigNode) -> MuFuncNode
        return self._ctx.c_new_func(self._ctx, b, sig)

    def new_func_ver(self, b, func):
        # type: (MuBundleNode, MuFuncNode) -> MuFuncVerNode
        return self._ctx.c_new_func_ver(self._ctx, b, func)

    def new_exp_func(self, b, func, callconv, cookie):
        # type: (MuBundleNode, MuFuncNode, MuCallConv, MuConstNode) -> MuExpFuncNode
        return self._ctx.c_new_exp_func(self._ctx, b, func, callconv, cookie)

    def new_bb(self, fv):
        # type: (MuFuncVerNode) -> MuBBNode
        return self._ctx.c_new_bb(self._ctx, fv)

    def new_nor_param(self, bb, ty):
        # type: (MuBBNode, MuTypeNode) -> MuNorParamNode
        return self._ctx.c_new_nor_param(self._ctx, bb, ty)

    def new_exc_param(self, bb):
        # type: (MuBBNode) -> MuExcParamNode
        return self._ctx.c_new_exc_param(self._ctx, bb)

    def get_inst_res(self, inst, idx):
        # type: (MuInstNode, int) -> MuInstResNode
        return self._ctx.c_get_inst_res(self._ctx, inst, rffi.cast(rffi.INT, idx))

    def get_num_inst_res(self, inst):
        # type: (MuInstNode) -> int
        return int(self._ctx.c_get_num_inst_res(self._ctx, inst))

    def add_dest(self, inst, kind, dest, vars):
        # type: (MuInstNode, MuDestKind, MuBBNode, [MuVarNode]) -> None
        with scoped_lst2arr(MuVarNode, vars) as (arr, sz):
            self._ctx.c_add_dest(self._ctx, inst, kind, dest, arr, sz)

    def add_keepalives(self, inst, vars):
        # type: (MuInstNode, [MuLocalVarNode]) -> None
        with scoped_lst2arr(MuLocalVarNode, vars) as (arr, sz):
            self._ctx.c_add_keepalives(self._ctx, inst, vars)

    def new_binop(self, bb, optr, ty, opnd1, opnd2):
        # type: (MuBBNode, MuBinOptr, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        return self._ctx.c_new_binop(self._ctx, bb, optr, ty, opnd1, opnd2)

    def new_cmp(self, bb, optr, ty, opnd1, opnd2):
        # type: (MuBBNode, MuCmpOptr, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        return self._ctx.c_new_cmp(self._ctx, bb, optr, ty, opnd1, opnd2)

    def new_conv(self, bb, optr, from_ty, to_ty, opnd):
        # type: (MuBBNode, MuConvOptr, MuTypeNode, MuTypeNode, MuVarNode) -> MuInstNode
        return self._ctx.c_new_conv(self._ctx, bb, optr, from_ty, to_ty, opnd)

    def new_select(self, bb, cond_ty, opnd_ty, cond, if_true, if_false):
        # type: (MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> MuInstNode
        return self._ctx.c_new_select(self._ctx, bb, cond_ty, opnd_ty, cond, if_true, if_false)

    def new_branch(self, bb):
        # type: (MuBBNode) -> MuInstNode
        return self._ctx.c_new_branch(self._ctx, bb)

    def new_branch_ex(self, bb, bbDest, args):
        # type: (MuBBNode, MuBBNode, [MuVarNode]) -> MuInstNode
        op = self.new_branch(bb)
        self.add_dest(op, MuDestKind.NORMAL, bbDest, args)
        return op

    def new_branch2(self, bb, cond):
        # type: (MuBBNode, MuVarNode) -> MuInstNode
        return self._ctx.c_new_branch2(self._ctx, bb, cond)

    def new_branch2_ex(self, bb, cond, bbTrue, argsTrue, bbFalse, argsFalse):
        # type: (MuBBNode, MuVarNode, MuBBNode, [MuVarNode], MuBBNode, [MuVarNode]) -> MuInstNode
        op = self.new_branch2(bb, cond)
        self.add_dest(op, MuDestKind.TRUE, bbTrue, argsTrue)
        self.add_dest(op, MuDestKind.FALSE, bbFalse, argsFalse)
        return op

    def new_switch(self, bb, opnd_ty, opnd):
        # type: (MuBBNode, MuTypeNode, MuVarNode) -> MuInstNode
        return self._ctx.c_new_switch(self._ctx, bb, opnd_ty, opnd)

    def add_switch_dest(self, sw, key, dest, vars):
        # type: (MuInstNode, MuConstNode, MuBBNode, [MuVarNode]) -> None
        with scoped_lst2arr(MuVarNode, vars) as (arr, sz):
            self._ctx.c_add_switch_dest(self._ctx, sw, key, dest, arr, sz)

    def new_call(self, bb, sig, callee, args):
        # type: (MuBBNode, MuFuncSigNode, MuVarNode, [MuVarNode]) -> MuInstNode
        with scoped_lst2arr(MuVarNode, args) as (arr, sz):
            return self._ctx.c_new_call(self._ctx, bb, sig, callee, arr, sz)

    def new_tailcall(self, bb, sig, callee, args):
        # type: (MuBBNode, MuFuncSigNode, MuVarNode, [MuVarNode]) -> MuInstNode
        with scoped_lst2arr(MuVarNode, args) as (arr, sz):
            return self._ctx.c_new_tailcall(self._ctx, bb, sig, callee, arr, sz)

    def new_ret(self, bb, rvs):
        # type: (MuBBNode, [MuVarNode]) -> MuInstNode
        with scoped_lst2arr(MuVarNode, rvs) as (arr, sz):
            return self._ctx.c_new_ret(self._ctx, bb, arr, sz)

    def new_throw(self, bb, exc):
        # type: (MuBBNode, MuVarNode) -> MuInstNode
        return self._ctx.c_new_throw(self._ctx, bb, exc)

    def new_extractvalue(self, bb, strty, index, opnd):
        # type: (MuBBNode, MuTypeNode, int, MuVarNode) -> MuInstNode
        return self._ctx.c_new_extractvalue(self._ctx, bb, strty, rffi.cast(rffi.INT, index), opnd)

    def new_insertvalue(self, bb, strty, index, opnd, newval):
        # type: (MuBBNode, MuTypeNode, int, MuVarNode, MuVarNode) -> MuInstNode
        return self._ctx.c_new_insertvalue(self._ctx, bb, strty, rffi.cast(rffi.INT, index), opnd, newval)

    def new_extractelement(self, bb, seqty, indty, opnd, index):
        # type: (MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        return self._ctx.c_new_extractelement(self._ctx, bb, seqty, indty, opnd, index)

    def new_insertelement(self, bb, seqty, indty, opnd, index, newval):
        # type: (MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> MuInstNode
        return self._ctx.c_new_insertelement(self._ctx, bb, seqty, indty, opnd, index, newval)

    def new_shufflevector(self, bb, vecty, maskty, vec1, vec2, mask):
        # type: (MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> MuInstNode
        return self._ctx.c_new_shufflevector(self._ctx, bb, vecty, maskty, vec1, vec2, mask)

    def new_new(self, bb, allocty):
        # type: (MuBBNode, MuTypeNode) -> MuInstNode
        return self._ctx.c_new_new(self._ctx, bb, allocty)

    def new_newhybrid(self, bb, allocty, lenty, length):
        # type: (MuBBNode, MuTypeNode, MuTypeNode, MuVarNode) -> MuInstNode
        return self._ctx.c_new_newhybrid(self._ctx, bb, allocty, lenty, length)

    def new_alloca(self, bb, allocty):
        # type: (MuBBNode, MuTypeNode) -> MuInstNode
        return self._ctx.c_new_alloca(self._ctx, bb, allocty)

    def new_allocahybrid(self, bb, allocty, lenty, length):
        # type: (MuBBNode, MuTypeNode, MuTypeNode, MuVarNode) -> MuInstNode
        return self._ctx.c_new_allocahybrid(self._ctx, bb, allocty, lenty, length)

    def new_getiref(self, bb, refty, opnd):
        # type: (MuBBNode, MuTypeNode, MuVarNode) -> MuInstNode
        return self._ctx.c_new_getiref(self._ctx, bb, refty, opnd)

    def new_getfieldiref(self, bb, is_ptr, refty, index, opnd):
        # type: (MuBBNode, bool, MuTypeNode, int, MuVarNode) -> MuInstNode
        return self._ctx.c_new_getfieldiref(self._ctx, bb, rffi.cast(MuBool, is_ptr),
                                            refty, rffi.cast(rffi.INT, index), opnd)

    def new_getelemiref(self, bb, is_ptr, refty, indty, opnd, index):
        # type: (MuBBNode, bool, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        return self._ctx.c_new_getelemiref(self._ctx, bb, rffi.cast(MuBool, is_ptr), refty, indty, opnd, index)

    def new_shiftiref(self, bb, is_ptr, refty, offty, opnd, offset):
        # type: (MuBBNode, bool, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        return self._ctx.c_new_shiftiref(self._ctx, bb, rffi.cast(MuBool, is_ptr), refty, offty, opnd, offset)

    def new_getvarpartiref(self, bb, is_ptr, refty, opnd):
        # type: (MuBBNode, bool, MuTypeNode, MuVarNode) -> MuInstNode
        return self._ctx.c_new_getvarpartiref(self._ctx, bb, rffi.cast(MuBool, is_ptr), refty, opnd)

    def new_load(self, bb, is_ptr, ord, refty, loc):
        # type: (MuBBNode, bool, MuMemOrd, MuTypeNode, MuVarNode) -> MuInstNode
        return self._ctx.c_new_load(self._ctx, bb, rffi.cast(MuBool, is_ptr), ord, refty, loc)

    def new_store(self, bb, is_ptr, ord, refty, loc, newval):
        # type: (MuBBNode, bool, MuMemOrd, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        return self._ctx.c_new_store(self._ctx, bb, rffi.cast(MuBool, is_ptr), ord, refty, loc, newval)

    def new_cmpxchg(self, bb, is_ptr, is_weak, ord_succ, ord_fail, refty, loc, expected, desired):
        # type: (MuBBNode, bool, bool, MuMemOrd, MuMemOrd, MuTypeNode, MuVarNode, MuVarNode, MuVarNode) -> MuInstNode
        return self._ctx.c_new_cmpxchg(self._ctx, bb, rffi.cast(MuBool, is_ptr), rffi.cast(MuBool, is_weak),
                                       ord_succ, ord_fail, refty, loc, expected, desired)

    def new_atomicrmw(self, bb, is_ptr, ord, optr, refTy, loc, opnd):
        # type: (MuBBNode, bool, MuMemOrd, MuAtomicRMWOptr, MuTypeNode, MuVarNode, MuVarNode) -> MuInstNode
        return self._ctx.c_new_atomicrmw(self._ctx, bb, rffi.cast(MuBool, is_ptr), ord, optr, refTy, loc, opnd)

    def new_fence(self, bb, ord):
        # type: (MuBBNode, MuMemOrd) -> MuInstNode
        return self._ctx.c_new_fence(self._ctx, bb, ord)

    def new_trap(self, bb, rettys):
        # type: (MuBBNode, [MuTypeNode]) -> MuInstNode
        with scoped_lst2arr(MuTypeNode, rettys) as (arr, sz):
            return self._ctx.c_new_trap(self._ctx, bb, arr, sz)

    def new_watchpoint(self, bb, wpid, rettys):
        # type: (MuBBNode, MuWPID, [MuTypeNode]) -> MuInstNode
        with scoped_lst2arr(MuTypeNode, rettys) as (arr, sz):
            return self._ctx.c_new_watchpoint(self._ctx, bb, wpid, arr, sz)

    def new_wpbranch(self, bb, wpid):
        # type: (MuBBNode, MuWPID) -> MuInstNode
        return self._ctx.c_new_wpbranch(self._ctx, bb, wpid)

    def new_wpbranch_ex(self, bb, wpid, bbDisable, argsDisable, bbEnable, argsEnable):
        # type: (MuBBNode, MuWPID, MuBBNode, [MuVarNode], MuBBNode, [MuVarNode]) -> MuInstNode
        op = self.new_wpbranch(bb, wpid)
        self.add_dest(op, MuDestKind.DISABLED, bbDisable, argsDisable)
        self.add_dest(op, MuDestKind.ENABLED, bbEnable, argsEnable)
        return op

    def new_ccall(self, bb, callconv, callee_ty, sig, callee, args):
        # type: (MuBBNode, MuCallConv, MuTypeNode, MuFuncSigNode, MuVarNode, [MuVarNode]) -> MuInstNode
        with scoped_lst2arr(MuVarNode, args) as (arr, sz):
            return self._ctx.c_new_ccall(self._ctx, bb, callconv, callee_ty, sig, callee, arr, sz)

    def new_newthread(self, bb, stack, threadlocal):
        # type: (MuBBNode, MuVarNode, MuVarNode) -> MuInstNode
        return self._ctx.c_new_newthread(self._ctx, bb, stack, threadlocal)

    def new_swapstack_ret(self, bb, swappee, ret_tys):
        # type: (MuBBNode, MuVarNode, [MuTypeNode]) -> MuInstNode
        with scoped_lst2arr(MuTypeNode, ret_tys) as (arr, sz):
            return self._ctx.c_new_swapstack_ret(self._ctx, bb, swappee, arr, sz)

    def new_swapstack_kill(self, bb, swappee):
        # type: (MuBBNode, MuVarNode) -> MuInstNode
        return self._ctx.c_new_swapstack_kill(self._ctx, bb, swappee)

    def set_newstack_pass_values(self, inst, tys, vars):
        # type: (MuInstNode, [MuTypeNode], [MuVarNode]) -> None
        with scoped_lst2arr(MuTypeNode, tys) as (arr_tys, sz_tys):
            with scoped_lst2arr(MuVarNode, vars) as (arr_vars, sz_vars):
                return self._ctx.c_set_newstack_pass_values(self._ctx, inst, arr_tys, arr_vars, sz_tys)

    def set_newstack_throw_exc(self, inst, exc):
        # type: (MuInstNode, MuVarNode) -> None
        return self._ctx.c_set_newstack_throw_exc(self._ctx, inst, exc)

    def new_comminst(self, bb, opcode, flags, tys, sigs, args):
        # type: (MuBBNode, MuCommInst, [MuFlag], [MuTypeNode], [MuFuncSigNode], [MuVarNode]) -> MuInstNode
        with scoped_lst2arr(MuFlag, flags) as (arr_flags, sz_flags):
            with scoped_lst2arr(MuTypeNode, tys) as (arr_tys, sz_tys):
                with scoped_lst2arr(MuFuncSigNode, sigs) as (arr_sigs, sz_sigs):
                    with scoped_lst2arr(MuVarNode, args) as (arr_args, sz_args):
                        return self._ctx.c_new_comminst(self._ctx, bb, opcode,
                                                        arr_flags, sz_flags,
                                                        arr_tys, sz_tys,
                                                        arr_sigs, sz_sigs,
                                                        arr_args, sz_args)

# --------------------------------
# Flags
class _MuFlagWrapper:
    _lltype = rffi.UINT     # MuFlag type
    def __init__(self, **value_dic):
        for key, val in value_dic.items():
            setattr(self, key, rffi.cast(_MuFlagWrapper._lltype, val))


MuTrapHandlerResult = _MuFlagWrapper(
    THREAD_EXIT = 0x00,
    REBIND_PASS_VALUES = 0x01,
    REBIND_THROW_EXC = 0x02,
)

MuDestKind = _MuFlagWrapper(
    NORMAL= 0x01,
    EXCEPT = 0x02,
    TRUE = 0x03,
    FALSE = 0x04,
    DEFAULT = 0x05,
    DISABLED = 0x06,
    ENABLED = 0x07,
)

MuBinOptr = _MuFlagWrapper(
    ADD = 0x01,
    SUB = 0x02,
    MUL = 0x03,
    SDIV = 0x04,
    SREM = 0x05,
    UDIV = 0x06,
    UREM = 0x07,
    SHL = 0x08,
    LSHR = 0x09,
    ASHR = 0x0A,
    AND = 0x0B,
    OR = 0x0C,
    XOR = 0x0D,
    FADD = 0xB0,
    FSUB = 0xB1,
    FMUL = 0xB2,
    FDIV = 0xB3,
    FREM = 0xB4,
)

MuCmpOptr = _MuFlagWrapper(
    EQ = 0x20,
    NE = 0x21,
    SGE = 0x22,
    SGT = 0x23,
    SLE = 0x24,
    SLT = 0x25,
    UGE = 0x26,
    UGT = 0x27,
    ULE = 0x28,
    ULT = 0x29,
    FFALSE = 0xC0,
    FTRUE = 0xC1,
    FUNO = 0xC2,
    FUEQ = 0xC3,
    FUNE = 0xC4,
    FUGT = 0xC5,
    FUGE = 0xC6,
    FULT = 0xC7,
    FULE = 0xC8,
    FORD = 0xC9,
    FOEQ = 0xCA,
    FONE = 0xCB,
    FOGT = 0xCC,
    FOGE = 0xCD,
    FOLT = 0xCE,
    FOLE = 0xCF,
)

MuConvOptr = _MuFlagWrapper(
    TRUNC = 0x30,
    ZEXT = 0x31,
    SEXT = 0x32,
    FPTRUNC = 0x33,
    FPEXT = 0x34,
    FPTOUI = 0x35,
    FPTOSI = 0x36,
    UITOFP = 0x37,
    SITOFP = 0x38,
    BITCAST = 0x39,
    REFCAST = 0x3A,
    PTRCAST = 0x3B,
)

MuMemOrd = _MuFlagWrapper(
    NOT_ATOMIC = 0x00,
    RELAXED = 0x01,
    CONSUME = 0x02,
    ACQUIRE = 0x03,
    RELEASE = 0x04,
    ACQ_REL = 0x05,
    SEQ_CST = 0x06,
)

MuAtomicRMWOptr = _MuFlagWrapper(
    XCHG = 0x00,
    ADD = 0x01,
    SUB = 0x02,
    AND = 0x03,
    NAND = 0x04,
    OR = 0x05,
    XOR = 0x06,
    MAX = 0x07,
    MIN = 0x08,
    UMAX = 0x09,
    UMIN = 0x0A,
)

MuCallConv = _MuFlagWrapper(DEFAULT = 0x00)

MuCommInst = _MuFlagWrapper(
    UVM_NEW_STACK = 0x201,
    UVM_KILL_STACK = 0x202,
    UVM_THREAD_EXIT = 0x203,
    UVM_CURRENT_STACK = 0x204,
    UVM_SET_THREADLOCAL = 0x205,
    UVM_GET_THREADLOCAL = 0x206,
    UVM_TR64_IS_FP = 0x211,
    UVM_TR64_IS_INT = 0x212,
    UVM_TR64_IS_REF = 0x213,
    UVM_TR64_FROM_FP = 0x214,
    UVM_TR64_FROM_INT = 0x215,
    UVM_TR64_FROM_REF = 0x216,
    UVM_TR64_TO_FP = 0x217,
    UVM_TR64_TO_INT = 0x218,
    UVM_TR64_TO_REF = 0x219,
    UVM_TR64_TO_TAG = 0x21a,
    UVM_FUTEX_WAIT = 0x220,
    UVM_FUTEX_WAIT_TIMEOUT = 0x221,
    UVM_FUTEX_WAKE = 0x222,
    UVM_FUTEX_CMP_REQUEUE = 0x223,
    UVM_KILL_DEPENDENCY = 0x230,
    UVM_NATIVE_PIN = 0x240,
    UVM_NATIVE_UNPIN = 0x241,
    UVM_NATIVE_EXPOSE = 0x242,
    UVM_NATIVE_UNEXPOSE = 0x243,
    UVM_NATIVE_GET_COOKIE = 0x244,
    UVM_META_ID_OF = 0x250,
    UVM_META_NAME_OF = 0x251,
    UVM_META_LOAD_BUNDLE = 0x252,
    UVM_META_LOAD_HAIL = 0x253,
    UVM_META_NEW_CURSOR = 0x254,
    UVM_META_NEXT_FRAME = 0x255,
    UVM_META_COPY_CURSOR = 0x256,
    UVM_META_CLOSE_CURSOR = 0x257,
    UVM_META_CUR_FUNC = 0x258,
    UVM_META_CUR_FUNC_VER = 0x259,
    UVM_META_CUR_INST = 0x25a,
    UVM_META_DUMP_KEEPALIVES = 0x25b,
    UVM_META_POP_FRAMES_TO = 0x25c,
    UVM_META_PUSH_FRAME = 0x25d,
    UVM_META_ENABLE_WATCHPOINT = 0x25e,
    UVM_META_DISABLE_WATCHPOINT = 0x25f,
    UVM_META_SET_TRAP_HANDLER = 0x260,
    UVM_IRBUILDER_NEW_BUNDLE = 0x300,
    UVM_IRBUILDER_LOAD_BUNDLE_FROM_NODE = 0x301,
    UVM_IRBUILDER_ABORT_BUNDLE_NODE = 0x302,
    UVM_IRBUILDER_GET_NODE = 0x303,
    UVM_IRBUILDER_GET_ID = 0x304,
    UVM_IRBUILDER_SET_NAME = 0x305,
    UVM_IRBUILDER_NEW_TYPE_INT = 0x306,
    UVM_IRBUILDER_NEW_TYPE_FLOAT = 0x307,
    UVM_IRBUILDER_NEW_TYPE_DOUBLE = 0x308,
    UVM_IRBUILDER_NEW_TYPE_UPTR = 0x309,
    UVM_IRBUILDER_SET_TYPE_UPTR = 0x30a,
    UVM_IRBUILDER_NEW_TYPE_UFUNCPTR = 0x30b,
    UVM_IRBUILDER_SET_TYPE_UFUNCPTR = 0x30c,
    UVM_IRBUILDER_NEW_TYPE_STRUCT = 0x30d,
    UVM_IRBUILDER_NEW_TYPE_HYBRID = 0x30e,
    UVM_IRBUILDER_NEW_TYPE_ARRAY = 0x30f,
    UVM_IRBUILDER_NEW_TYPE_VECTOR = 0x310,
    UVM_IRBUILDER_NEW_TYPE_VOID = 0x311,
    UVM_IRBUILDER_NEW_TYPE_REF = 0x312,
    UVM_IRBUILDER_SET_TYPE_REF = 0x313,
    UVM_IRBUILDER_NEW_TYPE_IREF = 0x314,
    UVM_IRBUILDER_SET_TYPE_IREF = 0x315,
    UVM_IRBUILDER_NEW_TYPE_WEAKREF = 0x316,
    UVM_IRBUILDER_SET_TYPE_WEAKREF = 0x317,
    UVM_IRBUILDER_NEW_TYPE_FUNCREF = 0x318,
    UVM_IRBUILDER_SET_TYPE_FUNCREF = 0x319,
    UVM_IRBUILDER_NEW_TYPE_TAGREF64 = 0x31a,
    UVM_IRBUILDER_NEW_TYPE_THREADREF = 0x31b,
    UVM_IRBUILDER_NEW_TYPE_STACKREF = 0x31c,
    UVM_IRBUILDER_NEW_TYPE_FRAMECURSORREF = 0x31d,
    UVM_IRBUILDER_NEW_TYPE_IRNODEREF = 0x31e,
    UVM_IRBUILDER_NEW_FUNCSIG = 0x31f,
    UVM_IRBUILDER_NEW_CONST_INT = 0x320,
    UVM_IRBUILDER_NEW_CONST_INT_EX = 0x321,
    UVM_IRBUILDER_NEW_CONST_FLOAT = 0x322,
    UVM_IRBUILDER_NEW_CONST_DOUBLE = 0x323,
    UVM_IRBUILDER_NEW_CONST_NULL = 0x324,
    UVM_IRBUILDER_NEW_CONST_SEQ = 0x325,
    UVM_IRBUILDER_NEW_GLOBAL_CELL = 0x326,
    UVM_IRBUILDER_NEW_FUNC = 0x327,
    UVM_IRBUILDER_NEW_FUNC_VER = 0x328,
    UVM_IRBUILDER_NEW_EXP_FUNC = 0x329,
    UVM_IRBUILDER_NEW_BB = 0x32a,
    UVM_IRBUILDER_NEW_NOR_PARAM = 0x32b,
    UVM_IRBUILDER_NEW_EXC_PARAM = 0x32c,
    UVM_IRBUILDER_NEW_INST_RES = 0x32d,
    UVM_IRBUILDER_ADD_DEST = 0x32e,
    UVM_IRBUILDER_ADD_KEEPALIVES = 0x32f,
    UVM_IRBUILDER_NEW_BINOP = 0x330,
    UVM_IRBUILDER_NEW_CMP = 0x331,
    UVM_IRBUILDER_NEW_CONV = 0x332,
    UVM_IRBUILDER_NEW_SELECT = 0x333,
    UVM_IRBUILDER_NEW_BRANCH = 0x334,
    UVM_IRBUILDER_NEW_BRANCH2 = 0x335,
    UVM_IRBUILDER_NEW_SWITCH = 0x336,
    UVM_IRBUILDER_ADD_SWITCH_DEST = 0x337,
    UVM_IRBUILDER_NEW_CALL = 0x338,
    UVM_IRBUILDER_NEW_TAILCALL = 0x339,
    UVM_IRBUILDER_NEW_RET = 0x33a,
    UVM_IRBUILDER_NEW_THROW = 0x33b,
    UVM_IRBUILDER_NEW_EXTRACTVALUE = 0x33c,
    UVM_IRBUILDER_NEW_INSERTVALUE = 0x33d,
    UVM_IRBUILDER_NEW_EXTRACTELEMENT = 0x33e,
    UVM_IRBUILDER_NEW_INSERTELEMENT = 0x33f,
    UVM_IRBUILDER_NEW_SHUFFLEVECTOR = 0x340,
    UVM_IRBUILDER_NEW_NEW = 0x341,
    UVM_IRBUILDER_NEW_NEWHYBRID = 0x342,
    UVM_IRBUILDER_NEW_ALLOCA = 0x343,
    UVM_IRBUILDER_NEW_ALLOCAHYBRID = 0x344,
    UVM_IRBUILDER_NEW_GETIREF = 0x345,
    UVM_IRBUILDER_NEW_GETFIELDIREF = 0x346,
    UVM_IRBUILDER_NEW_GETELEMIREF = 0x347,
    UVM_IRBUILDER_NEW_SHIFTIREF = 0x348,
    UVM_IRBUILDER_NEW_GETVARPARTIREF = 0x349,
    UVM_IRBUILDER_NEW_LOAD = 0x34a,
    UVM_IRBUILDER_NEW_STORE = 0x34b,
    UVM_IRBUILDER_NEW_CMPXCHG = 0x34c,
    UVM_IRBUILDER_NEW_ATOMICRMW = 0x34d,
    UVM_IRBUILDER_NEW_FENCE = 0x34e,
    UVM_IRBUILDER_NEW_TRAP = 0x34f,
    UVM_IRBUILDER_NEW_WATCHPOINT = 0x350,
    UVM_IRBUILDER_NEW_WPBRANCH = 0x351,
    UVM_IRBUILDER_NEW_CCALL = 0x352,
    UVM_IRBUILDER_NEW_NEWTHREAD = 0x353,
    UVM_IRBUILDER_NEW_SWAPSTACK_RET = 0x354,
    UVM_IRBUILDER_NEW_SWAPSTACK_KILL = 0x355,
    UVM_IRBUILDER_SET_NEWSTACK_PASS_VALUES = 0x356,
    UVM_IRBUILDER_SET_NEWSTACK_THROW_EXC = 0x357,
    UVM_IRBUILDER_NEW_COMMINST = 0x358,
)


# -------------------------------------------------------------------------------------------------------
# Types
_fnp = rffi.CCallback

MuValue = rffi.VOIDP
MuValuePtr = rffi.VOIDPP
MuID = rffi.UINT        # uint32_t
MuIDPtr = rffi.UINTP
MuName = rffi.CCHARP
MuNamePtr = rffi.CCHARPP
MuCPtr = rffi.VOIDP
MuCPtrPtr = rffi.VOIDPP
# MuCFP = _fnp([], lltype.Void)
MuCFP = rffi.VOIDP
MuCFPPtr = rffi.CArrayPtr(MuCFP)
MuBool = rffi.INT
MuBoolPtr = rffi.INTP
MuArraySize = rffi.UINTPTR_T
MuArraySizePtr = rffi.UINTPTR_TP
MuWPID = rffi.UINT
MuWPIDPtr = rffi.UINTP
MuFlag = rffi.UINT
MuFlagPtr = rffi.UINTP
MuValuesFreer = _fnp([MuValuePtr, MuCPtr], lltype.Void)

MuSeqValue = MuValue
MuGenRefValue = MuValue

MuIntValue = MuValue
MuFloatValue = MuValue
MuDoubleValue = MuValue
MuUPtrValue = MuValue
MuUFPValue = MuValue

MuStructValue = MuSeqValue
MuArrayValue = MuSeqValue
MuVectorValue = MuSeqValue

MuRefValue = MuGenRefValue
MuIRefValue = MuGenRefValue
MuTagRef64Value = MuGenRefValue
MuFuncRefValue = MuGenRefValue
MuThreadRefValue = MuGenRefValue
MuStackRefValue = MuGenRefValue
MuFCRefValue = MuGenRefValue
MuIRNodeRefValue = MuGenRefValue


MuIRNode = MuIRNodeRefValue
MuBundleNode = MuIRNode
MuChildNode = MuIRNode
MuTypeNode = MuChildNode
MuFuncSigNode = MuChildNode
MuVarNode = MuChildNode
MuGlobalVarNode = MuVarNode
MuConstNode = MuGlobalVarNode
MuGlobalNode = MuGlobalVarNode 
MuFuncNode = MuGlobalVarNode
MuExpFuncNode = MuGlobalVarNode
MuLocalVarNode = MuVarNode
MuNorParamNode = MuLocalVarNode
MuExcParamNode = MuLocalVarNode
MuInstResNode = MuLocalVarNode 
MuFuncVerNode = MuChildNode
MuBBNode = MuChildNode
MuInstNode = MuChildNode

MuIRNodePtr = rffi.CArrayPtr(MuIRNode)
MuBundleNodePtr = rffi.CArrayPtr(MuBundleNode)
MuChildNodePtr = rffi.CArrayPtr(MuChildNode)
MuTypeNodePtr = rffi.CArrayPtr(MuTypeNode)
MuFuncSigNodePtr = rffi.CArrayPtr(MuFuncSigNode)
MuVarNodePtr = rffi.CArrayPtr(MuVarNode)
MuGlobalVarNodePtr = rffi.CArrayPtr(MuGlobalVarNode)
MuConstNodePtr = rffi.CArrayPtr(MuConstNode)
MuGlobalNodePtr = rffi.CArrayPtr(MuGlobalNode)
MuFuncNodePtr = rffi.CArrayPtr(MuFuncNode)
MuExpFuncNodePtr = rffi.CArrayPtr(MuExpFuncNode)
MuLocalVarNodePtr = rffi.CArrayPtr(MuLocalVarNode)
MuNorParamNodePtr = rffi.CArrayPtr(MuNorParamNode)
MuExcParamNodePtr = rffi.CArrayPtr(MuExcParamNode)
MuInstResNodePtr = rffi.CArrayPtr(MuInstResNode)
MuFuncVerNodePtr = rffi.CArrayPtr(MuFuncVerNode)
MuBBNodePtr = rffi.CArrayPtr(MuBBNode)
MuInstNodePtr = rffi.CArrayPtr(MuInstNode)

MuTrapHandlerResultPtr = rffi.CArrayPtr(MuFlag)
MuStackRefValuePtr = rffi.CArrayPtr(MuStackRefValue)
MuValuesFreerPtr = rffi.CArrayPtr(MuValuesFreer)
MuRefValuePtr = rffi.CArrayPtr(MuRefValue)


MuVM = lltype.ForwardReference()
MuCtx = lltype.ForwardReference()
MuVMPtr = lltype.Ptr(MuVM)
MuCtxPtr = lltype.Ptr(MuCtx)

MuTrapHandler = _fnp([
    MuCtxPtr, MuThreadRefValue, MuStackRefValue, MuWPID,   # input
    MuTrapHandlerResultPtr, MuStackRefValuePtr, rffi.CArray(MuValuePtr), MuArraySizePtr, 
    MuValuesFreerPtr, MuCPtrPtr, MuRefValuePtr,             # output
    MuCPtr  #input
], lltype.Void)

MuVM.become(rffi.CStruct(
    'MuVM',
    ('header', rffi.VOIDP),
    ('new_context', _fnp([MuVMPtr], MuCtxPtr)),
    ('id_of', _fnp([MuVMPtr, MuName], MuID)),
    ('name_of', _fnp([MuVMPtr, MuID], MuName)),
    ('set_trap_handler', _fnp([MuVMPtr, MuTrapHandler, MuCPtr], lltype.Void)),
    ('make_boot_image', _fnp([MuVMPtr, MuIDPtr, MuArraySize, rffi.CCHARP], lltype.Void)),
    ('execute', _fnp([MuVMPtr], lltype.Void)),
    ('get_mu_error_ptr', _fnp([MuVMPtr], rffi.INTP))
))

MuCtx.become(rffi.CStruct(
    'MuCtx',
    ('header', rffi.VOIDP),
    ('id_of', rffi.CCallback([MuCtxPtr, MuName], MuID)),
    ('name_of', rffi.CCallback([MuCtxPtr, MuID], MuName)),
    ('close_context', rffi.CCallback([MuCtxPtr], lltype.Void)),
    ('load_bundle', rffi.CCallback([MuCtxPtr, rffi.CCHARP, MuArraySize], lltype.Void)),
    ('load_hail', rffi.CCallback([MuCtxPtr, rffi.CCHARP, MuArraySize], lltype.Void)),
    ('handle_from_sint8', rffi.CCallback([MuCtxPtr, rffi.CHAR, rffi.INT], MuIntValue)),
    ('handle_from_uint8', rffi.CCallback([MuCtxPtr, rffi.UCHAR, rffi.INT], MuIntValue)),
    ('handle_from_sint16', rffi.CCallback([MuCtxPtr, rffi.SHORT, rffi.INT], MuIntValue)),
    ('handle_from_uint16', rffi.CCallback([MuCtxPtr, rffi.USHORT, rffi.INT], MuIntValue)),
    ('handle_from_sint32', rffi.CCallback([MuCtxPtr, rffi.INT, rffi.INT], MuIntValue)),
    ('handle_from_uint32', rffi.CCallback([MuCtxPtr, rffi.UINT, rffi.INT], MuIntValue)),
    ('handle_from_sint64', rffi.CCallback([MuCtxPtr, rffi.LONG, rffi.INT], MuIntValue)),
    ('handle_from_uint64', rffi.CCallback([MuCtxPtr, rffi.ULONG, rffi.INT], MuIntValue)),
    ('handle_from_uint64s', rffi.CCallback([MuCtxPtr, rffi.ULONGP, MuArraySize, rffi.INT], MuIntValue)),
    ('handle_from_float', rffi.CCallback([MuCtxPtr, rffi.FLOAT], MuFloatValue)),
    ('handle_from_double', rffi.CCallback([MuCtxPtr, rffi.DOUBLE], MuDoubleValue)),
    ('handle_from_ptr', rffi.CCallback([MuCtxPtr, MuID, MuCPtr], MuUPtrValue)),
    ('handle_from_fp', rffi.CCallback([MuCtxPtr, MuID, MuCFP], MuUFPValue)),
    ('handle_to_sint8', rffi.CCallback([MuCtxPtr, MuIntValue], rffi.CHAR)),
    ('handle_to_uint8', rffi.CCallback([MuCtxPtr, MuIntValue], rffi.UCHAR)),
    ('handle_to_sint16', rffi.CCallback([MuCtxPtr, MuIntValue], rffi.SHORT)),
    ('handle_to_uint16', rffi.CCallback([MuCtxPtr, MuIntValue], rffi.USHORT)),
    ('handle_to_sint32', rffi.CCallback([MuCtxPtr, MuIntValue], rffi.INT)),
    ('handle_to_uint32', rffi.CCallback([MuCtxPtr, MuIntValue], rffi.UINT)),
    ('handle_to_sint64', rffi.CCallback([MuCtxPtr, MuIntValue], rffi.LONG)),
    ('handle_to_uint64', rffi.CCallback([MuCtxPtr, MuIntValue], rffi.ULONG)),
    ('handle_to_float', rffi.CCallback([MuCtxPtr, MuFloatValue], rffi.FLOAT)),
    ('handle_to_double', rffi.CCallback([MuCtxPtr, MuDoubleValue], rffi.DOUBLE)),
    ('handle_to_ptr', rffi.CCallback([MuCtxPtr, MuUPtrValue], MuCPtr)),
    ('handle_to_fp', rffi.CCallback([MuCtxPtr, MuUFPValue], MuCFP)),
    ('handle_from_const', rffi.CCallback([MuCtxPtr, MuID], MuValue)),
    ('handle_from_global', rffi.CCallback([MuCtxPtr, MuID], MuIRefValue)),
    ('handle_from_func', rffi.CCallback([MuCtxPtr, MuID], MuFuncRefValue)),
    ('handle_from_expose', rffi.CCallback([MuCtxPtr, MuID], MuValue)),
    ('delete_value', rffi.CCallback([MuCtxPtr, MuValue], lltype.Void)),
    ('ref_eq', rffi.CCallback([MuCtxPtr, MuGenRefValue, MuGenRefValue], MuBool)),
    ('ref_ult', rffi.CCallback([MuCtxPtr, MuIRefValue, MuIRefValue], MuBool)),
    ('extract_value', rffi.CCallback([MuCtxPtr, MuStructValue, rffi.INT], MuValue)),
    ('insert_value', rffi.CCallback([MuCtxPtr, MuStructValue, rffi.INT, MuValue], MuStructValue)),
    ('extract_element', rffi.CCallback([MuCtxPtr, MuSeqValue, MuIntValue], MuValue)),
    ('insert_element', rffi.CCallback([MuCtxPtr, MuSeqValue, MuIntValue, MuValue], MuSeqValue)),
    ('new_fixed', rffi.CCallback([MuCtxPtr, MuID], MuRefValue)),
    ('new_hybrid', rffi.CCallback([MuCtxPtr, MuID, MuIntValue], MuRefValue)),
    ('refcast', rffi.CCallback([MuCtxPtr, MuGenRefValue, MuID], MuGenRefValue)),
    ('get_iref', rffi.CCallback([MuCtxPtr, MuRefValue], MuIRefValue)),
    ('get_field_iref', rffi.CCallback([MuCtxPtr, MuIRefValue, rffi.INT], MuIRefValue)),
    ('get_elem_iref', rffi.CCallback([MuCtxPtr, MuIRefValue, MuIntValue], MuIRefValue)),
    ('shift_iref', rffi.CCallback([MuCtxPtr, MuIRefValue, MuIntValue], MuIRefValue)),
    ('get_var_part_iref', rffi.CCallback([MuCtxPtr, MuIRefValue], MuIRefValue)),
    ('load', rffi.CCallback([MuCtxPtr, MuMemOrd._lltype, MuIRefValue], MuValue)),
    ('store', rffi.CCallback([MuCtxPtr, MuMemOrd._lltype, MuIRefValue, MuValue], lltype.Void)),
    ('cmpxchg',
     rffi.CCallback([MuCtxPtr, MuMemOrd._lltype, MuMemOrd._lltype, MuBool, MuIRefValue, MuValue, MuValue, MuBoolPtr],
                    MuValue)),
    (
    'atomicrmw', rffi.CCallback([MuCtxPtr, MuMemOrd._lltype, MuAtomicRMWOptr._lltype, MuIRefValue, MuValue], MuValue)),
    ('fence', rffi.CCallback([MuCtxPtr, MuMemOrd._lltype], lltype.Void)),
    ('new_stack', rffi.CCallback([MuCtxPtr, MuFuncRefValue], MuStackRefValue)),
    ('new_thread_nor',
     rffi.CCallback([MuCtxPtr, MuStackRefValue, MuRefValue, MuValuePtr, MuArraySize], MuThreadRefValue)),
    ('new_thread_exc', rffi.CCallback([MuCtxPtr, MuStackRefValue, MuRefValue, MuRefValue], MuThreadRefValue)),
    ('kill_stack', rffi.CCallback([MuCtxPtr, MuStackRefValue], lltype.Void)),
    ('set_threadlocal', rffi.CCallback([MuCtxPtr, MuThreadRefValue, MuRefValue], lltype.Void)),
    ('get_threadlocal', rffi.CCallback([MuCtxPtr, MuThreadRefValue], MuRefValue)),
    ('new_cursor', rffi.CCallback([MuCtxPtr, MuStackRefValue], MuFCRefValue)),
    ('next_frame', rffi.CCallback([MuCtxPtr, MuFCRefValue], lltype.Void)),
    ('copy_cursor', rffi.CCallback([MuCtxPtr, MuFCRefValue], MuFCRefValue)),
    ('close_cursor', rffi.CCallback([MuCtxPtr, MuFCRefValue], lltype.Void)),
    ('cur_func', rffi.CCallback([MuCtxPtr, MuFCRefValue], MuID)),
    ('cur_func_ver', rffi.CCallback([MuCtxPtr, MuFCRefValue], MuID)),
    ('cur_inst', rffi.CCallback([MuCtxPtr, MuFCRefValue], MuID)),
    ('dump_keepalives', rffi.CCallback([MuCtxPtr, MuFCRefValue, MuValuePtr], lltype.Void)),
    ('pop_frames_to', rffi.CCallback([MuCtxPtr, MuFCRefValue], lltype.Void)),
    ('push_frame', rffi.CCallback([MuCtxPtr, MuStackRefValue, MuFuncRefValue], lltype.Void)),
    ('tr64_is_fp', rffi.CCallback([MuCtxPtr, MuTagRef64Value], MuBool)),
    ('tr64_is_int', rffi.CCallback([MuCtxPtr, MuTagRef64Value], MuBool)),
    ('tr64_is_ref', rffi.CCallback([MuCtxPtr, MuTagRef64Value], MuBool)),
    ('tr64_to_fp', rffi.CCallback([MuCtxPtr, MuTagRef64Value], MuDoubleValue)),
    ('tr64_to_int', rffi.CCallback([MuCtxPtr, MuTagRef64Value], MuIntValue)),
    ('tr64_to_ref', rffi.CCallback([MuCtxPtr, MuTagRef64Value], MuRefValue)),
    ('tr64_to_tag', rffi.CCallback([MuCtxPtr, MuTagRef64Value], MuIntValue)),
    ('tr64_from_fp', rffi.CCallback([MuCtxPtr, MuDoubleValue], MuTagRef64Value)),
    ('tr64_from_int', rffi.CCallback([MuCtxPtr, MuIntValue], MuTagRef64Value)),
    ('tr64_from_ref', rffi.CCallback([MuCtxPtr, MuRefValue, MuIntValue], MuTagRef64Value)),
    ('enable_watchpoint', rffi.CCallback([MuCtxPtr, MuWPID], lltype.Void)),
    ('disable_watchpoint', rffi.CCallback([MuCtxPtr, MuWPID], lltype.Void)),
    ('pin', rffi.CCallback([MuCtxPtr, MuValue], MuUPtrValue)),
    ('unpin', rffi.CCallback([MuCtxPtr, MuValue], lltype.Void)),
    ('expose', rffi.CCallback([MuCtxPtr, MuFuncRefValue, MuCallConv._lltype, MuIntValue], MuValue)),
    ('unexpose', rffi.CCallback([MuCtxPtr, MuCallConv._lltype, MuValue], lltype.Void)),
    ('new_bundle', rffi.CCallback([MuCtxPtr], MuBundleNode)),
    ('load_bundle_from_node', rffi.CCallback([MuCtxPtr, MuBundleNode], lltype.Void)),
    ('abort_bundle_node', rffi.CCallback([MuCtxPtr, MuBundleNode], lltype.Void)),
    ('get_node', rffi.CCallback([MuCtxPtr, MuBundleNode, MuID], MuChildNode)),
    ('get_id', rffi.CCallback([MuCtxPtr, MuBundleNode, MuChildNode], MuID)),
    ('set_name', rffi.CCallback([MuCtxPtr, MuBundleNode, MuChildNode, MuName], lltype.Void)),
    ('new_type_int', rffi.CCallback([MuCtxPtr, MuBundleNode, rffi.INT], MuTypeNode)),
    ('new_type_float', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('new_type_double', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('new_type_uptr', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('set_type_uptr', rffi.CCallback([MuCtxPtr, MuTypeNode, MuTypeNode], lltype.Void)),
    ('new_type_ufuncptr', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('set_type_ufuncptr', rffi.CCallback([MuCtxPtr, MuTypeNode, MuFuncSigNode], lltype.Void)),
    ('new_type_struct', rffi.CCallback([MuCtxPtr, MuBundleNode, MuTypeNodePtr, MuArraySize], MuTypeNode)),
    ('new_type_hybrid', rffi.CCallback([MuCtxPtr, MuBundleNode, MuTypeNodePtr, MuArraySize, MuTypeNode], MuTypeNode)),
    ('new_type_array', rffi.CCallback([MuCtxPtr, MuBundleNode, MuTypeNode, rffi.ULONG], MuTypeNode)),
    ('new_type_vector', rffi.CCallback([MuCtxPtr, MuBundleNode, MuTypeNode, rffi.ULONG], MuTypeNode)),
    ('new_type_void', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('new_type_ref', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('set_type_ref', rffi.CCallback([MuCtxPtr, MuTypeNode, MuTypeNode], lltype.Void)),
    ('new_type_iref', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('set_type_iref', rffi.CCallback([MuCtxPtr, MuTypeNode, MuTypeNode], lltype.Void)),
    ('new_type_weakref', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('set_type_weakref', rffi.CCallback([MuCtxPtr, MuTypeNode, MuTypeNode], lltype.Void)),
    ('new_type_funcref', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('set_type_funcref', rffi.CCallback([MuCtxPtr, MuTypeNode, MuFuncSigNode], lltype.Void)),
    ('new_type_tagref64', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('new_type_threadref', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('new_type_stackref', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('new_type_framecursorref', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('new_type_irnoderef', rffi.CCallback([MuCtxPtr, MuBundleNode], MuTypeNode)),
    ('new_funcsig',
     rffi.CCallback([MuCtxPtr, MuBundleNode, MuTypeNodePtr, MuArraySize, MuTypeNodePtr, MuArraySize], MuFuncSigNode)),
    ('new_const_int', rffi.CCallback([MuCtxPtr, MuBundleNode, MuTypeNode, rffi.ULONG], MuConstNode)),
    ('new_const_int_ex', rffi.CCallback([MuCtxPtr, MuBundleNode, MuTypeNode, rffi.ULONGP, MuArraySize], MuConstNode)),
    ('new_const_float', rffi.CCallback([MuCtxPtr, MuBundleNode, MuTypeNode, rffi.FLOAT], MuConstNode)),
    ('new_const_double', rffi.CCallback([MuCtxPtr, MuBundleNode, MuTypeNode, rffi.DOUBLE], MuConstNode)),
    ('new_const_null', rffi.CCallback([MuCtxPtr, MuBundleNode, MuTypeNode], MuConstNode)),
    ('new_const_seq', rffi.CCallback([MuCtxPtr, MuBundleNode, MuTypeNode, MuConstNodePtr, MuArraySize], MuConstNode)),
    ('new_const_extern', rffi.CCallback([MuCtxPtr, MuBundleNode, MuTypeNode, rffi.CCHARP], MuConstNode)),
    ('new_global_cell', rffi.CCallback([MuCtxPtr, MuBundleNode, MuTypeNode], MuGlobalNode)),
    ('new_func', rffi.CCallback([MuCtxPtr, MuBundleNode, MuFuncSigNode], MuFuncNode)),
    ('new_func_ver', rffi.CCallback([MuCtxPtr, MuBundleNode, MuFuncNode], MuFuncVerNode)),
    ('new_exp_func',
     rffi.CCallback([MuCtxPtr, MuBundleNode, MuFuncNode, MuCallConv._lltype, MuConstNode], MuExpFuncNode)),
    ('new_bb', rffi.CCallback([MuCtxPtr, MuFuncVerNode], MuBBNode)),
    ('new_nor_param', rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode], MuNorParamNode)),
    ('new_exc_param', rffi.CCallback([MuCtxPtr, MuBBNode], MuExcParamNode)),
    ('get_inst_res', rffi.CCallback([MuCtxPtr, MuInstNode, rffi.INT], MuInstResNode)),
    ('get_num_inst_res', rffi.CCallback([MuCtxPtr, MuInstNode], rffi.INT)),
    ('add_dest',
     rffi.CCallback([MuCtxPtr, MuInstNode, MuDestKind._lltype, MuBBNode, MuVarNodePtr, MuArraySize], lltype.Void)),
    ('add_keepalives', rffi.CCallback([MuCtxPtr, MuInstNode, MuLocalVarNodePtr, MuArraySize], lltype.Void)),
    ('new_binop',
     rffi.CCallback([MuCtxPtr, MuBBNode, MuBinOptr._lltype, MuTypeNode, MuVarNode, MuVarNode], MuInstNode)),
    ('new_cmp', rffi.CCallback([MuCtxPtr, MuBBNode, MuCmpOptr._lltype, MuTypeNode, MuVarNode, MuVarNode], MuInstNode)),
    ('new_conv',
     rffi.CCallback([MuCtxPtr, MuBBNode, MuConvOptr._lltype, MuTypeNode, MuTypeNode, MuVarNode], MuInstNode)),
    ('new_select',
     rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode], MuInstNode)),
    ('new_branch', rffi.CCallback([MuCtxPtr, MuBBNode], MuInstNode)),
    ('new_branch2', rffi.CCallback([MuCtxPtr, MuBBNode, MuVarNode], MuInstNode)),
    ('new_switch', rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode, MuVarNode], MuInstNode)),
    ('add_switch_dest',
     rffi.CCallback([MuCtxPtr, MuInstNode, MuConstNode, MuBBNode, MuVarNodePtr, MuArraySize], lltype.Void)),
    (
    'new_call', rffi.CCallback([MuCtxPtr, MuBBNode, MuFuncSigNode, MuVarNode, MuVarNodePtr, MuArraySize], MuInstNode)),
    ('new_tailcall',
     rffi.CCallback([MuCtxPtr, MuBBNode, MuFuncSigNode, MuVarNode, MuVarNodePtr, MuArraySize], MuInstNode)),
    ('new_ret', rffi.CCallback([MuCtxPtr, MuBBNode, MuVarNodePtr, MuArraySize], MuInstNode)),
    ('new_throw', rffi.CCallback([MuCtxPtr, MuBBNode, MuVarNode], MuInstNode)),
    ('new_extractvalue', rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode, rffi.INT, MuVarNode], MuInstNode)),
    ('new_insertvalue', rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode, rffi.INT, MuVarNode, MuVarNode], MuInstNode)),
    ('new_extractelement',
     rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode], MuInstNode)),
    ('new_insertelement',
     rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode], MuInstNode)),
    ('new_shufflevector',
     rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode, MuVarNode], MuInstNode)),
    ('new_new', rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode], MuInstNode)),
    ('new_newhybrid', rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode, MuTypeNode, MuVarNode], MuInstNode)),
    ('new_alloca', rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode], MuInstNode)),
    ('new_allocahybrid', rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode, MuTypeNode, MuVarNode], MuInstNode)),
    ('new_getiref', rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNode, MuVarNode], MuInstNode)),
    ('new_getfieldiref', rffi.CCallback([MuCtxPtr, MuBBNode, MuBool, MuTypeNode, rffi.INT, MuVarNode], MuInstNode)),
    ('new_getelemiref',
     rffi.CCallback([MuCtxPtr, MuBBNode, MuBool, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode], MuInstNode)),
    ('new_shiftiref',
     rffi.CCallback([MuCtxPtr, MuBBNode, MuBool, MuTypeNode, MuTypeNode, MuVarNode, MuVarNode], MuInstNode)),
    ('new_getvarpartiref', rffi.CCallback([MuCtxPtr, MuBBNode, MuBool, MuTypeNode, MuVarNode], MuInstNode)),
    ('new_load', rffi.CCallback([MuCtxPtr, MuBBNode, MuBool, MuMemOrd._lltype, MuTypeNode, MuVarNode], MuInstNode)),
    ('new_store',
     rffi.CCallback([MuCtxPtr, MuBBNode, MuBool, MuMemOrd._lltype, MuTypeNode, MuVarNode, MuVarNode], MuInstNode)),
    ('new_cmpxchg', rffi.CCallback(
        [MuCtxPtr, MuBBNode, MuBool, MuBool, MuMemOrd._lltype, MuMemOrd._lltype, MuTypeNode, MuVarNode, MuVarNode,
         MuVarNode], MuInstNode)),
    ('new_atomicrmw', rffi.CCallback(
        [MuCtxPtr, MuBBNode, MuBool, MuMemOrd._lltype, MuAtomicRMWOptr._lltype, MuTypeNode, MuVarNode, MuVarNode],
        MuInstNode)),
    ('new_fence', rffi.CCallback([MuCtxPtr, MuBBNode, MuMemOrd._lltype], MuInstNode)),
    ('new_trap', rffi.CCallback([MuCtxPtr, MuBBNode, MuTypeNodePtr, MuArraySize], MuInstNode)),
    ('new_watchpoint', rffi.CCallback([MuCtxPtr, MuBBNode, MuWPID, MuTypeNodePtr, MuArraySize], MuInstNode)),
    ('new_wpbranch', rffi.CCallback([MuCtxPtr, MuBBNode, MuWPID], MuInstNode)),
    ('new_ccall', rffi.CCallback(
        [MuCtxPtr, MuBBNode, MuCallConv._lltype, MuTypeNode, MuFuncSigNode, MuVarNode, MuVarNodePtr, MuArraySize],
        MuInstNode)),
    ('new_newthread', rffi.CCallback([MuCtxPtr, MuBBNode, MuVarNode, MuVarNode], MuInstNode)),
    ('new_swapstack_ret', rffi.CCallback([MuCtxPtr, MuBBNode, MuVarNode, MuTypeNodePtr, MuArraySize], MuInstNode)),
    ('new_swapstack_kill', rffi.CCallback([MuCtxPtr, MuBBNode, MuVarNode], MuInstNode)),
    ('set_newstack_pass_values',
     rffi.CCallback([MuCtxPtr, MuInstNode, MuTypeNodePtr, MuVarNodePtr, MuArraySize], lltype.Void)),
    ('set_newstack_throw_exc', rffi.CCallback([MuCtxPtr, MuInstNode, MuVarNode], lltype.Void)),
    ('new_comminst', rffi.CCallback(
        [MuCtxPtr, MuBBNode, MuCommInst._lltype, MuFlagPtr, MuArraySize, MuTypeNodePtr, MuArraySize, MuFuncSigNodePtr,
         MuArraySize, MuVarNodePtr, MuArraySize], MuInstNode)),
))

mu_new = rffi.llexternal('mu_refimpl2_new', [], MuVMPtr, compilation_info=eci)
mu_new_ex = rffi.llexternal('mu_refimpl2_new_ex', [rffi.CCHARP], MuVMPtr, compilation_info=eci)
mu_close = rffi.llexternal('mu_refimpl2_close', [MuVMPtr], lltype.Void, compilation_info=eci)


# -------------------------------------------------------------------------------------------------------
# Helpers
class scoped_lst2arr:
    def __init__(self, ELM_T, lst, need_rffi_cast=False):
        self.lst = lst
        self.ELM_T = ELM_T
        self.need_cast = need_rffi_cast

    def __enter__(self):
        buf = lltype.malloc(rffi.CArray(self.ELM_T), len(self.lst), flavor='raw')
        if self.need_cast:
            for i, e in enumerate(self.lst):
                buf[i] = rffi.cast(self.ELM_T, e)
        else:
            for i, e in enumerate(self.lst):
                buf[i] = e
        sz = rffi.cast(MuArraySize, len(self.lst))
        self.buf = buf
        return buf, sz

    def __exit__(self, *args):
        if self.buf:
            lltype.free(self.buf, flavor='raw')