from rpython.jit.metainterp.history import  (INT, FLOAT, VOID, 
                                            STRUCT, REF, VECTOR)
from rpython.jit.backend.muvm.arch import (WORD, DOUBLE_WORD, 
                                        JITFRAME_FIXED_SIZE, INT_WIDTH)

typemap = { INT : 'INT', FLOAT : 'FLOAT', VOID : 'VOID', STRUCT : 'STRCT', 
            REF : 'REF', VECTOR : 'VEC'}
class Type(object):
    ''' Type value for SSALocations. Includes type and width info.'''
    def __init__(self, t = INT, width = INT_WIDTH):
        self.t  = t
        self.width = width
    
    def prefix(self):
        """Return type signature"""
        res = self.t
        if self.t == INT:
            res += str(self.width)
        return res

    def __repr__(self):
        return '@' + self.prefix() + '_t'

class AssemblerLocation(object):
    _immutable_ = True
    value  = None
    t = Type(INT, INT_WIDTH)
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
    in [0..15] we let `value` member hold the value of the ssa variable. Thus,
    we are no longer treating it as a location but as a stand alone variable.

    __init__ is also updated so that it takes `value`, type `t` (INT default),
    and `width` (WORD*8 = 32 by default). The `width` parameter is necessary for
    ints and does not need to be specified for other types (as of now).
    """
    _immutable_ = True

    def __init__(self, value, t=INT, width=INT_WIDTH):
        '''Constructor for SSALocation class. Parameters as follow
            value: int:       index in registers
            t:     type str:  (INT = 'i', FLOAT = 'f', etc)
            width: int:       for int types only
                Defaults to 64 bits - we are doing 64 bit python for now
        '''
        self.value  = value
        self.t      = Type(t = t, width=width)
        self.type   = t

    def __repr__(self):
        """Temp implementation. Will update"""
        return '{}_{}'.format( self.t.prefix(), self.value)

    def is_core_reg(self):
        return True

    def is_local(self):
        return False

    def is_global(self):
        return False

    def is_constant(self):
        return False

    def as_key(self):       # 0 <= value < len(registers)
        return self.value

class LocalSSALocation(SSALocation):
    def is_local(self):
        return True
    
    def __repr__(self):
        return '%{}_{}'.format(self.t.prefix(), self.value)

class GlobalSSALocation(SSALocation):
    def is_global(self):
        return True

    def __repr__(self):
        return '@{}_{}'.format(self.t.prefix(), self.value)
    
    

### Maybe use this for constant class?
class ImmLocation(AssemblerLocation):
    _immutable_ = True
    width = WORD

    def __init__(self, value, t=INT, width=INT_WIDTH):
        self.type = Type(t=t, width=width)
        self.value = value

    def getint(self):
        return self.value

    def __repr__(self):
        return "imm(%d)" % (self.value)

    def is_imm(self):
        return True


class ConstFloatLoc(AssemblerLocation):
    """This class represents an imm float value which is stored in memory at
    the address stored in the field value"""
    _immutable_ = True
    width = 2 * WORD
    type = FLOAT

    def __init__(self, value):
        self.value = value

    def getint(self):
        return self.value

    def __repr__(self):
        return "imm_float(stored at %d)" % (self.value)

    def is_imm_float(self):
        return True

    def as_key(self):          # a real address + 1
        return self.value | 1

    def is_float(self):
        return True

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


def get_fp_offset(base_ofs, position):
    return base_ofs + WORD * (position + JITFRAME_FIXED_SIZE)
