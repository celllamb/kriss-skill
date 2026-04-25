# Source Materials

Use source materials to build a trip dossier before drafting the report.

## Source Priority

For `출장개요`:

1. Immigration certificate, boarding pass, or airline ticket for departure/entry dates.
2. Agenda, invitation, itinerary, and meeting announcement for meeting name, venue, country, and institution.
3. Presentation cover slides and participant lists for host organizations and interviewees.
4. User-provided traveler profile for traveler name, affiliation, title, and contact.

For `출장내용`:

1. Agenda or program for top-level organization.
2. Meeting materials, presentations, and minutes for updates, discussions, agreements, and follow-up plans.
3. Recordings only after a reliable transcript exists. If recordings are provided as a ZIP archive, prepare them with `scripts/prepare_recordings.py` first; use a separate transcription skill/tool when transcript creation is needed.
4. Photos as supporting evidence for attendance or visit context, not as the primary source for technical conclusions.

## Material Types

- Agenda/program: extract meeting name, dates, venue, agenda items, speakers, and expected outputs.
- Presentations: extract title, authors, institutions, key technical updates, conclusions, proposed next steps, and candidate slide pages.
- Minutes: extract decisions, actions, owners, dates, and unresolved issues.
- Recordings: inventory audio files and recording ZIP archives, then use linked transcript files to map statements to agenda items. Transcript creation itself belongs to a separate transcription skill/tool. Do not draft unsupported technical conclusions from untranscribed audio.
- Tickets/boarding passes/immigration certificates: use for period and `출입국 입증 자료`; check privacy rules before attachment. Do not list these travel evidence files under `수집자료`.
- Photos: use to identify site, participants, or event context when useful; avoid identifying people unless needed for the report.

## Final Report Hygiene

- Use source materials to write the report, but do not refer to the provided file set as an external dependency in the final body.
- Do not write statements such as `provided materials show`, `source file indicates`, `check transcript`, or `meeting minutes needed` in the final report.
- Attach rendered evidence images only after visual privacy review. Mask only 주민등록번호, 여권번호, and 외국인등록번호 by default.
- Use a full-page rendering for evidence documents so all visible content, seals, dates, barcodes, and verification blocks remain readable. Do not use cropped screenshots for final evidence pages.
- If an airline ticket or boarding pass is available, attach it as travel proof together with the immigration fact certificate unless the user requests a single proof type.

## Conflicts

When dates or institutions conflict:

- Prefer immigration/boarding evidence for travel period.
- Prefer official agenda or invitation for meeting dates and venue.
- Prefer presentation title slides for presenter names and institutions.
- Ask the user before choosing between conflicting evidence.
