"""Session credentials for the authenticated write path, loaded from a
git-ignored JSON file the user fills from their logged-in browser.

The schema is data-driven: whatever headers and cookies the file contains are
injected verbatim, because FPL's auth shape changes between seasons and must
never be hardcoded. Values are secrets — reprs redact them, and nothing in
this package logs, prints, or persists them.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, model_validator

DEFAULT_AUTH_PATH = Path("data/auth.json")


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
