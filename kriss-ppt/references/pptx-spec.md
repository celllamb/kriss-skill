# Native PPTX contract

`export-pptx.py` captures a final slide DOM at 1280×720 and derives a semantic model.
Text extraction lives in `text-block-extract.js`; visual primitives originate from
the native exporter. The native canvas is exactly 40/3 × 7.5 inches.

A coherent visual text block maps to one textbox or one text-bearing native shape.
Inline styles become runs, BR becomes an internal line break, and source paragraphs
remain paragraphs. Fixed-width blocks use native wrapping; intrinsic-width labels
preserve shrink-to-fit/no-wrap semantics without expanding their box. The exporter must preserve final browser text geometry and wrapping without PPTX-only correction.

Background border-box, CSS content-box and glyph-range rectangles are distinct.
Merged rounded rectangles/ellipses account for their DrawingML preset text rectangle
in addition to body insets. No empirical width growth or slide-dependent offsets.
Latin/East Asian/complex-script families are written explicitly. The exporter does
not install or bundle fonts.

All meaningful unsupported source structures are reported by HTML QA. Native QA
requires correspondence to the captured meaningful text/shape/connector inventory;
a screenshot plus a token text object is not acceptable. Global and regional image
comparisons must both pass. Native structure PASS alone is not a release.

Geometry must be fixed at its first divergent source stage, never by a PPTX-only
redesign. Main build command: `python scripts/build_release.py input.html out.pptx`.

## 1.1.0-rc3 source coverage

Each source role must map to a native object identifier, independently of exporter traversal. Shared text ownership is allowed only inside its coherent native text block. Basic SVG shapes and solid curved CSS paint have native support; unsupported SVG paths/filters/masks remain blockers. Full-slide static template chrome is not permission to flatten meaningful content. Reopen checks and native/global/local pixel QA are mandatory. A retained PPTX beside a new failed manifest is not approved.


## 1.2.0-rc3 — native master inheritance

`reference.html` remains the complete HTML scene (including all artwork). The
PowerPoint writer starts with the original `kriss-wide-master.pptx`, removes its
demo slide references, and binds each authored slide to an existing original
layout. Family mappings are source-asset asserted, not guessed from slide
numbers. An inherited full background is not a slide-level picture. Original
layout images (cover logos) are mapped only after checking source byte hash and
DOM-final geometry (2 px tolerance); otherwise fail closed on duplicate native
artwork with conflicting coordinates. Source inventory and native QA require
owner equivalence. All global/local pixel tolerances are unchanged.
