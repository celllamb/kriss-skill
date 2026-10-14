# KRISS Theme Specification

## Theme Policy

KRISS is the **only** allowed presentation theme. Do not offer theme choices. Do not import visual themes from make-slide's public theme gallery.

The bundled `reference.html` is the authoritative implementation. It combines the official KRISS wide template with recurring information structures observed in actual KRISS research, education, technical, strategic-planning, and institutional presentations.

## Visual Identity

Core palette from the reference:

- KRISS orange: `#F47B20` / orange emphasis family
- KRISS gray-green: `#596563`
- Deep gray-green: `#465250`
- White: `#FFFFFF`
- Main ink: `#1F2937`
- Supporting scientific accents may use restrained blue/teal/green/purple only where the canonical pattern already does so.

Orange is an accent and navigational emphasis, not a default background fill.

## Canvas

- 16:9 only.
- Keep the official KRISS background/header/footer geometry from the reference.
- Align content to the reference safe areas.
- Do not stretch or crop official logo/anniversary assets.
- On the light cover, preserve all three footer brand elements from `reference.html`: KRISS logotype, the Korean wordmark `한국표준과학연구원`, and the **dark** 50th-anniversary emblem.

## Cover Safe Zone

The cover contains large decorative geometry. Keep the copy block shifted right/down from the extreme upper-left area. Use the safe-zone behavior already implemented in `reference.html` rather than placing title text against the decorative motif.

Recommended cover copy behavior from the canonical reference:

- left: approximately 11.4% of slide width;
- top: approximately 27% of slide height;
- width: approximately 60% of slide width;
- avoid expanding left/up unless the background itself has been changed intentionally.

## Title Bar

For standard KRISS slides:

- title sits within the dark KRISS top bar;
- use white text;
- do not create a second competing title below the bar unless the canonical pattern specifically uses a subheading;
- keep titles concise enough to avoid wrapping into decorative areas.


Recommended standard title-bar geometry from the validated KRISS canonical reference:

- left: approximately 9.1% of slide width;
- top: approximately 2.5% of slide height;
- height: approximately 7.8% of slide height;
- title text: approximately 2.1vw, bold, white, single-line when possible.

## Typography

- Primary title font: the actual `--font` / title CSS in `reference.html` (currently `Noto Sans KR`). Preserve any explicitly declared body font; do not infer a substitute from this prose.
- Code: use the KRISS-approved monospace stack for literal code only. PPTX export preserves the final browser font choice as a native editable text object whenever the font is available.
- Use a clear hierarchy: title > major heading > body > caption.
- Body text should normally be left aligned.
- Avoid body text smaller than is comfortably readable on a projected 16:9 slide.

## Images

- Preserve original aspect ratio by default.
- Crop only when the visual role requires a framed image area and the crop does not remove scientific evidence.
- Prefer original figures/screenshots from source material over decorative stock images.
- For scientific figures, do not redraw quantitative plots unless the underlying data are available and a redraw is explicitly desired.

## Information Density

- Research/result slides may be dense, but hierarchy must remain obvious.
- Separate evidence from interpretation.
- Use one synthesis statement for multi-panel results.
- Avoid decorative boxes that do not encode structure.
- **Component dimensions follow content density.** A canonical pattern is not permission to stretch sparse content into large boxes.
- Use the `compact`, `standard`, or `expanded` density variant defined in `density-guide.md`.
- Prefer whitespace around a compact information cluster rather than large empty interiors inside cards.
- Horizontal workflows with short labels should be compact and vertically centered; `align-items:stretch` is not the default.
- Equal-height cards should be used when equality/comparison itself carries meaning, not simply to fill the canvas.

## External-template Design Elements

The canonical reference learned structural patterns from several non-identical KRISS planning templates. Their colors/branding are **not** copied. Only information architecture is retained and translated into the KRISS wide-template language.

## Canonical Pattern Policy

Use only the 25 patterns in `slide-types.md`. For merged families, use variants rather than creating a new type:

- Comparison / decision matrix includes two-way comparison, benchmark, dense table.
- Problem / transformation includes Problem→Solution and AS-IS→TO-BE.
- Roadmap / staged strategy includes year plan and chevron strategy.
- Workflow / process includes horizontal workflow and branching flowchart.
- Technical walkthrough includes code/status, before-after, step+terminal.
- Strategy / impact framework includes 4-card strategy and vision/mission/role.
- Section / closing uses a common branding family.

## Quality Gate

Reject or revise a slide when:

- title overlaps a motif;
- content crosses the slide safe area;
- figure aspect ratio is distorted;
- text is visibly too small at normal slideshow scale;
- a dense slide lacks visual hierarchy;
- sparse content is placed in unnecessarily tall or wide boxes;
- short workflow/card components are stretched only to occupy empty space;
- a palette/style from another template is copied directly;
- decorative novelty weakens KRISS identity;
- citations, labels, units, or scientific qualifiers are lost.

## Semantic density coverage

Every slide that contains a `.content` region must participate in the adaptive density system. The `.content` element declares `data-layout`, `data-density-container`, and `data-density-scope`. Reusable child cards/nodes/panels declare `data-component` and `data-density-component`. A deck with partial semantic coverage must not be exported.

Adaptive typography is preserve-first. Without measured pressure, keep the authored sizes and font family/weight. Explicit content-fit/uniform policies are applied in HTML; measured pressure is handled by gap, padding, then font reduction within declared floors. Do not enlarge sparse text automatically.

## Adaptive box geometry requirement

Typography adaptation alone is insufficient. Components marked with `data-density-component` must also adapt their box geometry: padding, min-height, height, grid/flex gaps, and synchronization behavior must respond to actual rendered content. Sparse KPI/cards should become compact content-height boxes; dense cards may reduce padding before typography reaches the minimum. Mixed component groups must not be synchronized to the height of the largest heterogeneous panel.

Validation must treat the following as failures: oversized empty component boxes without semantic reason, stretched KPI cards caused by parent grid rows, mixed dashboards synchronized to the tallest child, or render overflow after all text has reached `fitMin`.
