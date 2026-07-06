"""clair.config — repo/home path resolution (Contract §2). Stdlib-only."""

import os
from typing import Optional


def packaged_root():
    # type: () -> Optional[str]
    """The packaged asset root from $CLAIR_ROOT, if it names a real dir; else None."""
    root = os.environ.get("CLAIR_ROOT")
    if root and os.path.isdir(root):
        return root
    return None


def is_packaged():
    # type: () -> bool
    """True when running from a package install (CLAIR_ROOT points at a real dir)."""
    return packaged_root() is not None


def repo_root():
    # type: () -> str
    """Asset root: $CLAIR_ROOT when packaged, else two-up from this file (dev checkout)."""
    pkg = packaged_root()
    if pkg:
        return pkg
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def home_target():
    # type: () -> str
    """CLAUDE_CONFIG_DIR if set, else ~/.claude. Tests inject CLAUDE_CONFIG_DIR."""
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")


def home_claude_src(root):
    # type: (str) -> str
    """The base source-of-truth mirror: <root>/home/.claude."""
    return os.path.join(root, "home", ".claude")


def manifest_path(root):
    # type: (str) -> str
    """The base-layer manifest: <root>/manifest.json."""
    return os.path.join(root, "manifest.json")


def user_config_dir():
    # type: () -> str
    """Per-user config dir: $XDG_CONFIG_HOME/clair (default ~/.config/clair)."""
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "clair")


def localenv_path(root):
    # type: (str) -> str
    """Per-machine env file. First existing of: $CLAIR_LOCAL_ENV, the XDG path
    (~/.config/clair/local.env), <root>/local.env. If none exist, the packaged
    default is the XDG path; the dev default is <root>/local.env."""
    explicit = os.environ.get("CLAIR_LOCAL_ENV")
    if explicit:
        return explicit
    xdg = os.path.join(user_config_dir(), "local.env")
    dev = os.path.join(root, "local.env")
    for candidate in (xdg, dev):
        if os.path.isfile(candidate):
            return candidate
    return xdg if is_packaged() else dev


def backup_suffix():
    # type: () -> str
    """Suffix appended when backing up an existing live file before overwrite."""
    return ".clair.bak"
