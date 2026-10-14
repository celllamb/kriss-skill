# Direct Snapshot Parity Contract

HTML is the only source of truth. PPTX export is complete only when the generated editable native PPTX renders close to the final adaptive HTML screenshot.

Required order:

1. Finish HTML and adaptive layout.
2. Render HTML snapshots in Chromium.
3. Export editable native PPTX from final DOM geometry and computed style.
4. Render PPTX snapshots through LibreOffice/PDF.
5. Compare HTML and PPTX screenshots slide-by-slide.
6. Fail the deck if any slide exceeds tolerance.

Native object QA is necessary but not sufficient. A deck may have editable objects and still fail if text wrapping, boxes, connectors, z-order, radii, or styles visually diverge from HTML.


## Release-candidate evidence additions

Before exporter filtering, collect source text, paint, images, SVG primitives,
markers, pseudo-content and unsupported replaced elements. Enforce source/native
coverage and local presence independently of global pixel error.

Reopen the delivered final HTML in a fresh page, using ordinary slide activation
rather than an export-only adaptive call. Require exact captured source geometry
and computed-style equality plus the same global/local render metrics used for
HTML/PPTX. Store exact screenshot SHA equality separately as provenance; it is
not the sole approval test. Global mean <=3/255, fraction above 30 <=0.02,
fraction above 60 <=0.012; foreground missing/extra <=0.20 with 2px dilation.
Gradient paint regions additionally use the same global limits locally.
No image registration, pixel shifting or tolerance relaxation is permitted.

A successful fixture or structural check does not certify a bundled reference or
Microsoft PowerPoint. `pattern-support.json` distinguishes those scopes.
