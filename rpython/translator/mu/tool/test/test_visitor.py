from rpython.translator.mu.tool.visitor import *
from rpython.rtyper.lltypesystem import lltype

def test_dispatch_lltype():
    class TestVisitor(LLTypeVisitor):
        def visit_num(self, LLT):
            return 'num'
        def visit_arrfix(self, LLT):
            return 'arrfix'
        def visit_stt(self, LLT):
            return 'stt'

    v = TestVisitor()
    assert v.visit(lltype.Signed) == 'num'
    assert v.visit(lltype.FixedSizeArray(lltype.Signed, 5)) == 'arrfix'
    from rpython.rtyper.rclass import OBJECT
    assert v.visit(OBJECT) == 'stt'

def test_recursive_visit_lltype():
    class TestVisitor(LLTypeVisitor):
        def __init__(self):
            self.log = []
        def visit_num(self, LLT):
            self.log.append("visit_num")
            super(TestVisitor, self).visit_num(LLT)
        def visit_fixarr(self, LLT):
            self.log.append("visit_fixarr")
            super(TestVisitor, self).visit_fixarr(LLT)
        def visit_stt(self, LLT):
            self.log.append("visit_stt")
            super(TestVisitor, self).visit_stt(LLT)
        def visit_ptr(self, LLT):
            self.log.append("visit_ptr")
            super(TestVisitor, self).visit_ptr(LLT)

    v = TestVisitor()
    Node = lltype.GcForwardReference()
    PtrNode = lltype.Ptr(Node)
    Node.become(lltype.GcStruct("Node", ("payload", lltype.Signed), ("next", PtrNode)))
    ArrPtr = lltype.GcArray(PtrNode)

    v.visit(ArrPtr)
    assert v.log == ["visit_arr", "visit_ptr", "visit_stt", "visit_num"]
