"""Inspect .pptx OPC/OOXML packages for PowerPoint compatibility issues.

Key principle: Passing ZIP/XML validation does not guarantee Microsoft
PowerPoint compatibility. PowerPoint is strict about the presentation
relationship graph, especially slideMaster and slideLayout relationships. It
is also stricter than LibreOffice and python-pptx about slide XML details such
as p:cNvPr shape ID uniqueness and a:endParaRPr paragraph endings. If minimal
XML/package repair is not enough, rebuild a clean presentation graph.
"""

from __future__ import annotations

import json
import posixpath
import re
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree as ET

REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"

OFFICE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL = "http://schemas.openxmlformats.org/package/2006/relationships"

NS = {"p": P_NS, "r": R_NS, "a": A_NS}

REQUIRED_PARTS = {
    "[Content_Types].xml",
    "_rels/.rels",
    "ppt/presentation.xml",
    "ppt/_rels/presentation.xml.rels",
}

CONTENT_TYPES = {
    "presentation": "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml",
    "slide": "application/vnd.openxmlformats-officedocument.presentationml.slide+xml",
    "slideLayout": "application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml",
    "slideMaster": "application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml",
    "theme": "application/vnd.openxmlformats-officedocument.theme+xml",
    "notesSlide": "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml",
    "notesMaster": "application/vnd.openxmlformats-officedocument.presentationml.notesMaster+xml",
    "chart": "application/vnd.openxmlformats-officedocument.drawingml.chart+xml",
}

IMPORTANT_PART_PATTERNS = (
    (re.compile(r"^ppt/presentation\.xml$"), "presentation", "critical"),
    (re.compile(r"^ppt/slides/slide\d+\.xml$"), "slide", "warning"),
    (re.compile(r"^ppt/slideLayouts/slideLayout\d+\.xml$"), "slideLayout", "warning"),
    (re.compile(r"^ppt/slideMasters/slideMaster\d+\.xml$"), "slideMaster", "warning"),
    (re.compile(r"^ppt/theme/theme\d+\.xml$"), "theme", "warning"),
    (re.compile(r"^ppt/notesSlides/notesSlide\d+\.xml$"), "notesSlide", "warning"),
    (re.compile(r"^ppt/notesMasters/notesMaster\d+\.xml$"), "notesMaster", "warning"),
    (re.compile(r"^ppt/charts/chart\d+\.xml$"), "chart", "warning"),
)

CRITICAL_REL_SUFFIXES = {
    "/officeDocument",
    "/slide",
    "/slideLayout",
    "/slideMaster",
}

OPTIONAL_REL_KEYWORDS = (
    "notesSlide",
    "notesMaster",
    "comments",
    "commentAuthors",
    "chart",
    "image",
    "audio",
    "video",
    "media",
    "oleObject",
    "package",
    "thumbnail",
    "tags",
    "customXml",
    "theme",
)

ET.register_namespace("", REL_NS)
ET.register_namespace("ct", CT_NS)
ET.register_namespace("p", P_NS)
ET.register_namespace("r", R_NS)
ET.register_namespace("a", A_NS)


@dataclass
class DiagnosticIssue:
    """A single finding from PPTX inspection."""

    severity: str
    code: str
    message: str
    category: str = "package"
    part: str | None = None
    rels_file: str | None = None
    relationship_id: str | None = None
    target: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RelationshipRecord:
    """Parsed relationship with OPC target resolution results."""

    rels_file: str
    source_part: str
    relationship_id: str
    relationship_type: str
    target: str
    target_mode: str | None
    resolved_target: str | None
    is_external: bool
    exists: bool | None
    malformed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DiagnosticReport:
    """Structured diagnostics for a PPTX package."""

    input_path: str
    is_zip: bool = False
    zip_test_error: str | None = None
    package_parts: list[str] = field(default_factory=list)
    content_type_overrides: list[str] = field(default_factory=list)
    relationships: list[RelationshipRecord] = field(default_factory=list)
    slide_parts: list[str] = field(default_factory=list)
    slide_count: int = 0
    issues: list[DiagnosticIssue] = field(default_factory=list)

    def add_issue(
        self,
        severity: str,
        code: str,
        message: str,
        *,
        category: str = "package",
        part: str | None = None,
        rels_file: str | None = None,
        relationship_id: str | None = None,
        target: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.issues.append(
            DiagnosticIssue(
                severity=severity,
                code=code,
                message=message,
                category=category,
                part=part,
                rels_file=rels_file,
                relationship_id=relationship_id,
                target=target,
                details=details or {},
            )
        )

    @property
    def critical_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "critical")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "warning")

    @property
    def info_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "info")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["summary"] = {
            "critical": self.critical_count,
            "warning": self.warning_count,
            "info": self.info_count,
            "slide_count": self.slide_count,
        }
        return data

    def to_json(self, **kwargs: Any) -> str:
        return json.dumps(self.to_dict(), **kwargs)


