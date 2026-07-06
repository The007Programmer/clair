"""Lay managed files down: symlink / template / merge (Contract section 9).

Idempotent and safe: existing real files are backed up before overwrite. stdlib
only, Python 3.9 syntax. Depends on sibling clair modules config/manifest/
mergejson/template.
"""
import json
import os
import shutil
from typing import Dict, List, Optional, Tuple

from . import config, manifest, mergejson, template


def backup_then_write(target, content):
    # type: (str, str) -> Optional[str]
    parent = os.path.dirname(target)
    if parent:
        os.makedirs(parent, exist_ok=True)
    backup = None
    if os.path.isfile(target) and not os.path.islink(target):
        with open(target) as fh:
            existing = fh.read()
        if existing != content:
            backup = target + config.backup_suffix()
            shutil.copyfile(target, backup)
    elif os.path.islink(target):
        backup = target + config.backup_suffix()
        shutil.copyfile(target, backup)
        os.remove(target)
    with open(target, "w") as fh:
        fh.write(content)
    return backup


def apply_symlink(src_abs, target):
    # type: (str, str) -> str
    parent = os.path.dirname(target)
    if parent:
        os.makedirs(parent, exist_ok=True)
    if os.path.islink(target):
        # Compare the LITERAL link target, not its realpath: a link pointing at a
        # versioned Homebrew Cellar keg and one pointing at the stable `opt` prefix
        # resolve identically today, but only the latter survives `brew upgrade`.
        # Keying idempotency on realpath would skip repointing Cellar -> opt.
        if os.readlink(target) == src_abs:
            return "ok"
        os.remove(target)
    elif os.path.exists(target):
        # A prior copy-fallback (Windows / a filesystem that forbids symlinks)
        # leaves a REAL file here, not a link. If it already matches the source,
        # re-applying is a no-op — do not churn a fresh *.clair.bak every run.
        if _same_file(src_abs, target):
            return "ok"
        shutil.copyfile(target, target + config.backup_suffix())
        os.remove(target)
    try:
        os.symlink(src_abs, target)
        return "linked"
    except OSError:
        # Symlinks are unavailable (e.g. Windows without Developer Mode/admin).
        # Fall back to a real copy — drift detection and uninstall already treat
        # a real file at a symlink target correctly.
        _copy_path(src_abs, target)
        return "copied"


def _same_file(a, b):
    # type: (str, str) -> bool
    """True iff both are regular files with identical bytes. A directory never
    matches (a symlinked-dir install has no single-file body to compare)."""
    if os.path.isdir(a) or os.path.isdir(b):
        return False
    try:
        with open(a, "rb") as fa, open(b, "rb") as fb:
            return fa.read() == fb.read()
    except OSError:
        return False


def _copy_path(src_abs, target):
    # type: (str, str) -> None
    if os.path.isdir(src_abs):
        shutil.copytree(src_abs, target)
    else:
        shutil.copyfile(src_abs, target)


def apply_template(src_tmpl_path, target, vars, vault_enabled):
    # type: (str, str, Dict[str, str], bool) -> str
    if target.endswith(".tmpl"):
        target = target[: -len(".tmpl")]
    with open(src_tmpl_path) as fh:
        raw = fh.read()
    rendered = template.render(raw, vars, vault_enabled)
    backup_then_write(target, rendered)
    return "rendered"


def apply_merge_json(src_json_path, target):
    # type: (str, str) -> str
    with open(src_json_path) as fh:
        base_obj = json.load(fh)
    merged = mergejson.merge_settings_file(target, base_obj)
    backup_then_write(target, json.dumps(merged, indent=2))
    return "merged"


def apply_item(item, src_base_dir, home_target, vars, vault_enabled):
    # type: (manifest.Item, str, str, Dict[str, str], bool) -> str
    src = os.path.join(src_base_dir, item.path)
    target = os.path.join(home_target, item.path)
    if item.mode == "symlink":
        return apply_symlink(src, target)
    if item.mode == "template":
        return apply_template(src, target, vars, vault_enabled)
    if item.mode == "merge":
        return apply_merge_json(src, target)
    raise ValueError("unknown mode: " + repr(item.mode))


def apply_layer(items, layer, src_base_dir, home_target, vars, vault_enabled, os_name):
    # type: (List[manifest.Item], str, str, str, Dict[str, str], bool, str) -> List[Tuple[str, str]]
    results = []  # type: List[Tuple[str, str]]
    for item in items:
        if item.layer != layer:
            continue
        if not manifest.applies_to_os(item, os_name):
            continue
        result = apply_item(item, src_base_dir, home_target, vars, vault_enabled)
        results.append((item.path, result))
    return results
