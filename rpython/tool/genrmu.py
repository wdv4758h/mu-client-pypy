from muapiparser import parse_muapi
from pprint import PrettyPrinter
import sys
pprint = PrettyPrinter().pprint

idt = ' ' * 4
# ------------------------------------------------------------
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
muapi2rmu_type_map = {}

def get_rmu_def(c_type):
    if c_type in c2rffi_type_map:
        return c2rffi_type_map[c_type]
    if c_type in muapi2rmu_type_map:
        return muapi2rmu_type_map[c_type]
    if c_type in enum_types:
        return "MuFlag"

    raise KeyError("Can not map type %(c_type)s" % locals())

def gen_typedefs(db, fp):
    def define_type(muapi_t, rmu_t, rmu_def, rffi_ptr_type='rffi.CArrayPtr'):
        muapi2rmu_type_map[muapi_t] = rmu_t
        muapi2rmu_type_map[muapi_t + '*'] = rmu_t + 'Ptr'
        fp.write('%(rmu_t)s = %(rmu_def)s\n' % locals())
        fp.write('%(rmu_t)sPtr = %(rffi_ptr_type)s(%(rmu_t)s)\n' % locals())

    tdb = db['typedefs_order']
    specially_defined_types = {'MuValuesFreer', 'MuTrapHandler', 'MuBinOptr', 'MuCmpOptr', 'MuConvOptr',
                               'MuDestKind', 'MuMemOrd', 'MuAtomicRMWOptr', 'MuCallConv', 'MuCommInst'}

    fp.write('# -------------------------------------------------------------------------------------------------------\n')
    fp.write('# Type definitions\n')

    # common types
    for muapi_t, c_type in tdb:
        if not muapi_t in specially_defined_types:
            # print('%(c_type)s -> %(muapi_t)s' % locals())
            rffi_def = get_rmu_def(c_type)
            define_type(muapi_t, muapi_t, rffi_def)

    # specially defined types
    define_type('MuVM', '_MuVM', 'lltype.ForwardReference()', 'lltype.Ptr')
    define_type('MuCtx', '_MuCtx', 'lltype.ForwardReference()', 'lltype.Ptr')
    define_type('MuIRBuilder', '_MuIRBuilder', 'lltype.ForwardReference()', 'lltype.Ptr')

    define_type('MuValuesFreer', 'MuValuesFreer',
                'rffi.CCallback([MuValuePtr, MuCPtr], lltype.Void)')


    define_type('MuTrapHandler', 'MuTrapHandler',
"""\
rffi.CCallback([
    _MuCtxPtr, MuThreadRefValue, MuStackRefValue, MuWPID,   # input
    MuTrapHandlerResultPtr, MuStackRefValuePtr, rffi.CArray(MuValuePtr), MuArraySizePtr,
    MuValuesFreerPtr, MuCPtrPtr, MuRefValuePtr,             # output
    MuCPtr  #input
], lltype.Void)""")


    fp.write('\n')


# ------------------------------------------------------------
enum_types = set()
def gen_enums(db, fp):
    fp.write('# -------------------------------------------------------------------------------------------------------\n')
    fp.write('# Flags\n')
    for enum in db['enums']:
        if len(enum['defs']) == 0:
            continue
        _removable_prefixes = ['BINOP', 'BOS', 'CMP', 'CONV', 'ORD', 'ARMW', 'CC', 'CI_UVM']

        fp.write('class %(name)s:\n' % enum)
        enum_types.add(enum['name'])
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

            fp.write(idt + '%(defname)s = rffi.cast(MuFlag, %(value)s)\n' % locals())


    fp.write('\n')
    fp.write("MU_NO_ID = rffi.cast(MuID, 0)\n")
    fp.write('\n')


# ------------------------------------------------------------
def gen_structs(db, fp):
    def get_prm_type(c_type):
        try:
            return get_rmu_def(c_type)
        except KeyError as e:
            if c_type in enum_types:
                return 'MuFlag'
            raise e

    fp.write('# -------------------------------------------------------------------------------------------------------\n')
    fp.write('# Structs\n')
    for stt in db['structs']:
        fp.write('_%(name)s.become(rffi.CStruct(\n' % stt)
        fp.write(idt + '\'%(name)s\',\n' % stt)
        fp.write(idt + '(\'header\', rffi.VOIDP),\n')
        for mtd in stt['methods']:
            prm_ts = [get_prm_type(p['type']) for p in mtd['params']]
            for idx in range(len(prm_ts)):
                if prm_ts[idx] in enum_types:
                    prm_ts[idx] = 'MuFlag'
            rtn_t = get_prm_type(mtd['ret_ty'])
            fp.write(idt + '(\'%(name)s\', rffi.CCallback(%(arg_ts)s, %(ret_t)s)),\n' % {
                "name": mtd['name'],
                "arg_ts": '[%s]' % ', '.join(prm_ts),
                "ret_t": rtn_t
            })
        fp.write('))\n')

    fp.write('\n')


