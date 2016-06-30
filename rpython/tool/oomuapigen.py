from __future__ import print_function
from muapiparser import parse_muapi
from pprint import PrettyPrinter
from collections import OrderedDict

pprint = PrettyPrinter().pprint
idts = " " * 4

def c2rpytype(cty):
    _map = {
        "void": "lltype.Void",
        "void*": "rffi.VOIDP",
        "char": "rffi.CHAR",
        "int8_t": "rffi.CHAR",
        "uint8_t": "rffi.UCHAR",
        "int16_t": "rffi.SHORT",
        "uint16_t": "rffi.USHORT",
        "int32_t": "rffi.INT",
        "uint32_t": "rffi.UINT",
        "int64_t": "rffi.LONG",
        "uint64_t": "rffi.ULONG",
        "uintptr_t": "rffi.UINTPTR_T",
        "float": "rffi.FLOAT",
        "double": "rffi.DOUBLE",
        "char*": "rffi.CCHARP",
        "int8_t*": "rffi.CCHARP",
        "uint8_t*": "rffi.UCHARP",
        "int16_t*": "rffi.SHORTP",
        "uint16_t*": "rffi.USHORTP",
        "int32_t*": "rffi.INTP",
        "uint32_t*": "rffi.UINTP",
        "int64_t*": "rffi.LONGP",
        "uint64_t*": "rffi.ULONGP",
        "uintptr_t*": "rffi.UINTPTR_TP",
        "float*": "rffi.FLOATP",
        "double*": "rffi.DOUBLEP",
    }

    if cty in _map:
        return _map[cty]
    if '*' in cty:
        return cty[:-1]

    return cty


def rpy2prmtype(typ):
    _map = {
        "MuName": "str",
        "rffi.CCHARP": "str",
        "rffi.CHAR": "int",
        "rffi.UCHAR": "int",
        "rffi.SHORT": "int",
        "rffi.USHORT": "int",
        "rffi.INT": "int",
        "rffi.UINT": "int",
        "rffi.LONG": "int",
        "rffi.ULONG": "int",
        "rffi.UINTPTR_T": "int",
        "rffi.FLOAT": "float",
        "rffi.DOUBLE": "float"
    }
    if typ in _map:
        return _map[typ]
    if typ[:-1] in _map and typ[-1] == "P":
        return "[%s]" % _map[typ[:-1]]
    return _map.get(typ, typ)


def proc_params(mtd):
    def rpy2rtntype(typ):
        if typ == "lltype.Void":
            return "None"
        return typ

    c_prms = mtd['params'][1:]
    rpy_prms = ['self']
    if len(c_prms) == 0:
        return rpy_prms, [], rpy2rtntype(c2rpytype(mtd['ret_ty']))

    prms = [prm['name'] for prm in c_prms]
    types = list(map(rpy2prmtype, map(c2rpytype, [prm['type'] for prm in c_prms])))
    # process pragmas
    for pragma in mtd['pragmas']:
        if ':array:' in pragma:
            # convert it into a list
            arr_var, sz_var = pragma.split(':array:')
            idx_arr_var = prms.index(arr_var)
            idx_sz_var = prms.index(sz_var)
            prms.remove(sz_var)
            arr_ty = types[idx_arr_var]
            if not (arr_ty == "str" or arr_ty[0] == '['):
                types[idx_arr_var] = '[%s]' % arr_ty
            types.remove(types[idx_sz_var])

    rpy_prms.extend(prms)
    return rpy_prms, types, rpy2rtntype(c2rpytype(mtd['ret_ty']))

def gen_def(mtd):
    print(idts, end='')
    print("def %(name)s" % mtd, end='')
    arg_lst, typ_lst, rtn_t = proc_params(mtd)
    print("({}):".format(', '.join(arg_lst)))
    print(idts * 2, end='')
    print("# type: ({arg_ts}) -> {rtn_t}".format(arg_ts=', '.join(typ_lst), rtn_t=rtn_t))

def gen_body(mtd):
    pass

def main(argv):
    with open(argv[1], 'r') as fp:
        api = parse_muapi(fp.read())

    # Mu
    print("\n"
          "class Mu:\n"
          "    def __init__(self):\n"
          "        self._mu = mu_new()\n")
    stt = api['structs'][0]
    for mtd in stt['methods']:
        gen_def(mtd)
        gen_body(mtd)
        print()

    # MuContext
    print("\n"
          "class MuContext:\n"
          "    def __init__(self, rffi_ctx_ptr):\n"
          "        self._ctx = rffi_ctx_ptr\n")
    stt = api['structs'][1]
    for mtd in stt['methods']:
        gen_def(mtd)

if __name__ == "__main__":
    import sys
    main(sys.argv)