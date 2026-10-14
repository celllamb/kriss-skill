# Native reference paint contract — 1.1.0-rc3

`reference.html` is the design authority. The derived model is a capture, not a new
layout description to design independently.

A uniform four-sided border is a native outline, placed inward by half its width
because native strokes are centered. A single side is a hard-stop native fill;
it must NOT use the same offset as an outline. One-sided table rules introduce no
vertical grid lines. Mixed straight borders are separately named native edges;
solid mixed curved borders use native custom edge paths. Non-solid mixed curved
borders remain blockers. All four CSS corner radii (including elliptical pairs)
are captured; simple coherent text containers keep one text-bearing native shape.

A component linear gradient is a native gradient fill. Preserve CSS direction,
stop positions, colors, alpha and underlay; do not replace it with flat color or
raster content. Centered circular flat-step conic sectors are native custom wedge paths.
Continuous conic gradients, radial gradients, unsupported origins/directions and
unimplemented syntax remain blockers. No raster fallback is used for these components.

Default list markers are measured from Chromium DOMSnapshot, including ordered
start/value semantics; unsupported marker structures fail. Generated literal content is measured in the same browser layout. Probe nodes are
removed before final capture. A literal marker gets an explicit derived id under
its owner and must correspond to one native owner. An ordinary unpainted inline
literal shares the coherent text block as styled runs; positioned or painted
generated content remains independently mapped. Paragraph text is not split
into line textboxes to accommodate the marker.

Real standard-slide titles use `.kriss-title` and its span rule from reference, or
an explicit `data-reference-role="standard-title"` binding. The read-only title
checker compares computed values to actual reference defaults. Intentional style
deviations must specify `data-reference-overrides="fontSize,height"` and a meaningful
`data-reference-override-reason`. These attributes record a deliberate HTML change;
they are not instructions to adjust PPTX separately.

An unmarked custom title on `.slide.std` is blocked. Synthetic fixtures may declare
`<meta name="kriss-diagnostic" content="true">`; their special title CSS cannot
certify reference fidelity. Do not use that exemption on real presentations.

There are three independent checks: reference asset preservation; reference-to-
authored HTML design/default fidelity; final HTML-to-native PPTX parity. Success
in one must never be reported as success in all three.
