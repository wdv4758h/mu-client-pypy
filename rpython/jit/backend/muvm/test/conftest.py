"""
This conftest disables the backend tests on non MuVM platforms
"""
import py, os
from rpython.jit.backend import detect_cpu

#Temporarily set cpu to "mu"
cpu = "mu" #detect_cpu.autodetect()

def pytest_collect_directory(path, parent):
    if not cpu.startswith('mu'):
        py.test.skip("Mu tests skipped: cpu is %r" % (cpu,))
pytest_collect_file = pytest_collect_directory
