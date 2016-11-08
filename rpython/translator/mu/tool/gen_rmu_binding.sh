#!/usr/bin/env bash
PYTHONPATH=$MU/migrate_scripts python3 $PYPY_MU/rpython/tool/genrmu.py --impl ref $MU/cbinding/muapi.h > $PYPY_MU/rpython/rlib/rmu.py
PYTHONPATH=$MU/migrate_scripts python3 $PYPY_MU/rpython/tool/genrmu.py --impl fast $MU_RUST/src/vm/api/muapi.h > $PYPY_MU/rpython/rlib/rmu_fast.py
PYTHONPATH=$MU/migrate_scripts python3 $PYPY_MU/rpython/tool/genrmu_genc.py --impl ref $MU/cbinding/muapi.h > $PYPY_MU/rpython/rlib/rmu_genc.py
PYTHONPATH=$MU/migrate_scripts python3 $PYPY_MU/rpython/tool/genrmu_genc.py --impl fast $MU_RUST/src/vm/api/muapi.h > $PYPY_MU/rpython/rlib/rmu_genc_fast.py
