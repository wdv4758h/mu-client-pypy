import ctypes
import libmu

import argparse
import zipfile
import json


def slurp(filename):
    with open(filename) as t:
        return t.read()

SIZES = {
        "k": 1024**1,
        "m": 1024**2,
        "g": 1024**3,
        "t": 1024**4,
        }

def parse_size(sz_str):
    sz_str = sz_str.lower()

    for k,v in SIZES.items():
        if sz_str.endswith(k):
            num = int(sz_str[:-1]) * v
            break
    else:
        num = int(sz_str)

    return num

def get_vm_opts(ns):
    rv = {}
    for k in ["sosSize", "losSize", "globalSize", "stackSize", "vmLog", "gcLog"]:
        if hasattr(ns, k):
            v = getattr(ns, k)
            if v is not None:
                rv[k] = v

    rv['staticCheck'] = not ns.noCheck
    rv['sourceInfo'] = not ns.noSourceInfo

    return rv

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sosSize', type=parse_size,
                        help="small object space size (bytes). May have k, m, g or t as suffix. 1KiB=1024B")
    parser.add_argument('--losSize', type=parse_size,
                        help="large object space size (bytes)")
    parser.add_argument('--globalSize', type=parse_size,
                        help="global memory space size (bytes)")
    parser.add_argument('--stackSize', type=parse_size,
                        help="stack size (bytes). Size of each stack. Must be at least 8192 bytes.")
    parser.add_argument('--vmLog', choices="ALL, TRACE, DEBUG, INFO, WARN, ERROR, OFF".split(', '),
                        help="micro VM logging level.")
    parser.add_argument('--gcLog', choices="ALL, TRACE, DEBUG, INFO, WARN, ERROR, OFF".split(', '),
                        help="GC logging level (see vmLog).")
    parser.add_argument('--noCheck', action='store_true',
                        help="Skip static checking before VM execution.")
    parser.add_argument('--noSourceInfo', action='store_true',
                        help="""Do not generate source information when parsing.
                        Source information records and shows the line and column
                        of each identified entity. It is helpful when debugging,
                        but is very time-consumimg to generate. Disable it when
                        the bundle is big.""")
    parser.add_argument('--checkOnly', action='store_true',
                        help="Only run the static checker on the bundle without executing it.")
    parser.add_argument('bundle', help="generated RPython Mu bundle")
    parser.add_argument('prog_args', nargs='*', help="program arguments")
    return parser.parse_args()


def extract_bundle(bdl):
    zf = zipfile.ZipFile(bdl, 'r')
    ir, hail, info = map(zf.read, zf.namelist()[:3])    # disregard the 4-th text graph file.
    zf.close()
    return ir, hail, json.loads(info)


def get_c_args(ctx, args, info):
    length = len(args)
    argc = ctx.handle_from_int(length, 32)
    buf = (ctypes.c_char_p * length)()
    for i in range(length):
        arg = args[i]
        buf[i] = ctypes.cast(ctypes.create_string_buffer(arg), ctypes.c_char_p)

    argv = ctx.handle_from_ptr(ctx.id_of(info['argv_t']), ctypes.cast(buf, ctypes.c_void_p))
    return argc, argv


def launch(cmdargs, ir, hail, info, args):
    dll = libmu.MuRefImpl2StartDLL("libmurefimpl2start.so")
    vmopts = get_vm_opts(cmdargs)
    vmopts['extraLibs'] = info['libdeps']
    mu = dll.mu_refimpl2_new_ex(**vmopts)

    with mu.new_context() as ctx:
        ctx.load_bundle(ir)
        ctx.load_hail(hail)

        if cmdargs.checkOnly:
            return 0

        argc, argv = get_c_args(ctx, args, info)
        bundle_entry = ctx.handle_from_func(ctx.id_of(info['entrypoint']))
        st = ctx.new_stack(bundle_entry)
        th = ctx.new_thread(st, None, libmu.PassValues(argc, argv))

        mu.execute()

        # irefrtnbox = ctx.get_iref(refrtnbox)
        # hrtnval = ctx.load(irefrtnbox).cast(MuIntValue)
        # rtnval = ctx.handle_to_sint(hrtnval)
        #
        # # print("Program exited with value %(rtnval)d" % locals())
        # return rtnval
        return 0


def main():
    cmdargs = parse_args()
    rtnval = launch(cmdargs, *extract_bundle(cmdargs.bundle), args=[cmdargs.bundle] + cmdargs.prog_args)
    return rtnval


if __name__ == "__main__":
    import sys
    exitcode = main()
    sys.exit(exitcode)
