"""
Compile and run the targets as pytests
"""
import subprocess as sp
import os


targets_dir = os.path.dirname(__file__)


def _up(str_dir):
    return os.path.abspath(os.path.join(str_dir, os.pardir))


def compile_target(tmpdir, target, args=list()):
    if isinstance(args, list):
        args = ' '.join(args)
    output_file = os.path.join(tmpdir.strpath, target.replace('.py', '.mu'))
    target_file = os.path.join(targets_dir, target)

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


def run_bundle(bundle, cmdargs=list(), print_stderr_when_fail=True):
    if isinstance(cmdargs, list):
        cmdargs = ' '.join(cmdargs)

    env = os.environ
    env['PATH'] = env['MU'] + "/cbinding:" + env['PATH']
    murpy_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'mucli', 'murpy.py'))
    cmd = "python %(murpy_path)s %(bundle)s %(cmdargs)s" % locals()
    print cmd
    p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True, env=env)
    stdout_data, stderr_data = p.communicate()

    # print "-------------------------------- stdout --------------------------------"
    # print stdout_data
    # print "-------------------------------- stderr --------------------------------"
    # print stderr_data

    if p.returncode != 0:
        if print_stderr_when_fail:
            print "-------------------------------- stderr --------------------------------"
            print stderr_data
            print "------------------------------------------------------------------------"

    return p.returncode, stdout_data, stderr_data


def test_factorial_noprint(tmpdir):
    bundle_file = compile_target(tmpdir, "targetfactorial_noprint.py")
    n = 5
    rtncode, stdout, stderr = run_bundle(bundle_file, [str(n)], print_stderr_when_fail=False)
    from targetfactorial_noprint import fac
    assert rtncode == fac(n)


def test_print_helloworld(tmpdir):
    bundle_file = compile_target(tmpdir, "targetprint.py")
    r, out, err = run_bundle(bundle_file, [])
    assert out == "hello world\n"


def test_warningalone(tmpdir):
    bundle = compile_target(tmpdir, "targetwarningalone.py")
    r, out, err = run_bundle(bundle, ['0'])
    assert out == '9\n'
    r, out, err = run_bundle(bundle, ['4'])
    assert out == '1\n'
    r, out, err = run_bundle(bundle, ['2'])
    assert out == '2\n'
    r, out, err = run_bundle(bundle, ['1'])
    assert out == '0\n'


def test_testlistvsdict(tmpdir):
    bundle = compile_target(tmpdir, "targettestlistvsdict.py")
    r, out, err = run_bundle(bundle, ['d', '1234'])
    assert out == '1234\n'
    r, out, err = run_bundle(bundle, ['l', '234'])
    assert out == '1234\n'
    r, out, err = run_bundle(bundle, ['d', '234'], print_stderr_when_fail=False)
    assert r == 1


def test_targettestdicts(tmpdir):
    bundle = compile_target(tmpdir, "targettestdicts.py")
    r, out, err = run_bundle(bundle, ['d', '256'])
    assert out == '0x100\n'
    r, out, err = run_bundle(bundle, ['d', '4095'])
    assert out == '0xfff\n'
    r, out, err = run_bundle(bundle, ['d', '4096'], print_stderr_when_fail=False)
    assert r == 1
    r, out, err = run_bundle(bundle, ['r', '0x100'])
    assert out == '256\n'
    r, out, err = run_bundle(bundle, ['r', '0xfff'])
    assert out == '4095\n'


# This test target takes quite a while to run...
# def test_targetvarsized(tmpdir):
#     bundle = compile_target(tmpdir, "targetvarsized.py", ['1'])
#     r, out, err = run_bundle(bundle)
#     print out
#     assert r == 0

# This test also takes a LONG time...
# def test_targetsimplereadandwrite(tmpdir):
#     bundle = compile_target(tmpdir, "targetsimplewrite.py")
#     r, out, err = run_bundle(bundle, [])
#     assert r == 0
#
#     bundle = compile_target(tmpdir, "targetsimpleread.py")
#     r, out, err = run_bundle(bundle, [])
#     assert r == 0


def test_targetsha1sum(tmpdir):
    bundle = compile_target(tmpdir, "targetsha1sum.py")
    file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'requirements.txt'))
    r, out, err = run_bundle(bundle, [file])
    assert out.split(' ')[0] == '1a0f9d4af927a8d597dbc15f5bc09693da299cec'


def test_rpystonedalone(tmpdir):
    bundle = compile_target(tmpdir, "targetrpystonedalone.py")
    r, out, err = run_bundle(bundle, ["pystone", "1000"])
    print out
    assert r == 0

    r, out, err = run_bundle(bundle, ["richards", "1"])
    print out
    assert r == 0


def test_ackermann(tmpdir):
    bundle = compile_target(tmpdir, "targetackermann.py")
    r, out, err = run_bundle(bundle, ["3", "4"])
    assert out == "125\n"


def test_noop(tmpdir):
    bundle = compile_target(tmpdir, "targetreallynopstandalone.py")
    r, out, err = run_bundle(bundle, [])
    assert r == 0


def test_targetreadlines(tmpdir):
    bundle = compile_target(tmpdir, "targetreadlines.py")
    file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'requirements.txt'))
    r, out, err = run_bundle(bundle, ['\'enum34>=1.1.2\'', file])
    assert out == "enum34>=1.1.2\n\n"


def test_targetpushpop(tmpdir):
    bundle = compile_target(tmpdir, "targetpushpop.py")
    r, out, err = run_bundle(bundle, [])
    assert r == 11


# def test_targetosreadbench(tmpdir):
#     bundle = compile_target(tmpdir, "targetosreadbench.py")
#     r, out, err = run_bundle(bundle, [__file__])
#     assert r == 0


def test_targetlbench(tmpdir):
    bundle = compile_target(tmpdir, "targetlbench.py")
    r, out, err = run_bundle(bundle, ['20'])
    assert out == '0\n'
    assert r == 0
