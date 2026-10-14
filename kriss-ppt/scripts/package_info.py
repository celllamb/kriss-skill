"""Read package identity from VERSION; never substitute an exporter constant."""
from __future__ import annotations
import hashlib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
# SemVer core plus optional prerelease/build identifiers. Numeric prerelease
# identifiers cannot contain leading zeroes; numeric build identifiers may.
CORE = r"(?:0|[1-9][0-9]*)"
IDENT = r"(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
VERSION_RE = re.compile(
    rf"{CORE}\.{CORE}\.{CORE}(?:-{IDENT}(?:\.{IDENT})*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)


def version_metadata(root: Path | None = None) -> dict[str, str]:
    path = (Path(root) if root is not None else ROOT) / "VERSION"
    try:
        if path.is_symlink():
            raise ValueError("VERSION must not be a symbolic link")
        raw = path.read_bytes()
        value = raw.decode("utf-8").strip()
    except (OSError, UnicodeError) as error:
        raise ValueError(f"Cannot read package VERSION: {error}") from error
    if not VERSION_RE.fullmatch(value):
        raise ValueError("VERSION must contain exactly one valid semantic version")
    return {"version": value, "version_file_sha256": hashlib.sha256(raw).hexdigest()}


def read_version(root: Path | None = None) -> str:
    return version_metadata(root)["version"]
