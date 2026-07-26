from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from inspect_pptx import A_NS, CT_NS, OFFICE_REL, REL_NS, inspect_pptx  # noqa: E402
from repair_pptx_package import minimal_repair, structural_repair  # noqa: E402


def test_valid_minimal_pptx_passes_inspection(tmp_path: Path) -> None:
    pptx = make_pptx(tmp_path / "valid.pptx")

    report = inspect_pptx(pptx)

    assert report.critical_count == 0
    assert report.slide_count == 1


def test_dangling_content_type_override_is_detected(tmp_path: Path) -> None:
    pptx = make_pptx(tmp_path / "dangling-override.pptx", dangling_override=True)

    report = inspect_pptx(pptx)

    assert any(issue.code == "dangling_content_type_override" for issue in report.issues)


def test_missing_slide_master_relationship_is_critical(tmp_path: Path) -> None:
    pptx = make_pptx(tmp_path / "missing-master-rel.pptx", omit_layout_master_rel=True)

    report = inspect_pptx(pptx)

    assert any(issue.code == "missing_layout_slide_master_relationship" for issue in report.issues)
    assert report.critical_count > 0


def test_missing_optional_notes_slide_is_warning(tmp_path: Path) -> None:
    pptx = make_pptx(tmp_path / "missing-notes.pptx", missing_notes_rel=True)

    report = inspect_pptx(pptx)

    notes_issues = [issue for issue in report.issues if issue.category == "notesSlide"]
    assert notes_issues
    assert all(issue.severity == "warning" for issue in notes_issues)


def test_duplicate_shape_id_is_detected_as_critical(tmp_path: Path) -> None:
    pptx = make_pptx(tmp_path / "duplicate-shape-id.pptx", duplicate_shape_id=True)

    report = inspect_pptx(pptx)

    assert any(issue.code == "duplicate_shape_id" for issue in report.issues)
    assert report.critical_count > 0


def test_missing_end_para_rpr_is_detected_as_critical(tmp_path: Path) -> None:
    pptx = make_pptx(tmp_path / "missing-end-para-rpr.pptx", missing_end_para_rpr=True)

    report = inspect_pptx(pptx)

    issue = next(issue for issue in report.issues if issue.code == "missing_end_para_rpr")
    assert issue.severity == "critical"
    assert issue.details["missing_count"] == 2


def test_minimal_repair_removes_safe_dangling_override(tmp_path: Path) -> None:
    pptx = make_pptx(tmp_path / "dangling-override.pptx", dangling_override=True)
    repaired = tmp_path / "repaired.pptx"

    result = minimal_repair(pptx, repaired)
    report = inspect_pptx(repaired)

    assert repaired.exists()
    assert any(change.action == "remove_dangling_content_type_override" for change in result.changes)
    assert not any(issue.code == "dangling_content_type_override" for issue in report.issues)


def test_minimal_repair_fixes_powerpoint_strict_slide_xml(tmp_path: Path) -> None:
    pptx = make_pptx(
        tmp_path / "strict-slide-xml.pptx",
        duplicate_shape_id=True,
        missing_end_para_rpr=True,
    )
    repaired = tmp_path / "strict-slide-xml-repaired.pptx"

    result = minimal_repair(pptx, repaired)
    report = inspect_pptx(repaired)

    assert any(change.action == "renumber_duplicate_shape_id" for change in result.changes)
    assert any(change.action == "add_missing_end_para_rpr" for change in result.changes)
    assert not any(issue.code in {"duplicate_shape_id", "missing_end_para_rpr"} for issue in report.issues)
    assert not any(issue.severity == "critical" for issue in report.issues)

    with zipfile.ZipFile(repaired, "r") as zf:
        root = ET.fromstring(zf.read("ppt/slides/slide1.xml"))
    paragraphs = root.findall(f".//{{{A_NS}}}p")
    assert paragraphs
    assert all(list(paragraph)[-1].tag == f"{{{A_NS}}}endParaRPr" for paragraph in paragraphs)


