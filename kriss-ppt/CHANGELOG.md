# Stable distribution: 1.1.0 — 2026-10-15

- Promote the cumulative `1.1.0-rc3+ophthagen.1` package to the stable
  `1.1.0` distribution, as requested after external verification by the maintainer.
- Retain the original HTML source-of-truth workflow, editable native PPTX
  conversion, speaker-note and hyperlink preservation, and evidence-based
  HTML/native/render QA gates. No layout redesign or relaxed thresholds.
- Refresh installation integrity manifest and user-facing release designation.
- Store the large canonical HTML as byte-preserving gzip in Git; installation
  verification restores its exact bytes, failing on any SHA-256 discrepancy.
- Preserve historical RC test results and documented unsupported patterns as
  historical evidence; stable packaging does not automatically certify every
  pattern or third-party PowerPoint installation. External validation records
  were not supplied within this package.

# 1.1.0-rc3+ophthagen.1 — cumulative local update

- Check content-image bytes, crop, geometry, native effects and unique mapping,
  not only object presence and pixel similarity.
- Prevent legacy density height rules from overriding explicit size policies.
- Keep unmodified inline declarations unchanged during adaptive reset; preserve
  subpixel percentage precision across ordinary and export activation.
- Preserve plain-text note newlines and escape note markup in the two bundled
  popup implementations.
- No scientific-content routing, slide-specific exception, new template artwork,
  PPTX-side layout correction or relaxed pixel-parity threshold.

# 1.1.0-rc3+aav.1 — source-bound speaker notes

- Includes the preceding `1.1.0-rc3+gpn.1` fixes.
- Captures final DOM notes independently and writes that exact text to native notes.
- Fails native QA for missing/changed notes even with updated PPTX file hashes.
- Includes exact notes comparison in delivered-HTML reread approval.
- Preserves existing reference HTML/artwork and all pixel thresholds.
- Installation candidate only; existing all-pattern and PowerPoint app limits remain.

# 1.1.0-rc3+gpn.1 — source hyperlink correction

- Retain external text links on native rich-text runs; compare the complete
  source anchor text, resolved URL and actual PPTX relationships.
- Explicitly reject unsupported link semantics rather than silently approving
  matching screenshots.
- Prevent links/interactive controls from also advancing canonical/approved
  HTML decks. No reference layout or image bytes were changed.
- Select measured run text color instead of the theme hyperlink blue; validate
  explicit color and underline alongside the native target.
- Preserve prior rc3 features and unchanged visual comparison tolerances.

# 1.1.0-rc3 — 2026-10-05

- Integrate post-rc2 fixes for HTML closing-tag detection, `pre` blank-line/run
  preservation, and positioned badges inside owner padding. Synchronize bundled
  adaptive runtimes without changing reference artwork, layout or typography.
- Read execution identity from `VERSION` in export, build (including blocked
  inputs), and environment checks; bind original VERSION bytes in evidence.
- Add dependency-free installed-file integrity verification; reject missing,
  modified, untracked or unsafe manifest entries and version inconsistencies.
- Publish installation-only usage guidance. Development tests, CI and execution
  artifacts are external, not prerequisites or contents of the installation.
- Re-test this candidate and document actual outcomes separately from historical
  rc2 and post-rc2 runs. Unsupported vertical writing and render differences are
  still explicit blockers. No parity thresholds or PPTX geometry are relaxed.

# 1.1.0-rc2 — 2026-10-05

- Restore original standard artwork in H02–H06 and the V10 master; keep V10 dark emphasis inside the body. Canonical reference HTML remains byte-identical to rc1.
- Add explicit, idempotent legacy chrome migration and read-only original-image/placement/artwork checks. Embed and verify original template JPEG bytes in native PPTX.
- Bind native owner order to Chromium paint-layer/tree measurements; fix text behind opaque variant panels.
- Add editable simple CSS polygons/border wedges and exact affine SVG stroke geometry. Distinguish editable vector strokes from endpoint-attachable connectors.
- Read CSS counters and language-sensitive uppercase/lowercase from actual browser layout text.
- Extend unit, integration, and mutation regression tests. Keep existing pixel thresholds unchanged. Consult release-status.md for measured results and remaining blockers.

# Changelog

## 1.1.0-rc1

- Independent source inventory/native coverage closes silent SVG/replaced-element loss.
- Shared static validator, overflow/resource blockers and immediate manifest invalidation.
- Unified ordinary-navigation/export adaptive settle; exact known legacy runtime migration.
- Byte-preserving local assets; captured image bytes are reused by native PPTX.
- Basic SVG primitives, actual list markers, mixed paragraphs, solid curved borders,
  asymmetric/elliptical CSS corners and restricted flat-step conic native paths.
- Final HTML reopen verification of geometry, computed style and unchanged global/local pixel limits.
- Hashed source/model/assets/PPTX evidence with relocatable references; environment doctor.
- Development-only positive/negative fixtures, integrity tests and reference-audit tooling.
- Design resources retained without layout/font redesign; remaining reference failures are
  recorded rather than certified. This is not a stable all-pattern release.
