#!/usr/bin/env python3
"""Prepare meeting recording bundles for KRISS trip-report drafting.

The script inventories audio files inside folders or ZIP archives, optionally
extracts/copies them into a workspace, and links same-stem transcript files
when transcripts are supplied. It does not transcribe audio by itself.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


AUDIO_EXTS = {".m4a", ".mp3", ".wav", ".aac", ".flac", ".ogg"}
TRANSCRIPT_EXTS = {".txt", ".md", ".srt", ".vtt"}


@dataclass
class Recording:
    source: str
    filename: str
    size_bytes: int
    date_guess: str | None = None
    session_guess: str | None = None
    workspace_audio: str | None = None
    transcript: str | None = None
    transcript_source: str | None = None
    warnings: list[str] | None = None


@dataclass
class Transcript:
    source: str
    filename: str
    size_bytes: int
    workspace_path: str | None = None


def iter_inputs(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_dir():
            yield from sorted(p for p in path.rglob("*") if p.is_file())
        elif path.is_file():
            yield path


def safe_member_name(raw: str) -> Path | None:
    candidate = Path(raw)
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        return None
    return candidate


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    for idx in range(2, 10000):
        candidate = path.with_name(f"{stem}-{idx}{suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Could not allocate unique output path for {path}")


def normalize_stem(name: str) -> str:
    stem = Path(name).stem.lower()
    stem = re.sub(r"[^0-9a-z가-힣]+", "", stem)
    return stem


def guess_date(name: str) -> str | None:
    match = re.search(r"(20\d{2})(\d{2})(\d{2})", name)
    if not match:
        return None
    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"


def guess_session(name: str) -> str | None:
    stem = Path(name).stem
    date = re.search(r"20\d{6}", stem)
    if date:
        stem = stem.replace(date.group(0), " ")
    tokens = [token for token in re.split(r"[_\-\s]+", stem) if token]
    numeric = [token for token in tokens if re.fullmatch(r"\d+", token)]
    if numeric:
        return ".".join(numeric)
    return None


def collect_from_zip(path: Path, output_dir: Path, extract: bool) -> tuple[list[Recording], list[Transcript]]:
    recordings: list[Recording] = []
    transcripts: list[Transcript] = []
    with zipfile.ZipFile(path) as zf:
        for info in sorted(zf.infolist(), key=lambda item: item.filename):
            if info.is_dir():
                continue
            member = safe_member_name(info.filename)
            if member is None:
                continue
            suffix = member.suffix.lower()
            workspace_path: Path | None = None
            if suffix in AUDIO_EXTS and extract:
                workspace_path = unique_path(output_dir / "audio" / member.name)
                workspace_path.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as src, workspace_path.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
            elif suffix in TRANSCRIPT_EXTS and extract:
                workspace_path = unique_path(output_dir / "transcripts" / member.name)
                workspace_path.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as src, workspace_path.open("wb") as dst:
                    shutil.copyfileobj(src, dst)

            source = f"{path}::{info.filename}"
            if suffix in AUDIO_EXTS:
                recordings.append(
                    Recording(
                        source=source,
                        filename=member.name,
                        size_bytes=info.file_size,
                        date_guess=guess_date(member.name),
                        session_guess=guess_session(member.name),
                        workspace_audio=str(workspace_path) if workspace_path else None,
                    )
                )
            elif suffix in TRANSCRIPT_EXTS:
                transcripts.append(
                    Transcript(
                        source=source,
                        filename=member.name,
                        size_bytes=info.file_size,
                        workspace_path=str(workspace_path) if workspace_path else None,
                    )
                )
    return recordings, transcripts


def collect_file(path: Path, output_dir: Path, extract: bool) -> tuple[list[Recording], list[Transcript]]:
    suffix = path.suffix.lower()
    if suffix == ".zip":
        return collect_from_zip(path, output_dir, extract)
    workspace_path: Path | None = None
    if extract and suffix in AUDIO_EXTS:
        workspace_path = unique_path(output_dir / "audio" / path.name)
        workspace_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, workspace_path)
    elif extract and suffix in TRANSCRIPT_EXTS:
        workspace_path = unique_path(output_dir / "transcripts" / path.name)
        workspace_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, workspace_path)

    if suffix in AUDIO_EXTS:
        return [
            Recording(
                source=str(path),
                filename=path.name,
                size_bytes=path.stat().st_size,
                date_guess=guess_date(path.name),
                session_guess=guess_session(path.name),
                workspace_audio=str(workspace_path) if workspace_path else str(path),
            )
        ], []
    if suffix in TRANSCRIPT_EXTS:
        return [], [
            Transcript(
                source=str(path),
                filename=path.name,
                size_bytes=path.stat().st_size,
                workspace_path=str(workspace_path) if workspace_path else str(path),
            )
        ]
    return [], []


def match_transcripts(recordings: list[Recording], transcripts: list[Transcript]) -> None:
    transcript_by_stem = {normalize_stem(item.filename): item for item in transcripts}
    for recording in recordings:
        stem = normalize_stem(recording.filename)
        transcript = transcript_by_stem.get(stem)
        if transcript is None:
            for candidate_stem, candidate in transcript_by_stem.items():
                if candidate_stem and (candidate_stem.startswith(stem) or stem.startswith(candidate_stem)):
                    transcript = candidate
                    break
        if transcript is None:
            recording.warnings = ["No matching transcript found; do not use this recording for report facts until transcribed."]
        else:
            recording.transcript = transcript.workspace_path or transcript.source
            recording.transcript_source = transcript.source


def write_markdown(recordings: list[Recording], transcripts: list[Transcript], output: Path, extracted: bool) -> None:
    lines = [
        "# Meeting Recording Index",
        "",
        "Use recordings as report evidence only after transcription. Do not draft technical conclusions directly from untranscribed audio.",
        "",
        f"Extraction performed: `{str(extracted).lower()}`",
        "",
        "## Recordings",
        "",
        "| Date guess | Session guess | Size bytes | Recording | Transcript | Warnings |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for item in recordings:
        warnings = "; ".join(item.warnings or [])
        recording_path = item.workspace_audio or item.source
        transcript = item.transcript or ""
        lines.append(
            f"| {item.date_guess or ''} | {item.session_guess or ''} | {item.size_bytes} | `{recording_path}` | `{transcript}` | {warnings} |"
        )

    lines.extend(["", "## Transcript Files", "", "| Size bytes | Transcript | Source |", "| ---: | --- | --- |"])
    for item in transcripts:
        lines.append(f"| {item.size_bytes} | `{item.workspace_path or ''}` | `{item.source}` |")

    lines.extend(
        [
            "",
            "## Drafting Rules",
            "",
            "- Use transcript text only after checking it against agenda order and obvious transcription errors.",
            "- Map transcript excerpts to agenda items by date, session, slide title, speaker, or explicit agenda wording.",
            "- If a recording has no transcript, list it in the dossier only; do not use it as a factual basis in the report body.",
            "- If transcript and written meeting material conflict, prefer official agenda/minutes/presentation files unless the transcript clearly records a later decision.",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", help="Audio files, transcript files, folders, or ZIP archives.")
    parser.add_argument("--output-dir", default="recordings-work", help="Workspace for extracted/copied recordings and transcripts.")
    parser.add_argument("--output-md", default=None, help="Markdown recording index path.")
    parser.add_argument("--output-json", default=None, help="JSON recording manifest path.")
    parser.add_argument("--extract", action="store_true", help="Extract/copy audio and transcript files into the workspace.")
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir).resolve()
    recordings: list[Recording] = []
    transcripts: list[Transcript] = []
    for path in iter_inputs(Path(value).expanduser().resolve() for value in args.inputs):
        found_recordings, found_transcripts = collect_file(path, output_dir, args.extract)
        recordings.extend(found_recordings)
        transcripts.extend(found_transcripts)

    match_transcripts(recordings, transcripts)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_md = Path(args.output_md).resolve() if args.output_md else output_dir / "recording-index.md"
    output_json = Path(args.output_json).resolve() if args.output_json else output_dir / "recording-manifest.json"
    write_markdown(recordings, transcripts, output_md, args.extract)
    output_json.write_text(
        json.dumps(
            {
                "recordings": [asdict(item) for item in recordings],
                "transcripts": [asdict(item) for item in transcripts],
                "extracted": args.extract,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {output_md}")
    print(f"Wrote {output_json}")
    print(f"Recordings: {len(recordings)}")
    print(f"Transcripts: {len(transcripts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
