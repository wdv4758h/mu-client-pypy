#!/usr/bin/env bash
pytest --cmdopt='--impl fast --testjit'
python test_fib.py --impl fast --testjit -o test_fib.c
python test_multifunc.py --impl fast --testjit -o test_multifunc.c
python test_constfunc.py --impl fast --testjit -o test_constfunc.c
python test_ccall.py --impl fast --testjit -o test_ccall.c
python test_milsum.py --impl fast --testjit -o test_milsum.c
