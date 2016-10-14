"""
Perform transitive closure on LLType and MuType using Visitor pattern.
"""

from rpython.rtyper.lltypesystem import lltype, llmemory
from rpython.translator.mu import mutype

class Visitor:
    def visit(self, *args):
        raise NotImplementedError

class LLTypeVisitor(Visitor):
    # ABANDON: there is a problem with recursive visits
    _check_cls = {
        lltype.Primitive: "prim",
        lltype.Number: "num",
        lltype.Struct: "stt",
        lltype.GcStruct: "stt",
        lltype.FixedSizeArray: "arrfix",
        lltype.Array: "arr",
        lltype.GcArray: "arr",
        lltype.Ptr: "ptr",
        lltype.OpaqueType: "opq",
        lltype.GcOpaqueType: "opq"
    }

    _check_type = {
        llmemory.Address: "addr",
        llmemory.WeakRef: "wref"
    }

    def visit(self, LLT):
        for T, suffix in LLTypeVisitor._check_type.items():
            if LLT is T:
                return getattr(self, 'visit_' + suffix)(LLT)

        cls = type(LLT)
        if cls not in LLTypeVisitor._check_cls:
            raise KeyError("Type class %s not defined." % cls.__name__)
        suffix = LLTypeVisitor._check_cls[cls]
        return getattr(self, 'visit_' + suffix)(LLT)

    def visit_prim(self, LLT):
        pass

    visit_addr = visit_wref = visit_opq = visit_num = visit_prim

    def visit_arrfix(self, LLT):
        self.visit(LLT.OF)  # PROBLEM: reusable code or just template? Recursive call?
