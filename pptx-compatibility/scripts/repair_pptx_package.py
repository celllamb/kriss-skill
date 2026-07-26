"""Repair .pptx OPC packages without modifying the original file.

Level 1 minimal repair removes safe dangling package references, normalizes
PowerPoint-strict slide XML details, and repackages the archive. Level 2
structural repair reconnects the PowerPoint presentation graph where possible.

Key principle: Passing ZIP/XML validation does not guarantee Microsoft
PowerPoint compatibility. PowerPoint is strict about the presentation
relationship graph, especially slideMaster and slideLayout relationships. It
is also strict about per-slide shape ID uniqueness and DrawingML paragraph end
run properties. If minimal XML/package repair is not enough, rebuild a clean
presentation graph.
"""

from __future__ import annotations

import json
import posixpath
import re
import tempfile
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

try:  # pragma: no cover - exercised by standalone script use
    from inspect_pptx import (
        CONTENT_TYPES,
        CT_NS,
        OFFICE_REL,
        A_NS,
        P_NS,
        R_NS,
        REL_NS,
        DiagnosticReport,
        expected_content_type_for_part,
        inspect_pptx,
        is_optional_relationship,
        relationship_source_part,
        rels_path_for_source,
        resolve_relationship_target,
    )
except ImportError:  # pragma: no cover
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from inspect_pptx import (
        CONTENT_TYPES,
        CT_NS,
        OFFICE_REL,
        A_NS,
        P_NS,
        R_NS,
        REL_NS,
        DiagnosticReport,
        expected_content_type_for_part,
        inspect_pptx,
        is_optional_relationship,
        relationship_source_part,
        rels_path_for_source,
        resolve_relationship_target,
    )

ET.register_namespace("", REL_NS)
ET.register_namespace("p", P_NS)
ET.register_namespace("r", R_NS)
ET.register_namespace("a", A_NS)

SLIDE_LAYOUT_REL = f"{OFFICE_REL}/slideLayout"
SLIDE_MASTER_REL = f"{OFFICE_REL}/slideMaster"


