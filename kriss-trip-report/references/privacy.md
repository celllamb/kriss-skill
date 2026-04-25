# Privacy Rules

Final reports and attached evidence must not expose these three identifiers:

- 주민등록번호
- 여권번호
- 외국인등록번호

Apply these rules to immigration certificates, boarding passes, airline tickets, passport copies, scanned images, OCR text, transcripts, and any copied source material.

## Handling

1. If one of the three identifiers appears in extracted text, mask it before using the text in notes, dossier files, or reports.
2. If one of the three identifiers appears in an image or scanned PDF and the exact location is clear, create or request a masked copy before attaching it.
3. If the source is scanned and text extraction returns nothing, do not assume it is safe. Ask the user for a masked copy or inspect the rendered image before attachment.
4. Do not mask other information unless the user requests it. Airline reservation numbers, ticket numbers, QR codes, barcodes, emails, phone numbers, and names are not part of this skill's default masking rule.
5. Never recreate, infer, or restate a protected identifier in the body text.

## Text Masking Patterns

Use conservative masking for:

- 13-digit Korean resident/foreign registration patterns such as `######-#######`.
- Label-based passport patterns such as `passport no`, `passport number`, `여권번호`, or `여권 번호` followed by an alphanumeric token.

Pattern-based masking is a backstop, not proof. Evidence images still require visual review before final attachment.

