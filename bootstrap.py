#!/usr/bin/env python3
"""Cross-platform bootstrap for clair — the shell-free equivalent of install.sh.

Windows has no bash, brew, apt, sudo, or /dev/null, so install.sh cannot run
there. This script does the same job in pure Python (stdlib only) and works on
Windows, macOS, and Linux alike:

    python bootstrap.py

It resolves the repo root, detects the OS, best-effort ensures optional deps
(git/jq — the clair core itself is stdlib-only and needs neither), then hands
off to the headless `clair apply`, which replays your saved profile.

Set CLAIR_DRYRUN=1 to print the plan and stop before touching the machine.
"""
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))


def main():
    # Make the in-repo `clair` package importable without installation.
    sys.path.insert(0, REPO_ROOT)
    os.environ["PYTHONPATH"] = (
        REPO_ROOT + os.pathsep + os.environ.get("PYTHONPATH", "")
    ).rstrip(os.pathsep)

    import clair.osenv as osenv

    os_name = osenv.detect_os()
    print("bootstrap.py: repo root: " + REPO_ROOT)
    print("bootstrap.py: detected os: " + os_name)

    cmd = [sys.executable, "-m", "clair", "apply"]

    # Dry-run: print the plan and stop BEFORE ensure_deps touches anything.
    if os.environ.get("CLAIR_DRYRUN"):
        print("bootstrap.py: DRYRUN set; would run: " + " ".join(cmd) + " (stdin </dev/null)")
        print("bootstrap.py: with PYTHONPATH=" + os.environ["PYTHONPATH"])
        return 0

    # Best-effort optional deps. python3 is obviously present (it's running us);
    # git enables overlays, jq is used by some hooks. On Windows nothing is
    # auto-installed (osenv reports "missing") — we only warn.
    report = osenv.ensure_deps(os_name, ["git", "jq"])
    missing = [pkg for pkg, status in report.items() if status == "missing"]
    if missing:
        sys.stderr.write(
            "bootstrap.py: optional dependencies not found: "
            + ", ".join(missing)
            + "\n"
        )
        sys.stderr.write(
            "bootstrap.py: install them for full functionality "
            "(git for overlays, jq for some hooks), then re-run.\n"
        )

    # Hand off to the headless apply, stdin from the null device so clair
    # auto-detects a non-interactive session and replays the saved profile.
    with open(os.devnull, "r") as devnull:
        return subprocess.call(cmd, stdin=devnull)


if __name__ == "__main__":
    sys.exit(main())
