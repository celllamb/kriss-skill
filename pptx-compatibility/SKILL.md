---
name: pptx-compatibility
description: Diagnose and repair broken or PowerPoint-incompatible .pptx files. Use when a PowerPoint file cannot be opened, PowerPoint says it needs repair, a generated or edited .pptx opens in LibreOffice or python-pptx but not Microsoft PowerPoint, OOXML/OPC relationships are broken, or slide masters, slide layouts, content types, charts, media, notes, hyperlinks, or embedded object references may be invalid.
---

# PPTX Compatibility

## Core Principle

A `.pptx` file is a ZIP-based OPC/OOXML package. Passing ZIP/XML validation does not guarantee Microsoft PowerPoint compatibility. PowerPoint is strict about the presentation relationship graph, especially slideMaster and slideLayout relationships. It is also stricter than LibreOffice and `python-pptx` about some slide XML details such as per-slide shape ID uniqueness and DrawingML paragraph end properties. If minimal XML/package repair is not enough, rebuild a clean presentation graph.

Never modify the original file in place. Always work on a copy, write repaired output to a new path, produce a diagnostic report, and validate the result.

## Do Not / Negative Instructions

- Do not modify the original `.pptx` in place. Copy it first and write every repair, rebuild, or PowerPoint roundtrip to a new file.
- Do not assume a file is PowerPoint-compatible just because ZIP validation, XML parsing, `python-pptx`, or LibreOffice conversion succeeds.
- Do not treat external hyperlinks as missing package parts. Only internal OPC relationship targets should be checked for package existence.
- Do not remove slide relationships during minimal repair unless the slide XML itself is missing or unreadable. Escalate to structural repair or rebuild instead.
- Do not remove required presentation graph relationships, slide masters, slide layouts, or live slide targets as a quick fix for dangling references.
- Do not use Microsoft PowerPoint COM automation as the only validation step. It is optional, Windows-only, and can hang behind modal repair or security dialogs.
- Do not use tiny hand-made PPTX ZIP fixtures as proof of real PowerPoint compatibility. Use PowerPoint-authored or full-writer-authored decks for roundtrip demos.
- Do not promise exact visual fidelity after rebuild. Rebuild prioritizes openability and readable content.

## Use The Doctor CLI

Prefer the bundled CLI for end-to-end diagnosis and repair:

```bash
python scripts/pptx_doctor.py input.pptx --out-dir repaired/
```

Useful options:

```bash
python scripts/pptx_doctor.py input.pptx --out-dir repaired/ --repair-level auto --report both
python scripts/pptx_doctor.py input.pptx --out-dir repaired/ --repair-level minimal
python scripts/pptx_doctor.py input.pptx --out-dir repaired/ --repair-level structural --strict
python scripts/pptx_doctor.py input.pptx --out-dir repaired/ --repair-level rebuild --no-libreoffice
```

The CLI writes:

- `<stem>_diagnostic_report.md`
- `<stem>_diagnostic_report.json`
- `<stem>_repaired.pptx` for package or structural repairs
- `<stem>_rebuilt.pptx` when a full rebuild was required

## Examples

### Example 1: PowerPoint Repair Dialog

User input:

```text
PowerPoint says this deck has unreadable content. Diagnose and repair it.
```

Use:

```bash
python scripts/pptx_doctor.py damaged.pptx --out-dir repaired --repair-level auto --report both
```

Expected output:

- A diagnostic report listing critical issues such as missing slide layouts, missing slide masters, duplicate shape IDs, or missing `a:endParaRPr`.
- A new `damaged_repaired.pptx` when minimal or structural repair succeeds.
- A new `damaged_rebuilt.pptx` when the package is too inconsistent and rebuild is required.
- A validation section showing ZIP status, remaining critical issues, slide count, optional `python-pptx`, optional LibreOffice, and optional PowerPoint roundtrip findings when run separately.

### Example 2: LibreOffice Opens But PowerPoint Fails

User input:

```text
This generated PPTX converts to PDF with LibreOffice, but Microsoft PowerPoint repairs it and removes some slides.
```

Use `inspect_pptx.py` first when the user only wants a diagnosis:

```bash
python scripts/inspect_pptx.py generated.pptx --json
```

Look especially for:

- `duplicate_shape_id`
- `missing_end_para_rpr`
- `dangling_relationship`
- `missing_slide_layout_relationship`
- `missing_layout_slide_master_relationship`
- `notes_slide_missing_backlink`

Then run `pptx_doctor.py` with `--repair-level auto` if the user wants a fixed file.

## Repair Workflow

