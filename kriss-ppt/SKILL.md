---
name: kriss-ppt
description: Produce and revise KRISS presentations using HTML as the only layout source of truth, then export editable native PowerPoint with evidence-driven HTML-to-PPTX parity gates.
---

# KRISS PPT

## Stable distribution — 1.1.0

This is the stable distribution of the supported KRISS PPT workflow, promoted from 1.1.0-rc3+ophthagen.1 after external verification reported by the maintainer. Stable distribution does not certify every bundled visual pattern or every PowerPoint environment.
Read `references/release-status.md` and `references/pattern-support.json` before
selecting a pattern. “Approved” names refer to design authority, not a passing
native export test. S11/S12 vertical writing is unsupported: retain the original references, but do not select those structures for a completed native deck until implemented and verified. Do not conceal a remaining gate failure or lower tolerances.

## Core contract

HTML is the only authoring source of truth. Finish and validate the HTML first, then
derive editable native PowerPoint objects from the browser's final DOM geometry and
computed style. Do not redesign or independently correct the PPTX to hide drift.
A deck is complete only when native-object QA and HTML/PPTX render parity both pass.

## Authority and workflow

1. Read the user's sources and preserve their facts, framing, and qualifications.
2. Inspect `references/reference.html`, `references/slide-types.md`, and relevant approved,
   source-native, or architecture variants. Choose the content's best-fit structure.
3. When multiple patterns fit, briefly compare two alternatives. Diversity is a
   tie-breaker only. Neither a fixed DOM clone nor an invented generic card grid is
   mandatory. Record the chosen reference and any intentional departure.
4. Read `references/original-artwork-contract.md`. Preserve original KRISS chrome/assets; use the original image bytes, not redrawn title motifs or footer bands. Use the selected reference's geometry,
   spacing, typography, border, radius, shadow, and connector style as defaults.
   Do not replace the pattern to repair a local text inset or export error.
   Read `references/content-image-contract.md` when reusing figures from source decks. Preserve original bytes and scientific labels; do not reconstruct data from plotted pixels.
5. Complete the HTML first, with speaker notes (`data-notes`) and interaction
   controls. `references/core-features.md` supplies the interaction reference.
6. Apply adaptive policy in HTML. Capture the final DOM only after fonts/images,
   adaptive layout and semantic connectors have settled.
7. Export native objects without changing layout, font size, or content width.
8. Compare the captured HTML image and native PPTX render. Require all gates to pass
   before delivering a deck as complete. A `BLOCKED` build is diagnostic output only
   and must not be presented as a finished deck.

HTML is the single source of truth. A scene JSON is a derived, hash-bound snapshot,
not a second authoring format. Never independently correct the PPTX to hide drift.

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/verify_installation.py --strict
python -m pip install -r requirements.txt -c constraints-tested.txt
python -m playwright install chromium
python scripts/check_environment.py --font "Noto Sans KR" --font "JetBrains Mono"
python scripts/validate_html.py presentation.html
python scripts/build_release.py presentation.html presentation.pptx
```

The integrity command materializes byte-identical `references/reference.html` from the compressed Git transport on the first run; the restored SHA-256 is checked against `PACKAGE-MANIFEST.json`. Do not manually alter this canonical reference.

The build preserves the input and writes `<input>.final.html` beside it (with permitted local
image/CSS/script bytes embedded; font bytes are never embedded), `<output>.pptx`, and `<output>.evidence/` with captured models,
HTML images, PPTX renders, comparisons, QA JSON and a manifest. `RELEASED` requires
HTML, native correspondence and global/local parity to pass. Missing tools/fonts,
unsupported rendering, or failed gates produce `BLOCKED` or `BUILD_ERROR` and exit 1.

Reference/core helpers remain opt-in authoring aids. They are **not** automatically
run on the user's original HTML during release; their edits must be reviewed first.

## Reference title and native design defaults

Read `references/design-paint-contract.md`. Standard titles use the reference's
`.kriss-title` wrapper and span styles, or an explicit
`data-reference-role="standard-title"` binding. Their color is white on the dark
bar, but color alone is not fidelity: compare font family/size/weight/style,
letter-spacing, line-height, white-space, container height/position and alignment.
The exporter performs a read-only comparison to actual reference CSS/DOM defaults.
Unmarked custom titles on standard slides block release. Document intentional
HTML overrides with a property allowlist and a reason. Never recolor only the PPTX.

Production authoring must follow the actual reference title styles. Diagnostic or
noncanonical examples may declare explicit metadata, but they must never redefine
standard title defaults for real KRISS slides.

One-sided solid accents and bottom table rules stay single native shapes where
possible; they are never promoted to full outlines. Single linear/repeating-linear
gradients are native fills. Literal pseudo checkmarks/bullets and decorations are
measured from the browser with checked temporary probes. Unpainted, unpositioned
inline literal pseudo text becomes styled runs inside its coherent text block,
not a second overlapping textbox. Unsupported paint syntax,
complex generated content, and non-solid mixed curved borders are explicit blockers.
Solid mixed rounded borders, asymmetric/elliptical CSS corners, and a limited
centered circular flat-step conic syntax have editable native custom paths.
Basic SVG line/circle/ellipse/rect objects are native; unsupported SVG content
must be blocked by independent source inventory, never silently skipped.
Do not simplify or redesign the reference to fit exporter limitations.

Read `references/browser-paint-contract.md` for measured layer order, editable CSS polygons, resolved counters and affine SVG vector strokes. Affine vector strokes are editable shapes, not attached PowerPoint connectors.

## Adaptive contract

Default is `preserve`: no-pressure components are unchanged. Explicit attributes:

```html
<div data-density-component="standard" data-size-policy="preserve">...</div>
<div data-size-policy="content-fit">...</div>
<div data-size-policy="uniform"><div>...</div><div>...</div></div>
```

`content-fit` may change intrinsic height; `uniform` synchronizes the direct peers'
heights without redefining their column widths. Implicit equalization of unrelated
cards and global sparse-card shrinking are prohibited. Legacy density CSS must not override an explicit size policy. Reset only changed adaptive properties; reassigning unchanged percentage declarations can lose CSSOM precision.

Measured pressure is addressed in this order: gap → padding → font reduction,
with remeasurement after every adjustment. Floors are configurable with
`data-min-gap`, `data-min-padding`, `data-min-font-px`; `data-font-fit="false"`
disables font reduction. Preserve the reference if no pressure is measured.
Unresolved content overflow is a release blocker; automatic topology replacement is not performed.
Ordinary activation, resize, fonts/images and export use the same settled-layout
API (`krissActivateSlide`, `krissSettleLayout`, `__KRISS_LAYOUT_SETTLED`). Finite
animation reaches its final state; infinite animation is not a certifiable static
state. Known bundled legacy runtimes are migrated once, unknown competing runtimes
are blocked rather than removed by a broad script-pattern match.
Every actual adjustment records element/property/from/to/reason in the evidence.

## Text/shape contract

- One coherent text block becomes one native textbox or text-bearing shape.
- Inline bold/color/italic becomes runs, not separate boxes.
- `<br>` stays a line break inside that textbox; paragraphs stay paragraphs.
- Automatic wrapping uses native text flow in fixed-width blocks. Intrinsic-width
  labels/absolutely positioned shrink-to-fit text preserve their no-wrap semantics.
- A simple decorated text container becomes one native shape. Background and
  text are not split merely because the background has rounded corners.
- Content box, border path, and glyph rectangles are distinct. No heuristic width
  growth is allowed. Preserve padding once, including the preset shape's intrinsic
  text rectangle. Native inset values can therefore be negative for an ellipse.
- Set Latin, East Asian and complex-script faces explicitly. A family match is
  checked, but it is not proof that every glyph avoided font fallback.
- Independent columns, badges, rotations, or child visual regions remain separate.
- Unsupported structures are blockers, not excuses to rasterize meaningful content.

## Semantic connectors and symmetry

```html
<svg data-connector-source="#hub"
     data-connector-targets='["#a","#b"]'>...</svg>
