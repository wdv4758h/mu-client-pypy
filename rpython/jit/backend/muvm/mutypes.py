from rpython.jit.metainterp.history import  (INT, FLOAT, VOID,
                                            STRUCT, REF, VECTOR)
from rpython.jit.backend.muvm.arch import (WORD, DOUBLE_WORD,
                                        JITFRAME_FIXED_SIZE, INT_WIDTH)

## Some Mu types

# TYPE                  PARAMS
# INT                       # length
# FLOAT                     # None
# VOID                      # None
# STRUCT                    # < T1 T2 ... >
# REF                       # < T >
# VECTOR                    # < T length >
DOUBLE          = 'd'       # None
IREF            = 'ir'      # < T >
WEAKREF         = 'wr'      # < T >
HYBRID          = 'hy'      # < F1 F2 ... V >
ARRAY           = 'ar'      # < T length >
FUNCREF         = 'fr'      # < sig >
THREADREF       = 'tr'      # None
STACKREF        = 'sr'      # None
FRAMECURSORREF  = 'fcr'     # None
TAGREF64        = 'tgr'     # None
UPTR            = 'upt'     # < T >
UFUNCPTR        = 'ufpt'    # < sig >
# Type bindings
type_bindings = {}
sig_bindings  = {}

class MuType(object):
    def __init__(self):
        self.tp = "mutype"
    def __repr__(self):
        return '@' + self._prefix() + '_t'
    def __neq__(self, other):
        return not self == other
        
class MuIntType(MuType):
    def __init__(self, length):
        self.length = length
        self.tp     = INT

    def _prefix(self):
        return self.tp + str(self.length)

    def __eq__(self, other):
        return isinstance(other, MuIntType) and other.length == self.length

    def __hash__(self):
        return hash( (self.tp, self.length) )
        

class MuFloatType(MuType):
    def __init__(self):
        self.tp = FLOAT

    def _prefix(self):
        return self.tp 

    def __eq__(self, other):
        return isinstance(other, MuFloatType)

    def __hash__(self):
        return hash( self.tp )

class MuDoubleType(MuType):
    def __init__(self):
        self.tp = DOUBLE
    def _prefix(self):
        return self.tp
    def __eq__(self, other):
        return isinstance(other, MuDoubleType)
    def __hash__(self):
        return hash( self.tp )

class MuVoidType(MuType):
    def __init__(self):
        self.tp = VOID
    def _prefix(self):
        return self.tp
    def __eq__(self, other):
        return isinstance(other, MuVoidType)
    def __hash__(self):
        return hash( self.tp )

class MuStructType(MuType):
    # count keeps track of how many MuStructs have been created
    # Used for _prefix
    count = 0
    def __init__(self, types):
        self.tp  = STRUCT
        for t in types:
            assert isinstance(t, MuType), "MuStruct must be built from valid MuTypes"
        self.types = tuple(types)
        self.structnum = int(self.count)
        MuStructType.count += 1

    def _prefix(self):
        return self.tp + str(self.structnum)

    def __eq__(self, other):
        return isinstance(other, MuStructType) and self.types == other.types

    def __hash__(self):
        return hash( (self.tp, self.types) )

class MuRefType(MuType):
    count = 0       # Keep track of reference built so far
    def __init__(self, reftype):
        assert isinstance(reftype, MuType), "MuRef must reference a valid MuType"
        self.tp     = REF
        self.reftype = reftype
        self.refnum = int(self.count)  # Acts as an id
        MuRefType.count += 1

    def _prefix(self):
        return self.tp + str(self.refnum)

    def __eq__(self, other):
        return isinstance(other, MuRefType) and self.reftype == other.reftype

    def __hash__(self):
        return hash( (self.tp, self.reftype) )
    
class MuVectorType(MuType):
    count = 0
    def __init__(self, vectype, length):
        assert isinstance(vectype, MuType), "MuVector must be built from a valid MuType"
        self.tp         = VECTOR
        self.vectype    = vectype
        self.length     = length
        self.vecnum     = int(self.count)
        MuVectorType.count     += 1

    def _prefix(self):
        return self.tp + str(self.vecnum)

    def __eq__(self, other):
        return (isinstance(other, MuVectorType) 
                and self.vectype   == other.vectype
                and self.length == other.length
               )

    def __hash__(self):
        return hash( (self.tp, self.vectype, self.veclength) )
    
class MuIRefType(MuType):
    count = 0
    def __init__(self, reftype):
        assert isinstance(reftype, MuType), "MuIRefType must reference a valid MuType"
        self.tp         = IREF
        self.reftype    = reftype
        self.refcount   = int(self.count)
        MuIRefType.count     += 1

    def _prefix(self):
        return self.tp + str(self.refcount)

    def __eq__(self, other):
        return isinstance(other, MuIRefType) and self.reftype == other.reftype

    def __hash__(self):
        return hash( (self.tp, self.reftype) )

