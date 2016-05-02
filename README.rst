==============================
PyPy-Mu: A Mu Backend for PyPy
==============================

Welcome to PyPy-Mu!

PyPy-Mu is a fork of `PyPy <http://pypy.org>` that aims to
add a `Mu Micro Virtual Machine <http://microvm.org>` backend for it.

This project is currently under active development,
progressing towards a Mu backend that allows RPython to
successfully compile `SOM interpreter <https://github.com/SOM-st/RPySOM>`.

Building
========

Obtaining a Mu implementation
-----------------------------

The reference implementation for Mu can be found `here <https://github.com/microvm/microvm-refimpl2>`.
Build the Mu implementation, make sure to build the C binding as well.


Compiling some RPython C backend support source code
----------------------------------------------------
Currently the Mu backend still requires some support from the C backend function implementations.
We thus build them into a shared library that's loaded by the Mu RPython client launcher.

.. code-block:: console
    $ cd rpython/translator/mu/rpyc
    $ make

This will produce the shared library ``librpyc.so``.


Setting up environment variable
-------------------------------
.. role:: bash(code)
    :language: bash

- Set up an environment variable :bash:`$MU` to point to the cloned Mu MicroVM repository.
.. code-block:: console
    $ export MU=$REPOS/microvm-refimpl2

- Make an alias for the client launcher, adding Python binding and C binding to environment varible:
.. code-block:: console
    $ alias murpy="PYTHONPATH=$MU/pythonbinding:$PYTHONPATH LD_LIBRARY_PATH=$MU/cbinding:$LD_LIBRARY_PATH python $PYPY_MU/rpython/mucli/murpy.py"


Compiling & Executing RPython Target
------------------------------------

Specify :bash:`-b mu` option to compile using the Mu backend:
.. code-block:: console
    $ rpython/bin/rpython -O0 -b mu <target>

This outputs a ``<target>-mu.mu`` file in the current directory.
This is a zipped bundle of the IR, HAIL and external function list files.

Use ``murpy`` to load and run the compiled bundle program:
.. code-block:: console
    $ murpy <target>-mu.mu

Currently due to the limitation of the Mu implementation in Scala,
the performance of the Mu backend is about 100,000 times slower than that of the C backend...
