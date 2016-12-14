#!/usr/bin/env bash
PYTHONPATH=$MU/migrate_scripts python3 $PYPY_MU/rpython/tool/gen_rmu.py --impl ref $MU/cbinding/muapi.h > $PYPY_MU/rpython/rlib/rmu.py
PYTHONPATH=$MU/migrate_scripts python3 $PYPY_MU/rpython/tool/gen_rmu.py --impl fast $MU_RUST/src/vm/api/muapi.h > $PYPY_MU/rpython/rlib/rmu_fast.py
PYTHONPATH=$MU/migrate_scripts python3 $PYPY_MU/rpython/tool/gen_rmu_c.py --impl ref $MU/cbinding/muapi.h > $PYPY_MU/rpython/rlib/rmu_genc.py
PYTHONPATH=$MU/migrate_scripts python3 $PYPY_MU/rpython/tool/gen_rmu_c.py --impl fast $MU_RUST/src/vm/api/muapi.h > $PYPY_MU/rpython/rlib/rmu_genc_fast.py
