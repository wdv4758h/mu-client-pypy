from rpython.jit.metainterp.history import  (INT, FLOAT, VOID, 
                                            STRUCT, REF, VECTOR)
from rpython.jit.backend.muvm.arch import (WORD, DOUBLE_WORD, 
                                        JITFRAME_FIXED_SIZE, INT_WIDTH)
from rpython.jit.backend.muvm.mutypes import ( get_type, DOUBLE, IREF, WEAKREF,
                                               HYBRID, ARRAY, FUNCREF,
                                               THREADREF, FRAMECURSORREF,
                                               TAGREF64, UPTR, UFUNCPTR,
                                               INT_DEFAULT, INT32_t, INT64_t,
                                               FLOAT_t, DOUBLE_t, VOID_t)


class AssemblerLocation(object):
    _immutable_ = True
    value  = None
    tp = get_type(INT, INT_WIDTH)
    type = INT

    def is_imm(self):
        return False

    def is_stack(self):
        return False

    def is_raw_sp(self):
        return False

    def is_core_reg(self):
        return False

    def is_vfp_reg(self):
        return False

    def is_imm_float(self):
        return False

    def is_float(self):
        return False

    def as_key(self):
        raise NotImplementedError

    def get_position(self):
        raise NotImplementedError # only for stack
        
class SSALocation(AssemblerLocation):
    """This is replacing the RegisterLocation class. Rather than `value` being
    in [0..15] we let `value` member be arbitrarily large.

    __init__ is also updated so that it takes `value`, type `t` (INT default),
    and `width` (WORD*8 = 32 by default). The `width` parameter is necessary for
    ints and does not need to be specified for other types (as of now).
    """
    ### TODO t,width -> Type()
    _immutable_ = True

    def __init__(self, value, tp=INT_DEFAULT):
        '''Constructor for SSALocation class. Parameters as follow
           value: int:       index in registers. Default is none: auto
           tp:     type str:  (INT = 'i', FLOAT = 'f', etc)
           width: int:       for int types only
           Defaults to 64 bits - we are doing 64 bit python for now
        '''
        self.value  = value
        self.tp = tp

    def __repr__(self):
        """Temp implementation. Will update"""
        return '{}_{}'.format( self.tp.prefix(), self.value)
    
    def is_core_reg(self):
        # TODO find out what this implies
        return True

    def is_float(self):
        return self.tp.tp == FLOAT

    def is_local(self):
        return False

    def is_global(self):
        return False

    def is_constant(self):
        return False

    def as_key(self):       # 0 <= value < len(registers)
        return self.value

class LocalSSALocation(SSALocation):
    ''' Represents a local ssa variable in the Mu VM. 
        If `value` var of constructor is an instance of an SSALocation, cast it
        as a LocalSSALocation (acts as a copy constructor). Otherwise, 
        treat as normal.
    '''

    def __init__(self, value, tp=INT):
        self.value = value
        self.tp = tp

    def is_local(self):
        return True
    
    def __repr__(self):
        return '%{}_{}'.format(self.t.prefix(), self.value)
    
class GlobalSSALocation(SSALocation):
    def __init__(self, value=None, tp=None, ):
        if isinstance(value, SSALocation):
            super(GlobalSSALocation, self).__init__(value.value, value.tp)
        else:
            self.value = value
            self.tp = tp
    def is_global(self):
        return True

    def __repr__(self):
        return '@{}_{}'.format(self.t.prefix(), self.value)

class ConstLocation(SSALocation):
    def __init__(self, tp=INT_DEFAULT, value = 0):
        ''' Constructor:
            tp: Type() instance
            value: literal value of the constant
        '''
        #TODO: Check that value is of proper type?
        self.tp = tp
        self.value = value

    def getval(self):
        '''used to be getint()'''
        return self.value

    def __repr__(self):
        return "@const_{}_{}".format(self.t.prefix(), self.value)

    def is_imm_float(self):
        ''' Do we need this? '''
        return self.tp.tp == FLOAT

    def as_key(self):          # a real address + 1
        return self.value | 1

    def is_float(self):
        return self.tp.tp == FLOAT

    def is_int(self):
        return self.tp.tp == INT


"""
class StackLocation(AssemblerLocation):
    _immutable_ = True

    def __init__(self, position, fp_offset, type=INT):
        if type == FLOAT:
            self.width = DOUBLE_WORD
        else:
            self.width = WORD
        self.position = position
        self.value = fp_offset
        self.type = type

    def __repr__(self):
        return 'FP(%s)+%d' % (self.type, self.position,)

    def location_code(self):
        return 'b'

    def get_position(self):
        return self.position

    def assembler(self):
        return repr(self)

    def is_stack(self):
        return True

    def as_key(self):                # an aligned word + 10000
        return self.position + 10000

    def is_float(self):
        return self.type == FLOAT

class RawSPStackLocation(AssemblerLocation):
    _immutable_ = True

    def __init__(self, sp_offset, type=INT):
        if type == FLOAT:
            self.width = DOUBLE_WORD
        else:
            self.width = WORD
        self.value = sp_offset
        self.type = type

    def __repr__(self):
        return 'SP(%s)+%d' % (self.type, self.value,)

    def is_raw_sp(self):
        return True

    def is_float(self):
        return self.type == FLOAT

    def as_key(self):            # a word >= 1000, and < 1000 + size of SP frame
        return self.value + 1000

def imm(i):
    return ImmLocation(i)

def imm_float(i):
    return ImmLocation(i, t=FLOAT, width=INT_SIZE)

def imm_int(i):
    return ImmLocation(i, t=INT, width=INT_SIZE)

"""

DEFAULT_CONSTS = []
def get_fp_offset(base_ofs, position):
    return base_ofs + WORD * (position + JITFRAME_FIXED_SIZE)

for t in (INT32_t, INT64_t, FLOAT_t, DOUBLE_t):
    for v in (-1,0,1,2,4,8,16,32,64,128,256,512,1024):
        DEFAULT_CONSTS.append(ConstLocation(t,v))

