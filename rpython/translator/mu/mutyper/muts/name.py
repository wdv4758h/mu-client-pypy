"""
Global name identifier for entities in Mu.

Contains the notion of scope (local and global)
"""


SCOPE_GLOBAL = "global"


class Name(object):
    """
    Global unique name

    Uses a name counter dictionary to guarantee uniqueness.
    """
    _namectr_dic = {} # Name counter dictionary

    def __init__(self, str_name, scope=SCOPE_GLOBAL):
        """ Create a name for a SSA variable.

        :param str_name: name string
        :param scope: MuGraph, MuBlock defines local scope; default is SCOPE_GLOBAL
        :return: a Name instance
        """
        if (str_name, scope) not in Name._namectr_dic:
            self._name = str_name
            Name._namectr_dic[(str_name, scope)] = 2  # Counter naming starts from 2
        else:
            count = Name._namectr_dic[(str_name, scope)]
            self._name = "%s_%d" % (str_name, count)
            Name._namectr_dic[(str_name, scope)] = count + 1
        self.scope = scope

    def is_global(self):
        return self.scope == SCOPE_GLOBAL

    def __str__(self):
        if self.is_global():
            return "@%s" % self._name
        return "%%%s" % self._name

    def __repr__(self):
        if self.is_global():
            return str(self)

        # The global representation of local name
        prefix = ""
        parent = self.scope
        while parent != SCOPE_GLOBAL:
            prefix = parent.muname._name + "." + prefix
            parent = parent.muname.scope
        return "@%s.%s" % (prefix, self._name)

    def __eq__(self, other):
        return isinstance(other, Name) and self._name == other._name and self.scope == other.scope
