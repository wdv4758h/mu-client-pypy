from __future__ import division, absolute_import, print_function, unicode_literals
import sys

import ctypes, ctypes.util
from libmu import *
import os

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
    ir, hail, exfn = map(zf.read, zf.namelist()[:3])    # disregard the 4-th text graph file.
    zf.close()
    return ir, hail, json.loads(exfn)


def build_arglist(ctx, argv):
    _id = ctx.id_of

    def build_string(s):
        with DelayedDisposer() as dd:
            length = len(s)
            hlength = dd << ctx.handle_from_int(length, 64)
            hstr = ctx.new_hybrid(_id("@hybrpy_string_0"), hlength)   # don't add handle to dd
            ir = dd << ctx.get_iref(hstr)

            # hash
            hir_hash = dd << ctx.get_field_iref(ir, 1)
            ctx.store(hir_hash, dd << ctx.handle_from_int(hash(s), 64))

            # length
            hir_length = dd << ctx.get_field_iref(ir, 2)
            ctx.store(hir_length, hlength)

            # chars
            hir_var = dd << ctx.get_var_part_iref(ir)
            for i, ch in enumerate(s):
                with DelayedDisposer() as _dd:
                    hi = _dd << ctx.handle_from_int(i, 64)
                    hir_elm = _dd << ctx.shift_iref(hir_var, hi)
                    hch = _dd << ctx.handle_from_int(ord(ch), 8)
                    ctx.store(hir_elm, hch)
            return hstr

    with DelayedDisposer() as dd:
        # Create new list
        refstt = ctx.new_fixed(_id("@sttlist_0"))     # don't add to dd
        irefstt = dd << ctx.get_iref(refstt)

        # Set the length of the list
        ireffld_len = dd << ctx.get_field_iref(irefstt, 1)
        hlen = dd << ctx.handle_from_int(len(argv), 64)
        ctx.store(ireffld_len, hlen)

        # Create the hybrid items
        ireffld_items = dd << ctx.get_field_iref(irefstt, 2)
        refhyb_items = dd << ctx.new_hybrid(_id("@hybrpy_stringPtr_0"), hlen)
        ctx.store(ireffld_items, refhyb_items)

        # Set the length field of the hybrid type.
        irefhyb = dd << ctx.get_iref(refhyb_items)
        irefhyblen = dd << ctx.get_field_iref(irefhyb, 1)
        ctx.store(irefhyblen, hlen)

        # Store the strings
        irefvar = dd << ctx.get_var_part_iref(irefhyb)
        for i, s in enumerate(argv):
            hidx = dd << ctx.handle_from_int(i, 64)
            irefelm = ctx.shift_iref(irefvar, hidx)
            refhyb = build_string(s)
            ctx.store(irefelm, refhyb)

    return refstt

loaded_extfncs = []     # Keep them in a global variable so that PyPy's GC will not finalize these libraries.

def ensure_open_libs():
    if len(loaded_extfncs) != 0:
        return loaded_extfncs
    
    libc = ctypes.CDLL(ctypes.util.find_library("c"))
    libm = ctypes.CDLL(ctypes.util.find_library("m"))
    libutil = ctypes.CDLL(ctypes.util.find_library("util"))
    librt = ctypes.CDLL(ctypes.util.find_library("rt"))
    dir_rpython = os.path.dirname(os.path.dirname(__file__))
    dir_librpyc = os.path.join(dir_rpython, 'translator', 'mu', 'rpyc')
    path_librpyc = os.path.join(dir_librpyc, 'librpyc.so')

    try:
        librpyc = ctypes.CDLL(path_librpyc)
    except OSError as e:
        os.write(2, "ERROR: library {} not found. "
                    "Please execute 'make' in the directory {}\n".format(path_librpyc, dir_librpyc))
        raise e

    loaded_extfncs[:] = [librpyc, libc, libm, libutil, librt]
    
    return loaded_extfncs
    

def load_extfncs(ctx, exfns):
    _pypy_linux_prefix = "__pypy_mu_linux_"
    _pypy_apple_prefix = "__pypy_mu_apple_"
    _pypy_macro_prefix = "__pypy_macro_"

    def correct_name(c_name):
        """
        Correct some function naming
        especially needed for stat system calls.
        """
        if sys.platform.startswith('darwin'):  # Apple
            if c_name in ('stat', 'fstat', 'lstat'):
                return c_name + '64'    # stat64, fstat64, lstat64
            if c_name == "readdir":     # fixing the macro defined return type (struct dirent*)
                return _pypy_apple_prefix + c_name
        return c_name

    libs = ensure_open_libs()
    librpyc = libs[0]
    for c_name, fncptr_name, gcl_name, hdrs in exfns:
        c_name = correct_name(c_name)
        with DelayedDisposer() as dd:
            adr = None
            for lib in libs:
                try:
                    adr = ctypes.cast(getattr(lib, c_name), ctypes.c_void_p).value
                    break
                except AttributeError:
                    pass
            if adr is None:
                for prefix in (_pypy_linux_prefix, _pypy_macro_prefix):
                    try:
                        adr = ctypes.cast(getattr(librpyc, prefix + c_name), ctypes.c_void_p).value
                    except AttributeError:
                        pass
            if adr is None:
                os.write(2, "Failed to load function '%(c_name)s'.\n" % locals())
                raise NotImplementedError
            
            # print("func: {}, addr: {} 0x{:x}".format(c_name, adr, adr))

            hadr = dd << ctx.handle_from_fp(ctx.id_of(fncptr_name), adr)
            hgcl = dd << ctx.handle_from_global(ctx.id_of(gcl_name))
            ctx.store(hgcl, hadr)


def launch(cmdargs, ir, hail, exfns, args):
    dll = MuRefImpl2StartDLL("libmurefimpl2start.so")
    vmopts = get_vm_opts(cmdargs)
    mu = dll.mu_refimpl2_new_ex(**vmopts)

    with mu.new_context() as ctx:
        ctx.load_bundle(ir)
        ctx.load_hail(hail)
        load_extfncs(ctx, exfns)

        if cmdargs.checkOnly:
            return 0

        refstt_arglst = build_arglist(ctx, args)
        refrtnbox = ctx.new_fixed(ctx.id_of("@i64"))
        bundle_entry = ctx.handle_from_func(ctx.id_of("@_mu_bundle_entry"))
        st = ctx.new_stack(bundle_entry)
        reftl = ctx.new_fixed(ctx.id_of("@sttmu_threadlocal"))
        th = ctx.new_thread(st, reftl, PassValues(refstt_arglst, refrtnbox))

        mu.execute()

        irefrtnbox = ctx.get_iref(refrtnbox)
        hrtnval = ctx.load(irefrtnbox).cast(MuIntValue)
        rtnval = ctx.handle_to_sint(hrtnval)

        # print("Program exited with value %(rtnval)d" % locals())
        return rtnval


def main():
    cmdargs = parse_args()
    rtnval = launch(cmdargs, *extract_bundle(cmdargs.bundle), args=[cmdargs.bundle] + cmdargs.prog_args)
    return rtnval


if __name__ == "__main__":
    exitcode = main()
    sys.exit(exitcode)
