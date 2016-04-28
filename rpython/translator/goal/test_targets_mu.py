"""
Compile and run the targets as pytests
"""
import subprocess as sp
import os, sys
from py._path.local import LocalPath


pypy_dir = LocalPath(os.getenv("PYPY_MU"))
targets_dir = pypy_dir / "rpython/translator/goal"


def compile_target(tmpdir, target, args=[]):
    if isinstance(args, list):
        args = ' '.join(args)
    output_file = tmpdir / target.replace('.py', '.mu')
    target_file = targets_dir / target

    cmd = "rpython -O0 -b mu --output %(output_file)s %(target_file)s %(args)s" % locals()
    print cmd
    p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    stdout_data, stderr_data = p.communicate()

    if p.returncode != 0:
        print "Failed to compile!"
        print "-------------------------------- stdout --------------------------------"
        print stdout_data
        print "-------------------------------- stderr --------------------------------"
        print stderr_data
        raise Exception
    else:
        print "Successfully compiled to %s." % output_file

    return output_file


def run_bundle(bundle, cmdargs=[], print_stderr_when_fail=True):
    if isinstance(cmdargs, list):
        cmdargs = ' '.join(cmdargs)

    env = os.environ
    env['PATH'] = env['MU'] + "/cbinding:" + env['PATH']
    _pypy_dir = pypy_dir
    cmd = "python %(_pypy_dir)s/rpython/mucli/murpy.py %(bundle)s %(cmdargs)s" % locals()
    print cmd
    p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True, env=env)
    stdout_data, stderr_data = p.communicate()

    # print "-------------------------------- stdout --------------------------------"
    # print stdout_data
    # print "-------------------------------- stderr --------------------------------"
    # print stderr_data

    if p.returncode == 0:
        lines = stdout_data.split('\n')
        idx_start = lines.index("-------------------------------- program output --------------------------------")
        idx_end = lines.index("--------------------------------------------------------------------------------")
        output = '\n'.join(lines[idx_start + 1:idx_end])
        for idx in range(idx_start, idx_end + 1):
            print lines[idx]
    else:
        output = stdout_data
        if print_stderr_when_fail:
            print "-------------------------------- stderr --------------------------------"
            print stderr_data
            print "------------------------------------------------------------------------"

    return p.returncode, output, stderr_data


def test_factorial_noprint(tmpdir):
    bundle_file = compile_target(tmpdir, "targetfactorial_noprint.py")
    n = 5
    rtncode, stdout, stderr = run_bundle(bundle_file, [str(n)], print_stderr_when_fail=False)
    from targetfactorial_noprint import fac
    assert rtncode == fac(n)


def test_print_helloworld(tmpdir):
    bundle_file = compile_target(tmpdir, "targetprint.py")
    r, out, err = run_bundle(bundle_file, [])
    assert out == "hello world"


def test_warningalone(tmpdir):
    bundle = compile_target(tmpdir, "targetwarningalone.py")
    r, out, err = run_bundle(bundle, ['0'])
    assert out == '9'
    r, out, err = run_bundle(bundle, ['4'])
    assert out == '1'
    r, out, err = run_bundle(bundle, ['2'])
    assert out == '2'
    r, out, err = run_bundle(bundle, ['1'])
    assert out == '0'


def test_testlistvsdict(tmpdir):
    bundle = compile_target(tmpdir, "targettestlistvsdict.py")
    r, out, err = run_bundle(bundle, ['d', '1234'])
    assert out == '1234'
    r, out, err = run_bundle(bundle, ['l', '234'])
    assert out == '1234'
    r, out, err = run_bundle(bundle, ['d', '234'], print_stderr_when_fail=False)
    assert r == 1


def test_targettestdicts(tmpdir):
    bundle = compile_target(tmpdir, "targettestdicts.py")
    r, out, err = run_bundle(bundle, ['d', '256'])
    assert out == '0x100'
    r, out, err = run_bundle(bundle, ['d', '4095'])
    assert out == '0xfff'
    r, out, err = run_bundle(bundle, ['d', '4096'], print_stderr_when_fail=False)
    assert r == 1
    r, out, err = run_bundle(bundle, ['r', '0x100'])
    assert out == '256'
    r, out, err = run_bundle(bundle, ['r', '0xfff'])
    assert out == '4095'


def test_targetvarsized(tmpdir):
    bundle = compile_target(tmpdir, "targetvarsized.py", ['1'])
    r, out, err = run_bundle(bundle)
    print out
    assert r == 0
