"""Suite-wide guard: no test may change the repo's data/ tree.

data/ holds the live season — snapshots, decisions, executor audit records and
the run log. A CLI test that forgets --data-root or --executor-root while the
working directory is the repo root writes there and still passes. Every
in-process write, directory creation, rename or delete under data/ is refused
with RepoDataWriteError, and the test fails even when the code under test
catches the error. Reads stay allowed. Subprocesses are not covered.
"""

from __future__ import annotations

import builtins
import io
import os
from pathlib import Path

import pytest

REPO_DATA = Path(__file__).resolve().parent.parent / "data"
_DATA = os.path.realpath(REPO_DATA)
_WRITE_MODE = frozenset("wax+")
_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC

violations: list[str] = []


class RepoDataWriteError(AssertionError):
    pass


def _inside_repo_data(path: object, dir_fd: int | None = None) -> bool:
    # A path relative to dir_fd (shutil.rmtree walks this way) is not
    # resolvable against the working directory; the walk's top-level call
    # carries no dir_fd and is checked.
    if isinstance(path, int) or dir_fd is not None:
        return False
    try:
        target = os.path.realpath(os.fspath(path))
    except TypeError:
        return False
    return target == _DATA or target.startswith(_DATA + os.sep)


def _refuse(operation: str, path: object) -> None:
    message = f"a test changed the repo's data/ tree: {operation} {os.fspath(path)}"
    violations.append(message)
    raise RepoDataWriteError(message)


def _guard_open(original):
    def guarded(file, mode="r", *args, **kwargs):
        if _WRITE_MODE & set(mode) and _inside_repo_data(file):
            _refuse(f"open({mode!r})", file)
        return original(file, mode, *args, **kwargs)

    return guarded


def _guard_os_open(original):
    def guarded(path, flags, *args, **kwargs):
        if flags & _WRITE_FLAGS and _inside_repo_data(path, kwargs.get("dir_fd")):
            _refuse("os.open", path)
        return original(path, flags, *args, **kwargs)

    return guarded


def _guard_path_arg(name: str, original):
    def guarded(path, *args, **kwargs):
        if _inside_repo_data(path, kwargs.get("dir_fd")):
            _refuse(name, path)
        return original(path, *args, **kwargs)

    return guarded


def _guard_move(name: str, original):
    def guarded(src, dst, *args, **kwargs):
        for path, fd in ((src, kwargs.get("src_dir_fd")), (dst, kwargs.get("dst_dir_fd"))):
            if _inside_repo_data(path, fd):
                _refuse(name, path)
        return original(src, dst, *args, **kwargs)

    return guarded


@pytest.fixture(autouse=True, scope="session")
def _repo_data_is_read_only():
    patch = pytest.MonkeyPatch()
    patch.setattr(builtins, "open", _guard_open(builtins.open))
    patch.setattr(io, "open", _guard_open(io.open))
    patch.setattr(os, "open", _guard_os_open(os.open))
    for name in ("mkdir", "rmdir", "unlink", "remove"):
        patch.setattr(os, name, _guard_path_arg(f"os.{name}", getattr(os, name)))
    for name in ("rename", "replace"):
        patch.setattr(os, name, _guard_move(f"os.{name}", getattr(os, name)))
    yield
    patch.undo()


@pytest.fixture(autouse=True)
def _fail_on_repo_data_write(_repo_data_is_read_only):
    yield
    if violations:
        found = list(violations)
        violations.clear()
        pytest.fail("\n".join(found), pytrace=False)
