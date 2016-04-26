"""
Compile and run the targets as pytests
"""
import subprocess as sp
import os, sys
from py._path.local import LocalPath


pypy_dir = LocalPath(os.getenv("PYPY_MU"))
targets_dir = pypy_dir / "rpython/translator/goal"


def compile_target(tmpdir, target):
    output_file = tmpdir / target.replace('.py', '.mu')
    target_file = targets_dir / target

    p = sp.Popen("rpython -O0 -b mu --output %(output_file)s %(target_file)s" % locals(),
                 stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    stdout_data, stderr_data = p.communicate()

    if p.returncode != 0:
        print "Failed to compile!"
        print "-------------------------------- stdout --------------------------------"
        print stdout_data
        print "-------------------------------- stderr --------------------------------"
        print stderr_data
    else:
        print "Successfully compiled to %s." % output_file

    return output_file


def run_bundle(bundle, cmdargs):
    if isinstance(cmdargs, list):
        cmdargs = ' '.join(cmdargs)

    env = os.environ
    env['PATH'] = env['uVM'] + "/cbinding:" + env['PATH']
    _pypy_dir = pypy_dir
    p = sp.Popen("python %(_pypy_dir)s/rpython/mucli/murpy.py %(bundle)s %(cmdargs)s" % locals(),
                 stdout=sp.PIPE, stderr=sp.PIPE, shell=True, env=env)
    stdout_data, stderr_data = p.communicate()

    # print "-------------------------------- stdout --------------------------------"
    # print stdout_data
    # print "-------------------------------- stderr --------------------------------"
    # print stderr_data

    if p.returncode == 0:
        print "-------------------------------- Program Output --------------------------------"
        lines = stdout_data.split('\n')
        idx_start = lines.index("-------------------------------- program output --------------------------------")
        idx_end = lines.index("--------------------------------------------------------------------------------")
        output = '\n'.join(lines[idx_start + 1:idx_end])
        for idx in range(idx_start, idx_end + 1):
            print lines[idx]
    else:
        output = stdout_data
        print "-------------------------------- stderr --------------------------------"
        print stderr_data

    return p.returncode, stdout_data, stderr_data


def test_factorial_noprint(tmpdir):
    bundle_file = compile_target(tmpdir, "targetfactorial_noprint.py")
    rtncode, stdout, stderr = run_bundle(bundle_file, "10")
    from targetfactorial_noprint import fac
    assert rtncode == fac(10)
