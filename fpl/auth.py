"""Session credentials for the authenticated write path, loaded from a
git-ignored JSON file the user fills from their logged-in browser.

The schema is data-driven: whatever headers and cookies the file contains are
injected verbatim, because FPL's auth shape changes between seasons and must
never be hardcoded. Values are secrets — reprs redact them, and nothing in
this package logs, prints, or persists them.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, model_validator

DEFAULT_AUTH_PATH = Path("data/auth.json")
AUTH_FILE_MODE = 0o600
AUTH_HEADER_HINT = "authorization"


class AuthMissingError(FileNotFoundError):
    def __init__(self, path: Path) -> None:
        super().__init__(
            f"no auth credentials at {path} — copy data/auth.example.json "
            f"to {path} and fill it from your logged-in browser "
            "(see docs/api-write.md)"
        )
        self.path = path


class AuthCredentials(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    headers: dict[str, str] = {}
    cookies: dict[str, str] = {}

    @model_validator(mode="after")
    def _has_something_to_inject(self) -> AuthCredentials:
        if not self.headers and not self.cookies:
            raise ValueError(
                "auth file contains no credentials — add at least one header "
                "or cookie (see docs/api-write.md)"
            )
        return self

    def __repr__(self) -> str:
        return (
            f"AuthCredentials(headers=<{len(self.headers)} redacted>, "
            f"cookies=<{len(self.cookies)} redacted>)"
        )

    __str__ = __repr__


def load_auth(path: Path) -> AuthCredentials:
    if not path.is_file():
        raise AuthMissingError(path)
    return AuthCredentials.model_validate(
        json.loads(path.read_text(encoding="utf-8"))
    )


def save_auth(path: Path, credentials: AuthCredentials) -> None:
    """Atomic and owner-only from the first byte.

    Owner-only because the file holds a bearer token and must never exist at
    the umask default, even momentarily. Atomic because the usual caller is
    re-importing over a session that still works: a half-written file would
    destroy working credentials. os.replace carries the temp file's 0600
    across, so an existing file cannot keep a looser mode.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(
        {"headers": credentials.headers, "cookies": credentials.cookies}, indent=1
    )
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, AUTH_FILE_MODE)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(body + "\n")
        os.chmod(tmp_path, AUTH_FILE_MODE)
        os.replace(tmp_path, path)
    except OSError:
        tmp_path.unlink(missing_ok=True)
        raise


def redacted_summary(credentials: AuthCredentials) -> list[str]:
    """Key names and value lengths only — the one shape in which credentials
    may reach a terminal."""
    lines = [f"headers ({len(credentials.headers)}):"]
    lines += _redacted_entries(credentials.headers)
    lines.append(f"cookies ({len(credentials.cookies)}):")
    lines += _redacted_entries(credentials.cookies)
    return lines


def has_auth_bearing_header(credentials: AuthCredentials) -> bool:
    """Advisory only. The schema stays data-driven, so a false answer is a
    hint that the capture may be incomplete, never a gate."""
    return any(AUTH_HEADER_HINT in name.lower() for name in credentials.headers)


def _redacted_entries(values: dict[str, str]) -> list[str]:
    return [f"  {name}: <{len(value)} chars>" for name, value in sorted(values.items())]
