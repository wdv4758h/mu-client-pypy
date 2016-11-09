#!/usr/bin/env bash
pytest --cmdopt='--impl fast --testjit'
python test_multifunc.py --impl fast --testjit -o test_multifunc.c