class MuWeakRefType(MuType):
    count = 0
    def __init__(self, reftype):
        assert isinstance(reftype, MuType), "MuWeakRefType must reference a valid MuType"
        self.tp         = WEAKREF
        self.reftype    = reftype
        self.refcount   = int(self.count)
        MuWeakRefType.count     += 1

    def _prefix(self):
        return self.tp + str(self.refcount)

    def __eq__(self, other):
        return ( isinstance(other, MuWeakRefType) 
                 and self.reftype == other.reftype
               )

    def __hash__(self):
        return hash( (self.tp, self.reftype) )

class MuHybridType(MuType):
    count = 0
    def __init__(self, fixedtypes, vartype):
        assert hasattr(fixedtypes, '__iter__')
        for t in fixedtypes:
            assert isinstance(t, MuType), "MuHybridType's mixed types must be valid MuTypes"
        assert isinstance(vartype, MuType), "MuHybridType's variable type must be a valid MuType"
        
        self.tp          = HYBRID
        self.fixedtypes = tuple(fixedtypes)
        self.vartype    = vartype
        self.hybridcount = int(self.count)
        MuHybridType.count      += 1
        
    def _prefix(self):
        return self.tp + str(self.hybridcount)

    def __eq__(self, other):
        return ( isinstance(other, MuDoubleType) 
                 and self.fixedtypes == other.fixedtypes
                 and self.vartype    == other.vartype
               )

    def __hash__(self):
        return hash( (self.tp, self.fixedtypes, self.vartype) )

class MuArrayType(MuType):
    count = 0
    def __init__(self, arraytype, length):
        assert isinstance(arraytype, MuType), "MuArrayType must have elements of a valid MuType"
        assert length > 0, "MuArrayType must have length greater than zero"
        self.tp         = ARRAY
        self.arraytype  = arraytype
        self.length     = length
        self.arraycount = int(self.count)
        MuArrayType.count     += 1

    def _prefix(self):
        return self.tp + str(self.arraycount)

    def __eq__(self, other):
        return ( isinstance(other.MuArrayType) 
                 and self.arraytype == other.arraytype
                 and self.length    == other.length
               )
    def __hash__(self):
        return hash( (self.tp, self.arraytype, self.length) )
        

class MuFuncRefType(MuType):
    count = 0
    def __init__(self, sig):
        assert isinstance(sig, MuFuncSig), "MuFuncRefType must have of a valid MuFuncSig"
        self.tp           = FUNCREF
        self.sig          = sig
        self.refcount     = int(self.count)
        MuFuncRefType.count       += 1

    def _prefix(self):
        return self.tp + str(self.refcount)

    def __eq__(self, other):
        return ( isinstance(other.MuFuncRefType) 
                 and self.sig == other.sig
               )

    def __hash__(self):
        return hash( (self.tp, self.sig) )

class MuThreadRefType(MuType):
    def __init__(self):
        self.tp         = THREADREF

    def _prefix(self):
        return self.tp

    def __eq__(self, other):
        return isinstance(other.MuThreadRefType) 

    def __hash__(self):
        return hash( self.tp )

class MuStackRefType(MuType):
    def __init__(self):
        self.tp         = STACKREF

    def _prefix(self):
        return self.tp

    def __eq__(self, other):
        return isinstance(other.MuStackRefType) 

    def __hash__(self):
        return hash( self.tp )

class MuFrameCursorRefType(MuType):
    def __init__(self):
        self.tp            = FRAMEFURSORREF

    def _prefix(self):
        return self.tp

    def __eq__(self, other):
        return isinstance( other.MuFrameCursorRefType )

    def __hash__(self):
        return hash( self.tp )

class MuTagRef64Type(MuType):
    def __init__(self):
        self.tp            = TAGREF64

    def _prefix(self):
        return self.tp

    def __eq__(self, other):
        return isinstance( other.MuTagRef64Type )

    def __hash__(self):
        return hash( self.tp )

class MuPtrType(MuType):
    count = 0       # Keep track of reference built so far
    def __init__(self, ptrtype):
        assert isinstance(ptrtype, MuType), "MuPtrType must point to a valid MuType"
        self.tp     = UPTR
        self.ptrtype = ptrtype
        self.ptrnum = int(self.count)  # Acts as an id
        MuPtrType.count += 1

    def _prefix(self):
        return self.tp + str(self.ptrnum)

    def __eq__(self, other):
        return isinstance(other, MuPtrType) and self.ptrtype == other.ptrtype

    def __hash__(self):
        return hash( (self.tp, self.ptrtype) )

class MuFuncPtrType(MuType):
    count = 0       # Keep track of reference built so far
    def __init__(self, sig):
        assert isinstance(sig, MuFuncSig), "MuFuncPtrType must have a valid MuFuncSig"
        self.tp     = UFUNCPTR
        self.sig    = sig
        self.ptrnum = int(self.count)  # Acts as an id
        MuFuncPtrType.count += 1

    def _prefix(self):
        return self.tp + str(self.ptrnum)

    def __eq__(self, other):
        return isinstance(other, MuFuncPtrType) and self.sig == other.sig

    def __hash__(self):
        return hash( (self.tp, self.sig) )
    

