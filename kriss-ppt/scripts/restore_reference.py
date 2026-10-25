#!/usr/bin/env python3
"""Reconstitute byte-identical references from lossless repository transports."""
from __future__ import annotations
import gzip
import hashlib
import json
import lzma
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "PACKAGE-MANIFEST.json"
MASTER_PARTS = tuple(f"references/kriss-wide-master.pptx.xz.part{i:02d}" for i in range(4))


def _manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _restore_one(name: str, payload: bytes, expected: str) -> dict:
    if hashlib.sha256(payload).hexdigest() != expected:
        raise ValueError(f"Restored reference fails SHA-256: {name}")
    target = ROOT / name
    if target.is_symlink():
        raise ValueError(f"Refusing symbolic link in generated reference: {name}")
    if target.exists():
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Existing reference has been modified; refusing overwrite: {name}")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    return {"path": str(target), "sha256": expected, "bytes": len(payload)}


def restore_master() -> dict:
    """Restore original KRISS PPTX exactly, including all master/layout data."""
    generated = _manifest()["generated_files"]
    payload = lzma.decompress(b"".join((ROOT / path).read_bytes() for path in MASTER_PARTS))
    return _restore_one("references/kriss-wide-master.pptx", payload,
                        generated["references/kriss-wide-master.pptx"])


def restore() -> dict:
    """Prepare all generated references; fail closed on any checksum mismatch."""
    generated = _manifest()["generated_files"]
    result = {}
    key = "references/reference.html"
    result[key] = _restore_one(key, gzip.decompress(
        (ROOT / "references/reference.html.gz").read_bytes()), generated[key])
    key = "references/source-native-visual-variants.html"
    result[key] = _restore_one(key, lzma.decompress(
        (ROOT / "references/source-native-visual-variants.html.xz").read_bytes()), generated[key])
    key = "references/kriss-wide-master.pptx"
    result[key] = restore_master()
    return result


if __name__ == "__main__":
    try:
        print(json.dumps(restore(), ensure_ascii=False, indent=2))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
