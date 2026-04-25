---
name: kriss-trip-report
description: Create Korea Research Institute of Standards and Science (KRISS) 국외출장보고서 from meeting, conference, dispatched-research, agenda, recording/transcript, presentation, itinerary, boarding-pass, immigration-certificate, and trip-photo materials; use when drafting or generating HWPX reports with the KRISS overseas trip report template.
---

# KRISS Trip Report

## Overview

Use this skill to organize source materials and draft a KRISS 국외출장보고서 in the bundled HWPX template. It supports meeting-type, overseas-conference-type, and dispatched-research-type trips, including agenda-driven technical meetings.

## Always Read

Before drafting, read:

- `references/privacy.md` for required masking rules.
- `references/template-structure.md` for the HWPX report sections.
- `references/source-materials.md` for source priority and extraction rules.
- `references/report-types.md` for the selected trip type.
- `references/hwpx-hancom-compat-notes.md` before generating or editing image-bearing HWPX files.
- `references/recordings.md` when meeting recordings, audio files, transcripts, or recording ZIP archives are provided.

## Workflow

1. Build a source inventory.
   - Use `scripts/build_dossier.py` on the provided folder, ZIP, PDFs, and evidence files.
   - When recordings or recording ZIP archives are provided, run `scripts/prepare_recordings.py` to create a recording manifest and link matching transcript files when present.
   - Transcription conversion is intentionally out of scope for this skill. If audio must be transcribed, use a separate transcription skill/tool first, place transcript files next to the recordings or in a transcript folder, then rerun `prepare_recordings.py` so this skill can link and use the transcript files.
   - Treat recordings as source material only after a reliable transcript exists; if no transcript is available, ask for one or use other written sources first.
   - Keep scanned immigration certificates or boarding passes out of final output until the three protected identifiers have been checked.

2. Determine the trip type.
   - `meeting`: agenda, meeting material, minutes, recordings, and participant presentations drive the report.
   - `conference`: conference program, accepted abstract, presentation, poster, and session notes drive the report.
   - `dispatched-research`: host institution, research plan, daily work log, experiment notes, and outputs drive the report.

3. Fill `I. 출장개요`.
   - Purpose: use `"[회의명] 참석"` for meeting-type trips and `"[학회명] 참석"` for conference-type trips.
   - Period: derive from boarding pass, ticket, or immigration certificate; use departure and entry dates as the primary basis.
   - Countries and host institutions: write one encompassing country/city/institution line rather than listing every room, day, or sub-venue.
   - Traveler information: request it from the user or a local traveler profile; do not store private user data in this shared skill.
   - Interviewee information: infer from presentation material, agenda, participant list, email signatures, or transcript speakers. Do not invent contacts or meeting dates.

4. Draft `II. 출장내용`.
   - For meeting-type trips, use agenda items as the top-level units under `주요 활동 내용`.
   - Write in Korean bullet style (`개조식`) throughout. Avoid long narrative paragraphs in the final report body.
   - End final report bullets in concise Korean nominal/bullet-style endings, such as `필요함`, `확인`, `논의`, `제시`, `검토 필요`, or `반영 필요`. Avoid prose sentence endings such as `필요하다`, `확인하였다`, `논의되었다`, `제시되었다`, or `검토할 필요가 있다`.
   - For each agenda, write enough self-contained detail for a reader to understand the meeting content without opening the source files. For major agenda items, target roughly one HWPX page per agenda, usually 6-10 substantive `      - ...` sub-bullets plus one optional supporting image.
   - Cover updates, discussions/agreements, and follow-up plans, but do not label those categories explicitly in the final text. Write them as plain `      - ...` sub-bullets.
   - Do not include drafting trace text such as `확인 필요`, `자료상`, `입력자료`, `첨부자료`, `제공된 자료`, `녹취록 확인`, or `회의록 확인` in the final report body. Resolve the point from sources, ask the user, or leave the appropriate field blank.
   - If a representative slide, meeting photo, or figure exists for an agenda, insert at most one image immediately after that agenda's bullets. Choose one image that best represents that agenda's topic, result, KRISS contribution, decision, or timeline. Do not attach multiple slides to one agenda; omit the image when no clearly representative slide exists. The image supplements the written summary and does not replace it.