class MuFuncSig(object):
    count = 0  # Enumerate signatures
    def __init__(self, paramtys, returntys):
        '''
        paramtys: input types
        returntys: output types
        '''
        for t in paramtys + returntys:
            assert isinstance(t, MuType)
        self.paramtys   = tuple(paramtys )
        self.returntys  = tuple(returntys)
        self.signum     = int(self.count )
        MuFuncSig.count  += 1

    def __repr__(self):
        return '@funcsig{}'.format(self.signum)

    def decl_repr(self):
        params  = ','.join([str(p) for p in self.paramtys ])
        returns = ','.join([str(r) for r in self.returntys])
        return 'funcsig {} = ({}) -> ({})'.format(str(self), params, returns)

    def __eq__(self, other):
        return (     len(self.paramtys ) == len(other.paramtys )
                 and len(self.returntys) == len(other.returntys)
                 and reduce(lambda x, t: x and (t[0] == t[1]), zip(self.paramtys, other.paramtys), True)
                 and reduce(lambda x, t: x and (t[0] == t[1]), zip(self.returntys, other.returntys), True)
               )

    def __hash__(self):
        # the '(...,0,...)' is to keep things like (int) -> ()
        # and () -> (int) from colliding
        return hash((self.paramtys, 0, self.returntys) )

# This may be useful at some point. Originally made for get_type() but changed
# tactic. Keeping around in case it's useful.
MuTypeDict = { INT          : MuIntType
             , FLOAT        : MuFloatType
             , DOUBLE       : MuDoubleType
             , VOID         : MuVoidType
             , STRUCT       : MuStructType
             , REF          : MuRefType
             , VECTOR       : MuVectorType
             , IREF         : MuIRefType
             , WEAKREF      : MuWeakRefType
             , HYBRID       : MuHybridType
             , ARRAY        : MuArrayType
             , FUNCREF      : MuFuncRefType
             , THREADREF    : MuThreadRefType
             , STACKREF     : MuStackRefType
             , FRAMECURSORREF   : MuFrameCursorRefType
             , TAGREF64     : MuTagRef64Type
             , UPTR         : MuPtrType
             , UFUNCPTR     : MuFuncPtrType
             }
def get_func_sig(paramtys, returntys):
    p = tuple(paramtys)
    r = tuple(returntys)
    tps_tuple = (p,r)
    if tps_tuple in sig_bindings:
        return sig_bindings[tps_tuple]
    sig_bindings[tps_tuple] = MuFuncSig(p,r)
    return sig_bindings[tps_tuple]

def get_type( tp            = None
            , length        = None
            , types         = None
            , reftype       = None
            , vectype       = None
            , fixedtypes    = None
            , vartype       = None
            , arraytype     = None
            , sig           = None
            ):

    global MuTypeDict
    assert tp in MuTypeDict
    if types:
        types = tuple(types)
    if fixedtypes:
        fixedtypes = tuple(fixedtypes)
    args = locals().values()     # Get arguments
    args_tuple = tuple([a for a in args if a])
    if args_tuple in type_bindings:
        return type_bindings[args_tuple]
    
    if tp   == INT:
        t = MuIntType(length)
    elif tp == FLOAT:
        t = MuFloatType()
    elif tp == DOUBLE:
        t = MuDoubleType()
    elif tp == VOID:
        t = MuVoidType()
    elif tp == STRUCT:
        t = MuStructType(types)
    elif tp == REF:
        t = MuRefType(reftype)
    elif tp == VECTOR:
        t = MuVectorType(vectype, length)
    elif tp == IREF:
        t = MuIRefType(reftype)
    elif tp == WEAKREF:
        t = MuWeakRefType(reftype)
    elif tp == HYBRID:
        t = MuHybridType(fixedtypes, vartype)
    elif tp == ARRAY:
        t = MuArrayType(arraytype, length)
    elif tp == FUNCREF:
        t = MuFuncRefType(sig)
    elif tp == THREADREF: 
        t = MuThreadRefType()
    elif tp == STACKREF:
        t = MuStackRefType()
    elif tp == FRAMECURSORREF:
        t = MuFrameCursorRefType()
    elif tp == TAGREF64:
        t = MuTagRef64Type()
    elif tp == UPTR:
        t = MuPtrType(ptrtype)
    elif tp == UFUNCPTR:
        t = MuFuncPtr(sig)
    type_bindings[args_tuple] = t
    return type_bindings[args_tuple]

INT64_t  = get_type(INT, length=64)
INT32_t  = get_type(INT, length=32)
FLOAT_t  = get_type(FLOAT)
DOUBLE_t = get_type(DOUBLE)
VOID_t   = get_type(VOID)


INT_DEFAULT = INT64_t
if INT_WIDTH == 32:
    INT_DEFAULT = INT32_t

