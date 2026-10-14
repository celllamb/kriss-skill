# Text hyperlink contract — rc3+gpn.1

Visible external text anchors are semantic source content, not just underlined
pixels. Absolute HTTP/HTTPS, mailto and tel targets are captured from the final
browser DOM and retained as native DrawingML run hyperlinks. Nested bold/italic
text, normal wrapping and explicit line breaks retain their link targets. URLs
are not fetched by the converter. The author remains responsible for the cited
source and destination safety.

Independent source inventory records each anchor's resolved URL and rendered
text. Every non-whitespace character must map to linked native text, and each
native run's relationship target is checked. A missing/changed/partially removed
link cannot be approved merely because the screenshot is unchanged.

Relative URLs, in-document slide navigation links, download semantics,
image/SVG links and generated pseudo-element link content are not supported by
this mapping. They explicitly block release. Native hyperlinks do not guarantee
browser target-window semantics, custom JavaScript handlers, offline destination
availability or the receiving PowerPoint application's security prompts.

When composing a deck with clickable text, its general slide-click handler must
ignore anchors and interactive controls. Canonical and approved reference
navigation includes this guard. Do not intercept link navigation globally or
replace a valid hyperlink with slide navigation. Keyboard navigation and notes
are independent controls.

Original artwork is immutable. Place source footers wholly above the original
footer artwork; even a one-pixel underline over the artwork is a source-HTML
problem, not a reason to loosen the artwork comparison gate.

Native runs explicitly select their measured text color through Microsoft's
`hlinkClr val="tx"` extension. The native QA gate checks that policy, the explicit
RGB color and underline in addition to the address. No new palette or
renderer-specific numeric color correction is introduced. Older consumers may
ignore Office extensions; actual application rendering remains a separate gate.

Specification: https://learn.microsoft.com/en-us/openspecs/office_standards/ms-odrawxml/3c384794-9e01-480a-accf-8dfb4d99d645
Schema: https://learn.microsoft.com/en-us/openspecs/office_standards/ms-odrawxml/014fbc20-3705-4812-b8cd-93f5af05b504
