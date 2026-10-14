# Original KRISS artwork contract — 1.1.0-rc3

## Authority

`references/reference.html` is the current Project-backed template authority.
The standard background is the existing 4000 × 2250 JPEG, 196534 bytes, SHA-256:

```
aa16c6f15d5753c56b8715a7967b588f4e1a0ee20edb8d9b07b877058f90088a
```

This hash describes the supplied reference asset, not a separately verified
external PowerPoint master. Cover and divider families use their own existing
reference images; do not substitute the standard background for them.

## Authoring

Canonical and variant slides preserve original image bytes, placement, aspect,
and visible identity artwork. Do not redraw the title motif, dark band, or footer
using circles, rectangles, gradients, SVG or newly generated imagery. Copy the
actual image URI/resource from the reference. Do not resample, crop, recolor, or
recompress it. `background: ... !important` must not erase a background-image.

Variation changes the information layout inside the content area, not the
institutional master. V10's dark emphasis is a body panel; the original standard
header/footer remain visible. H02–H06 no longer have synthetic `.template-dot`,
`.template-footer`, or a replacement slide `::before` band. Standard title wrapper
and span rules are derived from canonical CSS, not a separately tuned imitation.

For the known older variant HTML, the explicit authoring migration is:

```bash
python scripts/sync_reference_chrome.py old.html --output restored.html
```

Review `restored.html` before export. The helper is idempotent. It only removes
recognized legacy reconstruction selectors and empty reconstruction nodes;
unknown user content is retained. It is **not** run implicitly by `build_release`.

## Read-only release checks

1. Compare the final DOM background resource hash and placement with reference.
2. Compare the original artwork pixels in fixed regions with browser screenshots.
   The reference content and title text slots, small bottom pattern annotations,
   and blank margins are excluded. Selected original artwork ink has zero pixel
   difference tolerance. This is an artwork check, not a whole-slide identity test.
3. When authored image and placement match, embed those same original bytes in
   the PPTX background picture and verify the embedded media hash. A wrong HTML
   background is **not** secretly replaced during export; it blocks release.
4. All existing semantic/native/global/local render gates remain mandatory with
   unchanged thresholds. Passing artwork preservation is not pattern certification.

Reference assets, background check, authoring helper, and schema belong in the
skill. Development tests and execution evidence are maintained outside the
installation-only repository and are not required to use the installed skill.

Standard-title geometry is measured after each slide becomes active and settles.
Inactive display:none elements may expose percentages instead of used pixel
values and must not be used as the geometry comparison target.
