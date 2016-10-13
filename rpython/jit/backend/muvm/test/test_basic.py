from rpython.jit.backend.muvm.test.support import JitMuMixin
from rpython.jit.metainterp.test import test_ajit
from rpython.rlib.jit import JitDriver


class TestBasic(JitMuMixin):
    # for the individual tests see
    # ====> ../../../metainterp/test/test_ajit.py
    def test_bug(self):
        jitdriver = JitDriver(greens=[], reds=['n'])

        class X(object):
            pass

        def f(n):
            while n > -100:
                jitdriver.can_enter_jit(n=n)
                jitdriver.jit_merge_point(n=n)
                x = X()
                x.arg = 5
                if n <= 0: break
                n -= x.arg
                x.arg = 6  # prevents 'x.arg' from being annotated as constant
            return n

        res = self.meta_interp(f, [31], enable_opts='')
        assert res == -4
