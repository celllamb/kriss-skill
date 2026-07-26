"""Validate repaired or rebuilt PPTX files without requiring PowerPoint.

Key principle: Passing ZIP/XML validation does not guarantee Microsoft
PowerPoint compatibility. PowerPoint is strict about the presentation
relationship graph, especially slideMaster and slideLayout relationships. It
is also strict about per-slide shape ID uniqueness and DrawingML paragraph end
run properties. If minimal XML/package repair is not enough, rebuild a clean
presentation graph.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

try:  # pragma: no cover
    from inspect_pptx import DiagnosticReport, inspect_pptx
except ImportError:  # pragma: no cover
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from inspect_pptx import DiagnosticReport, inspect_pptx


@dataclass
class ValidationResult:
    """Validation outcome for a PPTX output file."""

    path: str
    ok: bool
    zip_ok: bool
    no_critical_issues: bool
    slide_count: int
    expected_slide_count: int | None = None
    python_pptx_ok: bool | None = None
    libreoffice_ok: bool | None = None
    messages: list[str] = field(default_factory=list)
    diagnostic: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_pptx(
    path: str | Path,
    *,
    expected_slide_count: int | None = None,
    no_libreoffice: bool = False,
    strict: bool = False,
) -> ValidationResult:
    """Validate a repaired PPTX output."""

    pptx_path = Path(path)
    messages: list[str] = []
    zip_ok = _zip_ok(pptx_path, messages)
    diagnostic: DiagnosticReport = inspect_pptx(pptx_path)
    no_critical = diagnostic.critical_count == 0

    if not no_critical:
        messages.append(f"Inspection still reports {diagnostic.critical_count} critical issue(s).")
    if strict and diagnostic.warning_count:
        messages.append(f"Strict mode: inspection still reports {diagnostic.warning_count} warning(s).")

    if expected_slide_count is not None and diagnostic.slide_count != expected_slide_count:
        messages.append(
            f"Slide count changed from {expected_slide_count} to {diagnostic.slide_count}."
        )

    python_pptx_ok = _try_python_pptx(pptx_path, messages)
    libreoffice_ok = None if no_libreoffice else _try_libreoffice(pptx_path, messages)

    ok = zip_ok and no_critical
    if strict:
        ok = ok and diagnostic.warning_count == 0
    if expected_slide_count is not None:
        ok = ok and diagnostic.slide_count == expected_slide_count
    if python_pptx_ok is False:
        ok = False
    if libreoffice_ok is False:
        ok = False

    return ValidationResult(
        path=str(pptx_path),
        ok=ok,
        zip_ok=zip_ok,
        no_critical_issues=no_critical,
        slide_count=diagnostic.slide_count,
        expected_slide_count=expected_slide_count,
        python_pptx_ok=python_pptx_ok,
        libreoffice_ok=libreoffice_ok,
        messages=messages,
        diagnostic=diagnostic.to_dict(),
    )


def _zip_ok(path: Path, messages: list[str]) -> bool:
    try:
        with zipfile.ZipFile(path, "r") as zf:
            bad_member = zf.testzip()
            if bad_member:
                messages.append(f"ZIP CRC validation failed for {bad_member}.")
                return False
            return True
    except zipfile.BadZipFile as exc:
        messages.append(f"Not a valid ZIP package: {exc}")
    except OSError as exc:
        messages.append(f"Could not read file: {exc}")
    return False


def _try_python_pptx(path: Path, messages: list[str]) -> bool | None:
    try:
        from pptx import Presentation  # type: ignore
    except ImportError:
        messages.append("python-pptx is not installed; skipped python-pptx open check.")
        return None

    try:
        Presentation(str(path))
        return True
    except Exception as exc:  # pragma: no cover - depends on optional library behavior
        messages.append(f"python-pptx could not open the file: {exc}")
        return False


def _try_libreoffice(path: Path, messages: list[str]) -> bool | None:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        messages.append("LibreOffice soffice executable not found; skipped headless conversion check.")
        return None

    with tempfile.TemporaryDirectory(prefix="pptx-lo-") as temp_dir:
        result = subprocess.run(
            [
                soffice,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                temp_dir,
                str(path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
            check=False,
        )
        pdf_path = Path(temp_dir) / f"{path.stem}.pdf"
        if result.returncode == 0 and pdf_path.exists():
            return True
        messages.append(
            "LibreOffice headless conversion failed: "
            + (result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}")
        )
        return False


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Validate a repaired PPTX file.")
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--expected-slide-count", type=int)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--no-libreoffice", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = validate_pptx(
        args.pptx,
        expected_slide_count=args.expected_slide_count,
        strict=args.strict,
        no_libreoffice=args.no_libreoffice,
    )
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"{args.pptx}: {'ok' if result.ok else 'failed'}")
        for message in result.messages:
            print(f"- {message}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
