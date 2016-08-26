from muapiparser import parse_muapi
from pprint import PrettyPrinter
from collections import OrderedDict
from copy import copy
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
    if c_type in c2rffi_type_map:
        return c2rffi_type_map[c_type]

    if c_type.endswith('*'):
        c_type = c_type.replace('*', 'Ptr')

    if c_type in defined_types:
        return c_type

    if '_' + c_type in defined_types:       # prefix the structs with '_'
        return '_' + c_type

    raise KeyError("Can not map type %(c_type)s" % locals())

def gen_typedefs(db, fp):
    fp.write('# -------------------------------------------------------------------------------------------------------\n')
    fp.write('# Type definitions\n')
    specially_defined_types = {'MuValuesFreer', 'MuTrapHandler', 'MuBinOptr', 'MuCmpOptr', 'MuConvOptr', 'MuMemOrd',
                               'MuAtomicRMWOptr', 'MuCallConv', 'MuCommInst'}

    def define_type(type_name, type_def, ptr_type='rffi.CArrayPtr'):
        fp.write('%(type_name)s = %(type_def)s\n' % locals())
        fp.write('%(type_name)sPtr = %(ptr_type)s(%(type_name)s)\n' % locals())
        defined_types.add(type_name)
        defined_types.add(type_name + 'Ptr')

    tdb = db['typedefs_order']

    # common types
    for type_name, cdefstr in tdb:
        if not type_name in specially_defined_types:
            defstr = map_type(cdefstr)
            define_type(type_name, defstr)

    # define_type('MuTypeNode', 'MuID')   # somehow MuTypeNode is left out?

    # specially defined types
    define_type('MuValuesFreer',
                'rffi.CCallback([MuValuePtr, MuCPtr], lltype.Void)')


    define_type('_MuVM', 'lltype.ForwardReference()', 'lltype.Ptr')
    define_type('_MuCtx', 'lltype.ForwardReference()', 'lltype.Ptr')
    define_type('_MuIRBuilder', 'lltype.ForwardReference()', 'lltype.Ptr')

    define_type('MuTrapHandler',
"""\
rffi.CCallback([
    _MuCtxPtr, MuThreadRefValue, MuStackRefValue, MuWPID,   # input
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

    fp.write('\n')


# ------------------------------------------------------------
enum_types = ['MuFlag']
def gen_enums(db, fp):
    fp.write('# -------------------------------------------------------------------------------------------------------\n')
    fp.write('# Flags\n')
    for enum in db['enums']:
        if len(enum['defs']) == 0:
            continue
        _removable_prefixes = ['BINOP', 'CMP', 'CONV', 'ORD', 'ARMW', 'CC', 'CI_UVM']

        fp.write('class _%(name)sCls(MuFlag):\n' % enum)
        enum_types.append(enum['name'])
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

    fp.write('\n')


# ------------------------------------------------------------
def gen_structs(db, fp):
    fp.write('# -------------------------------------------------------------------------------------------------------\n')
    fp.write('# Structs\n')
    for stt in db['structs']:
        fp.write('_%(name)s.become(rffi.CStruct(\n' % stt)
        fp.write(idt + '\'_%(name)s\',\n' % stt)
        fp.write(idt + '(\'header\', rffi.VOIDP),\n')
        for mtd in stt['methods']:
            prm_ts = [p['type'] for p in mtd['params']]
            prm_ts = list(map(map_type, prm_ts))
            for idx in range(len(prm_ts)):
                if prm_ts[idx] in enum_types:
                    prm_ts[idx] = 'MuFlag._lltype'
            rtn_t = map_type(mtd['ret_ty'])
            fp.write(idt + '(\'%(name)s\', rffi.CCallback(%(arg_ts)s, %(ret_t)s)),\n' % {
                "name": mtd['name'],
                "arg_ts": '[%s]' % ', '.join(prm_ts),
                "ret_t": rtn_t
            })
        fp.write('))\n')

    fp.write('\n')


# ------------------------------------------------------------
struct_attr = {
    '_MuVMPtr': '_mu',
    '_MuCtxPtr': '_ctx',
    '_MuIRBuilderPtr': '_bldr'
}

def _oogen_method(sttname, mtd, fp):
    # pprint(mtd)
    def get_param_type(t, is_array=False):
        type_map = {
            'char*': 'str',
            'MuCString': 'str',
            'int8_t': 'int',
            'uint8_t': 'int',
            'int16_t': 'int',
            'uint16_t': 'int',
            'int32_t': 'int',
            'uint32_t': 'int',
            'int64_t': 'int',
            'uint64_t': 'int',
            'MuBool': 'bool',
            'void': 'None',
        }
        t = type_map.get(t, t)
        if t.endswith('*'):
            if is_array:   # an array
                elm_t = type_map.get(t[:-1], t[:-1])
                t = '[%(elm_t)s]' % locals()
            else:
                try:
                    t = map_type(t)
                except KeyError:
                    pass
        return t

    # Definition
    rpy_param_type_map = OrderedDict()
    for arg in mtd['params'][1:]:
        if not arg.get('is_sz_param', False):
            rpy_param_type_map[arg['name']] = get_param_type(arg['type'], arg.get('array_sz_param', False))

    # process the optionals
    arg_names = []
    params = copy(mtd['params'])
    params.reverse()
    can_be_optional = True
    for p in params:
        if p['name'] in rpy_param_type_map:
            if p.get('is_optional', False) and can_be_optional:
                arg_names.insert(0, '%(name)s=None' % p)
            else:
                arg_names.insert(0, '%(name)s' % p)
                can_be_optional = False
    # arg_names = [p['name'] for p in mtd['params'][1:]]
    arg_names.insert(0, 'self')
    fp.write(idt + 'def {}({}):\n'.format(
        mtd['name'],
        ', '.join(arg_names)
    ))
    fp.write(idt * 2 + '# type: ({}) -> {}\n'.format(
        ', '.join(rpy_param_type_map.values()),
        get_param_type(mtd['ret_ty'])
    ))
    org_mtd_type_map = OrderedDict()
    for p in mtd['params']:
        org_mtd_type_map[p['name']] = p['type']

    # Body
    cur_idt = idt * 2
    scoped_conv_map = {}
    for prm, prm_t in rpy_param_type_map.items():
        if prm_t == 'str':
            buf_var = prm + '_buf'
            scoped_conv_map[prm] = buf_var
            fp.write(cur_idt +
                     'with rffi.scoped_str2charp(%(prm)s) as %(buf_var)s:\n' %
                        locals())
            cur_idt += idt
        elif prm_t.startswith('['):  # a list
            elm_t = prm_t[1:-1]
            arr_var = prm + '_arr'
            sz_var = prm + '_sz'
            scoped_conv_map[prm] = (arr_var, sz_var)
            fp.write(cur_idt +
                     'with scoped_lst2arr(%(elm_t)s, %(prm)s) as (%(arr_var)s, %(sz_var)s):\n' %
                        locals())
            cur_idt += idt
        elif prm_t in ('int', 'float', 'double'):
            cast_var = prm + '_c'
            cast_t = map_type(org_mtd_type_map[prm])
            scoped_conv_map[prm] = cast_var
            fp.write(cur_idt +
                    '%(cast_var)s = rffi.cast(%(cast_t)s, %(prm)s)\n' % locals())


    stt_attr = struct_attr[map_type(mtd['params'][0]['type'])]
    mtd_name = mtd['name']
    call_args = []
    for prm, prm_t in rpy_param_type_map.items():
        if not prm in scoped_conv_map:
            call_args.append(prm)
        elif isinstance(scoped_conv_map[prm], str):
            call_args.append(scoped_conv_map[prm])
        elif isinstance(scoped_conv_map[prm], tuple):
            call_args.extend(scoped_conv_map[prm])
    call_args_str = ', '.join(call_args)
    call_str = 'self.%(stt_attr)s.c_%(mtd_name)s(%(call_args_str)s)\n' % locals()

    ret_t = get_param_type(mtd['ret_ty']) in ('int', 'float', 'bool')
    if ret_t in ('int', 'float', 'bool'):
        call_str = '%(ret_t)s(%(call_str)s)' % locals()

    if mtd['ret_ty'] != 'void':
        fp.write(cur_idt + 'return ' + call_str)
    else:
        fp.write(cur_idt + call_str)

    fp.write('\n')


def gen_oowrapper(db, fp):
    fp.write('# -------------------------------------------------------------------------------------------------------\n')
    fp.write('# OO wrappers\n')
    init_funcs = {
        'MuVM':
"""\
    def __init__(self, config_str=""):
        with rffi.scoped_str2charp(config_str) as buf:
            self._mu = mu_new_ex(buf)
""",
        'MuCtx':
"""\
    def __init__(self, rffi_ctx_ptr):
        self._ctx = rffi_ctx_ptr
""",
        'MuIRBuilder':
"""\
    def __init__(self, rffi_ctx_ptr):
        self._ctx = rffi_ctx_ptr
        self._bldr = self._ctx.c_new_ir_builder(self._ctx)
"""
    }

    for stt in db['structs']:
        fp.write('class %(name)s:\n' % stt)
        fp.write(init_funcs[stt['name']])
        for mtd in stt['methods']:
            _oogen_method(stt['name'], mtd, fp)

    fp.write('\n')


# ------------------------------------------------------------
def gen_extras(db, fp):
    fp.write('# -------------------------------------------------------------------------------------------------------\n')
    fp.write('# Mu reference implementation functions\n')
    fp.write(
"""\
mu_new = rffi.llexternal('mu_refimpl2_new', [], _MuVMPtr, compilation_info=eci)
mu_new_ex = rffi.llexternal('mu_refimpl2_new_ex', [rffi.CCHARP], _MuVMPtr, compilation_info=eci)
mu_close = rffi.llexternal('mu_refimpl2_close', [_MuVMPtr], lltype.Void, compilation_info=eci)
""")
    fp.write('\n')
    fp.write(
"""\
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
"""

    )

    fp.write('\n')


# ------------------------------------------------------------
def gen_header(db, fp):
    fp.write(
"""\
\"\"\"
Mu API RPython binding.
This file is auto-generated and then added a few minor modifications.
Note: environment variable $MU needs to be defined to point to the reference implementation!
\"\"\"

from rpython.rtyper.lltypesystem import rffi
from rpython.rtyper.lltypesystem import lltype
from rpython.translator.tool.cbuild import ExternalCompilationInfo
import os

mu_dir = os.path.join(os.getenv('MU'), 'cbinding')
eci = ExternalCompilationInfo(includes=['refimpl2-start.h', 'muapi.h'],
                              include_dirs=[mu_dir],
                              libraries=['murefimpl2start'],
                              library_dirs=[mu_dir])

"""
    )

    fp.write('\n')


# ------------------------------------------------------------
def main(argv):
    with open(argv[1], 'r') as fp:
        db = parse_muapi(fp.read())

    gen_header(db, sys.stdout)
    gen_typedefs(db, sys.stdout)
    gen_enums(db, sys.stdout)
    gen_oowrapper(db, sys.stdout)

    gen_structs(db, sys.stdout)
    gen_extras(db, sys.stdout)

if __name__ == '__main__':
    main(sys.argv)