5. Draft `III. 시사점 및 특이사항`.
   - Keep this section limited to the meeting content itself.
   - Write `시사점` in readable Korean bullet style. Prefer several short bullets or indented sub-bullets over long paragraph-like bullets.
   - Leave `건의사항` blank or ask the user for content; do not invent recommendations.
   - Write `특이사항` in readable Korean bullet style around issues that were discussed as agenda-level points of contention, risk, disagreement, or decision pressure.
   - In `특이사항`, write each issue group as a numbered item such as `1. [쟁점명]`, then write its details as indented `      - ...` sub-bullets. Do not use `- [쟁점명]` for an issue group heading because it is visually indistinguishable from the detail bullets.
   - Keep gift receipt and gift declaration checkbox lines unchanged unless the user explicitly provides final checked values.

6. Draft `IV. 기타자료`.
   - In `수집자료`, summarize only meeting/report source materials by type, such as agenda, minutes, presentations, photos, transcripts, and institutional materials. Do not include travel evidence documents in `수집자료`.
   - Treat airline tickets and boarding passes as travel-entry/departure proof materials, not as collected meeting materials.
   - When an airline ticket or boarding pass is available, include it under `출입국 입증 자료` together with any immigration fact certificate unless the user explicitly asks to attach only one proof type.
   - Insert the available boarding pass/airline-ticket copy and/or immigration fact certificate image as evidence. Mask 주민등록번호, 여권번호, and 외국인등록번호 before insertion.
   - Render evidence as full-page images when possible. Put each evidence category on its own page so the contents remain readable.

7. Generate or update HWPX.
   - Use the template at `assets/kriss-overseas-trip-report-template.hwpx`.
   - Use `scripts/render_pdf_pages.py` to render selected presentation, boarding-pass, or certificate PDF pages to PNG when Ghostscript is available. Keep the default 200 dpi or higher for evidence pages that must remain readable after insertion.
   - Use `scripts/draft_hwpx_from_markdown.py` for text drafts and drafts with rendered slide/evidence images.
   - The HWPX draft script normalizes inserted images to RGB PNG before packaging, caps embedded image edges, and stores `BinData/` entries without ZIP recompression. This mirrors Hancom Office `InsertPicture` output more closely than hand-authored JPEG/BMP variants, which can appear as broken picture objects in some HWPX viewers.
   - Do not encode source pixel dimensions directly as display dimensions. HWP-compatible picture XML uses page-sized HWP units for `orgSz`, `imgRect`, and `sz`, `curSz` set to `0`, and original-image crop units for `imgClip`/`imgDim`.
   - The scripts auto-detect bundled Codex Python packages and can install missing Python dependencies (`pypdf`, `Pillow`, and `PyMuPDF` fallback for PDF rendering) when needed. Set `KRISS_TRIP_REPORT_NO_AUTO_INSTALL=1` to disable automatic installation and receive the exact `pip install` command instead.
   - Validate generated HWPX with the HWPX editing/validation workflow available in the environment.
   - Run `scripts/validate_hwpx_images.py` on every generated report that contains images. It must pass before final delivery.
   - When Hancom Office is available, perform a round-trip check: keep a byte-for-byte copy of the generated HWPX, open it in Hancom Office, save as a separate HWPX, then run `scripts/compare_hwpx_packages.py before.hwpx after.hwpx`. Hancom Office may rewrite `content.hpf`, `header.xml`, `section0.xml`, `Preview/*`, and container metadata; accept that only when `image_payloads_unchanged` and `only_hancom_normalized_entries` are true. If image payloads are changed or dropped, treat the generated file as not deliverable and revise the image XML/encoding.
   - For slide/image insertion, render selected slides separately and insert only after privacy and sensitivity review. Check that each inserted image has a matching PNG file in `BinData`, `content.hpf` manifest item, and `hc:img binaryItemIDRef` reference before final delivery.

## Missing Information

Ask the user only for facts that cannot be derived from sources, especially:

- Traveler name, affiliation, title, and contact.
- Gift receipt/declaration status.
- Confirmation when evidence dates conflict with itinerary dates.
- Masked copies of evidence when protected identifiers appear and automatic masking is not reliable.