def inspect_pptx(path: str | Path) -> DiagnosticReport:
    """Inspect a PPTX file and return structured diagnostics."""

    pptx_path = Path(path)
    report = DiagnosticReport(input_path=str(pptx_path))

    if not pptx_path.exists():
        report.add_issue(
            "critical",
            "file_not_found",
            f"Input file does not exist: {pptx_path}",
        )
        return report

    try:
        with zipfile.ZipFile(pptx_path, "r") as zf:
            report.is_zip = True
            bad_member = zf.testzip()
            if bad_member:
                report.zip_test_error = bad_member
                report.add_issue(
                    "critical",
                    "zip_member_crc_error",
                    f"ZIP CRC validation failed for {bad_member}.",
                    part=bad_member,
                )

            parts = set(_normalize_zip_name(name) for name in zf.namelist() if not name.endswith("/"))
            report.package_parts = sorted(parts)

            _inspect_required_parts(parts, report)
            xml_roots = _parse_xml_parts(zf, parts, report)
            _inspect_content_types(parts, xml_roots.get("[Content_Types].xml"), report)
            relationships = _inspect_relationships(parts, xml_roots, report)
            report.relationships = relationships
            _inspect_presentation_graph(parts, xml_roots, relationships, report)
            _inspect_powerpoint_strict_slide_xml(parts, xml_roots, report)
    except zipfile.BadZipFile as exc:
        report.add_issue(
            "critical",
            "not_a_zip",
            f"File is not a valid ZIP package: {exc}",
        )
    except OSError as exc:
        report.add_issue(
            "critical",
            "read_error",
            f"Could not read file: {exc}",
        )

    return report


def relationship_source_part(rels_path: str) -> str:
    """Return the source part for an OPC .rels part path."""

    rels_path = _normalize_zip_name(rels_path)
    if rels_path == "_rels/.rels":
        return ""

    directory, filename = posixpath.split(rels_path)
    if not filename.endswith(".rels") or not directory.endswith("_rels"):
        return ""

    source_name = filename[: -len(".rels")]
    source_dir = posixpath.dirname(directory)
    if source_dir in ("", "."):
        return source_name
    return posixpath.normpath(posixpath.join(source_dir, source_name))


def rels_path_for_source(source_part: str) -> str:
    """Return the conventional .rels path for a source part."""

    if not source_part:
        return "_rels/.rels"
    directory, filename = posixpath.split(source_part)
    if directory:
        return posixpath.join(directory, "_rels", f"{filename}.rels")
    return posixpath.join("_rels", f"{filename}.rels")


def resolve_relationship_target(source_part: str, target: str) -> tuple[str | None, bool]:
    """Resolve an internal OPC relationship target.

    Returns `(resolved_part, malformed)`. External targets are handled by the
    caller and should not be passed here.
    """

    if target is None or target == "":
        return None, True

    decoded = unquote(target)
    if "\\" in decoded:
        return None, True

    parsed = urlparse(decoded)
    if parsed.scheme and not decoded.startswith("/"):
        return None, True

    if decoded.startswith("/"):
        resolved = posixpath.normpath(decoded.lstrip("/"))
    else:
        base_dir = posixpath.dirname(source_part) if source_part else ""
        resolved = posixpath.normpath(posixpath.join(base_dir, decoded))

    if resolved in ("", ".", "..") or resolved.startswith("../") or resolved.startswith("/"):
        return None, True
    return resolved, False


def is_optional_relationship(relationship_type: str) -> bool:
    """Return whether a missing target is usually content loss, not graph breakage."""

    return any(keyword in relationship_type for keyword in OPTIONAL_REL_KEYWORDS)


def is_critical_relationship(relationship_type: str) -> bool:
    """Return whether a missing target likely breaks PowerPoint openability."""

    return any(relationship_type.endswith(suffix) for suffix in CRITICAL_REL_SUFFIXES)


