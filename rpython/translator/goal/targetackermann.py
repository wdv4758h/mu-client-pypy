"""
Modification of targetrecursivestandalone.py
"""

def ackermann(x, y):
    if x == 0:
        return y + 1
    if y == 0:
        return ackermann(x - 1, 1)
    return ackermann(x - 1, ackermann(x, y - 1))

def entry_point(argv):
    print ackermann(int(argv[1]), int(argv[2]))
    return 0

# _____ Define and setup target ___

def target(*args):
    return entry_point, None