@dataclass
class RepairChange:
    """A single repair action."""

    level: str
    action: str
    part: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class RepairResult:
    """Result from a repair operation."""

    input_path: str
    output_path: str
    level: str
    changes: list[RepairChange] = field(default_factory=list)
    diagnostic_before: dict[str, Any] | None = None
    diagnostic_after: dict[str, Any] | None = None

    def add_change(
        self,
        level: str,
        action: str,
        part: str,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.changes.append(
            RepairChange(level=level, action=action, part=part, message=message, details=details or {})
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def minimal_repair(
    input_path: str | Path,
    output_path: str | Path,
    diagnostic: DiagnosticReport | None = None,
) -> RepairResult:
    """Perform Level 1 minimal package repair."""

    source = Path(input_path)
    output = Path(output_path)
    diagnostic = diagnostic or inspect_pptx(source)
    result = RepairResult(
        input_path=str(source),
        output_path=str(output),
        level="minimal",
        diagnostic_before=diagnostic.to_dict(),
    )

    parts = read_package(source)
    changed = False
    changed |= _remove_safe_dangling_content_type_overrides(parts, diagnostic, result)
    changed |= _remove_safe_dangling_optional_relationships(parts, diagnostic, result)
    changed |= _repair_duplicate_shape_ids(parts, result)
    changed |= _repair_missing_end_para_rpr(parts, result)

    if not changed:
        result.add_change(
            "minimal",
            "repackage",
            "(package)",
            "No safe minimal XML removals were needed; wrote a clean ZIP package.",
        )

    write_package(parts, output)
    result.diagnostic_after = inspect_pptx(output).to_dict()
    return result


def structural_repair(
    input_path: str | Path,
    output_path: str | Path,
    diagnostic: DiagnosticReport | None = None,
) -> RepairResult:
    """Perform Level 2 structural presentation graph repair."""

    source = Path(input_path)
    output = Path(output_path)
    diagnostic = diagnostic or inspect_pptx(source)

    with tempfile.TemporaryDirectory(prefix="pptx-structural-") as temp_dir:
        minimal_path = Path(temp_dir) / "minimal.pptx"
        minimal = minimal_repair(source, minimal_path, diagnostic)
        parts = read_package(minimal_path)

        result = RepairResult(
            input_path=str(source),
            output_path=str(output),
            level="structural",
            changes=list(minimal.changes),
            diagnostic_before=diagnostic.to_dict(),
        )

        valid_masters = _valid_parts(parts, r"^ppt/slideMasters/slideMaster\d+\.xml$")
        valid_layouts = _valid_parts(parts, r"^ppt/slideLayouts/slideLayout\d+\.xml$")
        slide_parts = _slide_parts_in_package(parts)

        if valid_masters:
            master_part = valid_masters[0]
            for layout_part in valid_layouts:
                _ensure_relationship(
                    parts,
                    layout_part,
                    SLIDE_MASTER_REL,
                    master_part,
                    result,
                    "structural",
                    "ensure_layout_master",
                )
            master_rid = _ensure_relationship(
                parts,
                "ppt/presentation.xml",
                SLIDE_MASTER_REL,
                master_part,
                result,
                "structural",
                "ensure_presentation_master",
            )
            _ensure_presentation_master_reference(parts, master_rid, result)
        else:
            result.add_change(
                "structural",
                "no_valid_master",
                "(package)",
                "No valid slide master XML part was available for structural reconnection.",
            )

        if valid_layouts:
            layout_part = valid_layouts[0]
            for slide_part in slide_parts:
                _ensure_relationship(
                    parts,
                    slide_part,
                    SLIDE_LAYOUT_REL,
                    layout_part,
                    result,
                    "structural",
                    "ensure_slide_layout",
                )
        else:
            result.add_change(
                "structural",
                "no_valid_layout",
                "(package)",
                "No valid slide layout XML part was available for structural reconnection.",
            )

        _ensure_content_type_defaults_and_overrides(parts, result)
        write_package(parts, output)
        result.diagnostic_after = inspect_pptx(output).to_dict()
        return result


def read_package(path: str | Path) -> dict[str, bytes]:
    """Read a ZIP package into memory."""

    with zipfile.ZipFile(path, "r") as zf:
        return {
            name.replace("\\", "/").lstrip("/"): zf.read(name)
            for name in zf.namelist()
            if not name.endswith("/")
        }


def write_package(parts: dict[str, bytes], output_path: str | Path) -> None:
    """Write package parts as a clean ZIP archive."""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    preferred = ["[Content_Types].xml", "_rels/.rels", "ppt/presentation.xml", "ppt/_rels/presentation.xml.rels"]
    ordered = [part for part in preferred if part in parts]
    ordered.extend(part for part in sorted(parts) if part not in set(ordered))
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for part in ordered:
            zf.writestr(part, parts[part])


def _remove_safe_dangling_content_type_overrides(
    parts: dict[str, bytes],
    diagnostic: DiagnosticReport,
    result: RepairResult,
) -> bool:
    content_types = parts.get("[Content_Types].xml")
    if not content_types:
        return False

    root = ET.fromstring(content_types)
    missing_required_targets = {
        rel.resolved_target
        for rel in diagnostic.relationships
        if rel.resolved_target and rel.exists is False and not is_optional_relationship(rel.relationship_type)
    }

    changed = False
    for override in list(root.findall(f"{{{CT_NS}}}Override")):
        part_name = override.get("PartName")
        if not part_name:
            continue
        part = part_name.lstrip("/")
        if part in parts:
            continue
        if part in missing_required_targets:
            continue
        root.remove(override)
        changed = True
        result.add_change(
            "minimal",
            "remove_dangling_content_type_override",
            "[Content_Types].xml",
            f"Removed Override for missing unreferenced part {part_name}.",
            details={"part_name": part_name},
        )

    if changed:
        parts["[Content_Types].xml"] = _xml_bytes(root)
    return changed


def _remove_safe_dangling_optional_relationships(
    parts: dict[str, bytes],
    diagnostic: DiagnosticReport,
    result: RepairResult,
) -> bool:
    removable = {
        (rel.rels_file, rel.relationship_id)
        for rel in diagnostic.relationships
        if rel.relationship_id
        and rel.exists is False
        and not rel.malformed
        and is_optional_relationship(rel.relationship_type)
    }
    if not removable:
        return False

    changed_any = False
    for rels_file in sorted({key[0] for key in removable}):
        root = ET.fromstring(parts[rels_file])
        changed = False
        for rel in list(_relationship_elements(root)):
            rid = rel.get("Id")
            if (rels_file, rid or "") not in removable:
                continue
            root.remove(rel)
            changed = True
            changed_any = True
            result.add_change(
                "minimal",
                "remove_optional_dangling_relationship",
                rels_file,
                f"Removed optional dangling relationship {rid}.",
                details={"relationship_id": rid, "relationship_type": rel.get("Type"), "target": rel.get("Target")},
            )
        if changed:
            parts[rels_file] = _xml_bytes(root)
    return changed_any


def _repair_duplicate_shape_ids(parts: dict[str, bytes], result: RepairResult) -> bool:
    changed_any = False
    for part in _slide_parts_in_package(parts):
        root = ET.fromstring(parts[part])
        cnvprs = root.findall(f".//{{{P_NS}}}cNvPr")
        used_ids = {
            int(shape_id)
            for cnvpr in cnvprs
            for shape_id in [cnvpr.get("id")]
            if shape_id and shape_id.isdigit()
        }
        next_id = max(used_ids, default=0) + 1
        seen: set[str] = set()
        changed_part = False
        for cnvpr in cnvprs:
            shape_id = cnvpr.get("id")
            if not shape_id:
                continue
            if shape_id not in seen:
                seen.add(shape_id)
                continue
            while next_id in used_ids:
                next_id += 1
            new_id = str(next_id)
            used_ids.add(next_id)
            next_id += 1
            cnvpr.set("id", new_id)
            changed_part = True
            changed_any = True
            result.add_change(
                "minimal",
                "renumber_duplicate_shape_id",
                part,
                f"Renumbered duplicate shape id {shape_id} to {new_id}.",
                details={"old_id": shape_id, "new_id": new_id, "shape_name": cnvpr.get("name")},
            )
        if changed_part:
            parts[part] = _xml_bytes(root)
    return changed_any


def _repair_missing_end_para_rpr(parts: dict[str, bytes], result: RepairResult) -> bool:
    changed_any = False
    for part in _slide_parts_in_package(parts):
        root = ET.fromstring(parts[part])
        changed_count = 0
        moved_count = 0
        for paragraph in root.findall(f".//{{{A_NS}}}p"):
            children = list(paragraph)
            if children and children[-1].tag == f"{{{A_NS}}}endParaRPr":
                continue

            existing = next((child for child in children if child.tag == f"{{{A_NS}}}endParaRPr"), None)
            if existing is not None:
                paragraph.remove(existing)
                paragraph.append(existing)
                moved_count += 1
            else:
                paragraph.append(_new_end_para_rpr(paragraph))
                changed_count += 1

        if changed_count or moved_count:
            parts[part] = _xml_bytes(root)
            changed_any = True
            if changed_count:
                result.add_change(
                    "minimal",
                    "add_missing_end_para_rpr",
                    part,
                    f"Added a:endParaRPr to {changed_count} paragraph(s).",
                    details={"count": changed_count},
                )
            if moved_count:
                result.add_change(
                    "minimal",
                    "move_end_para_rpr_to_end",
                    part,
                    f"Moved existing a:endParaRPr to the end of {moved_count} paragraph(s).",
                    details={"count": moved_count},
                )
    return changed_any


def _new_end_para_rpr(paragraph: ET.Element) -> ET.Element:
    end_pr = ET.Element(f"{{{A_NS}}}endParaRPr")
    end_pr.set("lang", "en-US")
    end_pr.set("dirty", "0")

    for child in reversed(list(paragraph)):
        if child.tag != f"{{{A_NS}}}r":
            continue
        run_pr = child.find(f"{{{A_NS}}}rPr")
        if run_pr is None:
            break
        for attr in ("sz", "lang"):
            value = run_pr.get(attr)
            if value:
                end_pr.set(attr, value)
        break
    return end_pr


def _relationship_elements(root: ET.Element) -> list[ET.Element]:
    elements = root.findall(f"{{{REL_NS}}}Relationship")
    if elements:
        return elements
    return [child for child in list(root) if child.tag.rsplit("}", 1)[-1] == "Relationship"]


def _valid_parts(parts: dict[str, bytes], pattern: str) -> list[str]:
    valid: list[str] = []
    regex = re.compile(pattern)
    for part in sorted(parts):
        if not regex.match(part):
            continue
        try:
            ET.fromstring(parts[part])
        except ET.ParseError:
            continue
        valid.append(part)
    return valid


def _slide_parts_in_package(parts: dict[str, bytes]) -> list[str]:
    return _valid_parts(parts, r"^ppt/slides/slide\d+\.xml$")


def _ensure_relationship(
    parts: dict[str, bytes],
    source_part: str,
    relationship_type: str,
    target_part: str,
    result: RepairResult,
    level: str,
    action: str,
) -> str:
    rels_file = rels_path_for_source(source_part)
    root = _get_or_create_rels_root(parts, rels_file)
    target = _relative_target(source_part, target_part)

    existing = [rel for rel in _relationship_elements(root) if rel.get("Type") == relationship_type]
    chosen_rid = ""
    changed = False
    for rel in existing:
        current_target = rel.get("Target") or ""
        resolved, malformed = resolve_relationship_target(source_part, current_target)
        rid = rel.get("Id") or _next_rid(root)
        if not rel.get("Id"):
            rel.set("Id", rid)
            changed = True
        if malformed or resolved not in parts:
            rel.set("Target", target)
            changed = True
            result.add_change(
                level,
                action,
                rels_file,
                f"Reconnected {relationship_type.rsplit('/', 1)[-1]} relationship {rid} to {target_part}.",
                details={"relationship_id": rid, "target_part": target_part},
            )
        if not chosen_rid:
            chosen_rid = rid
    if existing:
        if changed:
            parts[rels_file] = _xml_bytes(root)
        return chosen_rid

    rid = _next_rid(root)
    rel = ET.SubElement(root, f"{{{REL_NS}}}Relationship")
    rel.set("Id", rid)
    rel.set("Type", relationship_type)
    rel.set("Target", target)
    parts[rels_file] = _xml_bytes(root)
    result.add_change(
        level,
        action,
        rels_file,
        f"Added {relationship_type.rsplit('/', 1)[-1]} relationship {rid} to {target_part}.",
        details={"relationship_id": rid, "target_part": target_part},
    )
    return rid


def _get_or_create_rels_root(parts: dict[str, bytes], rels_file: str) -> ET.Element:
    if rels_file in parts:
        return ET.fromstring(parts[rels_file])
    parts[rels_file] = _xml_bytes(ET.Element(f"{{{REL_NS}}}Relationships"))
    return ET.fromstring(parts[rels_file])


def _next_rid(root: ET.Element) -> str:
    used = {rel.get("Id") for rel in _relationship_elements(root)}
    index = 1
    while f"rId{index}" in used:
        index += 1
    return f"rId{index}"


def _relative_target(source_part: str, target_part: str) -> str:
    base = posixpath.dirname(source_part)
    if not base:
        return target_part
    return posixpath.relpath(target_part, base).replace("\\", "/")


def _ensure_presentation_master_reference(
    parts: dict[str, bytes],
    master_rid: str,
    result: RepairResult,
) -> None:
    presentation_part = "ppt/presentation.xml"
    if presentation_part not in parts or not master_rid:
        return

    root = ET.fromstring(parts[presentation_part])
    master_list = root.find("p:sldMasterIdLst", {"p": P_NS})
    changed = False
    if master_list is None:
        master_list = ET.Element(f"{{{P_NS}}}sldMasterIdLst")
        root.insert(_presentation_master_insert_index(root), master_list)
        changed = True
    else:
        for child in list(master_list):
            master_list.remove(child)
        changed = True

    master_id = ET.SubElement(master_list, f"{{{P_NS}}}sldMasterId")
    master_id.set("id", "2147483648")
    master_id.set(f"{{{R_NS}}}id", master_rid)
    parts[presentation_part] = _xml_bytes(root)

    if changed:
        result.add_change(
            "structural",
            "rewrite_presentation_master_list",
            presentation_part,
            f"Rewrote slide master id list to reference {master_rid}.",
            details={"relationship_id": master_rid},
        )


def _presentation_master_insert_index(root: ET.Element) -> int:
    preferred_before = {
        f"{{{P_NS}}}notesMasterIdLst",
        f"{{{P_NS}}}handoutMasterIdLst",
        f"{{{P_NS}}}sldIdLst",
        f"{{{P_NS}}}sldSz",
    }
    for index, child in enumerate(list(root)):
        if child.tag in preferred_before:
            return index
    return 0


def _ensure_content_type_defaults_and_overrides(parts: dict[str, bytes], result: RepairResult) -> None:
    root = ET.fromstring(parts["[Content_Types].xml"])
    defaults = {default.get("Extension") for default in root.findall(f"{{{CT_NS}}}Default")}
    for extension, content_type in {
        "rels": "application/vnd.openxmlformats-package.relationships+xml",
        "xml": "application/xml",
    }.items():
        if extension not in defaults:
            default = ET.SubElement(root, f"{{{CT_NS}}}Default")
            default.set("Extension", extension)
            default.set("ContentType", content_type)
            result.add_change(
                "structural",
                "add_content_type_default",
                "[Content_Types].xml",
                f"Added Default for .{extension} files.",
            )

    overrides = {
        (override.get("PartName") or "").lstrip("/"): override
        for override in root.findall(f"{{{CT_NS}}}Override")
    }
    for part in sorted(parts):
        match = expected_content_type_for_part(part)
        if not match or part in overrides:
            continue
        _kind, content_type = match
        override = ET.SubElement(root, f"{{{CT_NS}}}Override")
        override.set("PartName", f"/{part}")
        override.set("ContentType", content_type)
        result.add_change(
            "structural",
            "add_content_type_override",
            "[Content_Types].xml",
            f"Added Override for /{part}.",
            details={"content_type": content_type},
        )

    parts["[Content_Types].xml"] = _xml_bytes(root)


def _xml_bytes(root: ET.Element) -> bytes:
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Repair PPTX package structure.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--level", choices=("minimal", "structural"), default="minimal")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.level == "minimal":
        result = minimal_repair(args.input, args.output)
    else:
        result = structural_repair(args.input, args.output)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"Wrote {result.output_path}")
        for change in result.changes:
            print(f"- {change.level}/{change.action}: {change.message}")
    after = result.diagnostic_after or {}
    critical = after.get("summary", {}).get("critical", 1)
    return 1 if critical else 0


if __name__ == "__main__":
    raise SystemExit(main())
