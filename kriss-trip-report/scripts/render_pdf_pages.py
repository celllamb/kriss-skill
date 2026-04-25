#!/usr/bin/env python3
"""Render selected PDF pages to PNG files with Ghostscript."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from _deps import import_or_install


def find_ghostscript() -> str | None:
    for candidate in ("gswin64c.exe", "gswin32c.exe", "gs"):
        path = shutil.which(candidate)
        if path:
            return path
    return None


def parse_pages(raw: str | list[int]) -> list[int]:
    if isinstance(raw, list):
        return [int(page) for page in raw]
    pages: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = [int(x) for x in part.split("-", 1)]
            pages.extend(range(start, end + 1))
        else:
            pages.append(int(part))
    return pages


def render_job(gs: str, pdf: Path, pages: list[int], output_dir: Path, prefix: str, dpi: int) -> list[Path]:
    if not pdf.exists():
        raise FileNotFoundError(f"PDF not found: {pdf}")
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for page in pages:
        out = output_dir / f"{prefix}-p{page:02d}.png"
        cmd = [
            gs,
            "-q",
            "-dSAFER",
            "-dBATCH",
            "-dNOPAUSE",
            "-sDEVICE=png16m",
            f"-r{dpi}",
            f"-dFirstPage={page}",
            f"-dLastPage={page}",
            f"-sOutputFile={out}",
            str(pdf),
        ]
        subprocess.run(cmd, check=True)
        outputs.append(out)
    return outputs


def render_job_with_pymupdf(pdf: Path, pages: list[int], output_dir: Path, prefix: str, dpi: int) -> list[Path]:
    fitz = import_or_install("fitz", "PyMuPDF")
    if not pdf.exists():
        raise FileNotFoundError(f"PDF not found: {pdf}")
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    with fitz.open(str(pdf)) as doc:
        for page in pages:
            if page < 1 or page > len(doc):
                raise ValueError(f"Page {page} is outside the PDF page range 1-{len(doc)}: {pdf}")
            out = output_dir / f"{prefix}-p{page:02d}.png"
            pix = doc[page - 1].get_pixmap(matrix=matrix, alpha=False)
            pix.save(str(out))
            outputs.append(out)
    return outputs


def load_jobs(args: argparse.Namespace) -> list[dict[str, object]]:
    if args.jobs:
        data = json.loads(Path(args.jobs).read_text(encoding="utf-8-sig"))
        if not isinstance(data, list):
            raise ValueError("Job JSON must be a list of objects.")
        return data
    if not args.pdf or not args.pages:
        raise ValueError("Provide either --jobs or both PDF and --pages.")
    return [
        {
            "pdf": args.pdf,
            "pages": args.pages,
            "output_dir": args.output_dir,
            "prefix": args.prefix or Path(args.pdf).stem,
        }
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", nargs="?", help="PDF file to render.")
    parser.add_argument("--pages", help="Pages to render, such as 1,3,5-7.")
    parser.add_argument("--output-dir", default="figures", help="Directory for rendered PNG files.")
    parser.add_argument("--prefix", help="Output filename prefix.")
    parser.add_argument("--dpi", type=int, default=200, help="Render resolution.")
    parser.add_argument("--jobs", help="UTF-8 JSON list with pdf, pages, output_dir, prefix, and optional dpi.")
    args = parser.parse_args(argv)

    gs = find_ghostscript()
    outputs: list[Path] = []
    for job in load_jobs(args):
        pdf = Path(str(job["pdf"]))
        pages = parse_pages(job["pages"])  # type: ignore[arg-type]
        output_dir = Path(str(job.get("output_dir", args.output_dir)))
        prefix = str(job.get("prefix") or pdf.stem)
        dpi = int(job.get("dpi", args.dpi))
        if gs:
            outputs.extend(render_job(gs, pdf, pages, output_dir, prefix, dpi))
        else:
            outputs.extend(render_job_with_pymupdf(pdf, pages, output_dir, prefix, dpi))
    for out in outputs:
        print(out.resolve())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