# ------------------------------------------------------------
struct_attr = {
    'MuVM': '_mu',
    'MuCtx': '_ctx',
    'MuIRBuilder': '_bldr'
}

_rmu2rpy_type_map = {
    'rffi.CCHARP': 'str',
    'MuCString': 'str',
    'MuName': 'str',
    'rffi.CHAR': 'int',
    'rffi.UCHAR': 'int',
    'rffi.SHORT': 'int',
    'rffi.USHORT': 'int',
    'rffi.INT': 'int',
    'rffi.UINT': 'int',
    'rffi.LONG': 'int',
    'rffi.ULONG': 'int',
    'rffi.FLOAT': 'float',
    'rffi.DOUBLE': 'float',
    'MuBool': 'bool',
    'lltype.Void': 'None',
    '_MuVMPtr': 'MuVM',
    '_MuCtxPtr': 'MuCtx',
    '_MuIRBuilderPtr': 'MuIRBuilder'
}

def get_rpyparam_type(prm):
    c_t = prm['type']
    rmu_t = prm['rmu_type']
    rpy_t = _rmu2rpy_type_map.get(rmu_t, rmu_t)
    if rpy_t == rmu_t and prm.get('array_sz_param'):
        assert c_t.endswith('*'), prm
        t = get_rmu_def(c_t[:-1])
        elm_t = _rmu2rpy_type_map.get(t, t)
        rpy_t = '[%(t)s]' % locals()

    return rpy_t

def get_rpyreturn_type(ret_rmu_t):
    return _rmu2rpy_type_map.get(ret_rmu_t, ret_rmu_t)

