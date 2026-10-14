#!/usr/bin/env python3
"""Check installed file inventory and hashes without third-party dependencies.

This is a local consistency check, not a signature or presentation certification.
Use --strict on a newly extracted package, before creating a virtual environment.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from package_info import ROOT, version_metadata
from restore_reference import restore


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate manifest key: {key}")
        result[key] = value
    return result


def verify(root: Path, strict: bool = False) -> dict:
    root = Path(root).resolve()
    report = {"pass": False, "version": None, "checked_files": 0,
              "strict": strict, "errors": [], "ignored": [],
              "scope": "File consistency only; not a signature or slide release approval."}
    errors = report["errors"]
    manifest_path = root / "PACKAGE-MANIFEST.json"
    try:
        report.update(version_metadata(root))
        if manifest_path.is_symlink():
            raise ValueError("Package manifest must not be a symbolic link")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"),
                              object_pairs_hook=unique_object)
        if not isinstance(manifest, dict):
            raise ValueError("Manifest must be an object")
        # The 7.7 MB canonical HTML is materialized from a compressed,
        # byte-identical repository transport and verified on every check.
        generated = manifest.get('generated_files', {})
        if generated:
            if generated.keys() != {'references/reference.html'}:
                raise ValueError('Unexpected generated file list')
            restore()
        files = manifest.get("files")
        if not isinstance(files, dict) or not files:
            raise ValueError("Manifest files must be a non-empty object")
        if manifest.get("version") != report["version"]:
            errors.append("Manifest version differs from VERSION")
        if "VERSION" not in files:
            errors.append("VERSION is missing from manifest inventory")
        expected = set()
        for name, digest in files.items():
            p = PurePosixPath(name)
            if (not name or "\\" in name or ":" in name or p.is_absolute()
                    or p.as_posix() != name or any(part in (".", "..") for part in p.parts)
                    or name == "PACKAGE-MANIFEST.json"):
                errors.append(f"Unsafe manifest path: {name}")
                continue
            expected.add(name)
            if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
                errors.append(f"Invalid SHA-256: {name}")
                continue
            target = root / name
            if any((root.joinpath(*p.parts[:n])).is_symlink()
                   for n in range(1, len(p.parts) + 1)):
                errors.append(f"Symbolic link is not an installed asset: {name}")
                continue
            if not target.is_file():
                errors.append(f"Missing file: {name}")
                continue
            actual = hashlib.sha256(target.read_bytes()).hexdigest()
            report["checked_files"] += 1
            if actual != digest:
                errors.append(f"SHA-256 mismatch: {name}")
        # rglob does not descend into symlink directories. Any encountered link
        # is nevertheless rejected; manifest paths also check every ancestor.
        harmless = {"__pycache__", ".git", ".venv", "node_modules"}
        for target in root.rglob("*"):
            relative = target.relative_to(root)
            if not strict and (harmless.intersection(relative.parts)
                               or target.name == ".DS_Store"):
                if target.is_file() or target.is_symlink():
                    report["ignored"].append(relative.as_posix())
                continue
            if target.is_symlink():
                errors.append(f"Unexpected symbolic link: {relative.as_posix()}")
            elif target.is_file() and relative.as_posix() not in expected | {"PACKAGE-MANIFEST.json"} | set(generated):
                errors.append(f"Untracked installed file: {relative.as_posix()}")
        report["manifest_sha256"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    except (OSError, ValueError, TypeError) as error:
        errors.append(str(error))
    report["pass"] = not errors
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    report = verify(ROOT, args.strict)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.json:
        # Verification evidence never belongs inside the installed package.
        if args.json.resolve().is_relative_to(ROOT):
            parser.error("Write verification results outside the installed skill")
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text, encoding="utf-8")
    print(text)
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
