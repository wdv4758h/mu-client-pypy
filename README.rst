==============================
PyPy-Mu: A Mu Backend for PyPy
==============================

Welcome to PyPy-Mu!

PyPy-Mu is a fork of `PyPy <http://pypy.org>`__ that aims to
add a `Mu Micro Virtual Machine <http://microvm.org>`__ backend for it.

This project is currently under active development,
right now we can compile PyPy interpreter with `--no-allworkingmodules` option.

Building
========

Obtaining a Mu implementation
-----------------------------

The reference implementation for Mu can be found `here <https://github.com/microvm/microvm-refimpl2>`__.
Build the Mu implementation, make sure to build the C binding as well.


Compiling some RPython C backend support source code
----------------------------------------------------
Currently the Mu backend still requires some support from the C backend function implementations.
We thus build them into a shared library that's loaded by the Mu RPython client launcher.

::

    $ cd rpython/translator/mu/rpyc
    $ make

This will produce the shared library ``librpyc.so``.


Setting up environment variable
-------------------------------
.. role:: bash(code)
    :language: bash

- Set up an environment variable :bash:`$MU` to point to the cloned Mu MicroVM repository.

::

    $ export MU=$REPOS/microvm-refimpl2

- Make an alias for the client launcher, adding Python binding and C binding to environment varible:

::

    $ alias murpy="PYTHONPATH=$MU/pythonbinding:$PYTHONPATH LD_LIBRARY_PATH=$MU/cbinding:$LD_LIBRARY_PATH python $PYPY_MU/rpython/mucli/murpy.py"

Compiling & Executing RPython Target
------------------------------------

Specify :bash:`-b mu` option to compile using the Mu backend:

::

    $ rpython/bin/rpython -b mu <target>

This outputs a ``<target>-mu.mu`` file in the current directory.
This is a zipped bundle of the IR, HAIL and external function list files.

Use ``murpy`` to load and run the compiled bundle program:

::

    $ murpy --noSourceInfo --vmLog=ERROR <target>-mu.mu


Note the default Mu code generation backend is textform which is going to be deprecated.
To use the API backend, do:

::

    $ PYTHONPATH=$MU/tools pypy rpython/bin/rpython -b mu --mugen=api <target>

Note that this backend depends on `$MU/tools/mar.py`, `PYTHONPATH` variable needs to be set.
This will start up a Mu instance, build a bundle in Mu via API calls, and dump a boot image.
To run the dumped boot image, use the `runmu.sh` provided by the reference implementation.

::

    $ $MU/tools/runmu.sh <mu-flags> <bootimage> <program-args>

--------------------------

Why not try compiling the PyPy interpreter (currently with some limitations)?

::

    $ rpython -O2 -b mu pypy/goal/targetpypystandalone.py --no-allworkingmodules
    $ murpy --noSourceInfo --vmLog=ERROR --sosSize=780M --losSize=780M pypy-mu.mu
