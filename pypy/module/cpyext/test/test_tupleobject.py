import py

from pypy.module.cpyext.pyobject import PyObject, PyObjectP, make_ref, from_ref
from pypy.module.cpyext.tupleobject import PyTupleObject
from pypy.module.cpyext.test.test_api import BaseApiTest
from pypy.module.cpyext.test.test_cpyext import AppTestCpythonExtensionBase
from rpython.rtyper.lltypesystem import rffi, lltype


class TestTupleObject(BaseApiTest):

    def test_tupleobject(self, space, api):
        assert not api.PyTuple_Check(space.w_None)
        assert api.PyTuple_SetItem(space.w_None, 0, space.w_None) == -1
        atuple = space.newtuple([space.wrap(0), space.wrap(1),
                                 space.wrap('yay')])
        assert api.PyTuple_Size(atuple) == 3
        #assert api.PyTuple_GET_SIZE(atuple) == 3  --- now a C macro
        raises(TypeError, api.PyTuple_Size(space.newlist([])))
        api.PyErr_Clear()
    
    def test_tuple_resize(self, space, api):
        w_42 = space.wrap(42)
        ar = lltype.malloc(PyObjectP.TO, 1, flavor='raw')

        py_tuple = api.PyTuple_New(3)
        # inside py_tuple is an array of "PyObject *" items which each hold
        # a reference
        rffi.cast(PyTupleObject, py_tuple).c_ob_item[0] = make_ref(space, w_42)
        ar[0] = py_tuple
        api._PyTuple_Resize(ar, 2)
        w_tuple = from_ref(space, ar[0])
        assert space.int_w(space.len(w_tuple)) == 2
        assert space.int_w(space.getitem(w_tuple, space.wrap(0))) == 42
        api.Py_DecRef(ar[0])

        py_tuple = api.PyTuple_New(3)
        rffi.cast(PyTupleObject, py_tuple).c_ob_item[0] = make_ref(space, w_42)
        ar[0] = py_tuple
        api._PyTuple_Resize(ar, 10)
        w_tuple = from_ref(space, ar[0])
        assert space.int_w(space.len(w_tuple)) == 10
        assert space.int_w(space.getitem(w_tuple, space.wrap(0))) == 42
        api.Py_DecRef(ar[0])

        lltype.free(ar, flavor='raw')

    def test_setitem(self, space, api):
        py_tuple = api.PyTuple_New(2)
        api.PyTuple_SetItem(py_tuple, 0, make_ref(space, space.wrap(42)))
        api.PyTuple_SetItem(py_tuple, 1, make_ref(space, space.wrap(43)))

        w_tuple = from_ref(space, py_tuple)
        assert space.eq_w(w_tuple, space.newtuple([space.wrap(42),
                                                   space.wrap(43)]))

    def test_getslice(self, space, api):
        w_tuple = space.newtuple([space.wrap(i) for i in range(10)])
        w_slice = api.PyTuple_GetSlice(w_tuple, 3, -3)
        assert space.eq_w(w_slice,
                          space.newtuple([space.wrap(i) for i in range(3, 7)]))


class AppTestTuple(AppTestCpythonExtensionBase):
    def test_refcounts(self):
        module = self.import_extension('foo', [
            ("run", "METH_NOARGS",
             """
                PyObject *item = PyTuple_New(0);
                PyObject *t = PyTuple_New(1);
                if (t->ob_refcnt != 1 || item->ob_refcnt != 1) {
                    PyErr_SetString(PyExc_SystemError, "bad initial refcnt");
                    return NULL;
                }

                PyTuple_SetItem(t, 0, item);
                if (t->ob_refcnt != 1) {
                    PyErr_SetString(PyExc_SystemError, "SetItem: t refcnt != 1");
                    return NULL;
                }
                if (item->ob_refcnt != 1) {
                    PyErr_SetString(PyExc_SystemError, "SetItem: item refcnt != 1");
                    return NULL;
                }

                if (PyTuple_GetItem(t, 0) != item ||
                    PyTuple_GetItem(t, 0) != item) {
                    PyErr_SetString(PyExc_SystemError, "GetItem: bogus item");
                    return NULL;
                }

                if (t->ob_refcnt != 1) {
                    PyErr_SetString(PyExc_SystemError, "GetItem: t refcnt != 1");
                    return NULL;
                }
                if (item->ob_refcnt != 1) {
                    PyErr_SetString(PyExc_SystemError, "GetItem: item refcnt != 1");
                    return NULL;
                }
                return t;
             """),
            ])
        x = module.run()
        assert x == ((),)
