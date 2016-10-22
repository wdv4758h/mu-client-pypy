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
            fldname = defname
            value = valdef['value']
            # remove prefixes
            fldname = fldname[3:]  # MU_
            try:
                prefix = next(filter(lambda p: fldname.startswith(p),
                                     _removable_prefixes))
                fldname = fldname[len(prefix) + 1:]
            except StopIteration:
                pass

            fp.write(idt + '%(fldname)s = "%(defname)s"\n' % locals())


    fp.write('\n')
    fp.write('MU_NO_ID = "MU_NO_ID"\n')
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

_ctype2basename = {
    'MuID': 'id',
    'MuIntValue': 'hintval',
    'MuFloatValue': 'hfltval',
    'MuDoubleValue': 'hdblval',
    'MuUPtrValue': 'huptrval',
    'MuUFPValue': 'hufpval',
    'MuValue': 'hdl',
    'MuRefValue': 'href',
    'MuIRefValue': 'hiref',
    'MuFuncRefValue': 'hfncref',
    'MuStructValue': 'hstt',
    'MuSeqValue': 'hseq',
    'MuStackRefValue': 'hstkref',
    'MuThreadRefValue': 'hthdref',
    'MuFCRefValue': 'hfcr',
    'MuTagRef64Value': 'htag',
    'MuIRBuilder': 'bldr',
    'MuCtx': 'ctx'
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
                prm['rpy_deflval'] = 'None' if prm['rpy_type'] == "str" else 'MU_NO_ID'
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

    if mtd['ret_rpy_type'] in ('int', 'float', 'bool', 'str'):
        fp.write(cur_idt + '# NOTE: runtime dependent method, '
                           'the return value should not be examined in Python.\n')

    # body
    c2rpy_param_map = {}
    for prm in rpy_params:
        c2rpy_param_map[prm['name']] = prm['name']
    c2rpy_param_map[c_params[0]['name']] = 'self.%(attr)s' % \
                                           {'attr': struct_attr[sttname]}
    arrs = []
    for prm in rpy_params:
        if prm['rpy_type'] == 'str':
            fp.write(cur_idt + '%(name)s_cstr = CStr(%(name)s) if %(name)s else NULL\n' % prm)
            c2rpy_param_map[prm['name']] = prm['name'] + '_cstr'
            sz_param_name = prm.get('array_sz_param', None)
            if sz_param_name:
                fp.write(cur_idt +
                         '%(sz_prm)s = len(%(prm_name)s_cstr)\n' % {
                             'sz_prm': sz_param_name,
                             'prm_name': prm['name']
                         })
                c2rpy_param_map[sz_param_name] = sz_param_name
        elif prm['rpy_type'].startswith('['):
            fp.write(cur_idt +
                     '%(prm_name)s_arr, %(prm_name)s_sz = lst2arr(\'%(c_elm_t)s\', %(prm_name)s)\n' % {
                         'c_elm_t': prm['type'][:-1],
                         'prm_name': prm['name']
                     })
            c2rpy_param_map[prm['name']] = prm['name'] + '_arr'
            c2rpy_param_map[prm['array_sz_param']] = prm['name'] + '_sz'
            arrs.append(prm['name'] + '_arr')
        elif prm['rpy_type'] == 'bool':
            fp.write(cur_idt +
                     '%(name)s_bool = \'true\' if %(name)s else \'false\'\n' % prm)
            c2rpy_param_map[prm['name']] = prm['name'] + '_bool'
        elif prm['rpy_type'] == 'float':    # float needs to be preserved over string
            fp.write(cur_idt +
                     '%(name)s_fltstr = \'%%.20f\' %% %(name)s\n' % prm)
            c2rpy_param_map[prm['name']] = prm['name'] + '_fltstr'

    if mtd['ret_rpy_type'] != 'None':
        basename = _ctype2basename.get(mtd['ret_rpy_type'], 'var')
        fp.write(cur_idt +
                 'res_var = CVar(\'%(ctype)s\', \'%(basename)s\')\n' % {
                     'ctype': mtd['ret_ty'],
                     'basename': basename
                 })
        mtd['ret_var'] = 'res_var'
    else:
        mtd['ret_var'] = 'None'

    call_str = '_apilog.logcall(\'%(mtd_name)s\', [%(args)s], %(rtn_var)s, %(context)s)' % {
        'mtd_name': mtd['name'],
        'args': ', '.join([c2rpy_param_map[p['name']] for p in c_params]),
        'rtn_var': mtd['ret_var'],
        'context': 'self.' + struct_attr[sttname]
    }
    fp.write(cur_idt + call_str + '\n')

    res_str = mtd['ret_var']
    if mtd['ret_rpy_type'] in ('MuCtx', 'MuIRBuilder'):
        res_str = '%(ret_t)s(%(res_var)s)' % {
            'ret_t': mtd['ret_rpy_type'],
            'res_var': mtd['ret_var']
        }

    if res_str != 'None':
        fp.write(cur_idt + 'return %(res_str)s\n' % locals())

    fp.write('\n')


def _gen_struct_extras(opts, stt, db, fp):
    if opts.impl == 'ref':
        if stt['name'] == 'MuVM':
            fp.write(
                "    def close(self):\n"
                "        _apilog.logcall('mu_refimpl2_close', [self._mu], None)\n"
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
                 "        self._mu = CVar('MuVM*', 'mu')\n"
                 "        _apilog.logcall('mu_refimpl2_new_ex', [CStr(config_str)], self._mu, check_err=False)\n"
                 "        muerrno = CVar('int*', 'muerrno')\n"
                 "        _apilog.logcall('get_mu_error_ptr', [self._mu], muerrno, self._mu, check_err=False)\n"
                 "\n"),
            'MuCtx':
                ("    def __init__(self, ctx_var):\n"
                 "        self._ctx = ctx_var"
                 "\n"),
            'MuIRBuilder':
                ("    def __init__(self, bldr_var):\n"
                 "        self._bldr = bldr_var\n"
                 "\n")
        }
    else:
        init_funcs = {
            'MuVM':
                ("    def __init__(self):\n"
                 "        self._mu = CVar('MuVM*', 'mu')\n"
                 "        _apilog.logcall('mu_fastimpl_new', [], self._mu)\n"
                 "\n"),
            'MuCtx':
                ("    def __init__(self, ctx_var):\n"
                 "        self._ctx = ctx_var"
                 "\n"),
            'MuIRBuilder':
                ("    def __init__(self, bldr_var):\n"
                 "        self._bldr = bldr_var\n"
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
def gen_extras(db, fp):
    fp.write(
"""\
# -------------------------------------------------------------------------------------------------------
# Helpers
def null(rmu_t):
    return NULL

def lst2arr(c_elm_t, lst):
    sz = len(lst)
    if len(lst) > 0:
        arr = CArrayConst(c_elm_t, lst)
    else:
        arr = NULL
    return arr, sz
""")

    fp.write('\n')


# ------------------------------------------------------------
def gen_header(opts, db, fp):
    fp.write(
"""\
\"\"\"
Mu API RPython binding with C backend.
This file is auto-generated and then added a few minor modifications.
NOTE: THIS FILE IS *NOT* RPYTHON.
\"\"\"

from rpython.rtyper.lltypesystem import rffi
from rpython.rtyper.lltypesystem import lltype

class CCall(object):
    __slots__ = ('fnc_name', 'args', 'rtn_var', 'context', 'check_err')

    def __init__(self, fnc_name, args, rtn_var, context=None, check_err=True):
        self.fnc_name = fnc_name
        self.args = args
        self.rtn_var = rtn_var
        self.context = context
        self.check_err = check_err

    def __str__(self):
        s = '{rtn_stm}{ctx}{fnc}({arg_lst})'.format(rtn_stm='%s = ' % self.rtn_var if self.rtn_var else '',
                                                    fnc=self.fnc_name,
                                                    arg_lst=', '.join(map(str, self.args)),
                                                    ctx='%s->' % self.context if self.context else '')
        if self.check_err:
            s = "CHECK(%s)" % s
        else:
            s = s + ";"
        return s

    __repr__ = __str__

class CStr(object):
    __slots__ = ('string', )

    def __init__(self, string):
        self.string = string

    def __str__(self):
        return '"%s"' % self.string

    def __len__(self):
        return len(self.string) - self.string.count('\\\\n')

    __repr__ = __str__

NULL = 'NULL'

class CArrayConst(object):
    def __init__(self, c_elm_t, lst):
        self.c_elm_t = c_elm_t
        self.lst = lst

    def __str__(self):
        return '({type}){value}'.format(type='%s [%d]' % (self.c_elm_t, len(self.lst)),
                                        value='{%s}' % ', '.join(map(str, self.lst)))

    __repr__ = __str__

class CVar(object):
    __slots__ = ('type', 'name')
    _name_dic = {}

    @staticmethod
    def new_name(base='var'):
        nd = CVar._name_dic
        if base in nd:
            count = nd[base]
            nd[base] += 1
            return '%(base)s_%(count)d' % locals()
        else:
            count = 2
            nd[base] = count
            return base

    def __init__(self, c_type, var_name=None):
        self.type = c_type
        if var_name:
            self.name = CVar.new_name(var_name)
        else:
            self.name = CVar.new_name()

    def __str__(self):
        return self.name

    __repr__ = __str__
"""
    )
    if opts.impl == 'ref':
        fp.write(
"""\
class APILogger:
    def __init__(self):
        self.ccalls = []
        self.decl_vars = []

    def logcall(self, fnc_name, args, rtn_var, context=None, check_err=True):
        self.ccalls.append(CCall(fnc_name, args, rtn_var, context, check_err))
        if rtn_var:
            self.decl_vars.append(rtn_var)
    def genc(self, fp, exitcode=0):
        fp.write('\\n'
                 '// Compile with flag -std=c99\\n'
                 '#include <stdio.h>\\n'
                 '#include <stdlib.h>\\n'
                 '#include <stdbool.h>\\n'
                 '#include "muapi.h"\\n'
                 '#include "refimpl2-start.h"\\n')
        fp.write('''
#define CHECK(line) line; \\\\
    if (*muerrno) {\\\\
        fprintf(stderr, "Line %d: Error thrown in Mu: %d\\\\n", \\\\
                __LINE__, *muerrno); \\\\
        exit(1); \\\\
    }\\\n
'''
        )
        fp.write('int main(int argc, char** argv) {\\n')
        idt = ' ' * 4
        for var in self.decl_vars:
            fp.write(idt + '%s %s;\\n' % (var.type, var.name))

        for ccall in self.ccalls:
            fp.write(idt + '%(ccall)s\\n' % locals())
        fp.write(idt + 'return %(exitcode)s;\\n' % locals())
        fp.write('}\\n')
"""
    )
    else:
        fp.write(
"""\
class APILogger:
    def __init__(self):
        self.ccalls = []
        self.decl_vars = []

    def logcall(self, fnc_name, args, rtn_var, context=None):
        self.ccalls.append(CCall(fnc_name, args, rtn_var, context, False))
        if rtn_var:
            self.decl_vars.append(rtn_var)
    def genc(self, fp, exitcode=0):
        fp.write('\\n'
                 '// Compile with flag -std=c99\\n'
                 '#include <stdio.h>\\n'
                 '#include <stdlib.h>\\n'
                 '#include <stdbool.h>\\n'
                 '#include "muapi.h"\\n'
                 '#include "mu-fastimpl.h"\\n')

        fp.write('int main(int argc, char** argv) {\\n')
        idt = ' ' * 4
        for var in self.decl_vars:
            fp.write(idt + '%s %s;\\n' % (var.type, var.name))

        for ccall in self.ccalls:
            fp.write(idt + '%(ccall)s\\n' % locals())
        fp.write(idt + 'return %(exitcode)s;\\n' % locals())
        fp.write('}\\n')
"""
        )

    fp.write(
"""\
_apilog = APILogger()
def get_global_apilogger():
    return _apilog
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

    # gen_structs(db, sys.stdout)
    gen_extras(db, sys.stdout)

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--impl', choices=['ref', 'fast'], required=True, help='Select targetting Mu implementation')
    parser.add_argument('api_h', help='Path to muapi.h')
    main(parser.parse_args())
