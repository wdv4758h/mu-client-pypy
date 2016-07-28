'''Current Dev: 
    Map out work flow in regalloc.py
    Remove free_regs from file
    Remove TempVars from file

    NOTE: ScratchMethod refers to an implementation that is for testing. We are
    trying to see what works/what breaks with certain things in place.
'''

from rpython.rtyper.annlowlevel import cast_instance_to_gcref
from rpython.rlib.debug import debug_print, debug_start, debug_stop
from rpython.jit.backend.llsupport.regalloc import FrameManager, \
        RegisterManager, TempVar, compute_vars_longevity, BaseRegalloc, \
        get_scale
from rpython.jit.backend.muvm import registers as r
from rpython.rlib.objectmodel import we_are_translated

#from rpython.jit.backend.arm import conditions as c
from rpython.jit.backend.muvm import locations
#from rpython.jit.backend.arm.locations import imm, get_fp_offset
from rpython.jit.backend.muvm.helper.regalloc import (prepare_op_by_helper_call,
                                                   prepare_unary_cmp,
                                                   prepare_op_ri,
                                                   prepare_int_cmp,
                                                   prepare_unary_op,
                                                   prepare_two_regs_op,
                                                   prepare_float_cmp,
                                                   check_imm_arg,
                                                   check_imm_box,
                                                   VMEM_imm_size,
                                                   default_imm_size,
                                                   )
#from rpython.jit.backend.arm.jump import remap_frame_layout_mixed
#from rpython.jit.backend.arm.arch import WORD, JITFRAME_FIXED_SIZE

from rpython.jit.codewriter import longlong
from rpython.jit.metainterp.history import (Const, ConstInt, ConstFloat,
                                            ConstPtr,
                                            INT, REF, FLOAT)
from rpython.jit.metainterp.history import TargetToken
from rpython.jit.metainterp.resoperation import rop
from rpython.jit.backend.llsupport.descr import ArrayDescr
from rpython.jit.backend.llsupport.gcmap import allocate_gcmap
from rpython.jit.backend.llsupport import symbolic
from rpython.rtyper.lltypesystem import lltype, rffi, rstr, llmemory
from rpython.rtyper.lltypesystem.lloperation import llop
from rpython.jit.codewriter.effectinfo import EffectInfo
from rpython.rlib.rarithmetic import r_uint
from rpython.jit.backend.llsupport.descr import CallDescr

try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict # too bad

# Temp Variables -- find out what these are
class TempInt(TempVar):
    type = INT

    def __repr__(self):
        return "<TempInt at %s>" % (id(self),)


class TempPtr(TempVar):
    type = REF

    def __repr__(self):
        return "<TempPtr at %s>" % (id(self),)


class TempFloat(TempVar):
    type = FLOAT

    def __repr__(self):
        return "<TempFloat at %s>" % (id(self),)

def void(self, op, fcond):
    return []

### I think we can get away with a single RegisterManager, namely this one.
class MuVMRegisterManager(RegisterManager):
    registers = r.registers  # Registers 
    
    ssanum = 0          # This will be incremented to generate unique names
                        # for each new SSA

    def __init__(self, longevity, frame_manager=None, assembler=None):
        self.longevity = longevity
        self.temp_boxes = []
        if not we_are_translated():
            self.reg_bindings = OrderedDict()
        else:
            self.reg_bindings = {}
        self.bindings_to_frame_reg = {}
        self.frame_manager = frame_manager
        self.assembler = assembler

    def return_constant(self, v, forbidden_vars=[], selected_reg=None):
        """DEV: Need to determine what this will do in our new model."""
        # (TempVar, [TempVar], SSA) -> (SSA)
        ### OVERRIDE
        self._check_type(v)
        assert isinstance(v,Const)
        immloc = self.convert_to_imm(v)
        return immloc

    def convert_to_imm(self, c):
        # (Const) -> (TempVar)
        #TODO
        return

    def is_still_alive(self, v):
        ### OVERRIDE
        return False

    def stays_alive(self, v):
        ### OVERRIDE
        return 0

    def possibly_free_var(self, v):
        ### OVERRIDE
        return None
    
    def _pick_variable_to_spill(self, v, forbidden_vars, selected_reg=None,
                                need_lower_byte=False):
        ### OVERRIDE
        return None
    
    def try_allocate_reg(self, v, selected_reg=None, need_lower_byte=False):
        """ Override from RegisterManager. This will always succeed.
        INPUTS:
            v: originally a temp var. Now an SSA variable. 
            selected_reg:    Ignored
            need_lower_byte: Ignored
        OUTPUS:
            self.register's location of `v`
        NOTE: Have not determined if TempVar is necessary for outside interface
        May need to incorporate tempvars again.
        """
        ### OVERRIDE
        ### Scratch Method
        try:
            assert is_instance(v, SSA)      # This is for debug purposes.
        except:
            print "ERROR: {} is not an SSA variable".format(v)
        self.registers.append(v)
        return len(self.registers) - 1  # Location of v

    def force_allocate_reg(self, v, forbidden_vars=[], selected_reg=None,
                           need_lower_byte=False):
        """ Forces an allocation of a register. Overridden from parent class.
        This is just a synonym for try_allocate_reg()
        """
        ### OVERRIDE
        return self.try_allocate_reg(v, selected_reg, need_lower_byte)

    def force_spill_var(self, var):
        ### OVERRIDE
        try:
            assert False        # This shouldn't be called
        except:
            print "ERROR: force_spill_var should not be called.",
            print "there is no variable spillage in MuVM."

