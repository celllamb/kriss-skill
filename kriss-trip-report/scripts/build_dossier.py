#!/usr/bin/env python3
"""Build a source dossier for a KRISS overseas trip report."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

try:
    from _deps import import_or_install

    PdfReader = import_or_install("pypdf", "pypdf").PdfReader
except Exception as exc:  # pragma: no cover
    PdfReader = None
    PDF_IMPORT_ERROR = exc
else:
    PDF_IMPORT_ERROR = None


PDF_EXT = ".pdf"
AUDIO_EXTS = {".m4a", ".mp3", ".wav", ".aac", ".flac", ".ogg"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".tif", ".tiff", ".webp"}
TRANSCRIPT_EXTS = {".txt", ".md", ".srt", ".vtt"}


@dataclass
class Material:
    path: str
    kind: str
    size_bytes: int | None = None
    pages: int | None = None
    text_chars: int = 0
    text_sample: str = ""
    warnings: list[str] | None = None


def mask_protected_identifiers(text: str) -> str:
    """Mask resident registration, foreign registration, and label-based passport numbers."""
    text = re.sub(r"\b\d{6}\s*[- ]\s*\d{7}\b", "[MASKED_ID]", text)
    passport_label = (
        r"(?i)((?:passport\s*(?:no\.?|number)?|"
        r"passport\s*#|"
        r"여권\s*번호|여권번호)\s*[:：#]?\s*)"
        r"([A-Z0-9][A-Z0-9 -]{4,18})"
    )
    text = re.sub(passport_label, r"\1[MASKED_PASSPORT]", text)
    return text


def normalize_text(text: str) -> str:
    text = mask_protected_identifiers(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def classify(path: Path) -> str:
    name = path.name.lower()
    suffix = path.suffix.lower()
    if suffix == PDF_EXT:
        if "agenda" in name:
            return "agenda"
        if any(token in name for token in ["boarding", "ticket", "airline", "flight", "e-ticket", "항공", "출입국"]):
            return "travel-evidence"
        if "minutes" in name:
            return "minutes"
        return "presentation-or-document"
    if suffix in AUDIO_EXTS:
        return "recording"
    if suffix in TRANSCRIPT_EXTS:
        name_tokens = ("transcript", "transcription", "recording", "audio", "녹취", "녹음", "전사")
        if any(token in name for token in name_tokens):
            return "transcript"
        return "text-document"
    if suffix in IMAGE_EXTS:
        return "photo-or-image"
    if suffix == ".zip":
        return "archive"
    return "other"


def iter_inputs(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_dir():
            yield from sorted(p for p in path.rglob("*") if p.is_file())
        elif path.is_file():
            yield path


def inspect_pdf(path: Path, max_pages: int) -> Material:
    warnings: list[str] = []
    if PdfReader is None:
        return Material(str(path), classify(path), size_bytes=path.stat().st_size, warnings=[f"pypdf unavailable: {PDF_IMPORT_ERROR}"])

    try:
        reader = PdfReader(str(path))
        pages = len(reader.pages)
        chunks: list[str] = []
        for page in reader.pages[:max_pages]:
            chunks.append(page.extract_text() or "")
        text = normalize_text("\n".join(chunks))
        if not text:
            warnings.append("No extractable text; scanned/image PDF may need OCR or visual inspection.")
        if classify(path) == "travel-evidence" and not text:
            warnings.append("Travel evidence has no extracted text; inspect before attaching and request a masked copy if needed.")
        return Material(
            path=str(path),
            kind=classify(path),
            size_bytes=path.stat().st_size,
            pages=pages,
            text_chars=len(text),
            text_sample=text[:1800],
            warnings=warnings,
        )
    except Exception as exc:
        return Material(str(path), classify(path), size_bytes=path.stat().st_size, warnings=[f"PDF read failed: {type(exc).__name__}: {exc}"])


def inspect_text(path: Path) -> Material:
    warnings: list[str] = []
    try:
        raw = path.read_text(encoding="utf-8-sig", errors="replace")
        text = normalize_text(raw)
        if classify(path) == "transcript" and not text:
            warnings.append("Transcript file is empty; do not use recording for report facts until transcribed.")
        return Material(
            str(path),
            classify(path),
            size_bytes=path.stat().st_size,
            text_chars=len(text),
            text_sample=text[:1800],
            warnings=warnings,
        )
    except Exception as exc:
        return Material(str(path), classify(path), size_bytes=path.stat().st_size, warnings=[f"Text read failed: {type(exc).__name__}: {exc}"])


def inspect_zip(path: Path) -> list[Material]:
    materials: list[Material] = [Material(str(path), "archive", size_bytes=path.stat().st_size)]
    try:
        with zipfile.ZipFile(path) as zf:
            for info in sorted(zf.infolist(), key=lambda item: item.filename):
                if info.is_dir():
                    continue
                pseudo = Path(info.filename)
                kind = classify(pseudo)
                warnings = None
                if kind == "recording":
                    warnings = ["Recording listed; transcribe before using for report facts."]
                text_sample = ""
                text_chars = 0
                if kind == "transcript":
                    try:
                        data = zf.read(info)
                        text = normalize_text(data.decode("utf-8-sig", errors="replace"))
                        text_chars = len(text)
                        text_sample = text[:1800]
                    except Exception as exc:
                        warnings = [f"Transcript read failed: {type(exc).__name__}: {exc}"]
                materials.append(
                    Material(
                        path=f"{path}::{info.filename}",
                        kind=kind,
                        size_bytes=info.file_size,
                        text_chars=text_chars,
                        text_sample=text_sample,
                        warnings=warnings,
                    )
                )
    except Exception as exc:
        materials.append(Material(str(path), "archive", warnings=[f"ZIP read failed: {type(exc).__name__}: {exc}"]))
    return materials


def build(paths: list[Path], max_pages: int) -> list[Material]:
    materials: list[Material] = []
    for path in iter_inputs(paths):
        suffix = path.suffix.lower()
        if suffix == PDF_EXT:
            materials.append(inspect_pdf(path, max_pages=max_pages))
        elif suffix == ".zip":
            materials.extend(inspect_zip(path))
        elif suffix in AUDIO_EXTS:
            materials.append(Material(str(path), "recording", size_bytes=path.stat().st_size, warnings=["Transcribe before using for report facts."]))
        elif suffix in TRANSCRIPT_EXTS:
            materials.append(inspect_text(path))
        elif suffix in IMAGE_EXTS:
            materials.append(Material(str(path), "photo-or-image", size_bytes=path.stat().st_size))
        else:
            materials.append(Material(str(path), classify(path), size_bytes=path.stat().st_size))
    return materials


def write_markdown(materials: list[Material], output: Path) -> None:
    lines = [
        "# Trip Source Dossier",
        "",
        "This dossier is an extraction aid. Re-check facts against source files before finalizing the report.",
        "",
        "## Inventory",
        "",
        "| Kind | Size | Pages | Text chars | Path | Warnings |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for item in materials:
        warnings = "; ".join(item.warnings or [])
        size = "" if item.size_bytes is None else str(item.size_bytes)
        pages = "" if item.pages is None else str(item.pages)
        lines.append(f"| {item.kind} | {size} | {pages} | {item.text_chars} | `{item.path}` | {warnings} |")

    lines.extend(["", "## Extracted Samples", ""])
    for item in materials:
        if not item.text_sample:
            continue
        lines.extend(
            [
                f"### {Path(item.path.split('::', 1)[0]).name}",
                "",
                f"Kind: `{item.kind}`",
                "",
                "```text",
                item.text_sample,
                "```",
                "",
            ]
        )
    output.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", help="Files or folders to inventory.")
    parser.add_argument("--output-md", default="trip-dossier.md", help="Markdown dossier path.")
    parser.add_argument("--output-json", default="trip-dossier.json", help="JSON inventory path.")
    parser.add_argument("--max-pages", type=int, default=5, help="Max pages to extract per PDF.")
    args = parser.parse_args(argv)

    inputs = [Path(p).expanduser().resolve() for p in args.inputs]
    materials = build(inputs, max_pages=args.max_pages)

    output_md = Path(args.output_md).resolve()
    output_json = Path(args.output_json).resolve()
    write_markdown(materials, output_md)
    output_json.write_text(
        json.dumps([asdict(item) for item in materials], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Wrote {output_md}")
    print(f"Wrote {output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
