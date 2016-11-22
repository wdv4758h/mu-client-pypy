import pytest

def pytest_addoption(parser):
    parser.addoption("--cmdopt", action="store", default="--impl ref --run",
                     help="command line arguments as a string passed to tests.")

@pytest.fixture
def cmdopt(request):
    """
    Some examples (NOT ALL IMPLEMENTED)s

    * Run the test script with a running Mu instance:
        ```bash
        $ pytest --impl <impl> --run
        ```
    * Compile to C, then compile with clang, then run:
        **NOT YET IMPLEMENTED**

        ```bash
        $ PYTHONPATH=$PYPY_MU python test_add.py --impl <impl> -o test_add.c
        ```
        - reference implementation:
            ```bash
            $ clang -std=c99 -I$MU/cbinding -L$MU/cbinding -lmurefimpl2start -o test_add test_add.c
            ```
        - fast implementation:
            ```bash
            $ clang -std=c99 -I$MU_RUST/src/vm/api -L$MU_RUST/target/debug -lmu -o test_add test_add.c
            ```
        $ ./test_add
    * Run JIT test for fast implementation:
            ```bash
            $ pytest --impl fast --testjit --run
            ```
    """
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--impl', type=str, choices=['ref', 'fast'], default='ref',
                        help='Compile script to C targeting the selected implementation of Mu.')
    parser.add_argument('--run', action='store_true',
                        help='Run the script under RPython FFI on Mu Scala reference implementation.')
    arg_testjit = parser.add_argument('--testjit', action='store_true',
                                      help='Renerate C source file that can be used to test the JIT.')
    parser.add_argument('-o', '--output', default=request.function.__name__ + '.c',
                        help='File name of the generated C source file.')
    argv = request.config.getoption("--cmdopt").split(' ')
    opts = parser.parse_args(argv)
    if opts.testjit:
        if not (opts.impl == 'fast'):
            raise argparse.ArgumentError(arg_testjit,
                                         "must be specified with '--impl fast'.")
    return opts