def _oogen_method(opts, sttname, mtd, fp):
    for p in mtd['params']:
        p['rmu_type'] = get_rmu_def(p['type'])
        p['rpy_type'] = get_rpyparam_type(p)
    mtd['ret_rmu_type'] = get_rmu_def(mtd['ret_ty'])
    mtd['ret_rpy_type'] = get_rpyreturn_type(mtd['ret_rmu_type'])

    can_opt = True
    for i in range(len(mtd['params']) - 1, -1, -1):
        prm = mtd['params'][i]
        if prm.get('is_optional', False):
            if can_opt:
                prm['rpy_optional'] = True
                prm['rpy_deflval'] = 'None' if prm['rpy_type'] == "str" else 'MU_NO_ID' % prm
        else:
            can_opt = False

    # definition
    rpy_params = list(filter(lambda p: not p.get('is_sz_param', False),
                             mtd['params'][1:]))
    c_params = mtd['params']

    cur_idt = idt
    fp.write(cur_idt + 'def %(mtd_name)s(%(arg_list)s):\n' % {
        'mtd_name': mtd['name'],
        'arg_list': ', '.join(['self'] + [p['name'] if not p.get('rpy_optional', False)
                                                    else '%(name)s=%(rpy_deflval)s' % p
                                          for p in rpy_params])
    })

    cur_idt += idt
    fp.write(cur_idt + '# type: (%(arg_ts)s) -> %(ret_t)s\n' % {
        'arg_ts': ', '.join([p['rpy_type'] for p in rpy_params]),
        'ret_t': mtd['ret_rpy_type']
    })

    # body
    c2rpy_param_map = {}
    for prm in rpy_params:
        c2rpy_param_map[prm['name']] = prm['name']
    c2rpy_param_map[c_params[0]['name']] = 'self.%(attr)s' % \
                                           {'attr': struct_attr[sttname]}
    arrs = []
    for prm in rpy_params:
        if prm['rpy_type'] == 'str':
            fp.write(cur_idt +
                     'with rffi.scoped_str2charp(%(name)s) as %(name)s_buf:\n' % prm)
            cur_idt += idt
            c2rpy_param_map[prm['name']] = prm['name'] + '_buf'
            sz_param_name = prm.get('array_sz_param', None)
            if sz_param_name:
                fp.write(cur_idt +
                         '%(sz_prm)s = rffi.cast(%(sz_type)s, len(%(prm_name)s))\n' % {
                             'sz_prm': sz_param_name,
                             'sz_type': 'MuArraySize',
                             'prm_name': prm['name']
                         })
                c2rpy_param_map[sz_param_name] = sz_param_name
        elif prm['rpy_type'].startswith('['):
            fp.write(cur_idt +
                     '%(prm_name)s_arr, %(prm_name)s_sz = lst2arr(%(elm_t)s, %(prm_name)s)\n' % {
                         'elm_t': prm['rpy_type'][1:-1],
                         'prm_name': prm['name']
                     })
            c2rpy_param_map[prm['name']] = prm['name'] + '_arr'
            c2rpy_param_map[prm['array_sz_param']] = prm['name'] + '_sz'
            arrs.append(prm['name'] + '_arr')
        elif prm['rpy_type'] in ('int', 'float', 'bool'):
            fp.write(cur_idt +
                     '%(name)s_c = rffi.cast(%(rmu_type)s, %(name)s)\n' % prm)
            c2rpy_param_map[prm['name']] = prm['name'] + '_c'

    call_str = 'self.%(attr)s.c_%(mtd_name)s(%(args)s)' % {
        'attr': struct_attr[sttname],
        'mtd_name': mtd['name'],
        'args': ', '.join([c2rpy_param_map[p['name']] for p in c_params])
    }

    res_str = call_str
    if mtd['ret_rpy_type'] in ('int', 'float', 'bool'):
        res_str = '%(ret_t)s(%(res_str)s)' % {'ret_t': mtd['ret_rpy_type'], 'res_str': res_str}
    elif mtd['ret_rpy_type'] == 'str':
        res_str = 'rffi.charp2str(%(res_str)s)' % locals()
    elif mtd['ret_rpy_type'] in ('MuCtx', 'MuIRBuilder'):
        res_str = '%(ret_t)s(self, %(res_str)s)' % {'ret_t': mtd['ret_rpy_type'], 'res_str': res_str}

    if mtd['ret_rpy_type'] != 'None':
        res_str = 'res = %(res_str)s' % locals()
    fp.write(cur_idt + res_str + '\n')

    if opts.impl == 'ref':
    # Mu error handling in reference implementation
        if mtd['name'] != 'get_mu_error_ptr':   # otherwise there will be infinite recursion...
            fp.write(cur_idt + 'muerrno = %(mu)s.get_errno()\n' % {
                'mu': 'self' if sttname == "MuVM" else "self._mu"
            })
            fp.write(cur_idt + 'if muerrno:\n')
            fp.write(cur_idt + idt + 'raise MuRuntimeError(muerrno)\n')

    for arr in arrs:
        fp.write(cur_idt + 'if %(arr)s:\n' % locals())
        fp.write(cur_idt + idt + 'lltype.free(%(arr)s, flavor=\'raw\')\n' % locals())

    if mtd['ret_rpy_type'] != 'None':
        fp.write(cur_idt + 'return res\n')

    fp.write('\n')


def _gen_struct_extras(opts, stt, db, fp):
    if opts.impl == 'ref':
        if stt['name'] == 'MuVM':
            fp.write(
                "    def get_errno(self):\n"
                "        # type: () -> int\n"
                "        return int(self._mu_errno_ptr[0])\n"
                "\n"
            )
            fp.write(
                "    def close(self):\n"
                "        mu_close(self._mu)\n"
                "\n"
            )