def relationship_kind(relationship_type: str) -> str:
    """Return the final relationship type token."""

    return relationship_type.rstrip("/").rsplit("/", 1)[-1]


def expected_content_type_for_part(part: str) -> tuple[str, str] | None:
    """Return `(kind, content_type)` for important PPTX parts."""

    for pattern, kind, _severity in IMPORTANT_PART_PATTERNS:
        if pattern.match(part):
            return kind, CONTENT_TYPES[kind]
    return None


def _normalize_zip_name(name: str) -> str:
    return name.replace("\\", "/").lstrip("/")


def _inspect_required_parts(parts: set[str], report: DiagnosticReport) -> None:
    for required in sorted(REQUIRED_PARTS):
        if required not in parts:
            report.add_issue(
                "critical",
                "missing_required_part",
                f"Required package part is missing: {required}",
                part=required,
            )


def _parse_xml_parts(
    zf: zipfile.ZipFile,
    parts: set[str],
    report: DiagnosticReport,
) -> dict[str, ET.Element]:
    roots: dict[str, ET.Element] = {}
    xml_parts = sorted(part for part in parts if part.endswith(".xml") or part.endswith(".rels"))
    for part in xml_parts:
        try:
            roots[part] = ET.fromstring(zf.read(part))
        except ET.ParseError as exc:
            severity = "critical" if _is_core_xml(part) else "warning"
            report.add_issue(
                severity,
                "xml_parse_error",
                f"XML parse error in {part}: {exc}",
                category="xml",
                part=part,
            )
        except KeyError:
            report.add_issue(
                "critical",
                "zip_member_missing",
                f"ZIP member listed but could not be read: {part}",
                part=part,
            )
    return roots


def _is_core_xml(part: str) -> bool:
    if part in REQUIRED_PARTS:
        return True
    return any(
        part.startswith(prefix)
        for prefix in (
            "ppt/slides/",
            "ppt/slideLayouts/",
            "ppt/slideMasters/",
        )
    )


def _inspect_content_types(
    parts: set[str],
    root: ET.Element | None,
    report: DiagnosticReport,
) -> None:
    if root is None:
        return

    overrides: set[str] = set()
    for override in root.findall(f"{{{CT_NS}}}Override"):
        part_name = override.get("PartName")
        if not part_name or not part_name.startswith("/"):
            report.add_issue(
                "warning",
                "malformed_content_type_override",
                f"Content type Override has malformed PartName: {part_name!r}",
                category="content-types",
                target=part_name,
            )
            continue
        part = _normalize_zip_name(part_name)
        overrides.add(part)
        if part not in parts:
            report.add_issue(
                "warning",
                "dangling_content_type_override",
                f"Content type Override points to a missing part: {part_name}",
                category="content-types",
                part=part,
            )

    report.content_type_overrides = sorted(overrides)

    for part in sorted(parts):
        match = expected_content_type_for_part(part)
        if not match or part in overrides:
            continue
        _kind, expected = match
        severity = "critical" if part == "ppt/presentation.xml" else "warning"
        report.add_issue(
            severity,
            "missing_content_type_override",
            f"Important PPTX part lacks a [Content_Types].xml Override: /{part}",
            category="content-types",
            part=part,
            details={"expected_content_type": expected},
        )


