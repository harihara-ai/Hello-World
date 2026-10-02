"""Thin wrappers around git and the filesystem."""
import hashlib
import os
import shutil
import stat
import subprocess
from pathlib import Path


class GitError(RuntimeError):
    pass


def git(repo, *args, check=True):
    proc = subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def worktree_add(repo, path, rev):
    git(repo, "worktree", "add", "--detach", "--force", str(path), rev)


def worktree_remove(repo, path):
    git(repo, "worktree", "remove", "--force", str(path), check=False)
    shutil.rmtree(path, ignore_errors=True)
    git(repo, "worktree", "prune", check=False)


def changed_files(worktree):
    """Paths (tracked or untracked) that differ from the checked-out commit."""
    out = git(worktree, "status", "--porcelain", "--untracked-files=all", "-z")
    paths = []
    entries = out.split("\0")
    i = 0
    while i < len(entries):
        entry = entries[i]
        i += 1
        if not entry:
            continue
        code, path = entry[:2], entry[3:]
        paths.append(path)
        if code[0] in "RC":  # rename/copy: next entry is the source path
            paths.append(entries[i])
            i += 1
    return paths


def diff_patch(worktree):
    git(worktree, "add", "-A", "--intent-to-add", check=False)
    return git(worktree, "diff", check=False)


def tree_hash(paths):
    """sha256 over the names and contents of every file under `paths`."""
    h = hashlib.sha256()
    for root in paths:
        root = Path(root)
        if not root.exists():
            h.update(f"missing:{root.name}".encode())
            continue
        files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
        for f in files:
            h.update(str(f.relative_to(root.parent)).encode())
            h.update(b"\0")
            h.update(f.read_bytes())
    return h.hexdigest()


def set_readonly(path, readonly=True):
    """chmod a tree read-only (or back to writable). Root ignores this; the hash check doesn't."""
    path = Path(path)
    items = [path] + (list(path.rglob("*")) if path.is_dir() else [])
    for p in sorted(items, key=lambda p: len(p.parts), reverse=not readonly):
        mode = p.stat().st_mode
        if readonly:
            mode &= ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
        else:
            mode |= stat.S_IWUSR
        os.chmod(p, mode)


def copy_tree(src, dst, exclude=()):
    """Copy src/* into dst, merging directories. Returns the relative paths written."""
    src, dst = Path(src), Path(dst)
    written = []
    for f in sorted(src.rglob("*")):
        rel = f.relative_to(src)
        if rel.parts[0] in exclude or not f.is_file():
            continue
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
        written.append(rel.as_posix())
    return written
