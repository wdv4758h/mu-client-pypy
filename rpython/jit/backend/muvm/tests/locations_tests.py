from rpython.jit.backend.muvm import locations as l
from rpython.jit.metainterp.history import  (INT, FLOAT, VOID, 
                                            STRUCT, REF, VECTOR)

from rpython.jit.backend.muvm.arch import DOUBLE_WORD, INT_WIDTH
from rpython.jit.backend.muvm.tests.helper import (printErr, printOK, 
                                            printWarn,printInfo)

errors = 0
def testType():
    global errors
    INT32 = l.Type(INT, 32)
    INT64 = l.Type(INT, 64)
    FLOAT_t = l.Type(FLOAT)
    failed = 0
    try:
        assert str(INT32) == '@i32_'
    except Exception as e:
        printErr(e)
        
        failed += 1
    try:
        assert str(INT64) == '@i64_t'
    except Exception as e:
        printErr(e)
        failed += 1
    try:
        assert str(FLOAT_t) == "@f_t"
    except Exception as e:
        printErr(e,"testType", "Type __repr__ failed")
        failed += 1
    if failed == 0:
        printOK( "testType: all tests passed")
    else:
        printWarn ("testType() ran with {} errors".format(failed))
    errors += failed
        
def testLocalSSALocation():
    global errors
    failed = 0
    regs = []
    try:
        for i in range(100):
            regs.append(l.LocalSSALocation(i, t=INT, width=DOUBLE_WORD*8))
            assert regs[-1].mustr() == '%i64_{}'.format(i)
        printOK("testLocalSSALocation: all tests passed")
    except Exception as e:
        printErr(e, 'testLocalSSALocation', 'mustr() failed')
        failed += 1
    errors += failed

def testGlobalSSALocation():
    global errors
    failed = 0
    regs = []
    try:
        for i in range(100):
            regs.append(l.GlobalSSALocation(i, t=INT, width=INT_WIDTH))
            assert regs[-1].mustr() == '@i64_{}'.format(i)
        printOK("testGlobalSSALocation: all tests passed")
    except Exception as e:
        printErr(e, "testGlobalSSALocation", 'mustr() failed')
        failed += 1
    errors += failed

def testImmLocation():
    global errors
    failed = 0
    imms = []
    try:
        for i in range(100):
            imms.append(l.ImmLocation(i))
            assert imms[-1].mustr() == "@i64_{}".format(i)
        printOK( "testImmLocation: all tests passed")
    except Exception as e:
        printErr(e, "testImmLocation", "mustr() failed")
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