def _inspect_relationships(
    parts: set[str],
    xml_roots: dict[str, ET.Element],
    report: DiagnosticReport,
) -> list[RelationshipRecord]:
    records: list[RelationshipRecord] = []
    rels_parts = sorted(part for part in parts if part.endswith(".rels"))

    for rels_file in rels_parts:
        root = xml_roots.get(rels_file)
        if root is None:
            continue

        source_part = relationship_source_part(rels_file)
        seen_ids: set[str] = set()
        for rel in _relationship_elements(root):
            rid = rel.get("Id") or ""
            rtype = rel.get("Type") or ""
            target = rel.get("Target") or ""
            target_mode = rel.get("TargetMode")
            is_external = (target_mode or "").lower() == "external"

            if not rid:
                report.add_issue(
                    "warning",
                    "missing_relationship_id",
                    f"Relationship in {rels_file} is missing Id.",
                    category="relationships",
                    rels_file=rels_file,
                    target=target,
                )
            elif rid in seen_ids:
                report.add_issue(
                    "critical",
                    "duplicate_relationship_id",
                    f"Duplicate relationship Id {rid} in {rels_file}.",
                    category="relationships",
                    rels_file=rels_file,
                    relationship_id=rid,
                )
            seen_ids.add(rid)

            resolved: str | None = None
            exists: bool | None = None
            malformed = False
            if is_external:
                exists = None
            else:
                resolved, malformed = resolve_relationship_target(source_part, target)
                exists = resolved in parts if resolved else False
                if malformed:
                    severity = "critical" if is_critical_relationship(rtype) else "warning"
                    report.add_issue(
                        severity,
                        "malformed_relationship_target",
                        f"Relationship {rid or '<missing id>'} in {rels_file} has malformed target: {target!r}.",
                        category="relationships",
                        rels_file=rels_file,
                        relationship_id=rid or None,
                        target=target,
                    )
                elif not exists:
                    severity = "critical" if is_critical_relationship(rtype) else "warning"
                    report.add_issue(
                        severity,
                        "dangling_relationship",
                        f"Relationship {rid or '<missing id>'} in {rels_file} points to missing part: {resolved}.",
                        category=relationship_kind(rtype) or "relationships",
                        rels_file=rels_file,
                        relationship_id=rid or None,
                        target=resolved,
                        details={"relationship_type": rtype},
                    )

            records.append(
                RelationshipRecord(
                    rels_file=rels_file,
                    source_part=source_part,
                    relationship_id=rid,
                    relationship_type=rtype,
                    target=target,
                    target_mode=target_mode,
                    resolved_target=resolved,
                    is_external=is_external,
                    exists=exists,
                    malformed=malformed,
                )
            )

    return records


def _relationship_elements(root: ET.Element) -> Iterable[ET.Element]:
    elements = root.findall(f"{{{REL_NS}}}Relationship")
    if elements:
        return elements
    return [child for child in list(root) if child.tag.rsplit("}", 1)[-1] == "Relationship"]


def _inspect_presentation_graph(
    parts: set[str],
    xml_roots: dict[str, ET.Element],
    relationships: list[RelationshipRecord],
    report: DiagnosticReport,
) -> None:
    presentation = xml_roots.get("ppt/presentation.xml")
    if presentation is None:
        report.slide_parts = sorted(part for part in parts if re.match(r"^ppt/slides/slide\d+\.xml$", part))
        report.slide_count = len(report.slide_parts)
        return

    by_source: dict[str, list[RelationshipRecord]] = {}
    for rel in relationships:
        by_source.setdefault(rel.source_part, []).append(rel)

    presentation_rels = by_source.get("ppt/presentation.xml", [])
    presentation_by_id = {rel.relationship_id: rel for rel in presentation_rels if rel.relationship_id}

    slide_parts: list[str] = []
    for sld_id in presentation.findall(".//p:sldId", NS):
        rid = sld_id.get(f"{{{R_NS}}}id")
        if not rid:
            report.add_issue(
                "critical",
                "slide_id_missing_relationship_id",
                "presentation.xml contains a slide id without an r:id.",
                category="presentation-graph",
                part="ppt/presentation.xml",
            )
            continue
        rel = presentation_by_id.get(rid)
        if rel is None:
            report.add_issue(
                "critical",
                "slide_id_missing_relationship",
                f"presentation.xml slide id references missing relationship {rid}.",
                category="presentation-graph",
                part="ppt/presentation.xml",
                relationship_id=rid,
            )
            continue
        if not rel.relationship_type.endswith("/slide"):
            report.add_issue(
                "critical",
                "slide_id_wrong_relationship_type",
                f"presentation.xml slide id {rid} does not reference a slide relationship.",
                category="presentation-graph",
                part="ppt/presentation.xml",
                relationship_id=rid,
                details={"relationship_type": rel.relationship_type},
            )
            continue
        if not rel.exists or not rel.resolved_target:
            report.add_issue(
                "critical",
                "slide_relationship_target_missing",
                f"presentation.xml slide relationship {rid} does not point to an existing slide part.",
                category="presentation-graph",
                part="ppt/presentation.xml",
                relationship_id=rid,
                target=rel.resolved_target,
            )
            continue
        slide_parts.append(rel.resolved_target)

    report.slide_parts = slide_parts
    report.slide_count = len(slide_parts)

    _inspect_presentation_masters(presentation, presentation_rels, report)
    _inspect_slide_layout_links(slide_parts, by_source, report)
    _inspect_layout_master_links(parts, slide_parts, by_source, report)
    _inspect_notes_slide_consistency(by_source, report)


