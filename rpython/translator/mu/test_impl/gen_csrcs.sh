#!/usr/bin/env bash
pytest --cmdopt='--impl fast --testjit'
python --impl fast --testjit -o test_fib.c test_fib.py
python --impl fast --testjit -o test_multifunc.c test_multifunc.py
python --impl fast --testjit -o test_constfunc.c test_constfunc.py
