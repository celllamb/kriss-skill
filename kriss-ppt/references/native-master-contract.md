# Native KRISS PowerPoint master contract — v1.2.0-rc3

## Authoring authority

HTML, including its original background, logos, text, and content, remains the
only source of visual authoring truth. The PPTX template is a native *asset
owner*, not a competing layout engine. The export step may not redesign or
reflow any measured DOM element to fit the template.

## Included native template

`references/kriss-wide-master.pptx` is the actual supplied official wide
PowerPoint reference (one master, 14 layouts). `scripts/master_template.py`
asserts its 16:9 dimensions, layout count, background picture identity, and
layout family. The original sample slides are excluded from generated outputs,
but the native master and layout definitions are preserved intact.

Layout binding for the supplied specific PPTX:

- Cover: layout 0; full-bleed JPEG and cover logos inherit from native layout
- Standard: layout 10; full-bleed JPEG inherits from slide master
- Divider: layout 6; full-bleed JPEG inherits from layout; a separate divider
  logo not present in that layout remains an authored image/native slide picture

If the supplied template changes, the SHA-256 and layout checks must fail,
not silently reselect a visually different master.

## Coverage and QA

`static-background` from the independent DOM inventory maps to a
`master-background` owner. Captured source images matching an existing native
layout picture by *both* embedded-image SHA-256 and browser-measured image
rectangle map to `master-image` owners. Different artwork stays an independently
exported native image. Same-byte artwork at inconsistent coordinates is a
release blocker, not a reason for a duplicate picture.

Final PPTX-native QA independently resolves each inherited owner, checks its
media digest and the absence of a slide-level `kriss:background`, while
text/shape/image/link/note parity remains mandatory.

## Master typography

`python scripts/master_typography.py` extracts and asserts the source XML
properties. For this template: title font `나눔바른고딕`, standard 28 pt and
cover 40 pt, body hierarchy 28/24/20/18/18 pt. Use source-specific smaller
captions/data labels where necessary, after HTML readability review; do not
globally force all dense scientific content to 18 pt.

## Release status

Local diagnostic confirms 3/3 HTML and 3/3 native structural coverage. Strict
HTML/PPTX pixel parity did not pass; there is no unconditional RELEASED claim.
