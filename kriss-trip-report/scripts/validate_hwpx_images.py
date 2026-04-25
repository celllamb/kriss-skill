#!/usr/bin/env python3
"""Validate embedded image references in a generated HWPX file."""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

from _deps import import_or_install

Image = import_or_install("PIL.Image", "Pillow")


NS = {
    "hc": "http://www.hancom.co.kr/hwpml/2011/core",
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
    "opf": "http://www.idpf.org/2007/opf/",
}
SECTION_RE = re.compile(r"^Contents/section\d+\.xml$", re.IGNORECASE)
MAX_DISPLAY_HWP_UNIT = 90000
MAX_SOURCE_IMAGE_UNIT = 180000
MAX_EMBEDDED_PIXEL_EDGE = 2200
ALLOWED_IMAGE_TYPES = {"image/jpeg": (".jpg", ".jpeg"), "image/png": (".png",), "image/bmp": (".bmp",)}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def section_paths(names: list[str]) -> list[str]:
    return sorted(name for name in names if SECTION_RE.match(name))


def image_manifest_items(zf: zipfile.ZipFile) -> dict[str, dict[str, str]]:
    root = ET.fromstring(zf.read("Contents/content.hpf"))
    items: dict[str, dict[str, str]] = {}
    for item in root.findall(".//opf:item", NS):
        item_id = item.get("id")
        href = item.get("href", "")
        media_type = item.get("media-type", "")
        if item_id and (href.startswith("BinData/") or media_type.startswith("image/")):
            items[item_id] = dict(item.attrib)
    return items


def child_by_name(elem: ET.Element, name: str) -> ET.Element | None:
    for child in list(elem):
        if local_name(child.tag) == name:
            return child
    return None


def max_int_attr(elem: ET.Element | None, attrs: tuple[str, ...]) -> int:
    if elem is None:
        return 0
    values: list[int] = []
    for attr in attrs:
        raw = elem.get(attr)
        if raw and raw.lstrip("-").isdigit():
            values.append(abs(int(raw)))
    return max(values, default=0)


def inspect_picture_dimensions(pic: ET.Element) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for child_name, attrs in (
        ("orgSz", ("width", "height")),
        ("curSz", ("width", "height")),
        ("sz", ("width", "height")),
    ):
        value = max_int_attr(child_by_name(pic, child_name), attrs)
        if value > MAX_DISPLAY_HWP_UNIT:
            errors.append(f"{child_name} has suspiciously large HWP unit value {value}")
    img_dim_value = max_int_attr(child_by_name(pic, "imgDim"), ("dimwidth", "dimheight"))
    if img_dim_value > MAX_SOURCE_IMAGE_UNIT:
        errors.append(f"imgDim has suspiciously large source image unit value {img_dim_value}")
    img_clip_value = max_int_attr(child_by_name(pic, "imgClip"), ("left", "right", "top", "bottom"))
    if img_clip_value > MAX_SOURCE_IMAGE_UNIT:
        warnings.append(
            f"imgClip has suspiciously large source image unit value {img_clip_value}; Hancom Office may add this during save"
        )

    img_rect = child_by_name(pic, "imgRect")
    if img_rect is not None:
        for point in list(img_rect):
            value = max_int_attr(point, ("x", "y"))
            if value > MAX_DISPLAY_HWP_UNIT:
                errors.append(f"imgRect has suspiciously large HWP unit value {value}")
                break

    rendering = child_by_name(pic, "renderingInfo")
    if rendering is not None:
        sca = child_by_name(rendering, "scaMatrix")
        if sca is not None and (sca.get("e1") != "1" or sca.get("e5") != "1"):
            errors.append("scaMatrix is not identity; avoid pixel-to-HWP scaling for compatibility")
    return errors, warnings


