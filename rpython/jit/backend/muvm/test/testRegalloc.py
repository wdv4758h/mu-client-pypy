from rpython.jit.backend.muvm import regalloc
from rpython.jit.backend.muvm import locations as l
from rpython.jit.metainterp.history import  (INT, FLOAT, VOID, 
                                            STRUCT, REF, VECTOR)

from rpython.jit.backend.muvm.arch import DOUBLE_WORD, INT_WIDTH
from rpython.jit.backend.muvm.tests.helper import (printErr, printOK, 
                                            printWarn,printInfo)

errors = 0

def test_try_allocate_reg():
    global errors
    failed = 0
    rm = regalloc.MuVMRegisterManager([], [], [])
    t1 = l.Type(INT, 64)
    try:
        for i in range(100):
            assert rm.try_allocate_reg() == i
            assert rm.registers[-1].value == i
    except Exception as e:
        printErr(e, "test_try_allocate_reg()")
        failed += 1
    errors += failed

def main():
    tests = [ g for g in globals() if  g.startswith('test') ]
    
    for test in tests:
        globals()[test]()
    printInfo( "=" * 80, '')
    printInfo( "Summary: errors = {}".format(errors))

if __name__ == '__main__':
    main()