def _inspect_presentation_masters(
    presentation: ET.Element,
    presentation_rels: list[RelationshipRecord],
    report: DiagnosticReport,
) -> None:
    by_id = {rel.relationship_id: rel for rel in presentation_rels if rel.relationship_id}
    master_id_elements = presentation.findall(".//p:sldMasterId", NS)

    valid_master_rels = [
        rel
        for rel in presentation_rels
        if rel.relationship_type.endswith("/slideMaster") and rel.exists
    ]

    if not master_id_elements:
        report.add_issue(
            "critical",
            "missing_presentation_slide_master_list",
            "presentation.xml has no slide master id list.",
            category="presentation-graph",
            part="ppt/presentation.xml",
        )

    for master_id in master_id_elements:
        rid = master_id.get(f"{{{R_NS}}}id")
        if not rid:
            report.add_issue(
                "critical",
                "slide_master_id_missing_relationship_id",
                "presentation.xml contains a slide master id without an r:id.",
                category="presentation-graph",
                part="ppt/presentation.xml",
            )
            continue
        rel = by_id.get(rid)
        if rel is None:
            report.add_issue(
                "critical",
                "slide_master_id_missing_relationship",
                f"presentation.xml slide master id references missing relationship {rid}.",
                category="presentation-graph",
                part="ppt/presentation.xml",
                relationship_id=rid,
            )
        elif not rel.relationship_type.endswith("/slideMaster"):
            report.add_issue(
                "critical",
                "slide_master_id_wrong_relationship_type",
                f"presentation.xml relationship {rid} is not a slideMaster relationship.",
                category="presentation-graph",
                part="ppt/presentation.xml",
                relationship_id=rid,
                details={"relationship_type": rel.relationship_type},
            )
        elif not rel.exists:
            report.add_issue(
                "critical",
                "presentation_slide_master_missing",
                f"presentation.xml slide master relationship {rid} points to a missing part.",
                category="presentation-graph",
                part="ppt/presentation.xml",
                relationship_id=rid,
                target=rel.resolved_target,
            )

    if not valid_master_rels:
        report.add_issue(
            "critical",
            "no_valid_presentation_slide_master_relationship",
            "presentation.xml.rels has no valid slideMaster relationship.",
            category="presentation-graph",
            part="ppt/_rels/presentation.xml.rels",
        )


def _inspect_slide_layout_links(
    slide_parts: list[str],
    by_source: dict[str, list[RelationshipRecord]],
    report: DiagnosticReport,
) -> None:
    for slide_part in slide_parts:
        slide_rels = [
            rel for rel in by_source.get(slide_part, []) if rel.relationship_type.endswith("/slideLayout")
        ]
        if not slide_rels:
            report.add_issue(
                "critical",
                "missing_slide_layout_relationship",
                f"Slide has no slideLayout relationship: {slide_part}",
                category="presentation-graph",
                part=slide_part,
            )
            continue
        for rel in slide_rels:
            if not rel.exists:
                report.add_issue(
                    "critical",
                    "slide_layout_relationship_target_missing",
                    f"Slide layout relationship {rel.relationship_id} points to a missing layout.",
                    category="presentation-graph",
                    part=slide_part,
                    rels_file=rel.rels_file,
                    relationship_id=rel.relationship_id,
                    target=rel.resolved_target,
                )


def _inspect_layout_master_links(
    parts: set[str],
    slide_parts: list[str],
    by_source: dict[str, list[RelationshipRecord]],
    report: DiagnosticReport,
) -> None:
    referenced_layouts = {
        rel.resolved_target
        for slide_part in slide_parts
        for rel in by_source.get(slide_part, [])
        if rel.relationship_type.endswith("/slideLayout") and rel.resolved_target
    }
    existing_layouts = {
        part for part in parts if re.match(r"^ppt/slideLayouts/slideLayout\d+\.xml$", part)
    }
    layouts_to_check = sorted(existing_layouts | {part for part in referenced_layouts if part})

    for layout_part in layouts_to_check:
        if layout_part not in parts:
            continue
        layout_rels = [
            rel for rel in by_source.get(layout_part, []) if rel.relationship_type.endswith("/slideMaster")
        ]
        if not layout_rels:
            report.add_issue(
                "critical",
                "missing_layout_slide_master_relationship",
                f"Slide layout has no slideMaster relationship: {layout_part}",
                category="presentation-graph",
                part=layout_part,
            )
            continue
        for rel in layout_rels:
            if not rel.exists:
                report.add_issue(
                    "critical",
                    "layout_slide_master_relationship_target_missing",
                    f"Slide layout master relationship {rel.relationship_id} points to a missing master.",
                    category="presentation-graph",
                    part=layout_part,
                    rels_file=rel.rels_file,
                    relationship_id=rel.relationship_id,
                    target=rel.resolved_target,
                )


