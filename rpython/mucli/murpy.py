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


def open_context():
    libc = ctypes.CDLL(ctypes.util.find_library("c"))
    libc.write.restype = ctypes.c_ssize_t
    libc.write.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t]

    dll = MuRefImpl2StartDLL("libmurefimpl2start.so")
    mu = dll.mu_refimpl2_new()

    return mu.new_context()


def prep_args(ctx, argv):
    _id = ctx.id_of
    def build_string(s, x=DelayedDisposer()):
        with DelayedDisposer() as x:
            length = len(s)
            hlength = x << ctx.handle_from_int(length, 64)
            hstr = x << ctx.new_hybrid(_id("@hybrpy_string"), hlength)
            ir = x << ctx.get_iref(hstr)

            # hash
            hir_hash = ctx.get_field_iref(ir, 0)
            ctx.store(hir_hash, x << ctx.handle_from_int(hash(s)))

            # length
            hir_length = ctx.get_field_iref(ir, 1)
            ctx.store(hir_length, hlength)

            # chars
            # TODO: finish rest.

    nargs = len(argv)
    hnargs = ctx.handle_from_int(nargs, 64)
    args = ctx.new_hybrid(_id("@array_ref_string"), hnargs)


def launch(ir, hail, exfn, args):
    with open_context() as ctx:
        ctx.load_bundle(ir)
        ctx.load_hail(hail)

        # TODO: prepare extern functions.


def main(argv):
    launch(*extract_bundle(argv[0]), args=argv[1:])


if __name__ == "__main__":
    main(sys.argv)
