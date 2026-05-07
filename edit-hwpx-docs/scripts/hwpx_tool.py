#!/usr/bin/env python3
"""Small HWPX utilities for extraction and conservative text edits.

The script intentionally uses only the Python standard library so it can run
inside a normal Codex workspace without project-specific dependencies.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


SECTION_RE = re.compile(r"^Contents/section(\d+)\.xml$", re.IGNORECASE)
TEXT_BREAK_TAGS = {"lineBreak", "br"}
TEXT_TAB_TAGS = {"tab"}
REQUIRED_ENTRIES = ("mimetype", "Contents/content.hpf", "Contents/header.xml")


class HwpxError(RuntimeError):
    pass


def local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def namespace_uri(tag: str) -> Optional[str]:
    if tag.startswith("{") and "}" in tag:
        return tag[1:].split("}", 1)[0]
    return None


def qname(ns: Optional[str], name: str) -> str:
    return f"{{{ns}}}{name}" if ns else name


def collect_namespaces(data: bytes) -> List[Tuple[str, str]]:
    namespaces: List[Tuple[str, str]] = []
    try:
        for _, ns in ET.iterparse(io.BytesIO(data), events=("start-ns",)):
            if ns not in namespaces:
                namespaces.append(ns)
    except ET.ParseError:
        return namespaces
    return namespaces


def register_namespaces(namespaces: Iterable[Tuple[str, str]]) -> None:
    for prefix, uri in namespaces:
        if prefix.lower().startswith("xml"):
            continue
        try:
            ET.register_namespace(prefix, uri)
        except ValueError:
            continue


def parse_xml(data: bytes) -> ET.Element:
    register_namespaces(collect_namespaces(data))
    return ET.fromstring(data)


def serialize_xml(root: ET.Element) -> bytes:
    return ET.tostring(
        root,
        encoding="utf-8",
        xml_declaration=True,
        short_empty_elements=False,
    )


def print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def require_hwpx(path: Path) -> None:
    if not path.exists():
        raise HwpxError(f"File not found: {path}")
    if not path.is_file():
        raise HwpxError(f"Not a file: {path}")
    if path.suffix.lower() != ".hwpx":
        raise HwpxError(f"Expected a .hwpx file: {path}")


def section_sort_key(path: str) -> Tuple[int, str]:
    match = SECTION_RE.match(path)
    if match:
        return (int(match.group(1)), path)
    return (10**9, path)


def section_paths(zf: zipfile.ZipFile) -> List[str]:
    paths = [name for name in zf.namelist() if SECTION_RE.match(name)]
    return sorted(paths, key=section_sort_key)


def choose_section(paths: Sequence[str], selector: Optional[str]) -> str:
    if not paths:
        raise HwpxError("No Contents/section*.xml files found")
    if selector in (None, "", "last"):
        return paths[-1]
    if selector == "first":
        return paths[0]
    if selector and selector.isdigit():
        target = f"Contents/section{selector}.xml"
        if target in paths:
            return target
    normalized = selector.replace("\\", "/") if selector else ""
    if normalized in paths:
        return normalized
    raise HwpxError(f"Unknown section selector {selector!r}; available: {', '.join(paths)}")


def paragraph_text(paragraph: ET.Element) -> str:
    pieces: List[str] = []
    for elem in paragraph.iter():
        name = local_name(elem.tag)
        if name == "t":
            pieces.append(elem.text or "")
        elif name in TEXT_BREAK_TAGS:
            pieces.append("\n")
        elif name in TEXT_TAB_TAGS:
            pieces.append("\t")
    return "".join(pieces)


def extract_section_text(data: bytes) -> List[str]:
    root = parse_xml(data)
    lines: List[str] = []
    for elem in root.iter():
        if local_name(elem.tag) == "p":
            lines.append(paragraph_text(elem))
    return lines


def validate_section_layout_refs(section: str, root: ET.Element) -> List[str]:
    errors: List[str] = []
    paragraphs = [elem for elem in root.iter() if local_name(elem.tag) == "p"]
    for index, paragraph in enumerate(paragraphs, start=1):
        text = paragraph_text(paragraph)
        text_len = len(text)
        paragraph_id = paragraph.get("id", "")

        char_count = paragraph.get("charCnt")
        if char_count and char_count.isdigit() and int(char_count) != text_len:
            errors.append(
                f"{section} paragraph {index} id={paragraph_id}: charCnt={char_count} "
                f"but text length is {text_len}"
            )

        for elem in paragraph.iter():
            if local_name(elem.tag) != "lineseg":
                continue
            text_pos = elem.get("textpos", "0")
            if text_pos.lstrip("-").isdigit() and int(text_pos) > text_len:
                snippet = text[:80].replace("\n", " ")
                errors.append(
                    f"{section} paragraph {index} id={paragraph_id}: hp:lineseg textpos={text_pos} "
                    f"exceeds text length {text_len}; HWP2018 may reject the file. "
                    f"Text starts: {snippet!r}"
                )
    return errors


def repair_section_layout_refs(root: ET.Element) -> int:
    fixes = 0
    for paragraph in [elem for elem in root.iter() if local_name(elem.tag) == "p"]:
        text_len = len(paragraph_text(paragraph))

        char_count = paragraph.get("charCnt")
        if char_count and char_count.isdigit() and int(char_count) != text_len:
            paragraph.set("charCnt", str(text_len))
            fixes += 1

        for elem in paragraph.iter():
            if local_name(elem.tag) != "lineseg":
                continue
            text_pos = elem.get("textpos", "0")
            if text_pos.lstrip("-").isdigit() and int(text_pos) > text_len:
                elem.set("textpos", str(text_len))
                fixes += 1
    return fixes


def extract_text_from_updates(
    zf: zipfile.ZipFile,
    updates: Optional[Dict[str, bytes]] = None,
) -> str:
    updates = updates or {}
    lines: List[str] = []
    first_section = True
    for path in section_paths(zf):
        data = updates.get(path)
        if data is None:
            data = zf.read(path)
        section_lines = extract_section_text(data)
        if not first_section and section_lines:
            lines.append("")
        lines.extend(section_lines)
        first_section = False
    return "\n".join(lines).rstrip() + "\n" if lines else ""


def clone_info(info: zipfile.ZipInfo, compress_type: Optional[int] = None) -> zipfile.ZipInfo:
    cloned = zipfile.ZipInfo(info.filename, info.date_time)
    cloned.comment = info.comment
    cloned.extra = info.extra
    cloned.internal_attr = info.internal_attr
    cloned.external_attr = info.external_attr
    cloned.create_system = info.create_system
    cloned.compress_type = info.compress_type if compress_type is None else compress_type
    return cloned


def write_zip_with_updates(
    src: Path,
    dest: Path,
    updates: Dict[str, bytes],
    update_preview: bool = True,
) -> None:
    if src.resolve() == dest.resolve():
        raise HwpxError("Refusing in-place writes; choose a different output path")

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_name = tempfile.mkstemp(suffix=".hwpx", dir=str(dest.parent))
    os.close(tmp_fd)
    tmp_path = Path(tmp_name)
    try:
        with zipfile.ZipFile(src, "r") as zin:
            all_updates = dict(updates)
            if update_preview and "Preview/PrvText.txt" in zin.namelist():
                all_updates["Preview/PrvText.txt"] = extract_text_from_updates(
                    zin,
                    all_updates,
                ).encode("utf-8")

            with zipfile.ZipFile(tmp_path, "w") as zout:
                names = zin.namelist()
                if "mimetype" in names:
                    info = zin.getinfo("mimetype")
                    data = all_updates.get("mimetype", zin.read("mimetype"))
                    zout.writestr(clone_info(info, zipfile.ZIP_STORED), data)

                for info in zin.infolist():
                    if info.filename == "mimetype":
                        continue
                    data = all_updates.get(info.filename)
                    if data is None:
                        data = b"" if info.is_dir() else zin.read(info.filename)
                    zout.writestr(clone_info(info), data)

        shutil.move(str(tmp_path), str(dest))
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def command_inspect(args: argparse.Namespace) -> int:
    path = Path(args.input)
    require_hwpx(path)
    with zipfile.ZipFile(path, "r") as zf:
        names = zf.namelist()
        encrypted = [
            info.filename
            for info in zf.infolist()
            if info.flag_bits & 0x1
        ]
        result = {
            "path": str(path),
            "entries": len(names),
            "mimetype": zf.read("mimetype").decode("utf-8", "replace") if "mimetype" in names else None,
            "required_present": {entry: entry in names for entry in REQUIRED_ENTRIES},
            "sections": section_paths(zf),
            "has_preview_text": "Preview/PrvText.txt" in names,
            "encrypted_entries": encrypted,
        }
    print_json(result)
    return 0


def command_validate(args: argparse.Namespace) -> int:
    path = Path(args.input)
    require_hwpx(path)
    errors: List[str] = []
    details: Dict[str, object] = {"path": str(path)}

    try:
        with zipfile.ZipFile(path, "r") as zf:
            names = zf.namelist()
            missing = [entry for entry in REQUIRED_ENTRIES if entry not in names]
            if missing:
                errors.append(f"Missing required entries: {', '.join(missing)}")

            sections = section_paths(zf)
            details["sections"] = sections
            if not sections:
                errors.append("No Contents/section*.xml files found")

            if names and names[0] != "mimetype":
                errors.append("mimetype is not the first ZIP entry")
            if "mimetype" in names:
                info = zf.getinfo("mimetype")
                mimetype = zf.read("mimetype").decode("utf-8", "replace").strip()
                details["mimetype"] = mimetype
                if info.compress_type != zipfile.ZIP_STORED:
                    errors.append("mimetype is not stored/uncompressed")

            for entry in ("Contents/content.hpf", "Contents/header.xml", *sections):
                if entry in names:
                    try:
                        root = parse_xml(zf.read(entry))
                        if entry in sections:
                            errors.extend(validate_section_layout_refs(entry, root))
                    except ET.ParseError as exc:
                        errors.append(f"XML parse error in {entry}: {exc}")

    except zipfile.BadZipFile as exc:
        errors.append(f"Invalid ZIP/HWPX container: {exc}")

    details["ok"] = not errors
    details["errors"] = errors
    print_json(details)
    return 0 if not errors else 1


def command_extract(args: argparse.Namespace) -> int:
    path = Path(args.input)
    require_hwpx(path)
    with zipfile.ZipFile(path, "r") as zf:
        text = extract_text_from_updates(zf)

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


def replace_in_section(data: bytes, old: str, new: str) -> Tuple[bytes, int]:
    root = parse_xml(data)
    count = 0
    for elem in root.iter():
        if local_name(elem.tag) == "t" and elem.text and old in elem.text:
            occurrences = elem.text.count(old)
            elem.text = elem.text.replace(old, new)
            count += occurrences
    if count:
        repair_section_layout_refs(root)
    return serialize_xml(root), count


def command_replace(args: argparse.Namespace) -> int:
    src = Path(args.input)
    dest = Path(args.output)
    require_hwpx(src)
    if args.old == "":
        raise HwpxError("--old must not be empty")

    updates: Dict[str, bytes] = {}
    total = 0
    with zipfile.ZipFile(src, "r") as zf:
        paths = section_paths(zf)
        target_paths = [choose_section(paths, args.section)] if args.section else paths
        for path in target_paths:
            updated, count = replace_in_section(zf.read(path), args.old, args.new)
            if count:
                updates[path] = updated
                total += count

    write_zip_with_updates(src, dest, updates, update_preview=not args.no_preview)
    print_json({"output": str(dest), "replacements": total, "updated_sections": sorted(updates)})
    return 0 if total else 2


def max_paragraph_id(paragraphs: Sequence[ET.Element]) -> Optional[int]:
    values: List[int] = []
    for paragraph in paragraphs:
        value = paragraph.get("id")
        if value and value.isdigit():
            values.append(int(value))
    return max(values) if values else None


def first_child_by_local_name(root: ET.Element, name: str) -> Optional[ET.Element]:
    for elem in root.iter():
        if local_name(elem.tag) == name:
            return elem
    return None


def append_paragraphs_to_section(data: bytes, paragraphs_to_add: Sequence[str]) -> bytes:
    root = parse_xml(data)
    paragraphs = [elem for elem in root.iter() if local_name(elem.tag) == "p"]
    if not paragraphs:
        raise HwpxError("Target section has no hp:p paragraphs to use as a template")

    parent_map = {child: parent for parent in root.iter() for child in list(parent)}
    template_p = paragraphs[-1]
    container = parent_map.get(template_p, root)
    hp_ns = namespace_uri(template_p.tag)
    max_id = max_paragraph_id(paragraphs)

    template_run = first_child_by_local_name(template_p, "run")
    run_attrs: Dict[str, str] = {}
    if template_run is not None:
        for key in ("charPrIDRef", "charTcId"):
            if key in template_run.attrib:
                run_attrs[key] = template_run.attrib[key]

    for offset, text in enumerate(paragraphs_to_add, start=1):
        p_attrs = dict(template_p.attrib)
        if max_id is not None:
            p_attrs["id"] = str(max_id + offset)
        else:
            p_attrs.pop("id", None)
        if "charCnt" in p_attrs:
            p_attrs["charCnt"] = str(len(text))

        paragraph = ET.Element(qname(hp_ns, "p"), p_attrs)
        run = ET.SubElement(paragraph, qname(hp_ns, "run"), run_attrs)
        t = ET.SubElement(run, qname(hp_ns, "t"))
        t.text = text
        container.append(paragraph)

    return serialize_xml(root)


def read_append_text(args: argparse.Namespace) -> List[str]:
    if args.text is None and args.text_file is None:
        raise HwpxError("Provide --text or --text-file")
    if args.text is not None and args.text_file is not None:
        raise HwpxError("Use only one of --text or --text-file")
    if args.text_file:
        raw = Path(args.text_file).read_text(encoding="utf-8")
    else:
        raw = args.text

    lines = raw.splitlines()
    if not lines and raw:
        lines = [raw]
    if not lines:
        raise HwpxError("No text to append")
    return lines


def command_append(args: argparse.Namespace) -> int:
    src = Path(args.input)
    dest = Path(args.output)
    require_hwpx(src)
    additions = read_append_text(args)

    with zipfile.ZipFile(src, "r") as zf:
        paths = section_paths(zf)
        target = choose_section(paths, args.section)
        updated = append_paragraphs_to_section(zf.read(target), additions)

    write_zip_with_updates(src, dest, {target: updated}, update_preview=not args.no_preview)
    print_json({"output": str(dest), "section": target, "paragraphs_added": len(additions)})
    return 0


def safe_extract(zf: zipfile.ZipFile, output_dir: Path) -> None:
    base = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    for info in zf.infolist():
        target = (output_dir / info.filename).resolve()
        try:
            target.relative_to(base)
        except ValueError as exc:
            raise HwpxError(f"Refusing unsafe ZIP path: {info.filename}") from exc
        if info.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(info, "r") as source, target.open("wb") as dest:
            shutil.copyfileobj(source, dest)


def command_unpack(args: argparse.Namespace) -> int:
    src = Path(args.input)
    output_dir = Path(args.output_dir)
    require_hwpx(src)
    if output_dir.exists() and any(output_dir.iterdir()) and not args.force:
        raise HwpxError(f"Output directory is not empty: {output_dir}; use --force")
    with zipfile.ZipFile(src, "r") as zf:
        safe_extract(zf, output_dir)
    print_json({"output_dir": str(output_dir), "entries": len(list(output_dir.rglob('*')))})
    return 0


def command_pack(args: argparse.Namespace) -> int:
    input_dir = Path(args.input_dir)
    output = Path(args.output)
    if not input_dir.is_dir():
        raise HwpxError(f"Not a directory: {input_dir}")
    if output.exists() and not args.force:
        raise HwpxError(f"Output exists: {output}; use --force")

    output.parent.mkdir(parents=True, exist_ok=True)
    files = [path for path in input_dir.rglob("*") if path.is_file()]

    def rel(path: Path) -> str:
        return path.relative_to(input_dir).as_posix()

    with zipfile.ZipFile(output, "w") as zf:
        mimetype = input_dir / "mimetype"
        if mimetype.exists():
            zf.write(mimetype, "mimetype", compress_type=zipfile.ZIP_STORED)
        for path in sorted(files, key=rel):
            name = rel(path)
            if name == "mimetype":
                continue
            zf.write(path, name, compress_type=zipfile.ZIP_DEFLATED)

    print_json({"output": str(output), "files": len(files)})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read and conservatively edit HWPX files.")
    sub = parser.add_subparsers(dest="command", required=True)

    inspect_p = sub.add_parser("inspect", help="Print package structure as JSON.")
    inspect_p.add_argument("input")
    inspect_p.set_defaults(func=command_inspect)

    validate_p = sub.add_parser("validate", help="Validate package basics and section XML.")
    validate_p.add_argument("input")
    validate_p.set_defaults(func=command_validate)

    extract_p = sub.add_parser("extract", help="Extract plain text from section XML.")
    extract_p.add_argument("input")
    extract_p.add_argument("--output", "-o")
    extract_p.set_defaults(func=command_extract)

    replace_p = sub.add_parser("replace", help="Replace text within hp:t nodes.")
    replace_p.add_argument("input")
    replace_p.add_argument("output")
    replace_p.add_argument("--old", required=True)
    replace_p.add_argument("--new", required=True)
    replace_p.add_argument("--section", help="first, last, numeric index, or Contents/sectionN.xml")
    replace_p.add_argument("--no-preview", action="store_true", help="Do not update Preview/PrvText.txt")
    replace_p.set_defaults(func=command_replace)

    append_p = sub.add_parser("append", help="Append one paragraph per input line.")
    append_p.add_argument("input")
    append_p.add_argument("output")
    append_p.add_argument("--text")
    append_p.add_argument("--text-file")
    append_p.add_argument("--section", default="last", help="first, last, numeric index, or Contents/sectionN.xml")
    append_p.add_argument("--no-preview", action="store_true", help="Do not update Preview/PrvText.txt")
    append_p.set_defaults(func=command_append)

    unpack_p = sub.add_parser("unpack", help="Safely extract an HWPX package.")
    unpack_p.add_argument("input")
    unpack_p.add_argument("output_dir")
    unpack_p.add_argument("--force", action="store_true", help="Allow extracting into a non-empty directory")
    unpack_p.set_defaults(func=command_unpack)

    pack_p = sub.add_parser("pack", help="Create an HWPX package from an unpacked directory.")
    pack_p.add_argument("input_dir")
    pack_p.add_argument("output")
    pack_p.add_argument("--force", action="store_true", help="Overwrite an existing output file")
    pack_p.set_defaults(func=command_pack)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except HwpxError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except zipfile.BadZipFile as exc:
        print(f"error: invalid ZIP/HWPX file: {exc}", file=sys.stderr)
        return 1
    except ET.ParseError as exc:
        print(f"error: XML parse error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
