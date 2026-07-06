"""OS detection and dependency installation (contract section 4).

Stdlib-only. Production functions accept an injected ``run`` so tests
never execute real package managers.
"""

import platform
import shutil
import subprocess
from typing import Dict, List


def detect_os() -> str:
    """Return "darwin", "windows", or "linux" (the catch-all for every other
    POSIX system)."""
    system = platform.system()
    if system == "Darwin":
        return "darwin"
    if system == "Windows":
        return "windows"
    return "linux"


def have(cmd: str) -> bool:
    """True if ``cmd`` is resolvable on PATH."""
    return shutil.which(cmd) is not None


def install_cmd(os_name: str, pkg: str) -> List[str]:
    """argv to install ``pkg``: brew on darwin, apt-get otherwise."""
    if os_name == "darwin":
        return ["brew", "install", pkg]
    return ["sudo", "apt-get", "install", "-y", pkg]


def ensure_deps(os_name, pkgs, run=subprocess.run):
    # type: (str, List[str], object) -> Dict[str, str]
    """Ensure each pkg is present; never raises.

    For each pkg already on PATH -> "present". Otherwise attempt
    ``install_cmd`` via the injected ``run``; "installed" on success
    (returncode 0), "missing" on a non-zero returncode or any
    exception.
    """
    status = {}  # type: Dict[str, str]
    for pkg in pkgs:
        if have(pkg):
            status[pkg] = "present"
            continue
        if os_name == "windows":
            # No package manager is committed to on Windows; report honestly and
            # let the bootstrap tell the user to install it themselves. (git/jq
            # are optional — the stdlib-only clair core never shells out to them.)
            status[pkg] = "missing"
            continue
        try:
            completed = run(install_cmd(os_name, pkg))
            returncode = getattr(completed, "returncode", 0)
            if returncode == 0:
                status[pkg] = "installed"
            else:
                status[pkg] = "missing"
        except Exception:
            status[pkg] = "missing"
    return status


def stat_mtime_cmd(os_name: str, path: str) -> List[str]:
    """argv to print mtime as epoch seconds: BSD stat on darwin, GNU otherwise."""
    if os_name == "darwin":
        return ["stat", "-f", "%m", path]
    return ["stat", "-c", "%Y", path]
