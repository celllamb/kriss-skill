# Typography — preserve defaults, review readability

The selected reference remains the starting typography. Do not shrink every body
block for convenience, enlarge every sparse slide, or rewrite all reference fonts.
Inherited font sizes can be preserved even when the text is shorter than the
placeholder. Adapt only when actual content/geometry requires it.

The recovered reference contains some small type. Those values are not certified
presentation minima. Inspect title, body, auxiliary description, badges, tables and
citations separately at actual presentation size. The current HTML QA emits a
small-font review warning below 16 CSS px; this is a diagnostic threshold, not a
mandatory global replacement font size or an aesthetic FAIL condition.

At a 1280px / 13⅓in canvas, CSS pixels are mapped at 72/96 points per pixel. Viewport
units must be interpreted through computed DOM styles, not re-evaluated in PPTX.
Exact font families must be installed in the renderer. Family matching does not
prove glyph coverage. The software package must not distribute font binaries.

Adaptive font reduction happens only after gap/padding relief is insufficient.
Paragraphs, explicit breaks and inline runs are preserved in the same native text
container. The current Korean renderer parity limitations remain release blockers.
