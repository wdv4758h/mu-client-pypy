"""
Definition of a general entity in Mu.
"""
import re


SCOPE_GLOBAL = "global"


class MuName(object):
    """
    Global unique name

    Uses a name counter dictionary to guarantee uniqueness.
    """
    _namectr_dic = {} # Name counter dictionary
    _cache = {}
    _pattern = r'[^0-9a-zA-Z_\-.]'

    def __new__(cls, str_name, scope=SCOPE_GLOBAL, **kwargs):
        key = (str_name, scope)
        try:
            return MuName._cache[key]
        except KeyError:
            obj = object.__new__(cls)
            MuName._cache[key] = obj
            return obj

    def __init__(self, str_name, scope=SCOPE_GLOBAL):
        """
        :param str_name: name string
        :param scope: MuGraph, MuBlock defines local scope; default is SCOPE_GLOBAL
        """
        self._name = re.sub(MuName._pattern, '_', str_name)     # ensures that the name is valid.
        self.scope = scope

    def is_global(self):
        return self.scope == SCOPE_GLOBAL

    def global_id(self):
        # The global representation of local name
        prefix = ""
        parent = self.scope
        while parent != SCOPE_GLOBAL:
            prefix = parent.mu_name._name + "." + prefix if prefix != "" else parent.mu_name._name
            parent = parent.mu_name.scope
        return "@%s.%s" % (prefix, self._name)

    def __str__(self):
        # if self.is_global():
        #     return "@%s" % self._name
        # return "%%%s" % self._name
        return self.global_id()

    def __repr__(self):
        if self.is_global():
            return str(self)
        return self.global_id()

    def __hash__(self):
        return hash(self.global_id())

    def __eq__(self, other):
        return isinstance(other, MuName) and self.global_id() == other.global_id()


class MuEntity(object):
    def __init__(self, mu_name):
        if not isinstance(mu_name, MuName):
            raise TypeError("MuEntity must be initialised with a MuName")

        self.mu_name = mu_name
        self.__name__ = repr(mu_name)

    def __str__(self):
        return str(self.mu_name)


class MuGlobalCell(MuEntity):
    prefix = "gcl"
    _name_dic = {}
    _cache = {}

    def __new__(cls, mu_type, mu_val=None):
        if mu_val and mu_val in MuGlobalCell._cache:
            return MuGlobalCell._cache[mu_val]
        obj = object.__new__(cls)
        MuGlobalCell._cache[mu_val] = obj
        return obj

    def __init__(self, mu_type, mu_val=None):
        name = MuGlobalCell.prefix + mu_type.mu_name._name
        if name in MuGlobalCell._name_dic:
            n = MuGlobalCell._name_dic[name] + 1
        else:
            n = 0
        MuGlobalCell._name_dic[name] = n
        name = "%s_%d" % (name, n)
        MuEntity.__init__(self, MuName(name))
        self._T = mu_type
        self.value = mu_val if mu_val else mu_type._defl()

    @property
    def mu_type(self):
        from rpython.mutyper.muts.mutype import MuIRef
        return MuIRef(self._T)

    def __repr__(self):
        return "MuGlobalCell <%s> { %r }" % (self._T, self.value)

    def _store(self, mu_val):
        if mu_val._TYPE != self._T:
            raise TypeError("Cannot store '%r' of type '%r' to global cell that holds '%r' type" %
                            (mu_val, mu_val._TYPE, self._T))

        self.value = mu_val

    def _load(self):
        return self.value

    _obj = property(_load, _store)

    def __eq__(self, other):
        return isinstance(other, MuGlobalCell) and self.mu_type == other.mu_type and self.value == other.value
