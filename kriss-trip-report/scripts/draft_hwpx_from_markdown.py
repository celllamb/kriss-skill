#!/usr/bin/env python3
"""Create a HWPX report draft from Markdown-ish text and image markers."""

from __future__ import annotations

import argparse
import copy
import mimetypes
import re
import shutil
import sys
import uuid
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

from _deps import import_or_install

Image = import_or_install("PIL.Image", "Pillow")
ImageOps = import_or_install("PIL.ImageOps", "Pillow")


NS = {
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
    "hs": "http://www.hancom.co.kr/hwpml/2011/section",
    "hc": "http://www.hancom.co.kr/hwpml/2011/core",
    "opf": "http://www.idpf.org/2007/opf/",
}
ET.register_namespace("hp", NS["hp"])
ET.register_namespace("hs", NS["hs"])
ET.register_namespace("hc", NS["hc"])
ET.register_namespace("opf", NS["opf"])

HWPUNIT_PER_INCH = 7200
MM_PER_INCH = 25.4
IMG_SOURCE_UNIT_PER_PIXEL = 75

# HWP's InsertPicture output stores display sizes in HWP units. The KRISS
# template text column is about 150 mm wide.
MAX_NORMAL_IMAGE_W_MM = 150
MAX_NORMAL_IMAGE_H_MM = 220
MAX_FULL_PAGE_IMAGE_W_MM = 150
MAX_FULL_PAGE_IMAGE_H_MM = 245
MAX_EMBEDDED_PIXEL_EDGE = 2200


def default_template() -> Path:
    return Path(__file__).resolve().parents[1] / "assets" / "kriss-overseas-trip-report-template.hwpx"


def read_items(path: Path) -> list[tuple[str, str, str | None]]:
    raw = path.read_text(encoding="utf-8")
    items: list[tuple[str, str, str | None]] = []
    for line in raw.splitlines():
        line = line.rstrip()
        image_match = re.match(r"!\[([^\]]*)\]\((.+)\)\s*$", line)
        if image_match:
            caption = image_match.group(1).strip()
            kind = "image"
            if caption.lower().startswith("fullpage:"):
                kind = "image-full"
                caption = caption.split(":", 1)[1].strip()
            items.append((kind, image_match.group(2).strip(), caption))
        elif line.strip().lower() in {"[page_break]", "[pagebreak]", "<!-- pagebreak -->"}:
            items.append(("pagebreak", "", None))
        elif line.startswith("# "):
            items.append(("text", line[2:].strip(), None))
        elif line.startswith("## "):
            items.append(("text", line[3:].strip(), None))
        elif line.startswith("### "):
            items.append(("text", line[4:].strip(), None))
        elif line.startswith("- "):
            items.append(("text", "      - " + line[2:].strip(), None))
        elif re.match(r"^\d+\.\s+", line):
            items.append(("text", "   " + line, None))
        elif line:
            items.append(("text", line, None))
        else:
            items.append(("text", "", None))
    return items


def paragraph_text(para: ET.Element) -> str:
    return "".join(t.text or "" for t in para.findall(".//hp:t", NS))


def set_paragraph_text(para: ET.Element, text: str) -> ET.Element:
    text_nodes = para.findall(".//hp:t", NS)
    if text_nodes:
        text_nodes[0].text = text
        for node in text_nodes[1:]:
            node.text = ""
        return para

    run = para.find("./hp:run", NS)
    if run is None:
        run = ET.SubElement(para, f"{{{NS['hp']}}}run")
    t = ET.SubElement(run, f"{{{NS['hp']}}}t")
    t.text = text
    return para


def remove_layout_cache(para: ET.Element) -> None:
    """Remove cached line segments so the HWPX viewer can recalculate layout."""
    for child in list(para):
        if child.tag == f"{{{NS['hp']}}}linesegarray":
            para.remove(child)


def clear_paragraph(para: ET.Element) -> None:
    for child in list(para):
        para.remove(child)


def set_paragraph_id(para: ET.Element, para_id: int) -> None:
    if "id" in para.attrib:
        para.set("id", str(para_id))


def qname(ns: str, name: str) -> str:
    return f"{{{ns}}}{name}"


