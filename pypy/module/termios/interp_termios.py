
""" Termios module. I'm implementing it directly here, as I see
little use of termios module on RPython level by itself
"""

from pypy.interpreter.gateway import unwrap_spec
from pypy.interpreter.error import wrap_oserror, OperationError
from rpython.rlib import rtermios

class Cache:
    def __init__(self, space):
        self.w_error = space.new_exception_class("termios.error")

def convert_error(space, error):
    w_exception_class = space.fromcache(Cache).w_error
    return wrap_oserror(space, error, w_exception_class=w_exception_class)

@unwrap_spec(when=int)
def tcsetattr(space, w_fd, when, w_attributes):
    fd = space.c_filedescriptor_w(w_fd)
    if not space.isinstance_w(w_attributes, space.w_list) or \
            space.len_w(w_attributes) != 7:
        raise OperationError(space.w_TypeError, space.wrap(
            "tcsetattr, arg 3: must be 7 element list"))
    w_iflag, w_oflag, w_cflag, w_lflag, w_ispeed, w_ospeed, w_cc = \
             space.unpackiterable(w_attributes, expected_length=7)
    w_builtin = space.getbuiltinmodule('__builtin__')
    cc = []
    for w_c in space.unpackiterable(w_cc):
        if space.isinstance_w(w_c, space.w_int):
            ch = space.call_function(space.getattr(w_builtin,
                                          space.wrap('chr')), w_c)
            cc.append(space.str_w(ch))
        else:
            cc.append(space.str_w(w_c))
    tup = (space.int_w(w_iflag), space.int_w(w_oflag),
           space.int_w(w_cflag), space.int_w(w_lflag),
           space.int_w(w_ispeed), space.int_w(w_ospeed), cc)
    try:
        rtermios.tcsetattr(fd, when, tup)
    except OSError, e:
        raise convert_error(space, e)

def tcgetattr(space, w_fd):
    fd = space.c_filedescriptor_w(w_fd)
    try:
        tup = rtermios.tcgetattr(fd)
    except OSError, e:
        raise convert_error(space, e)
    iflag, oflag, cflag, lflag, ispeed, ospeed, cc = tup
    l_w = [space.wrap(i) for i in [iflag, oflag, cflag, lflag, ispeed, ospeed]]
    # last one need to be chosen carefully
    cc_w = [space.wrap(i) for i in cc]
    if lflag & rtermios.ICANON:
        cc_w[rtermios.VMIN] = space.wrap(ord(cc[rtermios.VMIN][0]))
        cc_w[rtermios.VTIME] = space.wrap(ord(cc[rtermios.VTIME][0]))
    w_cc = space.newlist(cc_w)
    l_w.append(w_cc)
    return space.newlist(l_w)

@unwrap_spec(duration=int)
def tcsendbreak(space, w_fd, duration):
    fd = space.c_filedescriptor_w(w_fd)
    try:
        rtermios.tcsendbreak(fd, duration)
    except OSError, e:
        raise convert_error(space, e)

def tcdrain(space, w_fd):
    fd = space.c_filedescriptor_w(w_fd)
    try:
        rtermios.tcdrain(fd)
    except OSError, e:
        raise convert_error(space, e)

@unwrap_spec(queue=int)
def tcflush(space, w_fd, queue):
    fd = space.c_filedescriptor_w(w_fd)
    try:
        rtermios.tcflush(fd, queue)
    except OSError, e:
        raise convert_error(space, e)

@unwrap_spec(action=int)
def tcflow(space, w_fd, action):
    fd = space.c_filedescriptor_w(w_fd)
    try:
        rtermios.tcflow(fd, action)
    except OSError, e:
        raise convert_error(space, e)