class CoreRegisterManager(MuVMRegisterManager):
    all_regs = r.all_regs
    box_types = None       # or a list of acceptable types
    no_lower_byte_regs = all_regs
    save_around_call_regs = r.caller_resp

    def __init__(self, longevity, frame_manager=None, assembler=None):
        RegisterManager.__init__(self, longevity, frame_manager, assembler)

    def call_result_location(self, v):
        #TODO
        return

    def convert_to_imm(self, c):
        #TODO
        return

    def get_scratch_reg(self, type=INT, forbidden_vars=[], selected_reg=None):
        #TODO
        return

    def get_free_reg(self):
        #TODO
        return


class Regalloc(BaseRegalloc):

    def __init__(self, assembler):
        self.cpu = assembler.cpu
        self.assembler = assembler
        self.frame_manager = None
        self.jump_target_descr = None
        self.final_jump_op = None

    def loc(self, var):
        #TODO
        pass

    def position(self):
        #TODO
        pass

    def next_instruction(self):
        #TODO
        pass

    def _check_invariants(self):
        #TODO
        pass

    def stays_alive(self, v):
        #TODO
        pass

    def call_result_location(self, v):
        #TODO
        pass

    def after_call(self, v):
        #TODO
        pass

    def force_allocate_reg(self, var, forbidden_vars=[], selected_reg=None,
                           need_lower_byte=False):
        #TODO
        pass

    def force_allocate_reg_or_cc(self, var, forbidden_vars=[]):
        #TODO
        pass

    def try_allocate_reg(self, v, selected_reg=None, need_lower_byte=False):
        #TODO
        pass

    def possibly_free_var(self, var):
        #TODO
        pass

    def possibly_free_vars_for_op(self, op):
        #TODO
        pass

    def possibly_free_vars(self, vars):
        #TODO
        pass

    def get_scratch_reg(self, type, forbidden_vars=[], selected_reg=None):
        #TODO
        pass

    def get_free_reg(self):
        #TODO
        pass

    def free_temp_vars(self):
        #TODO
        pass
    def make_sure_var_in_reg(self, var, forbidden_vars=[],
                         selected_reg=None, need_lower_byte=False):
        #TODO
        pass

    def convert_to_imm(self, value):
        #TODO
        pass

    def _prepare(self, inputargs, operations, allgcrefs):
        #TODO
        pass

    def prepare_loop(self, inputargs, operations, looptoken, allgcrefs):
        #TODO
        pass

    def prepare_bridge(self, inputargs, arglocs, operations, allgcrefs,
                       frame_info):
        #TODO
        pass

    def get_final_frame_depth(self):
        #TODO
        pass

    def _update_bindings(self, locs, inputargs):
        #TODO
        pass

    def get_gcmap(self, forbidden_regs=[], noregs=False):
        #TODO
        pass
    # ------------------------------------------------------------
    def perform_enter_portal_frame(self, op):
        #TODO
        pass

    def perform_leave_portal_frame(self, op):
        #TODO
        pass

    def perform_extra(self, op, args, fcond):
        #TODO
        pass

    def force_spill_var(self, var):
        #TODO
        pass

    def before_call(self, force_store=[], save_all_regs=False):
        #TODO
        pass

    def _sync_var(self, v):
        #TODO
        pass

    def _prepare_op_int_add(self, op, fcond):
        #TODO
        pass

    def prepare_op_int_add(self, op, fcond):
        #TODO
        pass

    prepare_op_nursery_ptr_increment = prepare_op_int_add

    def _prepare_op_int_sub(self, op, fcond):
        #TODO
        pass

    def prepare_op_int_sub(self, op, fcond):
        #TODO
        pass

    def prepare_op_int_mul(self, op, fcond):
        #TODO
        pass

    def prepare_op_int_force_ge_zero(self, op, fcond):
        #TODO
        pass

    def prepare_op_int_signext(self, op, fcond):
        #TODO
        pass

    prepare_op_int_floordiv = prepare_op_by_helper_call('int_floordiv')
    prepare_op_int_mod = prepare_op_by_helper_call('int_mod')
    prepare_op_uint_floordiv = prepare_op_by_helper_call('unit_floordiv')

    prepare_op_int_and = prepare_op_ri('int_and')
    prepare_op_int_or = prepare_op_ri('int_or')
    prepare_op_int_xor = prepare_op_ri('int_xor')
    prepare_op_int_lshift = prepare_op_ri('int_lshift', imm_size=0x1F,
                                        allow_zero=False, commutative=False)
    prepare_op_int_rshift = prepare_op_ri('int_rshift', imm_size=0x1F,
                                        allow_zero=False, commutative=False)
    prepare_op_uint_rshift = prepare_op_ri('uint_rshift', imm_size=0x1F,
                                        allow_zero=False, commutative=False)

    prepare_op_int_lt = prepare_int_cmp
    prepare_op_int_le = prepare_int_cmp
    prepare_op_int_eq = prepare_int_cmp
    prepare_op_int_ne = prepare_int_cmp
    prepare_op_int_gt = prepare_int_cmp
    prepare_op_int_ge = prepare_int_cmp

    prepare_op_uint_le = prepare_int_cmp
    prepare_op_uint_gt = prepare_int_cmp

    prepare_op_uint_lt = prepare_int_cmp
    prepare_op_uint_ge = prepare_int_cmp

    prepare_op_ptr_eq = prepare_op_instance_ptr_eq = prepare_op_int_eq
    prepare_op_ptr_ne = prepare_op_instance_ptr_ne = prepare_op_int_ne

    prepare_op_int_add_ovf = prepare_op_int_add
    prepare_op_int_sub_ovf = prepare_op_int_sub
    prepare_op_int_mul_ovf = prepare_op_int_mul

    prepare_op_int_is_true = prepare_unary_cmp
    prepare_op_int_is_zero = prepare_unary_cmp

    prepare_op_int_neg = prepare_unary_op
    prepare_op_int_invert = prepare_unary_op

    def _prepare_op_call(self, op, fcond):
        #TODO
        pass
    
    prepare_op_call_i = _prepare_op_call
    prepare_op_call_r = _prepare_op_call
    prepare_op_call_f = _prepare_op_call
    prepare_op_call_n = _prepare_op_call

    def _prepare_call(self, op, force_store=[], save_all_regs=False,
                      first_arg_index=1):
        #TODO
        pass

    def _call(self, op, arglocs, force_store=[], save_all_regs=False):
        #TODO
        pass

    def prepare_op_call_malloc_gc(self, op, fcond):
        #TODO
        pass
        return self._prepare_call(op)

    def _prepare_llong_binop_xx(self, op, fcond):
        #TODO
        pass

    def _prepare_llong_to_int(self, op, fcond):
        #TODO
        pass

    def _prepare_threadlocalref_get(self, op, fcond):
        #TODO
        pass

    def _prepare_guard(self, op, args=None):
        #TODO
        pass

    def prepare_op_finish(self, op, fcond):
        #TODO
        pass

    def load_condition_into_cc(self, box):
        #TODO
        pass

    def _prepare_guard_cc(self, op, fcond):
        #TODO
        pass

    prepare_op_guard_true = _prepare_guard_cc
    prepare_op_guard_false = _prepare_guard_cc
    prepare_op_guard_nonnull = _prepare_guard_cc
    prepare_op_guard_isnull = _prepare_guard_cc

    def prepare_op_guard_value(self, op, fcond):
        #TODO
        pass

    def prepare_op_guard_no_overflow(self, op, fcond):
        #TODO
        pass

    prepare_op_guard_overflow = prepare_op_guard_no_overflow
    prepare_op_guard_not_invalidated = prepare_op_guard_no_overflow
    prepare_op_guard_not_forced = prepare_op_guard_no_overflow

    def prepare_op_guard_exception(self, op, fcond):
        #TODO
        pass

    def prepare_op_save_exception(self, op, fcond):
        #TODO
        pass
    prepare_op_save_exc_class = prepare_op_save_exception

    def prepare_op_restore_exception(self, op, fcond):
        #TODO
        pass

    def prepare_op_guard_no_exception(self, op, fcond):
        #TODO
        pass

    def prepare_op_guard_class(self, op, fcond):
        #TODO
        pass

    prepare_op_guard_nonnull_class = prepare_op_guard_class
    prepare_op_guard_gc_type = prepare_op_guard_class
    prepare_op_guard_subclass = prepare_op_guard_class

    def prepare_op_guard_is_object(self, op, fcond):
        #TODO
        pass

    def compute_hint_frame_locations(self, operations):
        #TODO
        pass

    def _compute_hint_frame_locations_from_descr(self, descr):
        #TODO
        pass

    def prepare_op_jump(self, op, fcond):
        #TODO
        pass

    def prepare_op_gc_store(self, op, fcond):
        #TODO
        pass

    def _prepare_op_gc_load(self, op, fcond):
        #TODO
        pass

    def prepare_op_increment_debug_counter(self, op, fcond):
        #TODO
        pass

    def prepare_op_gc_store_indexed(self, op, fcond):
        #TODO
        pass

    def _prepare_op_gc_load_indexed(self, op, fcond):
        #TODO
        pass

    def _prepare_op_same_as(self, op, fcond):
        #TODO
        pass

    def prepare_op_load_from_gc_table(self, op, fcond):
        #TODO
        pass

    def prepare_op_call_malloc_nursery(self, op, fcond):
        #TODO
        pass

    def prepare_op_call_malloc_nursery_varsize_frame(self, op, fcond):
        #TODO
        pass

    def prepare_op_call_malloc_nursery_varsize(self, op, fcond):
        #TODO
        pass

    def prepare_op_cond_call_gc_wb(self, op, fcond):
        #TODO
        pass

    def prepare_op_cond_call(self, op, fcond):
        #TODO
        pass

    def prepare_op_force_token(self, op, fcond):
        #TODO
        pass

    def prepare_op_label(self, op, fcond):
        #TODO
        pass

    def prepare_op_guard_not_forced_2(self, op, fcond):
        #TODO
        pass

    def _prepare_op_call_may_force(self, op, fcond):
        #TODO
        pass

    def _prepare_op_call_release_gil(self, op, fcond):
        #TODO
        pass


    def _prepare_op_call_assembler(self, op, fcond):
        #TODO
        pass

    def _prepare_op_math_sqrt(self, op, fcond):
        #TODO
        pass

    def prepare_op_cast_float_to_int(self, op, fcond):
        #TODO
        pass

    def prepare_op_cast_int_to_float(self, op, fcond):
        #TODO
        pass

    def prepare_force_spill(self, op, fcond):
        #TODO
        pass


    def prepare_op_cast_float_to_singlefloat(self, op, fcond):
        #TODO
        pass

    def prepare_op_cast_singlefloat_to_float(self, op, fcond):
        #TODO
        pass


def notimplemented(self, op, fcond):
    print "[MuVM/regalloc] %s not implemented" % op.getopname()
    raise NotImplementedError(op)




#for key, value in rop.__dict__.items():
#    key = key.lower()
#    if key.startswith('_'):
#        continue
#    methname = 'prepare_op_%s' % key
#    if hasattr(Regalloc, methname):
#        func = getattr(Regalloc, methname).im_func
#        operations[value] = func
