---
name: edit-hwpx-docs
description: Read, inspect, extract text from, unpack, modify, repack, and validate Hancom HWPX (.hwpx) documents. Use when Codex needs to work with HWPX/OWPML files, summarize or extract document text, append paragraphs, replace placeholders or simple text runs, inspect package structure, or safely edit Contents/section*.xml while preserving the ZIP package.
---

# Edit HWPX Docs

## Overview

Use this skill for Hancom HWPX documents. Treat `.hwpx` files as ZIP packages containing OWPML XML, with document text usually stored in `Contents/section*.xml` as `hp:p` paragraphs, `hp:run` runs, and `hp:t` text nodes.

Prefer the bundled script for routine operations:

```bash
python scripts/hwpx_tool.py validate document.hwpx
python scripts/hwpx_tool.py extract document.hwpx --output text.txt
python scripts/hwpx_tool.py append template.hwpx output.hwpx --text-file addition.txt
python scripts/hwpx_tool.py replace template.hwpx output.hwpx --old "{{NAME}}" --new "Kim"
python scripts/hwpx_tool.py unpack document.hwpx unpacked/
python scripts/hwpx_tool.py pack unpacked/ output.hwpx
```

Read `references/hwpx-format.md` before manual XML edits, table edits, image edits, section reordering, or any change more complex than appending paragraphs or replacing text inside existing `hp:t` nodes.

## Workflow

1. Validate the input with `validate`.
2. Extract text with `extract` when the user asks to read, summarize, translate, compare, or analyze the document.
3. Use `replace` for template placeholders that are contained inside single `hp:t` nodes.
4. Use `append` for adding plain paragraphs to an existing document or template.
5. Use `unpack`, edit XML carefully, then `pack` only when scripted operations are insufficient.
6. Re-run `validate` on every produced `.hwpx`.
7. When possible, ask the user to open the result in Hancom Office or an HWPX-compatible viewer for final layout validation.

## Safe Editing Rules

- Preserve the original `.hwpx`; write edits to a new output path.
- Keep `mimetype` first and stored when repacking; the script handles this.
- Preserve namespaces and existing XML prefixes. Do not create namespace-free HWPX tags.
- Do not put newline characters inside `hp:t`. Use separate `hp:p` paragraphs for new lines.
- Avoid editing `header.xml` unless the change requires new styles, fonts, numbering, or layout definitions.
- Prefer copying an existing paragraph's paragraph/style attributes when adding text.
- Treat tables, shapes, fields, tracked changes, footnotes, comments, equations, and images as advanced edits. Inspect the package first and update related relationships, binary parts, and references together.
- Do not attempt direct `.hwp` binary editing with this skill. Convert `.hwp` to `.hwpx` first using a trusted local tool, then work on the `.hwpx`.

## Manual XML Fallback

When the script cannot express the requested edit:

1. Run `unpack`.
2. Find section files with `inspect` or by listing `Contents/section*.xml`.
3. Edit the smallest possible XML region.
4. Keep `hp:secPr` in place, usually in the first paragraph of a section.
5. Preserve references such as `paraPrIDRef`, `styleIDRef`, and `charPrIDRef` unless intentionally changing formatting.
6. Run `pack`, then `validate`.

For text extraction, collect `hp:t` text in paragraph order. For writing body text, add `hp:p` elements with `hp:run` and `hp:t`, using nearby paragraph/run attributes as templates.

## Validation

Use HWPX document validation first:

```bash
python scripts/hwpx_tool.py validate output.hwpx
```

Validation checks the ZIP container, expected package files, and XML parseability of section files. It does not prove visual fidelity. Complex layout edits still require opening the result in Hancom Office or another HWPX-compatible viewer.

Use the self-contained skill validator after editing this skill:

```bash
python scripts/validate_skill.py .
```

The validator uses only the Python standard library. This skill has no runtime dependency on other skills, `PyYAML`, or external Python packages.