def inspect_hwpx(path: Path) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    image_refs: list[str] = []
    picture_count = 0

    try:
        with zipfile.ZipFile(path, "r") as zf:
            names = zf.namelist()
            name_set = set(names)
            if "Contents/content.hpf" not in name_set:
                errors.append("Missing Contents/content.hpf")
                return {"path": str(path), "ok": False, "errors": errors, "warnings": warnings}

            manifest = image_manifest_items(zf)

            for section in section_paths(names):
                root = ET.fromstring(zf.read(section))
                parent_map = {child: parent for parent in root.iter() for child in list(parent)}
                paragraph_ids: list[str] = []
                for paragraph in root.findall(".//hp:p", NS):
                    paragraph_id = paragraph.get("id")
                    if paragraph_id:
                        paragraph_ids.append(paragraph_id)
                duplicate_ids = sorted({value for value in paragraph_ids if paragraph_ids.count(value) > 1})
                if duplicate_ids:
                    warnings.append(f"{section} has repeated hp:p id values: {', '.join(duplicate_ids[:5])}")
                for img in root.findall(".//hc:img", NS):
                    ref = img.get("binaryItemIDRef", "")
                    if ref:
                        image_refs.append(ref)
                for pic in root.findall(".//hp:pic", NS):
                    picture_count += 1
                    dimension_errors, dimension_warnings = inspect_picture_dimensions(pic)
                    errors.extend(f"picture {picture_count}: {msg}" for msg in dimension_errors)
                    warnings.extend(f"picture {picture_count}: {msg}" for msg in dimension_warnings)
                    run = parent_map.get(pic)
                    if run is not None and not any(local_name(child.tag) == "t" for child in list(run)):
                        errors.append(f"picture {picture_count}: missing sibling hp:t in hp:run")

            unique_refs = sorted(set(image_refs))
            for ref in unique_refs:
                item = manifest.get(ref)
                if item is None:
                    errors.append(f"Image ref {ref!r} has no content.hpf manifest item")
                    continue
                href = item.get("href", "")
                media_type = item.get("media-type", "")
                if not href:
                    errors.append(f"Image ref {ref!r} has empty manifest href")
                    continue
                if href not in name_set:
                    errors.append(f"Image ref {ref!r} points to missing package entry {href!r}")
                    continue
                if media_type not in ALLOWED_IMAGE_TYPES:
                    errors.append(f"Image ref {ref!r} should be image/jpeg, image/png, or image/bmp, got {media_type!r}")
                elif not href.lower().endswith(ALLOWED_IMAGE_TYPES[media_type]):
                    errors.append(f"Image ref {ref!r} has media type {media_type!r} but points to {href!r}")
                data = zf.read(href)
                try:
                    with Image.open(io.BytesIO(data)) as img:
                        image_format = img.format
                        image_size = img.size
                        is_progressive = bool(img.info.get("progressive") or img.info.get("progression"))
                        img.verify()
                    expected_format = {"image/jpeg": "JPEG", "image/png": "PNG", "image/bmp": "BMP"}[media_type]
                    if image_format != expected_format:
                        errors.append(f"Image ref {ref!r} is {image_format}, expected {expected_format}")
                    if image_format == "JPEG" and is_progressive:
                        errors.append(f"Image ref {ref!r} is progressive JPEG; use baseline JPEG")
                    if max(image_size) > MAX_EMBEDDED_PIXEL_EDGE:
                        errors.append(
                            f"Image ref {ref!r} has edge {max(image_size)} px; keep embedded images <= {MAX_EMBEDDED_PIXEL_EDGE}px"
                        )
                    if image_size[0] < 1 or image_size[1] < 1:
                        errors.append(f"Image ref {ref!r} has invalid size {image_size}")
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"Image ref {ref!r} cannot be decoded: {exc}")

            bindata_images = sorted(
                name
                for name in names
                if name.startswith("BinData/") and name.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))
            )
            referenced_hrefs = {manifest[ref].get("href") for ref in unique_refs if ref in manifest}
            for href in bindata_images:
                if href not in referenced_hrefs:
                    warnings.append(f"Unreferenced BinData image: {href}")
                if zf.getinfo(href).compress_type != zipfile.ZIP_STORED:
                    warnings.append(f"{href} is ZIP-compressed; Hancom Office usually stores BinData images uncompressed")

    except zipfile.BadZipFile as exc:
        errors.append(f"Invalid HWPX ZIP container: {exc}")
    except ET.ParseError as exc:
        errors.append(f"XML parse error: {exc}")

    return {
        "path": str(path),
        "ok": not errors,
        "picture_count": picture_count,
        "image_ref_count": len(image_refs),
        "unique_image_ref_count": len(set(image_refs)),
        "errors": errors,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Generated .hwpx file to validate.")
    args = parser.parse_args(argv)

    result = inspect_hwpx(Path(args.input))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
