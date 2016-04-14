from __future__ import division, absolute_import, print_function, unicode_literals
import sys

import ctypes, ctypes.util
from libmu import *

import argparse
import zipfile
import json


def slurp(filename):
    with open(filename) as t:
        return t.read()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('bundle', help="Generated RPython Mu bundle.")
    return parser.parse_args()


def extract_bundle(bdl):
    zf = zipfile.ZipFile(bdl, 'r')
    ir, hail, exfn = map(zf.read, zf.namelist())
    zf.close()
    return ir, hail, json.loads(exfn)


def build_arglist(ctx, argv):
    _id = ctx.id_of

    def build_string(s):
        with DelayedDisposer() as dd:
            length = len(s)
            hlength = dd << ctx.handle_from_int(length, 64)
            hstr = ctx.new_hybrid(_id("@hybrpy_string"), hlength)   # don't add handle to dd
            ir = dd << ctx.get_iref(hstr)

            # hash
            hir_hash = dd << ctx.get_field_iref(ir, 0)
            ctx.store(hir_hash, dd << ctx.handle_from_int(hash(s), 64))

            # length
            hir_length = dd << ctx.get_field_iref(ir, 1)
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
        refstt = ctx.new_fixed(_id("@sttlist"))     # don't add to dd
        irefstt = dd << ctx.get_iref(refstt)

        # Set the length of the list
        ireffld_len = dd << ctx.get_field_iref(irefstt, 0)
        hlen = dd << ctx.handle_from_int(len(argv), 64)
        ctx.store(ireffld_len, hlen)

        # Create the hybrid items
        ireffld_items = dd << ctx.get_field_iref(irefstt, 1)
        refhyb_items = dd << ctx.new_hybrid(_id("@hybrpy_stringPtr"), hlen)
        ctx.store(ireffld_items, refhyb_items)

        # Set the length field of the hybrid type.
        irefhyb = dd << ctx.get_iref(refhyb_items)
        irefhyblen = dd << ctx.get_field_iref(irefhyb, 0)
        ctx.store(irefhyblen, hlen)

        # Store the strings
        irefvar = dd << ctx.get_var_part_iref(irefhyb)
        for i, s in enumerate(argv):
            hidx = dd << ctx.handle_from_int(i, 64)
            irefelm = ctx.shift_iref(irefvar, hidx)
            refhyb = build_string(s)
            ctx.store(irefelm, refhyb)

    return refstt


def launch(ir, hail, exfn, args):
    # libc = ctypes.CDLL(ctypes.util.find_library("c"))
    # libc.write.restype = ctypes.c_ssize_t
    # libc.write.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t]

    dll = MuRefImpl2StartDLL("libmurefimpl2start.so")
    mu = dll.mu_refimpl2_new()

    with mu.new_context() as ctx:
        ctx.load_bundle(ir)
        ctx.load_hail(hail)

        # TODO: prepare extern functions.

        refstt_arglst = build_arglist(ctx, args)

        refrtnbox = ctx.new_fixed(ctx.id_of("@i64"))
        bundle_entry = ctx.handle_from_func(ctx.id_of("@_mu_bundle_entry"))
        st = ctx.new_stack(bundle_entry)
        th = ctx.new_thread(st, PassValues(refstt_arglst, refrtnbox))

        mu.execute()

        irefrtnbox = ctx.get_iref(refrtnbox)
        hrtnval = ctx.load(irefrtnbox).cast(MuIntValue)
        rtnval = ctx.handle_to_sint(hrtnval)

        print("Program exited with value {}".format(rtnval))


def main(argv):
    launch(*extract_bundle(argv[1]), args=argv[2:])


if __name__ == "__main__":
    main(sys.argv)
