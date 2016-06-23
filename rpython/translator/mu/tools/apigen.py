"""
Use muapiparser.py in Mu spec to parse and generate API
Usage: python3 apigen.py /path/to/muapi.h
"""
from __future__ import print_function
from muapiparser import parse_muapi


def main(argv):
    with open(argv[1], "r") as fp:
        api = parse_muapi(fp.read())
        idt = 4
        for enum in api['enums']:
            print("class %(name)s:" % enum)
            for _def in enum['defs']:
                print(" " * idt, end='')
                print("%(name)s = %(value)s" % _def)

        print('\n')

        stt = next(filter(lambda s: s['name'] == 'MuCtx', api['structs']))  # only taking out MuCtx
        print("class %(name)s:" % stt)
        for fn in stt['methods']:
            print(' ' * idt, end='')
            print("def {name}({arg_lst}):".format(name=fn['name'],
                                                  arg_lst=', '.join(
                                                      ['self'] + [arg['name'] for arg in fn['params'][1:]])))
            print(' ' * idt * 2, end='')
            print("# type: ({arg_ts}) -> {rtn_t}".format(arg_ts=', '.join([arg['type'].replace('*', '')
                                                                           for arg in fn['params'][1:]]),
                                                         rtn_t=fn['ret_ty'].replace('*', '')))
            print(' ' * idt * 2, end='')
            print("raise NotImplementedError")

if __name__ == "__main__":
    import sys
    main(sys.argv)