"""Browser 'Copy as cURL' capture → AuthCredentials.

FPL's auth shape drifts between seasons, so the parser stays data-driven: it
keeps whatever the browser sent and drops only what would break the request
or poison a replayed one. Nothing here returns, logs, or raises a credential
value — errors quote the URL and key names at most.
"""

from __future__ import annotations

import re
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from fpl.auth import AuthCredentials

FPL_HOST = "fantasy.premierleague.com"
GIT_CHECK_TIMEOUT_S = 5.0

# A capture is an untrusted file: it reaches both a terminal and a request
# header. RFC 7230 tchar for names, no C0/C1 controls in values — which also
# closes header injection and terminal-escape injection.
HEADER_NAME = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f-\x9f]")

# Headers requests/urllib3 must own, or that describe the captured body.
TRANSPORT_HEADERS = frozenset(
    {
        "cookie",
        "content-length",
        "host",
        "connection",
        "accept-encoding",
        "content-type",
        "te",
        "trailer",
        "transfer-encoding",
        "upgrade",
    }
)

# Per-request Sentry tracing. Replaying one capture's trace id on every
# subsequent request is misleading at best and fingerprintable at worst.
TRACING_HEADERS = frozenset({"baggage", "sentry-trace"})

DROP_HEADERS = TRANSPORT_HEADERS | TRACING_HEADERS

HEADER_FLAGS = ("-H", "--header")
COOKIE_FLAGS = ("-b", "--cookie")
URL_FLAGS = ("--url",)
# Flags whose value must not be mistaken for the request URL.
VALUE_FLAGS = (
    "-d",
    "--data",
    "--data-raw",
    "--data-ascii",
    "--data-binary",
    "--data-urlencode",
    "-X",
    "--request",
    "-A",
    "--user-agent",
    "-e",
    "--referer",
    "-o",
    "--output",
)


class CurlParseError(ValueError):
    pass


@dataclass(frozen=True)
class CurlCapture:
    url: str
    credentials: AuthCredentials


def parse_curl(text: str) -> CurlCapture:
    headers, cookie_blobs, url = _scan(shlex.split(_join_continuations(text)))
    cookies = _split_cookies(cookie_blobs)
    if not headers and not cookies:
        raise CurlParseError(
            "no headers or cookies parsed — is this a browser 'Copy as cURL' "
            "capture? (Chrome devtools → Network → right-click the request)"
        )
    if url is None:
        raise CurlParseError(
            "no request URL found in the capture — copy the whole cURL command"
        )
    return CurlCapture(
        url=_require_fpl_url(url),
        credentials=AuthCredentials(headers=headers, cookies=cookies),
    )


def is_git_ignored(path: Path) -> bool | None:
    """None means 'unknown' — no git, or the file is outside a repository."""
    try:
        result = subprocess.run(
            ["git", "check-ignore", "--quiet", "--", path.name],
            cwd=path.resolve().parent,
            capture_output=True,
            timeout=GIT_CHECK_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def _join_continuations(text: str) -> str:
    return text.replace("\\\r\n", " ").replace("\\\n", " ")


def _scan(tokens: list[str]) -> tuple[dict[str, str], list[str], str | None]:
    headers: dict[str, str] = {}
    cookie_blobs: list[str] = []
    url: str | None = None
    index = 0
    while index < len(tokens):
        token = tokens[index]
        following = tokens[index + 1] if index + 1 < len(tokens) else None
        if token in HEADER_FLAGS and following is not None:
            _absorb_header(following, headers, cookie_blobs)
            index += 2
        elif token in COOKIE_FLAGS and following is not None:
            cookie_blobs.append(following)
            index += 2
        elif token in URL_FLAGS and following is not None:
            url = url or following
            index += 2
        elif token in VALUE_FLAGS and following is not None:
            index += 2
        elif url is None and token.startswith(("http://", "https://")):
            url = token
            index += 1
        else:
            index += 1
    return headers, cookie_blobs, url


def _absorb_header(
    raw: str, headers: dict[str, str], cookie_blobs: list[str]
) -> None:
    raw = raw.strip()
    if raw.startswith(":") or ":" not in raw:
        # HTTP/2 pseudo-header, or not a header at all.
        return
    name, _, value = raw.partition(":")
    name, value = name.strip(), value.strip()
    if not HEADER_NAME.match(name) or CONTROL_CHARS.search(value):
        return
    if name.lower() == "cookie":
        cookie_blobs.append(value)
    elif name.lower() not in DROP_HEADERS:
        headers[name] = value


def _split_cookies(blobs: list[str]) -> dict[str, str]:
    cookies: dict[str, str] = {}
    for blob in blobs:
        for part in blob.split(";"):
            part = part.strip()
            if not part or "=" not in part:
                continue
            name, _, value = part.partition("=")
            name, value = name.strip(), value.strip()
            if not name or CONTROL_CHARS.search(name + value):
                continue
            cookies[name] = value
    return cookies


def _require_fpl_url(url: str) -> str:
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    if host != FPL_HOST and not host.endswith(f".{FPL_HOST}"):
        raise CurlParseError(
            f"capture is not a {FPL_HOST} request (host: {host or 'none'}) — "
            "capture a my-team request while logged in"
        )
    # Everything but scheme/host/port/path is dropped before the URL is ever
    # printed: query, fragment and userinfo are the three places a credential
    # could ride along in plain sight.
    authority = f"{host}:{parts.port}" if parts.port else host
    return urlunsplit((parts.scheme, authority, parts.path, "", ""))