def test_structural_repair_reconnects_layout_and_master(tmp_path: Path) -> None:
    pptx = make_pptx(
        tmp_path / "broken-graph.pptx",
        slide_layout_target="../slideLayouts/missingLayout.xml",
        layout_master_target="../slideMasters/missingMaster.xml",
    )
    repaired = tmp_path / "structural.pptx"

    result = structural_repair(pptx, repaired)
    report = inspect_pptx(repaired)

    assert repaired.exists()
    assert any(change.action == "ensure_slide_layout" for change in result.changes)
    assert any(change.action == "ensure_layout_master" for change in result.changes)
    assert not any(issue.severity == "critical" for issue in report.issues)


def test_cli_writes_diagnostic_report_and_repaired_output(tmp_path: Path) -> None:
    pptx = make_pptx(tmp_path / "cli-input.pptx", dangling_override=True)
    out_dir = tmp_path / "out"

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "pptx_doctor.py"),
            str(pptx),
            "--out-dir",
            str(out_dir),
            "--repair-level",
            "auto",
            "--report",
            "both",
            "--no-libreoffice",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    assert (out_dir / "cli-input_diagnostic_report.md").exists()
    assert (out_dir / "cli-input_diagnostic_report.json").exists()
    assert (out_dir / "cli-input_repaired.pptx").exists()
    data = json.loads((out_dir / "cli-input_diagnostic_report.json").read_text(encoding="utf-8"))
    assert data["status"] == "validated"


