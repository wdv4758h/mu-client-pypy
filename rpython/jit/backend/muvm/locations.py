from rpython.jit.metainterp.history import  (INT, FLOAT, VOID, 
                                            STRUCT, REF, VECTOR)
from rpython.jit.backend.muvm.arch import (WORD, DOUBLE_WORD, 
                                        JITFRAME_FIXED_SIZE, INT_WIDTH)

# Type bindings 
type_bindings = {}

class Type(object):
    ''' Type value for SSALocations. Includes type and width info.'''
    def __init__(self, tp = INT, width = INT_WIDTH):
        self.tp  = tp
        self.width = width
    
    def prefix(self):
        """Return type signature"""
        res = self.tp
        if self.tp == INT:
            res += str(self.width)
        return res

    def __repr__(self):
        return '@' + self.prefix() + '_t'
    
    def __eq__(self, other):
        return self.tp == other.tp and self.width == other.width
    def __ne__(self, other):
        return not self.__eq__(other)
    def __hash__(self):
        return hash( (self.tp, self.width) )   # Just hash the tuple

def get_type(tp, width):
    if (tp, width) not in type_bindings:
        type_bindings[ (tp, width) ] = Type(tp, width)
    return type_bindings[ (tp, width) ]

INT64   = get_type(INT,   64)
INT32   = get_type(INT,   32)
FLOAT32 = get_type(FLOAT, 32)
FLOAT64 = get_type(FLOAT, 64)



INT_DEFAULT = INT64
if INT_WIDTH == 32:
    INT_DEFAULT = INT32



class AssemblerLocation(object):
    _immutable_ = True
    value  = None
    tp = Type(INT, INT_WIDTH)
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
    def __init__(self, value, tp=Type()):
        ''' Constructor:
            value: literal value of the constant
            tp: Type() instance
        '''
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
"""

def imm(i):
    return ImmLocation(i)

def imm_float(i):
    return ImmLocation(i, t=FLOAT, width=INT_SIZE)

def imm_int(i):
    return ImmLocation(i, t=INT, width=INT_SIZE)


def get_fp_offset(base_ofs, position):
    return base_ofs + WORD * (position + JITFRAME_FIXED_SIZE)
