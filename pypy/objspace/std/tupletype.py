from pypy.objspace.std.stdtypedef import *


def descr__new__(space, w_tupletype, w_items=None):
    if w_items is None:
        tuple_w = []
    else:
        tuple_w = space.unpackiterable(w_items)
    w_obj = space.newtuple(tuple_w)
    return space.w_tuple.build_user_subclass(w_tupletype, w_obj)

# ____________________________________________________________

tuple_typedef = StdTypeDef("tuple",
    __new__ = newmethod(descr__new__),
    )