1. Inspect the package first. Check ZIP health, required OPC files, XML parseability, content types, relationships, the presentation graph, and PowerPoint-strict slide XML.
2. Attempt minimal package repair when the file is mostly valid. Remove safe dangling content-type overrides and optional dangling relationships, repair duplicate slide shape IDs, add missing `a:endParaRPr` paragraph endings, then repackage cleanly.
3. Attempt structural repair when the presentation graph is broken. Reconnect slides to valid layouts, layouts to valid masters, and presentation master references to valid masters when possible.
4. Rebuild when minimal and structural repair are not enough. Use `python-pptx` to create a new presentation with a clean default master/layout structure and salvage readable slide content.
5. Validate the repaired or rebuilt output. Re-run inspection, confirm no critical issues remain, confirm slide count, try `python-pptx` if available, and optionally try LibreOffice headless conversion when available.

## Script Roles

- `scripts/inspect_pptx.py`: Read-only inspection. Returns a structured diagnostic object that can be serialized to JSON.
- `scripts/repair_pptx_package.py`: Level 1 minimal repair and Level 2 structural graph repair. Never edits the source file in place.
- `scripts/rebuild_pptx.py`: Level 3 rebuild with `python-pptx`. Preserves slide order and readable content where possible.
- `scripts/validate_repaired_pptx.py`: Output validation without requiring Microsoft PowerPoint automation.
- `scripts/powerpoint_roundtrip.ps1`: Optional Windows-only Microsoft PowerPoint COM validation. Use only when PowerPoint is installed and the user wants a real PowerPoint open/save/reopen check.
- `scripts/pptx_doctor.py`: Main orchestration CLI.

## Severity Guidance

- `critical`: PowerPoint is likely to reject or repair the file. Examples include missing required package files, unreadable core XML, dangling slide relationships, missing slideLayout links, missing slideMaster links, duplicate `p:cNvPr id` values inside one slide, and slide paragraphs missing trailing `a:endParaRPr`.
- `warning`: The file may open but content may be missing. Examples include missing notes slides, charts, images, media, comments, thumbnails, themes, or embedded objects.
- `info`: Harmless or optional inconsistencies.

External hyperlinks are not package parts. Do not report external hyperlink targets as missing files.

## PowerPoint-Strict Checks

Run these checks whenever a generated or edited deck opens in LibreOffice or `python-pptx` but fails or repairs in Microsoft PowerPoint:

- Every `p:cNvPr id` must be unique within its slide XML. When repairing, assign duplicate shapes new IDs above the current maximum ID in that slide.
- Every DrawingML paragraph `a:p` in slide XML should end with `a:endParaRPr`. Although the element can appear optional in OOXML references, PowerPoint may treat paragraphs without default end run properties as unreadable content.
- Notes slide relationships are optional, but if a slide links to an existing notes slide, the notes slide should link back to the owning slide.
- `python-pptx` access and LibreOffice PDF conversion are useful smoke tests, but they are lenient and do not prove Microsoft PowerPoint compatibility.

When hand-editing or generating new slides, compare element counts against a known-good slide from the same deck. Large asymmetric differences, such as many `a:p` elements but zero `a:endParaRPr` elements, are strong clues.

## Optional PowerPoint Roundtrip

When Microsoft PowerPoint is installed on Windows and the user needs the strongest local validation, run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/powerpoint_roundtrip.ps1 repaired.pptx -Json
```

This opens the file with PowerPoint COM, saves a separate `<stem>_powerpoint_roundtrip.pptx`, reopens that output, and reports JSON. It can still hang if PowerPoint shows a modal repair or security dialog, so run it with a command timeout and never use it as the only validation step.

For PowerPoint roundtrip demos, prefer a deck originally authored by PowerPoint or another full PPTX writer. Tiny hand-made ZIP fixtures are useful for unit tests, but they may omit subtle master, theme, or layout XML that PowerPoint expects even after the targeted defect is repaired.

## Composability

Use this skill before or after other slide-generation work:

- With the `presentations` skill: generate or edit a `.pptx` there, then run this skill to inspect PowerPoint compatibility. If this skill rebuilds a file, return to `presentations` for visual QA, rendering, or layout polish.
- With PowerPoint COM automation: use `scripts/powerpoint_roundtrip.ps1` only as an optional final check on Windows systems with Microsoft PowerPoint installed.
- With LibreOffice: use headless PDF conversion as a smoke test, not a compatibility proof.
- With `python-pptx`: use it for rebuilds and openability checks, but do not treat it as a strict PowerPoint validator.
- With manual OOXML edits: run `inspect_pptx.py` before editing, edit the smallest package region possible, then run `pptx_doctor.py` or `validate_repaired_pptx.py` afterward.

Order matters: create or edit slides first, run PPTX compatibility checks second, perform minimal/structural repair third, rebuild only if needed, and use visual QA last.

## Rebuild Limitations

Full rebuild intentionally prioritizes openability and readable content over exact fidelity. Warn the user that animations, transitions, comments, custom layouts, notes, OLE objects, exact positioning, and some charts may not be preserved. Rebuild is the right fallback when a package passes basic ZIP/XML checks but Microsoft PowerPoint still rejects the slide master/layout relationship graph.
