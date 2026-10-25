# v1.2.0-rc3 — local candidate, 2026-10-24

Status: **RELEASE CANDIDATE — not a production release.** Historical v1.1.0-rc3+ophthagen.1 source was the accessible base; earlier v1.2.0-rc2 archive was unavailable for byte-wise comparison. No claim of binary equivalence to earlier rc2.

New capability: retain full master artwork in authoring/delivered HTML, inherit original KRISS PPTX slide master or native layout picture in PPTX (family mapping cover 0, standard 10, divider 6), and deduplicate only matching layout images. Master SHA-256 and image SHA-256 are checked. Original KRISS master typography is verified from XML: 나눔바른고딕, 28 pt standard title, 40 pt cover title, body levels 28/24/20/18/18 pt.

Three-slide local diagnostic with original template background and cover logos:
- STATIC: PASS
- HTML/re-open: PASS
- NATIVE: PASS
- PARITY: FAIL

The diagnostic contains slides representing cover, standard and divider, not all bundled 53 canonical/variant patterns. No relaxation of global/local thresholds. S11/S12 vertical writing, unsupported SVG/CSS forms and Microsoft PowerPoint app compatibility remain unverified/blocked as described in the historical status below. Every deck must pass all gates before RELEASED.

---

# Local functional update: 1.1.0-rc3+ophthagen.1

Installation-only release candidate. This cumulative update retains AAV notes and
GPN hyperlink contracts, adds exact content-image correspondence, respects explicit
size policy in legacy density CSS, avoids CSSOM precision loss on unchanged
adaptive properties, and renders popup notes as escaped pre-wrapped plain text.

This update changes the shared runtime in all four references and only the density
selectors/notes-window code in canonical and approved references. Original image
bytes, other reference CSS and slide content remain unchanged. The historical
all-pattern results below are not certification of this new version.

Validation evidence is supplied separately from the installation. The local
source test run passed 134 unit contracts. Final unpacked-package and presentation
results must be read from their actual reports; they are not implied by this file.
Remaining S11/S12 vertical-writing, typography/renderer and Microsoft PowerPoint
application limitations remain. All per-deck gates are mandatory. Exact image
identity does not make a deck with failed pixel parity RELEASED.

---
The following sections preserve historical release scopes and test results; their
references to unchanged files/current counts refer to those historical builds.

# Local functional update: 1.1.0-rc3+aav.1

This installation includes the previous hyperlink fixes plus source-bound plain-text
speaker notes. Notes must survive native export and the delivered-HTML reread.
A missing or changed note cannot be approved based on identical visible pixels.
Validation of this local update is reported separately with the produced deck;
the historical rc3 53-slide table below is not a rerun for this version.
All-pattern typography/vertical writing and actual Microsoft PowerPoint validation
remain limited as described below. Each deck still requires all gates to pass.

# Local functional update: 1.1.0-rc3+gpn.1

This build incorporates a source/native hyperlink correction and reference
click-navigation guard. The prior rc3 all-pattern results below are historical
results, not reruns for this build. Whole-pattern typography limitations, S11/S12
unsupported vertical writing and Microsoft PowerPoint application validation
limits remain. Build status for each generated deck is decided by its actual
HTML/native/parity gates; source and native passes do not override parity failure.

# Release status — 1.1.0-rc3

**Installation-only release candidate; not an all-pattern certified stable release.**

## Actual rc3 validation — 2026-10-05

The following checks were executed against this candidate, not copied from rc2:

- Unit contracts: 72/72 (52 existing plus 20 package/version checks).
- Positive/negative integration fixtures: 41/41 expected outcomes,
  comprising 26 RELEASED, 12 BLOCKED and 3 BUILD_ERROR. Rejected inputs are not
  completed presentations.
- Integrity/navigation checks: 16/16. Native object/order/geometry
  mutation rejection with refreshed PPTX hashes: 4/4.
- Runtime-version paths: 4/4; successful, static-blocked and
  build-error records use VERSION. Missing VERSION invalidates old success.
  All 41 fixture manifests also bind the current version and VERSION-file hash.
- A four-slide Korean-content H01/H04/H06 short/long application was rebuilt and
  passed HTML, native, artwork, reopen and pixel gates (RELEASED).

These results apply to the exact test inputs and installed toolchain. They do not
make every use of a passing pattern automatically RELEASED. Final archive hashes,
unpacked-package validation and raw test evidence are supplied separately, not as
installation dependencies. Run `scripts/verify_installation.py` for installed-file
consistency and `scripts/build_release.py` for a particular deck's actual gates.

## Bundled references — new diagnostic-font execution

| Reference | Slides | Structural HTML | Native objects | Render parity | Deck |
|---|---:|---:|---:|---:|---|
| `reference.html` | 25 | 23/25 | 25/25 | 0/25 | BLOCKED |
| `approved-visual-variants.html` | 9 | 6/9 | 9/9 | 0/9 | BLOCKED |
| `source-native-visual-variants.html` | 13 | 8/13 | 11/13 | 0/13 | BLOCKED |
| `architecture-visual-variants.html` | 6 | 5/6 | 6/6 | 3/6 | BLOCKED |

`references/pattern-support.json` contains the corresponding per-slide failures.
The 53-slide audit explicitly substituted Noto Sans KR → Noto Sans CJK KR and
JetBrains Mono → DejaVu Sans Mono; external font stylesheet links were removed
only in diagnostic copies. The installed reference HTML files were not rewritten.
Global font/title/reopen/artwork gates apply in addition to per-slide counts.
Passing source-object correspondence is not proof of pixel identity.

The four installed reference HTML files remain byte-identical to the previously
validated cumulative source, including images, layout, typography and adaptive
runtime. Original KRISS artwork is not replaced or regenerated. Inherited image
checks are rerun by the build; exact failures remain recorded in the support table.

## Remaining limitations

S11/S12 vertical writing and S12 mixed-text/source coverage remain unsupported.
Keep original reference assets but do not choose unsupported structures for a
completed native deck. They are blocked; no meaningful text is rasterized to
hide unsupported semantics. Other failures include source overflow and mixed
Korean/Latin punctuation spacing, line positions, marker and border-region render
differences. Do not label every failure as merely a missing font or antialiasing.

No global/local comparison threshold, PPTX font, width, position or layout was
relaxed. Required gates remain fail-closed. H01 affine diagonal strokes remain
editable vector shapes, not endpoint-attachable PowerPoint connectors.

## Historical results are not rc3 results

rc2 reported 34/34 unit contracts. The post-rc2 cumulative application fixes
reported 52/52; that previous 15-slide application passed HTML/native 15/15 but
pixel parity 0/15. Those counts describe prior runs, not new certification. The
current 72/72 unit and 53-slide table above come from the new rc3 runs.

## Validated environment and distribution

Python 3.13.5 / Linux x86_64; Playwright 1.57.0; python-pptx 1.0.2;
Pillow 12.3.0; NumPy 2.3.5; Chromium 144.0.7559.96;
LibreOffice 25.2.3.2; Poppler 25.06.0. Dependencies were already installed.
Fresh network installation, Windows/macOS, and Microsoft PowerPoint app rendering
are not verified. Fonts are neither bundled nor embedded.

The repository payload is the installable `kriss-ppt/` directory only. Development
tests, CI, generated decks, execution logs, evidence, patches and `.agent` are
excluded. Runtime QA and file-integrity verification remain part of the skill.