def gen_oowrapper(opts, db, fp):
    fp.write(
        '# -------------------------------------------------------------------------------------------------------\n')
    fp.write('# OO wrappers\n')
    if opts.impl == 'ref':
        init_funcs = {
            'MuVM':
                ("    def __init__(self, config_str=\"\"):\n"
                 "        with rffi.scoped_str2charp(config_str) as buf:\n"
                 "            self._mu = mu_new_ex(buf)\n"
                 "        self._mu_errno_ptr = rffi.cast(rffi.CArrayPtr(rffi.INT), self.get_mu_error_ptr())\n"
                 "\n"),
            'MuCtx':
                ("    def __init__(self, mu, rffi_ctx_ptr):\n"
                 "        self._mu = mu\n"
                 "        self._ctx = rffi_ctx_ptr\n"
                 "\n"),
            'MuIRBuilder':
                ("    def __init__(self, ctx, rffi_bldr_ptr):\n"
                 "        self._mu = ctx._mu\n"
                 "        self._bldr = rffi_bldr_ptr\n"
                 "\n")
        }
        fp.write(
            "class MuRuntimeError(Exception):\n"
            "    def __init__(self, muerrno):\n"
            "        self.muerrno = muerrno\n"
            "\n"
            "    def __str__(self):\n"
            "        return 'Error thrown in Mu: %d' % self.muerrno \n"
            "\n"
        )
    else:
        init_funcs = {
            'MuVM':
                ("    def __init__(self):\n"
                 "        self._mu = mu_new()\n"
                 "\n"),
            'MuCtx':
                ("    def __init__(self, mu, rffi_ctx_ptr):\n"
                 "        self._mu = mu\n"
                 "        self._ctx = rffi_ctx_ptr\n"
                 "\n"),
            'MuIRBuilder':
                ("    def __init__(self, ctx, rffi_bldr_ptr):\n"
                 "        self._mu = ctx._mu\n"
                 "        self._bldr = rffi_bldr_ptr\n"
                 "\n")
        }
    for stt in db['structs']:
        fp.write('class %(name)s:\n' % stt)
        fp.write(init_funcs[stt['name']])
        for mtd in stt['methods']:
            _oogen_method(opts, stt['name'], mtd, fp)
        _gen_struct_extras(opts, stt, db, fp)
        fp.write('\n')


# ------------------------------------------------------------
def gen_extras(opts, db, fp):
    fp.write('# -------------------------------------------------------------------------------------------------------\n')
    if opts.impl == 'ref':
        fp.write('# Mu reference implementation functions\n')
        fp.write(
    """\
mu_new = rffi.llexternal('mu_refimpl2_new', [], _MuVMPtr, compilation_info=eci)
mu_new_ex = rffi.llexternal('mu_refimpl2_new_ex', [rffi.CCHARP], _MuVMPtr, compilation_info=eci)
mu_close = rffi.llexternal('mu_refimpl2_close', [_MuVMPtr], lltype.Void, compilation_info=eci)
""")
    else:
        fp.write('# Mu fast implementation functions\n')
        fp.write(
            """\
mu_new = rffi.llexternal('mu_fastimpl_new', [], _MuVMPtr, compilation_info=eci)
""")
    fp.write('\n')
    fp.write(
"""\
# -------------------------------------------------------------------------------------------------------
# Helpers
def null(rmu_t):
    return lltype.nullptr(rmu_t.TO)

@specialize.ll()
def lst2arr(ELM_T, lst):
    sz = rffi.cast(MuArraySize, len(lst))

    if len(lst) == 0:
        buf = lltype.nullptr(rffi.CArray(ELM_T))
    else:
        buf = lltype.malloc(rffi.CArray(ELM_T), len(lst), flavor='raw')
        for i, e in enumerate(lst):
            buf[i] = rffi.cast(ELM_T, e)

    return buf, sz
"""

    )

    fp.write('\n')


# ------------------------------------------------------------
def gen_header(opts, db, fp):
    if opts.impl == 'ref':
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
from rpython.rlib.objectmodel import specialize
import os

mu_dir = os.path.join(os.getenv('MU'), 'cbinding')
eci = ExternalCompilationInfo(includes=['refimpl2-start.h', 'muapi.h'],
                              include_dirs=[mu_dir],
                              libraries=['murefimpl2start'],
                              library_dirs=[mu_dir])

"""
        )
    else:
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
from rpython.rlib.objectmodel import specialize
import os

libmu_dir = os.path.join(os.getenv('MU_RUST'), 'target', 'debug')
muapi_dir = os.path.join(os.getenv('MU_RUST'), 'src', 'vm', 'api')
eci = ExternalCompilationInfo(includes=['muapi.h'],
                              include_dirs=[muapi_dir],
                              libraries=['mu'],
                              library_dirs=[libmu_dir])

"""
        )

    fp.write('\n')


# ------------------------------------------------------------
def main(opts):
    with open(opts.api_h, 'r') as fp:
        db = parse_muapi(fp.read())

    gen_header(opts, db, sys.stdout)
    gen_typedefs(db, sys.stdout)
    gen_enums(db, sys.stdout)
    gen_oowrapper(opts, db, sys.stdout)

    gen_structs(db, sys.stdout)
    gen_extras(opts, db, sys.stdout)

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--impl', choices=['ref', 'fast'], required=True, help='Select targetting Mu implementation')
    parser.add_argument('api_h', help='Path to muapi.h')
    main(parser.parse_args())
