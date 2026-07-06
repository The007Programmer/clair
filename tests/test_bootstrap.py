import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
BOOTSTRAP = os.path.join(REPO_ROOT, "bootstrap.py")


def _run_bootstrap(extra_env, cwd=None):
    env = dict(os.environ)
    env.update(extra_env)
    return subprocess.run(
        [sys.executable, BOOTSTRAP],
        cwd=cwd or os.path.expanduser("~"),  # prove it does not depend on cwd
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )


def test_bootstrap_exists():
    assert os.path.isfile(BOOTSTRAP)


def test_bootstrap_dryrun_exits_zero_and_reports_plan():
    proc = _run_bootstrap({"CLAIR_DRYRUN": "1"})
    assert proc.returncode == 0, proc.stdout
    # resolves the repo root regardless of the caller's cwd
    assert REPO_ROOT in proc.stdout
    # detects an os value from osenv.detect_os()
    assert any(o in proc.stdout for o in ("darwin", "linux", "windows"))
    # reports it would run the headless apply, and marks the dry-run
    assert "clair apply" in proc.stdout
    assert "DRYRUN" in proc.stdout


def test_bootstrap_dryrun_does_not_attempt_package_install(tmp_path):
    # Same guarantee as install.sh: a dry-run short-circuits BEFORE ensure_deps.
    sentinel = tmp_path / "install_attempted"
    bindir = tmp_path / "bin"
    bindir.mkdir()
    for name in ("brew", "apt-get", "sudo"):
        stub = bindir / name
        stub.write_text(
            "#!/usr/bin/env bash\n"
            'echo "$0 $*" >> "%s"\n'
            "exit 0\n" % str(sentinel)
        )
        stub.chmod(0o755)
    env = {"CLAIR_DRYRUN": "1", "PATH": str(bindir) + os.pathsep + os.environ["PATH"]}
    proc = _run_bootstrap(env)
    assert proc.returncode == 0, proc.stdout
    assert not sentinel.exists(), (
        "dry-run attempted a package install:\n" + sentinel.read_text()
    )


def test_bootstrap_is_shell_free_and_cross_platform():
    # The whole point of bootstrap.py is to NOT depend on bash/POSIX shell.
    with open(BOOTSTRAP, "r") as fh:
        body = fh.read()
    # drives the current interpreter, not a hardcoded python3 binary
    assert "sys.executable" in body
    # uses os.devnull rather than a literal /dev/null redirect
    assert "os.devnull" in body
    # invokes the clair CLI as a module
    assert "clair" in body and "apply" in body
