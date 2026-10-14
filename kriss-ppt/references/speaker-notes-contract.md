# Speaker notes: source and native fidelity

`data-notes` is required plain-text source content, not a comment exempt from QA.
The settled DOM inventory records the attribute presence and exact decoded string
in `speakerNotes` (`kriss-speaker-notes-v1`). Do not infer notes from slide text,
regenerate source citations, discard qualifiers or trim blank lines.

The exporter writes the captured text into the native notes body. A fresh HTML
page must reproduce the same source notes during ordinary activation. Native QA
reads the existing notes relationship and body without creating a missing part,
and compares exact text with the hash-bound source inventory. Missing source,
missing part/body, changed text/whitespace and unreadable relationships fail.
Hashes and character counts are reported instead of copying private note text
into error messages. Hashes are consistency checks, not digital signatures.

Existing evidence without a notes-source contract must be recaptured with the
current skill. Its visible slide pixels alone cannot certify speaker notes.
Notes formatting, timed speaker-view UI, printed notes layout and PowerPoint
application behavior are not visually certified by this plain-text contract.

There are no subject, guideline, slide-number or fixed-phrase exceptions. All
notes content is treated identically. Development tests and mutation evidence
are maintained outside the installation package.

## Browser notes window

`data-notes` is plain text, not HTML. Bundled canonical/approved note windows escape
HTML-significant characters and use `white-space: pre-wrap`, preserving newlines
and blank lines without executing note markup. This does not sanitize arbitrary
user JavaScript or authorize running untrusted HTML outside an isolated browser.
