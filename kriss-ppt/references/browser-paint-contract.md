# Browser paint and native vector contract — 1.1.0-rc3

Chromium DOMSnapshot is read after the settled DOM and before export. Paint layers,
flattened tree sequence, and resolved generated text are retained in the hash-bound
model. Paint order is not guessed from the number of emitted PowerPoint objects.

## Ordering

Every text block, painted owner, basic SVG object and generated object carries
its browser paint layer and sequence. Text and opaque backgrounds participate in
the same ordering pass. Native QA checks source-bound order, so a background moved
after foreground text is rejected even when text objects and PPTX hashes exist.
DOMSnapshot paintOrders identify co-painted layers, not a complete display-list
API. Tree sequence orders members of a layer. Pixel parity remains mandatory for
stacking cases not fully distinguished by these measurements.

## Geometry

Resolved simple CSS `polygon()` becomes native editable custom geometry using
measured vertices. A zero-inner-size one-face CSS border triangle becomes the
actual triangular face, not a rectangular outline. Self-crossing/complex clipping,
clipped images and unsupported clipped borders are blocked rather than simplified.
Restricted zero-offset, zero-blur inset paint on a clipped polygon is intersected
with the original CSS rectangular shadow bands. It is not converted into a new
polygon perimeter border.

Ordinary SVG lines remain native connectors. Anisotropically transformed SVG
butt strokes become native **editable vector shapes** whose four vertices are the
browser CTM-transformed stroke corners. These are explicitly `svg-stroke` objects,
not connector objects and not raster images. They do not acquire PowerPoint
endpoint attachment behavior. H01 has two ordinary connectors and four such
vector strokes. Native QA compares each vector vertex to source geometry. Do not
claim all six are native connectors.

## Text

CSS counter strings are taken from resolved browser pseudo text, including actual
numbering and formatting. No slide-specific numbering algorithm is used. Supported
uppercase/lowercase text is taken from browser layout text nodes and honors the
source language; it is not reconstructed with Python/JavaScript casing rules.
Unmeasured text transformations and unsupported capitalization remain blocked.

References: Chromium DevTools DOMSnapshot protocol and SVG2 stroke geometry.
The implementation relies on the installed Chromium protocol; browser version is
recorded in each evidence manifest. This does not promise all-browser support.
