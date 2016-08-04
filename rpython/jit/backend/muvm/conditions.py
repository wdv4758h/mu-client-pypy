class MuCondition:

    def __init__(self, ssaReg=None, inverted=False):
        self.ssaReg   = ssaReg
        self.inverted = inverted

    def get_opposite_of(self):
        return MuCondition(self.ssaReg, not self.inverted)

cond_none   = MuCondition(None, False)
cond_always = MuCondition(None, True)