```

Endpoints are recomputed from final DOM box edges using the SVG transform matrix.
No subject- or slide-number coordinates are embedded in the runtime. Legacy lines
without metadata are preserved, not automatically reinterpreted.

Mirror adjustment is opt-in with `data-symmetry="mirror"` and paired absolutely
positioned peers sharing `data-mirror-pair`. It does not generate a hub topology
from an arbitrary node count. Inspect the HTML before approving a new arrangement.

## Regression and release scope

```bash
python scripts/build_release.py revised.html revised.pptx \
  --baseline baseline.evidence --allow-slides 4
```

Compare final models and captured HTML renders against the explicit baseline.
Changes outside the allowed slide set fail. A common exporter fix may legitimately
change several slides, but those changes must be identified and reviewed.

Source inventory precedes all export filters. Every visible content role must
map to a native owner, or fail explicitly. Final HTML is reopened in a fresh page
and ordinary activation must reproduce geometry, computed styles and render
parity. Static validator errors are shared by the release entrypoint.

Native QA checks side-border/gradient native mapping, semantic object correspondence, text, paragraph/manual-break/run
counts, font sizes, alignment, effective content boxes, and native connectors.
It does not accept a full-slide image plus token text as native content.
Global parity uses strict thresholds (mean 3/255, major 2%, strong 1.2%).
Local foreground and paint-region comparison supplement—not replace—those thresholds. Never
relax tolerances just to certify the current deck.

## Design review is not a pixel gate

Reference defaults can contain small type. Flag role-specific readability concerns
and inspect at presentation size; do not enlarge/shrink every reference globally.
Balance, density and aesthetic overlap remain review items rather than blanket
automatic layout rewrites. Fix the first divergent stage: reference → authored
HTML → adaptive DOM → native mapping → renderer. Do not guess from PPTX alone.


## Installation-only distribution

The repository contains this installable `kriss-ppt/` directory only. Runtime QA stays; development tests, CI, generated decks and evidence are not installation dependencies. Read runtime identity from `VERSION`; `PACKAGE-MANIFEST.json` verifies the inventory. Historical validation and this package's actual re-tests are distinguished in `references/release-status.md`.

## External text references (rc3+gpn.1)

Source citations that are HTML anchors must remain native text hyperlinks. Use
absolute HTTP(S) URLs for academic references. Inspect both URL identity and
visible HTML–PPTX parity; underlined pixels alone are not link preservation.
See `references/hyperlink-contract.md` for supported forms and explicit blocks.
This functionality was introduced in the preceding `+gpn.1` candidate;
its historical test report does not imply whole-pattern certification.


## Source-bound speaker notes

Plain-text `data-notes` is captured from the settled DOM before export filtering.
The native notes body must match exactly, including Unicode, paragraphs, blank
lines and whitespace. The delivered HTML reread must reproduce the same notes.
Missing, changed or unreadable notes block approval even when slide pixels match.
See `references/speaker-notes-contract.md`. Rebuild older evidence without this
contract rather than treating a missing notes record as a pass. This distribution includes the earlier hyperlink fixes; stable release
status does not waive per-deck validation or certify all patterns.