def add_manifest_item(work_dir: Path, image_id: str, rel_path: str, media_type: str) -> None:
    hpf_path = work_dir / "Contents" / "content.hpf"
    tree = ET.parse(hpf_path)
    root = tree.getroot()
    manifest = root.find("./opf:manifest", NS)
    if manifest is None:
        raise ValueError("content.hpf has no opf:manifest")
    ET.SubElement(
        manifest,
        qname(NS["opf"], "item"),
        {
            "id": image_id,
            "href": rel_path,
            "media-type": media_type,
            "isEmbeded": "1",
        },
    )
    tree.write(hpf_path, encoding="utf-8", xml_declaration=True)


def prepare_embedded_image(src: Path, dest_stem: Path, *, full_page: bool = False) -> tuple[Path, str, str]:
    """Normalize images to the same PNG payload style Hancom Office writes."""
    dest = dest_stem.with_suffix(".png")
    suffix = ".png"
    media_type = "image/png"
    with Image.open(src) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode in {"RGBA", "LA"} or "transparency" in img.info:
            rgba = img.convert("RGBA")
            background = Image.new("RGB", rgba.size, "white")
            background.paste(rgba, mask=rgba.getchannel("A"))
            normalized = background
        else:
            normalized = img.convert("RGB")
        if max(normalized.size) > MAX_EMBEDDED_PIXEL_EDGE:
            normalized.thumbnail(
                (MAX_EMBEDDED_PIXEL_EDGE, MAX_EMBEDDED_PIXEL_EDGE),
                Image.Resampling.LANCZOS,
            )
        normalized.save(dest, "PNG", optimize=False, dpi=(150, 150))
    return dest, suffix, media_type


def apply_page_break(para: ET.Element) -> None:
    para.set("pageBreak", "1")


def mm_to_hwpunit(value: int) -> int:
    return max(1, round(value / MM_PER_INCH * HWPUNIT_PER_INCH))


def fit_image_size(pixel_w: int, pixel_h: int, *, full_page: bool = False) -> tuple[int, int]:
    max_w = MAX_FULL_PAGE_IMAGE_W_MM if full_page else MAX_NORMAL_IMAGE_W_MM
    max_h = MAX_FULL_PAGE_IMAGE_H_MM if full_page else MAX_NORMAL_IMAGE_H_MM
    cur_w = max_w
    cur_h = max(10, round(cur_w * pixel_h / pixel_w))
    if cur_h > max_h:
        cur_h = max_h
        cur_w = max(10, round(cur_h * pixel_w / pixel_h))
    return mm_to_hwpunit(cur_w), mm_to_hwpunit(cur_h)


