"""
Generate the Heap Allocation and Initialisation Language (HAIL) script
to initialise the global cells.
"""
from rpython.mutyper.muts import mutype
from rpython.mutyper.muts.muentity import MuGlobalCell, MuName


class _HAILName:
    _name_dic = {}

    def __init__(self, name):
        if name in _HAILName._name_dic:
            n = _HAILName._name_dic[name] + 1
        else:
            n = 0
        _HAILName._name_dic[name] = n
        self.name = "%s_%d" % (name, n)

    def __str__(self):
        return "$%s" % self.name


class HAILGenerator:
    def __init__(self):
        self.gcells = []
        self._refs = {}

    def add_gcell(self, gcell):
        self.gcells.append(gcell)

        self._find_refs(gcell._obj, gcell)

    def _find_refs(self, obj, gcell=None):
        if isinstance(obj, (mutype._muref, mutype._muiref)):
            refnt = obj._obj0
            if refnt not in self._refs:
                self._refs[refnt] = gcell.mu_name if gcell else _HAILName(mutype.mu_typeOf(obj).mu_name._name)
            elif isinstance(self._refs[refnt], _HAILName) and gcell:
                self._refs[refnt] = gcell.mu_name
            else:
                return
            self._find_refs(refnt)

        elif isinstance(obj, (mutype._mustruct, mutype._muhybrid)):
            for fld in mutype.mu_typeOf(obj)._flds:
                self._find_refs(obj._getattr(fld))

        elif isinstance(obj, (mutype._mumemarray)):
            if isinstance(obj._OF, (mutype.MuContainerType, mutype.MuRef, mutype.MuIRef)):
                for itm in obj:
                    self._find_refs(itm)

    def codegen(self, fp):
        # Allocate everything first
        for r, n in self._refs.items():
            obj_t = mutype.mu_typeOf(r)
            if isinstance(obj_t, mutype.MuHybrid):
                fp.write(".newhybrid %s <%s> %d\n" % (n, obj_t.mu_name, len(r._getattr(obj_t._varfld))))
            else:
                fp.write(".new %s <%s>\n" % (n, obj_t.mu_name))

        for r, n in self._refs.items():
            fp.write(".init %s = %s\n" % (n, self._getinitstr(r)))

    def _getinitstr(self, obj):
        if isinstance(obj, (mutype._muprimitive, mutype._munullref)):
            return str(obj)

        elif isinstance(obj, (mutype._mustruct, mutype._muhybrid)):
            return "{%s}" % ' '.join([self._getinitstr(obj._getattr(fld)) for fld in mutype.mu_typeOf(obj)._names])

        elif isinstance(obj, mutype._mumemarray):
            return "{%s}" % ' '.join([self._getinitstr(itm) for itm in obj])

        elif isinstance(obj, (mutype._muref, mutype._muiref)):
            assert obj._obj0 in self._refs
            name = self._refs[obj._obj0]
            if isinstance(name, MuName) and 'gcl' in str(name):
                return "*%s" % name
            return str(name)
        else:
            raise TypeError("Unknown value '%s' of type '%s'." % (obj, mutype.mu_typeOf(obj)))
