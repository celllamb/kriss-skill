#!/usr/bin/env python3
"""Compare two HWPX packages entry-by-entry after a Hancom Office round trip."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import sys
import zipfile
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def package_snapshot(path: Path) -> dict[str, dict[str, object]]:
    snapshot: dict[str, dict[str, object]] = {}
    with zipfile.ZipFile(path, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            data = zf.read(info.filename)
            snapshot[info.filename] = {
                "sha256": sha256(data),
                "size": len(data),
                "compress_type": info.compress_type,
                "compressed_size": info.compress_size,
            }
    return snapshot


def compare(before: Path, after: Path) -> dict[str, object]:
    before_snapshot = package_snapshot(before)
    after_snapshot = package_snapshot(after)
    before_names = set(before_snapshot)
    after_names = set(after_snapshot)
    added = sorted(after_names - before_names)
    removed = sorted(before_names - after_names)
    changed = []
    metadata_only = []
    for name in sorted(before_names & after_names):
        before_entry = before_snapshot[name]
        after_entry = after_snapshot[name]
        if before_entry["sha256"] != after_entry["sha256"]:
            changed.append(
                {
                    "name": name,
                    "before_size": before_entry["size"],
                    "after_size": after_entry["size"],
                    "before_sha256": before_entry["sha256"],
                    "after_sha256": after_entry["sha256"],
                }
            )
        elif (
            before_entry["compress_type"] != after_entry["compress_type"]
            or before_entry["compressed_size"] != after_entry["compressed_size"]
        ):
            metadata_only.append(name)

    before_image_hashes = Counter(
        entry["sha256"] for name, entry in before_snapshot.items() if name.startswith("BinData/")
    )
    after_image_hashes = Counter(
        entry["sha256"] for name, entry in after_snapshot.items() if name.startswith("BinData/")
    )
    changed_entry_names = {entry["name"] for entry in changed}
    image_payloads_unchanged = before_image_hashes == after_image_hashes
    only_hancom_normalized_entries = (
        not added
        and not removed
        and image_payloads_unchanged
        and changed_entry_names.issubset(
            {
                "Contents/content.hpf",
                "Contents/header.xml",
                "Contents/section0.xml",
                "Preview/PrvImage.png",
                "Preview/PrvText.txt",
            }
        )
    )
    acceptable = not added and not removed and (not changed or only_hancom_normalized_entries)
    return {
        "before": str(before),
        "after": str(after),
        "ok": acceptable,
        "image_payloads_unchanged": image_payloads_unchanged,
        "only_hancom_normalized_entries": only_hancom_normalized_entries,
        "added": added,
        "removed": removed,
        "changed": changed,
        "metadata_only_changes": metadata_only,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", help="Generated HWPX before opening/saving in Hancom Office.")
    parser.add_argument("after", help="HWPX after opening/saving in Hancom Office.")
    args = parser.parse_args(argv)

    result = compare(Path(args.before), Path(args.after))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