def make_image_paragraph(
    proto: ET.Element,
    image_id: str,
    image_path: Path,
    caption: str | None,
    pic_no: int,
    *,
    full_page: bool = False,
) -> ET.Element:
    with Image.open(image_path) as img:
        pixel_w, pixel_h = img.size

    target_w, target_h = fit_image_size(pixel_w, pixel_h, full_page=full_page)
    source_w = max(1, round(pixel_w * IMG_SOURCE_UNIT_PER_PIXEL))
    source_h = max(1, round(pixel_h * IMG_SOURCE_UNIT_PER_PIXEL))

    para = copy.deepcopy(proto)
    clear_paragraph(para)
    remove_layout_cache(para)

    run_attrs: dict[str, str] = {}
    proto_run = proto.find("./hp:run", NS)
    if proto_run is not None and "charPrIDRef" in proto_run.attrib:
        run_attrs["charPrIDRef"] = proto_run.attrib["charPrIDRef"]
    run = ET.SubElement(para, qname(NS["hp"], "run"), run_attrs)

    pic = ET.SubElement(
        run,
        qname(NS["hp"], "pic"),
        {
            "id": str(1800000000 + pic_no),
            "zOrder": str(pic_no),
            "numberingType": "PICTURE",
            "textWrap": "TOP_AND_BOTTOM",
            "textFlow": "BOTH_SIDES",
            "lock": "0",
            "dropcapstyle": "None",
            "href": "",
            "groupLevel": "0",
            "instid": str(1900000000 + pic_no),
            "reverse": "0",
        },
    )
    ET.SubElement(pic, qname(NS["hp"], "offset"), {"x": "0", "y": "0"})
    ET.SubElement(pic, qname(NS["hp"], "orgSz"), {"width": str(target_w), "height": str(target_h)})
    ET.SubElement(pic, qname(NS["hp"], "curSz"), {"width": "0", "height": "0"})
    ET.SubElement(pic, qname(NS["hp"], "flip"), {"horizontal": "0", "vertical": "0"})
    ET.SubElement(
        pic,
        qname(NS["hp"], "rotationInfo"),
        {"angle": "0", "centerX": str(target_w // 2), "centerY": str(target_h // 2), "rotateimage": "1"},
    )
    rendering = ET.SubElement(pic, qname(NS["hp"], "renderingInfo"))
    ET.SubElement(rendering, qname(NS["hc"], "transMatrix"), {"e1": "1", "e2": "0", "e3": "0", "e4": "0", "e5": "1", "e6": "0"})
    ET.SubElement(rendering, qname(NS["hc"], "scaMatrix"), {"e1": "1", "e2": "0", "e3": "0", "e4": "0", "e5": "1", "e6": "0"})
    ET.SubElement(rendering, qname(NS["hc"], "rotMatrix"), {"e1": "1", "e2": "0", "e3": "0", "e4": "0", "e5": "1", "e6": "0"})
    img_rect = ET.SubElement(pic, qname(NS["hp"], "imgRect"))
    ET.SubElement(img_rect, qname(NS["hc"], "pt0"), {"x": "0", "y": "0"})
    ET.SubElement(img_rect, qname(NS["hc"], "pt1"), {"x": str(target_w), "y": "0"})
    ET.SubElement(img_rect, qname(NS["hc"], "pt2"), {"x": str(target_w), "y": str(target_h)})
    ET.SubElement(img_rect, qname(NS["hc"], "pt3"), {"x": "0", "y": str(target_h)})
    ET.SubElement(pic, qname(NS["hp"], "imgClip"), {"left": "0", "right": str(source_w), "top": "0", "bottom": str(source_h)})
    ET.SubElement(pic, qname(NS["hp"], "inMargin"), {"left": "0", "right": "0", "top": "0", "bottom": "0"})
    ET.SubElement(pic, qname(NS["hp"], "imgDim"), {"dimwidth": str(source_w), "dimheight": str(source_h)})
    ET.SubElement(pic, qname(NS["hc"], "img"), {"binaryItemIDRef": image_id, "bright": "0", "contrast": "0", "effect": "REAL_PIC", "alpha": "0"})
    ET.SubElement(pic, qname(NS["hp"], "effects"))
    ET.SubElement(pic, qname(NS["hp"], "sz"), {"width": str(target_w), "widthRelTo": "ABSOLUTE", "height": str(target_h), "heightRelTo": "ABSOLUTE", "protect": "0"})
    ET.SubElement(
        pic,
        qname(NS["hp"], "pos"),
        {
            "treatAsChar": "1",
            "affectLSpacing": "0",
            "flowWithText": "1",
            "allowOverlap": "0",
            "holdAnchorAndSO": "0",
            "vertRelTo": "PARA",
            "horzRelTo": "COLUMN",
            "vertAlign": "TOP",
            "horzAlign": "LEFT",
            "vertOffset": "0",
            "horzOffset": "0",
        },
    )
    ET.SubElement(pic, qname(NS["hp"], "outMargin"), {"left": "0", "right": "0", "top": "0", "bottom": "0"})
    comment = ET.SubElement(pic, qname(NS["hp"], "shapeComment"))
    comment.text = caption or image_path.name
    ET.SubElement(run, qname(NS["hp"], "t")).text = ""
    return para


def choose_proto(line: str, prototypes: dict[str, ET.Element]) -> ET.Element:
    stripped = line.strip()
    if not stripped:
        return prototypes["blank"]
    if re.match(r"^[ⅠⅡⅢⅣV]+\.", stripped) or re.match(r"^[IVX]+\.", stripped):
        return prototypes["section"]
    if stripped.startswith("○"):
        return prototypes["bullet"]
    if stripped.startswith("-") or stripped.startswith("·") or stripped.startswith("※"):
        return prototypes["subbullet"]
    if re.match(r"^\d+\.", stripped):
        return prototypes["bullet"]
    return prototypes["body"]


def rewrite_section(template: Path, markdown: Path, output: Path) -> None:
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.parent / f".kriss-hwpx-work-{uuid.uuid4().hex}"
    tmp.mkdir()
    try:
        with zipfile.ZipFile(template) as zf:
            zf.extractall(tmp)

        section_path = tmp / "Contents" / "section0.xml"
        tree = ET.parse(section_path)
        root = tree.getroot()
        paras = root.findall("./hp:p", NS)
        if len(paras) < 8:
            raise ValueError("Template section does not contain expected paragraphs.")

        prototypes = {
            "title": paras[0],
            "blank": paras[1],
            "section": paras[2],
            "bullet": paras[3],
            "body": paras[7],
            "subbullet": paras[7],
        }

        for child in list(root):
            root.remove(child)

        title = copy.deepcopy(prototypes["title"])
        all_items = read_items(markdown)
        if not all_items:
            all_items = [("text", "국외출장보고서", None)]
        first_kind, first_value, _ = all_items[0]
        first_line = first_value if first_kind == "text" else "국외출장보고서"
        body_items = all_items[1:]
        set_paragraph_text(title, first_line or "국외출장보고서")
        remove_layout_cache(title)
        next_para_id = 0
        set_paragraph_id(title, next_para_id)
        next_para_id += 1
        root.append(title)
        blank = copy.deepcopy(prototypes["blank"])
        remove_layout_cache(blank)
        set_paragraph_id(blank, next_para_id)
        next_para_id += 1
        root.append(blank)

        bin_dir = tmp / "BinData"
        bin_dir.mkdir(exist_ok=True)
        image_no = 1
        pending_page_break = False
        preview_lines = [first_line or "국외출장보고서", ""]

        for kind, value, caption in body_items:
            if kind == "pagebreak":
                pending_page_break = True
                preview_lines.append("[쪽 나누기]")
                continue

            if kind in {"image", "image-full"}:
                src = Path(value)
                if not src.exists():
                    raise FileNotFoundError(f"Image not found: {src}")
                image_id = f"image{image_no}"
                embedded, suffix, media_type = prepare_embedded_image(
                    src,
                    bin_dir / image_id,
                    full_page=(kind == "image-full"),
                )
                rel_path = f"BinData/{embedded.name}"
                add_manifest_item(tmp, image_id, rel_path, media_type or mimetypes.types_map.get(suffix, "image/jpeg"))
                para = make_image_paragraph(prototypes["body"], image_id, embedded, caption, image_no, full_page=(kind == "image-full"))
                if pending_page_break:
                    apply_page_break(para)
                    pending_page_break = False
                set_paragraph_id(para, next_para_id)
                next_para_id += 1
                root.append(para)
                preview_lines.append(f"[그림] {caption or src.name}")
                image_no += 1
                continue

            line = value
            proto = choose_proto(line, prototypes)
            para = copy.deepcopy(proto)
            set_paragraph_text(para, line)
            remove_layout_cache(para)
            if pending_page_break:
                apply_page_break(para)
                pending_page_break = False
            set_paragraph_id(para, next_para_id)
            next_para_id += 1
            root.append(para)
            preview_lines.append(line)

        tree.write(section_path, encoding="utf-8", xml_declaration=True)
        preview = tmp / "Preview" / "PrvText.txt"
        if preview.exists():
            preview.write_text("\n".join(preview_lines).rstrip() + "\n", encoding="utf-8")
        pack_hwpx(tmp, output)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def pack_hwpx(src_dir: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w") as zf:
        mimetype = src_dir / "mimetype"
        if mimetype.exists():
            zf.write(mimetype, "mimetype", compress_type=zipfile.ZIP_STORED)
        for path in sorted(src_dir.rglob("*")):
            if path.is_dir() or path.name == "mimetype":
                continue
            rel_path = path.relative_to(src_dir).as_posix()
            compress_type = zipfile.ZIP_STORED if rel_path.startswith("BinData/") else zipfile.ZIP_DEFLATED
            zf.write(path, rel_path, compress_type=compress_type)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", help="UTF-8 Markdown or plain-text draft.")
    parser.add_argument("output", help="Output .hwpx path.")
    parser.add_argument("--template", default=str(default_template()), help="Template .hwpx path.")
    args = parser.parse_args(argv)

    rewrite_section(Path(args.template), Path(args.markdown), Path(args.output))
    print(f"Wrote {Path(args.output).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
