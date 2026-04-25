# HWPX Format Notes

Use this reference when an HWPX edit requires manual XML work or when a generated file fails validation.

## Package Map

HWPX is an OWPML package stored as a ZIP archive. Common entries:

- `mimetype`: format signature. Keep first in the ZIP and uncompressed when repacking.
- `version.xml`: OWPML and producer version data.
- `settings.xml`: application settings such as caret position.
- `META-INF/`: container and manifest files.
- `Contents/content.hpf`: package metadata, manifest, and spine.
- `Contents/header.xml`: document-wide mappings and settings such as fonts, styles, paragraph properties, character properties, numbering, borders, and compatibility data.
- `Contents/section0.xml`, `Contents/section1.xml`, ...: section body XML. Most text operations happen here.
- `BinData/`: embedded binaries such as images and OLE data.
- `Preview/PrvText.txt`: optional preview text.

Hancom's technical article describes HWPX as ZIP-based XML and explains that section files contain body paragraphs. It also notes that `hp:p` separates paragraphs, `hp:run` represents character-style runs, and `hp:t` stores text.

## Text Extraction

Extract section files in document order, usually by numeric `Contents/sectionN.xml` order when the spine is not being inspected. For each `hp:p`, concatenate descendant `hp:t` values in run order. Represent each paragraph as a line.

Be aware that:

- Text can be split across multiple `hp:t` nodes because of style changes.
- Tables and shapes can contain nested paragraphs.
- Fields, footnotes, comments, and tracked changes may require extra interpretation.
- Preview text is not authoritative; extract from section XML instead.

## Writing Plain Text

For simple body additions:

1. Choose the target section, usually the last section.
2. Find an adjacent `hp:p`.
3. Copy safe paragraph attributes such as `paraPrIDRef`, `styleIDRef`, `pageBreak`, `columnBreak`, and `merged`.
4. Use a fresh `id` when the surrounding document uses paragraph ids.
5. Add one `hp:run` using a nearby run's `charPrIDRef`.
6. Add one `hp:t` with the paragraph text.
7. Use one `hp:p` per new line; do not embed newline characters inside `hp:t`.

For placeholder replacement, prefer placeholders that exist entirely inside a single `hp:t`. If a placeholder is split across runs, either edit the XML manually with care or simplify the template.

## Advanced Edits

Update related files together when changing:

- Styles or fonts: edit `Contents/header.xml` and referenced IDs.
- Images or binaries: add files under `BinData/` and update object references and manifests.
- Section order: update section files and the package spine in `Contents/content.hpf`.
- Tables: preserve nested paragraphs and cell/row structures.
- Footnotes, comments, fields, equations, and tracked changes: inspect the relevant XML parts before editing.

## Sources

- Hancom Help: HWPX is based on KS X 6101 OWPML and supports machine-readable extraction and processing. https://help.hancom.com/hoffice130_assistant/ko-KR/Hwp/file/open/open%28other%29.htm
- Hancom Tech: HWPX uses ZIP-based XML; `Contents/content.hpf`, `Contents/header.xml`, and `Contents/section*.xml` carry package metadata, formatting maps, and body contents. https://tech.hancom.com/hwpxformat/
