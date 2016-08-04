from rpython.jit.backend.muvm import locations as l
from rpython.jit.metainterp.history import  (INT, FLOAT, VOID, 
                                            STRUCT, REF, VECTOR)


errors = 0
def testType():
    global errors
    INT32 = l.Type(INT, 32)
    INT64 = l.Type(INT, 64)
    FLOAT_t = l.Type(FLOAT)
    failed = 0
    try:
        assert str(INT32) == '@i32_t'
    except:
        print "[!] ERROR: testType failed: "
        failed += 1
    try:
        assert str(INT64) == '@i64_t'
    except:
        print "[!] ERROR: testType failed: "
        failed += 1
    try:
        assert str(FLOAT_t) == "@f_t"
    except:
        print "[!] ERROR: testType failed assertion: str(FLOAT_t) == '@f_t' "
        failed += 1
    if failed == 0:
        print "[!] INFO: testType() succeeded."
    else:
        print "[!] INFO: testType() ran with {} errors".format(failed)
    errors += failed
        
def testLocalSSALocation():
    global errors
    failed = 0
    regs = []
    try:
        for i in range(100):
            regs.append(l.LocalSSALocation(i, t=INT, width=DOUBLE_WORD*8))
            print "regs[-1] = " + regs[-1]
            assert str(regs[-1]) == '%i64_{}'.format(i)
        print "[!] INFO: testLocalSSALocation successful"
    except e:
        print "[!] ERROR: testLocalSSALocation failed"
        print e
        errors += 1

def main():
    testType()
    testLocalSSALocation()
    print "Summary: errors = {}".format(errors)

if __name__ == '__main__':
    main()
