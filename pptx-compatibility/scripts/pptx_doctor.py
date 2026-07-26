"""End-to-end PPTX diagnosis, repair, rebuild, and validation CLI.

Key principle: Passing ZIP/XML validation does not guarantee Microsoft
PowerPoint compatibility. PowerPoint is strict about the presentation
relationship graph, especially slideMaster and slideLayout relationships. It
is also strict about per-slide shape ID uniqueness and DrawingML paragraph end
run properties. If minimal XML/package repair is not enough, rebuild a clean
presentation graph.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:  # pragma: no cover
    from inspect_pptx import DiagnosticReport, inspect_pptx
    from rebuild_pptx import rebuild_presentation
    from repair_pptx_package import minimal_repair, structural_repair
    from validate_repaired_pptx import validate_pptx
except ImportError:  # pragma: no cover
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from inspect_pptx import DiagnosticReport, inspect_pptx
    from rebuild_pptx import rebuild_presentation
    from repair_pptx_package import minimal_repair, structural_repair
    from validate_repaired_pptx import validate_pptx


def run_doctor(
    input_path: str | Path,
    *,
    out_dir: str | Path,
    repair_level: str = "auto",
    report_format: str = "both",
    keep_temp: bool = False,
    strict: bool = False,
    no_libreoffice: bool = False,
) -> dict[str, Any]:
    """Run inspection, repair, validation, and report generation."""

    source = Path(input_path)
    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = source.stem

    temp_context = _temp_context(output_dir, keep_temp)
    temp_dir = temp_context.__enter__()
    try:
        working_copy = temp_dir / source.name
        shutil.copy2(source, working_copy)

        initial = inspect_pptx(working_copy)
        expected_slide_count = initial.slide_count
        result: dict[str, Any] = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "input_path": str(source),
            "working_copy": str(working_copy),
            "repair_level": repair_level,
            "initial_diagnostic": initial.to_dict(),
            "repair_attempts": [],
            "validation": None,
            "output_path": None,
            "status": "unrepaired",
        }

        output_path: Path | None = None
        if repair_level == "minimal":
            output_path = output_dir / f"{stem}_repaired.pptx"
            attempt = minimal_repair(working_copy, output_path, initial)
            result["repair_attempts"].append(attempt.to_dict())
            result["validation"] = validate_pptx(
                output_path,
                expected_slide_count=expected_slide_count,
                no_libreoffice=no_libreoffice,
                strict=strict,
            ).to_dict()
        elif repair_level == "structural":
            output_path = output_dir / f"{stem}_repaired.pptx"
            attempt = structural_repair(working_copy, output_path, initial)
            result["repair_attempts"].append(attempt.to_dict())
            result["validation"] = validate_pptx(
                output_path,
                expected_slide_count=expected_slide_count,
                no_libreoffice=no_libreoffice,
                strict=strict,
            ).to_dict()
        elif repair_level == "rebuild":
            output_path = output_dir / f"{stem}_rebuilt.pptx"
            attempt = rebuild_presentation(
                working_copy,
                output_path,
                no_libreoffice=no_libreoffice,
                strict=strict,
            )
            result["repair_attempts"].append({"level": "rebuild", **attempt.to_dict()})
            result["validation"] = attempt.validation
        else:
            output_path = _run_auto(
                working_copy,
                output_dir,
                stem,
                initial,
                expected_slide_count,
                no_libreoffice,
                strict,
                result,
            )

        result["output_path"] = str(output_path) if output_path else None
        validation = result.get("validation") or {}
        result["status"] = "validated" if validation.get("ok") else "validation_failed"

        _write_reports(result, output_dir, stem, report_format)
        return result
    finally:
        temp_context.__exit__(None, None, None)


def _run_auto(
    working_copy: Path,
    output_dir: Path,
    stem: str,
    initial: DiagnosticReport,
    expected_slide_count: int,
    no_libreoffice: bool,
    strict: bool,
    result: dict[str, Any],
) -> Path:
    minimal_path = output_dir / f"{stem}_repaired.pptx"
    minimal = minimal_repair(working_copy, minimal_path, initial)
    result["repair_attempts"].append(minimal.to_dict())
    validation = validate_pptx(
        minimal_path,
        expected_slide_count=expected_slide_count,
        no_libreoffice=no_libreoffice,
        strict=strict,
    )
    result["validation"] = validation.to_dict()
    if validation.ok:
        return minimal_path

    structural_path = output_dir / f"{stem}_repaired.pptx"
    structural = structural_repair(working_copy, structural_path, initial)
    result["repair_attempts"].append(structural.to_dict())
    validation = validate_pptx(
        structural_path,
        expected_slide_count=expected_slide_count,
        no_libreoffice=no_libreoffice,
        strict=strict,
    )
    result["validation"] = validation.to_dict()
    if validation.ok:
        return structural_path

    rebuilt_path = output_dir / f"{stem}_rebuilt.pptx"
    try:
        rebuilt = rebuild_presentation(
            working_copy,
            rebuilt_path,
            no_libreoffice=no_libreoffice,
            strict=strict,
        )
    except RuntimeError as exc:
        result["repair_attempts"].append({"level": "rebuild", "error": str(exc)})
        return structural_path

    result["repair_attempts"].append({"level": "rebuild", **rebuilt.to_dict()})
    result["validation"] = rebuilt.validation
    return rebuilt_path


class _temp_context:
    def __init__(self, output_dir: Path, keep: bool) -> None:
        self.output_dir = output_dir
        self.keep = keep
        self.path: Path | None = None

    def __enter__(self) -> Path:
        if self.keep:
            self.path = self.output_dir / "_pptx_doctor_temp"
            self.path.mkdir(parents=True, exist_ok=True)
            return self.path
        self._manager = tempfile.TemporaryDirectory(prefix="pptx-doctor-")  # type: ignore[attr-defined]
        self.path = Path(self._manager.__enter__())  # type: ignore[attr-defined]
        return self.path

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if not self.keep:
            self._manager.__exit__(exc_type, exc, tb)  # type: ignore[attr-defined]


def _write_reports(result: dict[str, Any], output_dir: Path, stem: str, report_format: str) -> None:
    if report_format in ("json", "both"):
        (output_dir / f"{stem}_diagnostic_report.json").write_text(
            json.dumps(result, indent=2),
            encoding="utf-8",
        )
    if report_format in ("markdown", "both"):
        (output_dir / f"{stem}_diagnostic_report.md").write_text(
            format_markdown_report(result),
            encoding="utf-8",
        )


def format_markdown_report(result: dict[str, Any]) -> str:
    """Format the doctor result as a concise Markdown report."""

    initial = result.get("initial_diagnostic", {})
    summary = initial.get("summary", {})
    validation = result.get("validation") or {}
    lines = [
        "# PPTX Diagnostic Report",
        "",
        f"- Input: `{result.get('input_path')}`",
        f"- Status: `{result.get('status')}`",
        f"- Repair level: `{result.get('repair_level')}`",
        f"- Output: `{result.get('output_path')}`",
        "",
        "## Initial Inspection",
        "",
        f"- Critical: {summary.get('critical', 0)}",
        f"- Warnings: {summary.get('warning', 0)}",
        f"- Info: {summary.get('info', 0)}",
        f"- Slides: {summary.get('slide_count', 0)}",
        "",
    ]

    issues = initial.get("issues", [])
    if issues:
        lines.extend(["### Findings", ""])
        for issue in issues:
            location = issue.get("part") or issue.get("rels_file") or issue.get("target") or "(package)"
            lines.append(f"- **{issue.get('severity')}** `{issue.get('code')}` at `{location}`: {issue.get('message')}")
        lines.append("")

    attempts = result.get("repair_attempts", [])
    if attempts:
        lines.extend(["## Repair Attempts", ""])
        for attempt in attempts:
            level = attempt.get("level", "unknown")
            if "error" in attempt:
                lines.append(f"- `{level}` failed: {attempt['error']}")
                continue
            changes = attempt.get("changes", [])
            if not changes:
                lines.append(f"- `{level}` completed with no recorded changes.")
                continue
            lines.append(f"- `{level}` recorded {len(changes)} change(s):")
            for change in changes[:20]:
                lines.append(f"  - `{change.get('action')}` in `{change.get('part')}`: {change.get('message')}")
            if len(changes) > 20:
                lines.append(f"  - ... {len(changes) - 20} more change(s)")
        lines.append("")

    lines.extend(
        [
            "## Validation",
            "",
            f"- OK: {validation.get('ok')}",
            f"- ZIP OK: {validation.get('zip_ok')}",
            f"- No critical issues: {validation.get('no_critical_issues')}",
            f"- Slide count: {validation.get('slide_count')}",
            f"- python-pptx open: {validation.get('python_pptx_ok')}",
            f"- LibreOffice headless: {validation.get('libreoffice_ok')}",
        ]
    )
    messages = validation.get("messages") or []
    if messages:
        lines.extend(["", "### Validation Messages", ""])
        lines.extend(f"- {message}" for message in messages)
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diagnose and repair a broken PPTX file.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--repair-level", choices=("auto", "minimal", "structural", "rebuild"), default="auto")
    parser.add_argument("--report", choices=("markdown", "json", "both"), default="both")
    parser.add_argument("--keep-temp", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--no-libreoffice", action="store_true")
    args = parser.parse_args(argv)

    result = run_doctor(
        args.input,
        out_dir=args.out_dir,
        repair_level=args.repair_level,
        report_format=args.report,
        keep_temp=args.keep_temp,
        strict=args.strict,
        no_libreoffice=args.no_libreoffice,
    )

    print(f"Status: {result['status']}")
    print(f"Output: {result.get('output_path')}")
    print(f"Report: {args.out_dir / (args.input.stem + '_diagnostic_report.md')}")
    return 0 if result["status"] == "validated" else 1


if __name__ == "__main__":
    raise SystemExit(main())
