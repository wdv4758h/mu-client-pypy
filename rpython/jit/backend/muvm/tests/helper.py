import inspect

class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m' 

def printErr(e,m=None):
    s = "{}[!] {}() raised exception:\n".format(colors.FAIL, inspect.stack()[1][3])
    s += "    {}".format(e)
    if m:
        s += "\n    {}".format(m)
    s += colors.ENDC
    print s

def printOK(s):
    print '{}[*] {}{}'.format(colors.OKGREEN, s, colors.ENDC)

def printInfo(s,pre='[*] '):
    print '{}{}{}{}'.format(colors.OKBLUE,pre, s, colors.ENDC)

def printWarn(s):
    print '{}[!] {}{}'.format(colors.WARNING, s, colors.ENDC)

