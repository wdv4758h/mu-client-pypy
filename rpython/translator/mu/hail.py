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
    def __init__(self, objtracer):
        self.objtracer = objtracer
        self._objname_map = {}

    def codegen(self, fp):
        # create a HAIL name for every object
        self._objname_map = {}
        for obj in self.objtracer.objs:
            self._objname_map[obj] = _HAILName(mutype.mu_typeOf(obj).mu_name._name)
        
        # Allocate everything first
        for obj, hailname in self._objname_map.items():
            obj_t = mutype.mu_typeOf(obj)
            if isinstance(obj_t, mutype.MuHybrid):
                fp.write(".newhybrid %s <%s> %d\n" % (hailname, obj_t.mu_name, len(obj._getattr(obj_t._varfld))))
            else:
                fp.write(".new %s <%s>\n" % (hailname, obj_t.mu_name))

        for obj, hailname in self._objname_map.items():
            fp.write(".init %s = %s\n" % (hailname, self._getinitstr(obj)))

        for gcl, obj in self.objtracer.gcells.items():
            hailname = self._objname_map[obj]
            fp.write(".init %s = %s\n" % (gcl.mu_name, hailname))

    def _getinitstr(self, obj):
        if isinstance(obj, (mutype._muprimitive, mutype._munullref)):
            return repr(obj)

        elif isinstance(obj, (mutype._mustruct, mutype._muhybrid)):
            return "{%s}" % ' '.join([self._getinitstr(obj._getattr(fld)) for fld in mutype.mu_typeOf(obj)._names])

        elif isinstance(obj, mutype._mumemarray):
            return "{%s}" % ' '.join([self._getinitstr(itm) for itm in obj])

        elif isinstance(obj, (mutype._muref, mutype._muiref)):
            refrnt = obj._obj0
            if isinstance(refrnt, mutype._mustruct):
                refrnt = refrnt._top_container()
            assert refrnt in self._objname_map
            name = self._objname_map[refrnt]
            if isinstance(name, MuName) and 'gcl' in str(name):
                return "*%s" % name
            return str(name)
        elif isinstance(obj, mutype._mufuncref):
            assert hasattr(obj, 'graph')
            assert obj.graph.mu_name is not None
            return str(obj.graph.mu_name)
        else:
            raise TypeError("Unknown value '%s' of type '%s'." % (obj, mutype.mu_typeOf(obj)))
