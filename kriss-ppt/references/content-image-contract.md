# Source and content-image correspondence

For user-supplied presentations, preserve scientific image bytes unless the user
explicitly requests an image edit. Preserve source framing, values, coordinates,
units, annotations and limitations. Do not recover new numeric data by reading a
plot as if raw data were supplied. Record a per-slide source map outside the
installation. Source figures remain pictures; editable slide text is not
rasterized to approximate a layout.

The author chooses image placement in HTML. Supply a box with the original aspect
ratio to avoid stretching. The supported direct image path currently uses the
full uncropped image. A crop/rotation or image-effect use case needs an explicitly
implemented DOM/native mapping; it must not silently be accepted by image-presence
checks or by whole-slide pixel similarity.

Native QA independently verifies each content image against the captured asset:
exact embedded SHA-256 and size, one named native picture per image layer,
uncropped geometry within 0.10 CSS px (coordinate serialization allowance), no
unrequested flip, rotation, clipping preset, tile mode or native color/alpha
transformation, and no additional unmapped pictures. Template backgrounds have a
separate original-artwork contract. Small changed regions do not bypass byte
identity. Two image layers sharing one owner are ambiguous and blocked until
layer-specific identities are implemented.

This is source/native correspondence, not authentication of the user's scientific
results or a cryptographic signature. A party able to rewrite all source, model,
assets and hashes can replace the recorded authority. Render parity is still
required in addition to exact image correspondence.