def make_pptx(
    path: Path,
    *,
    dangling_override: bool = False,
    omit_layout_master_rel: bool = False,
    missing_notes_rel: bool = False,
    duplicate_shape_id: bool = False,
    missing_end_para_rpr: bool = False,
    slide_layout_target: str = "../slideLayouts/slideLayout1.xml",
    layout_master_target: str = "../slideMasters/slideMaster1.xml",
) -> Path:
    parts = minimal_parts(
        dangling_override=dangling_override,
        omit_layout_master_rel=omit_layout_master_rel,
        missing_notes_rel=missing_notes_rel,
        duplicate_shape_id=duplicate_shape_id,
        missing_end_para_rpr=missing_end_para_rpr,
        slide_layout_target=slide_layout_target,
        layout_master_target=layout_master_target,
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in parts.items():
            zf.writestr(name, data)
    return path


def minimal_parts(
    *,
    dangling_override: bool,
    omit_layout_master_rel: bool,
    missing_notes_rel: bool,
    duplicate_shape_id: bool,
    missing_end_para_rpr: bool,
    slide_layout_target: str,
    layout_master_target: str,
) -> dict[str, bytes]:
    overrides = [
        ("ppt/presentation.xml", "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"),
        ("ppt/slides/slide1.xml", "application/vnd.openxmlformats-officedocument.presentationml.slide+xml"),
        ("ppt/slideLayouts/slideLayout1.xml", "application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"),
        ("ppt/slideMasters/slideMaster1.xml", "application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"),
        ("ppt/theme/theme1.xml", "application/vnd.openxmlformats-officedocument.theme+xml"),
    ]
    if dangling_override:
        overrides.append(("ppt/charts/chart99.xml", "application/vnd.openxmlformats-officedocument.drawingml.chart+xml"))

    parts: dict[str, bytes] = {
        "[Content_Types].xml": content_types_xml(overrides),
        "_rels/.rels": relationships_xml(
            [("rId1", f"{OFFICE_REL}/officeDocument", "ppt/presentation.xml")]
        ),
        "ppt/presentation.xml": presentation_xml(),
        "ppt/_rels/presentation.xml.rels": relationships_xml(
            [
                ("rId1", f"{OFFICE_REL}/slideMaster", "slideMasters/slideMaster1.xml"),
                ("rId2", f"{OFFICE_REL}/slide", "slides/slide1.xml"),
            ]
        ),
        "ppt/slides/slide1.xml": slide_xml(
            duplicate_shape_id=duplicate_shape_id,
            missing_end_para_rpr=missing_end_para_rpr,
        ),
        "ppt/slides/_rels/slide1.xml.rels": relationships_xml(
            [
                ("rId1", f"{OFFICE_REL}/slideLayout", slide_layout_target),
                *(
                    [("rId2", f"{OFFICE_REL}/notesSlide", "../notesSlides/notesSlide1.xml")]
                    if missing_notes_rel
                    else []
                ),
            ]
        ),
        "ppt/slideLayouts/slideLayout1.xml": slide_layout_xml(),
        "ppt/slideMasters/slideMaster1.xml": slide_master_xml(),
        "ppt/slideMasters/_rels/slideMaster1.xml.rels": relationships_xml(
            [
                ("rId1", f"{OFFICE_REL}/slideLayout", "../slideLayouts/slideLayout1.xml"),
                ("rId2", f"{OFFICE_REL}/theme", "../theme/theme1.xml"),
            ]
        ),
        "ppt/theme/theme1.xml": theme_xml(),
    }
    if not omit_layout_master_rel:
        parts["ppt/slideLayouts/_rels/slideLayout1.xml.rels"] = relationships_xml(
            [("rId1", f"{OFFICE_REL}/slideMaster", layout_master_target)]
        )
    return parts


def content_types_xml(overrides: list[tuple[str, str]]) -> bytes:
    root = ET.Element(f"{{{CT_NS}}}Types")
    default_rels = ET.SubElement(root, f"{{{CT_NS}}}Default")
    default_rels.set("Extension", "rels")
    default_rels.set("ContentType", "application/vnd.openxmlformats-package.relationships+xml")
    default_xml = ET.SubElement(root, f"{{{CT_NS}}}Default")
    default_xml.set("Extension", "xml")
    default_xml.set("ContentType", "application/xml")
    for part, content_type in overrides:
        override = ET.SubElement(root, f"{{{CT_NS}}}Override")
        override.set("PartName", f"/{part}")
        override.set("ContentType", content_type)
    return xml_bytes(root)


def relationships_xml(rows: list[tuple[str, str, str]]) -> bytes:
    root = ET.Element(f"{{{REL_NS}}}Relationships")
    for rid, rtype, target in rows:
        rel = ET.SubElement(root, f"{{{REL_NS}}}Relationship")
        rel.set("Id", rid)
        rel.set("Type", rtype)
        rel.set("Target", target)
    return xml_bytes(root)


def presentation_xml() -> bytes:
    return b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
  <p:sldIdLst><p:sldId id="256" r:id="rId2"/></p:sldIdLst>
  <p:sldSz cx="9144000" cy="6858000" type="screen4x3"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>"""


def slide_xml(*, duplicate_shape_id: bool = False, missing_end_para_rpr: bool = False) -> bytes:
    second_shape_id = "2" if duplicate_shape_id else "3"
    end_para = "" if missing_end_para_rpr else '<a:endParaRPr lang="en-US" sz="1200" dirty="0"/>'
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:cSld><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr/>
    <p:sp>
      <p:nvSpPr><p:cNvPr id="2" name="TitleBox"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
      <p:spPr/>
      <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US" sz="1200"/><a:t>Hello from a test slide</a:t></a:r>{end_para}</a:p></p:txBody>
    </p:sp>
    <p:sp>
      <p:nvSpPr><p:cNvPr id="{second_shape_id}" name="BodyBox"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
      <p:spPr/>
      <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US" sz="1000"/><a:t>Second paragraph</a:t></a:r>{end_para}</a:p></p:txBody>
    </p:sp>
  </p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>""".encode("utf-8")


def slide_layout_xml() -> bytes:
    return b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" type="blank" preserve="1">
  <p:cSld name="Blank"><p:spTree><p:nvGrpSpPr/><p:grpSpPr/></p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>"""


def slide_master_xml() -> bytes:
    return b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:cSld><p:spTree><p:nvGrpSpPr/><p:grpSpPr/></p:spTree></p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles/>
</p:sldMaster>"""


def theme_xml() -> bytes:
    return b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Test Theme">
  <a:themeElements/>
</a:theme>"""


def xml_bytes(root: ET.Element) -> bytes:
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)
