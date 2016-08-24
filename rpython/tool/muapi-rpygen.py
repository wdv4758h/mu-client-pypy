from muapiparser import parse_muapi
from pprint import PrettyPrinter
import sys
pprint = PrettyPrinter().pprint

# ------------------------------------------------------------
defined_types = set()
c2rffi_type_map = {
    'char*': 'rffi.CCHARP',

    'void': 'lltype.Void',
    'int8_t': 'rffi.CHAR',
    'uint8_t': 'rffi.UCHAR',
    'int16_t': 'rffi.SHORT',
    'uint16_t': 'rffi.USHORT',
    'int32_t': 'rffi.INT',
    'uint32_t': 'rffi.UINT',
    'int64_t': 'rffi.LONG',
    'uint64_t': 'rffi.ULONG',
    'int': 'rffi.INT',
    'float': 'rffi.FLOAT',
    'double': 'rffi.DOUBLE',

    'void*': 'rffi.VOIDP',
    'int8_t*': 'rffi.CHARP',
    'uint8_t*': 'rffi.UCHARP',
    'int16_t*': 'rffi.SHORTP',
    'uint16_t*': 'rffi.USHORTP',
    'int32_t*': 'rffi.INTP',
    'uint32_t*': 'rffi.UINTP',
    'int64_t*': 'rffi.LONGP',
    'uint64_t*': 'rffi.ULONGP',
    'int*': 'rffi.INTP',
    'float*': 'rffi.FLOATP',
    'double*': 'rffi.DOUBLEP',

    '_MuCFP_Func*': 'rffi.VOIDP',
    'uintptr_t': 'rffi.UINTPTR_T',
    }

idt = ' ' * 4
def map_type(c_type):
    if c_type in defined_types:
        return c_type
    if c_type.endswith('*') and c_type[:-1] in defined_types:
        return c_type.replace('*', 'Ptr')
    if c_type in c2rffi_type_map:
        return c2rffi_type_map[c_type]
    raise KeyError("Can not map type %(c_type)s" % locals())

def gen_typedefs(db, fp):
    specially_defined_types = {'MuValuesFreer', 'MuTrapHandler', 'MuBinOptr', 'MuCmpOptr', 'MuConvOptr', 'MuMemOrd',
                               'MuAtomicRMWOptr', 'MuCallConv', 'MuCommInst', 'MuTypeNode'}

    def define_type(type_name, type_def):
        fp.write('%(type_name)s = %(type_def)s\n' % locals())
        fp.write('%(type_name)sPtr = rffi.CArrayPtr(%(type_name)s)\n' % locals())
        defined_types.add(type_name)
        defined_types.add(type_name + 'Ptr')

    tdb = db['typedefs_order']

    # common types
    for type_name, cdefstr in tdb:
        if not type_name in specially_defined_types:
            defstr = map_type(cdefstr)
            define_type(type_name, defstr)

    define_type('MuTypeNode', 'MuID')   # somehow MuTypeNode is left out?

    # specially defined types
    define_type('MuValuesFreer',
                'rffi.CCallback([MuValuePtr, MuCPtr], lltype.Void)')

    define_type('MuVM', 'lltype.ForwardReference()')
    define_type('MuCtx', 'lltype.ForwardReference()')
    define_type('MuIRBuilder', 'lltype.ForwardReference()')

    define_type('MuTrapHandler',
"""\
rffi.CCallback([
    MuCtxPtr, MuThreadRefValue, MuStackRefValue, MuWPID,   # input
    MuTrapHandlerResultPtr, MuStackRefValuePtr, rffi.CArray(MuValuePtr), MuArraySizePtr,
    MuValuesFreerPtr, MuCPtrPtr, MuRefValuePtr,             # output
    MuCPtr  #input
], lltype.Void)""")

    # type classes
    def define_type_class(type_class, defstr):
        fp.write(defstr + '\n')
        defined_types.add(type_class)

    define_type_class('MuFlag',
"""\
class MuFlag:
    _lltype = rffi.UINT
    def __getattribute__(self, attr):
        return rffi.cast(MuFlag._lltype, object.__getattribute__(self, attr))
""")


# ------------------------------------------------------------
def gen_enums(db, fp):
    for enum in db['enums']:

        _removable_prefixes = ['BINOP', 'CMP', 'CONV', 'ORD', 'ARMW', 'CC', 'CI_UVM']

        fp.write('class _%(name)sCls(MuFlag):\n' % enum)

        for valdef in enum['defs']:
            defname = valdef['name']
            value = valdef['value']
            # remove prefixes
            defname = defname[3:]  # MU_
            try:
                prefix = next(filter(lambda p: defname.startswith(p),
                                     _removable_prefixes))
                defname = defname[len(prefix) + 1:]
            except StopIteration:
                pass

            fp.write(idt + '%(defname)s = %(value)s\n' % locals())

        fp.write('%(name)s = _%(name)sCls()\n' % enum)

        defined_types.add(enum['name'])


# ------------------------------------------------------------
def gen_structs(db, fp):
    for stt in db['structs']:
        fp.write('%(name)s.become(rffi.CStruct(\n' % stt)
        fp.write(idt + '\'%(name)s\',\n' % stt)
        fp.write(idt + '(\'header\', rffi.VOIDP),\n')
        for mtd in stt['methods']:
            prm_ts = [p['type'] for p in mtd['params']]
            prm_ts = list(map(map_type, prm_ts))
            rtn_t = map_type(mtd['ret_ty'])
            fp.write(idt + '(\'%(name)s\', rffi.CCallback(%(arg_ts)s, %(ret_t)s)\n' % {
                "name": mtd['name'],
                "arg_ts": prm_ts,
                "ret_t": rtn_t
            })
        fp.write(')\n')
# ------------------------------------------------------------
def main(argv):
    with open(argv[1], 'r') as fp:
        db = parse_muapi(fp.read())

    gen_typedefs(db, sys.stdout)
    gen_enums(db, sys.stdout)
    gen_structs(db, sys.stdout)

if __name__ == '__main__':
    main(sys.argv)