def _inspect_notes_slide_consistency(
    by_source: dict[str, list[RelationshipRecord]],
    report: DiagnosticReport,
) -> None:
    for slide_part, slide_rels in sorted(by_source.items()):
        if not re.match(r"^ppt/slides/slide\d+\.xml$", slide_part):
            continue
        for rel in slide_rels:
            if not rel.relationship_type.endswith("/notesSlide") or not rel.exists or not rel.resolved_target:
                continue
            notes_rels = by_source.get(rel.resolved_target, [])
            backlinks = [
                notes_rel
                for notes_rel in notes_rels
                if notes_rel.relationship_type.endswith("/slide")
                and notes_rel.resolved_target == slide_part
                and notes_rel.exists
            ]
            if not backlinks:
                report.add_issue(
                    "warning",
                    "notes_slide_missing_backlink",
                    f"Notes slide does not link back to its owning slide: {rel.resolved_target}",
                    category="notesSlide",
                    part=rel.resolved_target,
                    target=slide_part,
                    details={"slide_relationship_id": rel.relationship_id},
                )


def _inspect_powerpoint_strict_slide_xml(
    parts: set[str],
    xml_roots: dict[str, ET.Element],
    report: DiagnosticReport,
) -> None:
    for part in sorted(parts):
        if not re.match(r"^ppt/slides/slide\d+\.xml$", part):
            continue
        root = xml_roots.get(part)
        if root is None:
            continue
        _inspect_duplicate_shape_ids(part, root, report)
        _inspect_missing_end_para_rpr(part, root, report)


def _inspect_duplicate_shape_ids(part: str, root: ET.Element, report: DiagnosticReport) -> None:
    seen: dict[str, str | None] = {}
    duplicates: dict[str, list[str | None]] = {}
    for cnvpr in root.findall(".//p:cNvPr", NS):
        shape_id = cnvpr.get("id")
        if not shape_id:
            continue
        shape_name = cnvpr.get("name")
        if shape_id in seen:
            duplicates.setdefault(shape_id, [seen[shape_id]]).append(shape_name)
        else:
            seen[shape_id] = shape_name

    for shape_id, names in sorted(duplicates.items(), key=lambda item: _numeric_sort_key(item[0])):
        report.add_issue(
            "critical",
            "duplicate_shape_id",
            f"Slide contains duplicate p:cNvPr shape id {shape_id}.",
            category="powerpoint-strict",
            part=part,
            details={"shape_id": shape_id, "shape_names": names},
        )


def _inspect_missing_end_para_rpr(part: str, root: ET.Element, report: DiagnosticReport) -> None:
    missing_indexes: list[int] = []
    for index, paragraph in enumerate(root.findall(".//a:p", NS), start=1):
        children = list(paragraph)
        if not children or children[-1].tag != f"{{{A_NS}}}endParaRPr":
            missing_indexes.append(index)

    if missing_indexes:
        report.add_issue(
            "critical",
            "missing_end_para_rpr",
            f"Slide has {len(missing_indexes)} paragraph(s) that do not end with a:endParaRPr.",
            category="powerpoint-strict",
            part=part,
            details={
                "missing_count": len(missing_indexes),
                "paragraph_indexes": missing_indexes[:25],
                "truncated": len(missing_indexes) > 25,
            },
        )


def _numeric_sort_key(value: str) -> tuple[int, str]:
    return (int(value), value) if value.isdigit() else (10**9, value)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Inspect a PPTX package for compatibility issues.")
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--json", action="store_true", help="Print JSON diagnostics.")
    args = parser.parse_args(argv)

    report = inspect_pptx(args.pptx)
    if args.json:
        print(report.to_json(indent=2))
    else:
        print(f"{args.pptx}: {report.critical_count} critical, {report.warning_count} warnings, {report.info_count} info")
        for issue in report.issues:
            print(f"[{issue.severity}] {issue.code}: {issue.message}")
    return 1 if report.critical_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
