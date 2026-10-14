# Adaptive contract

Default policy is preserve. With no measured pressure, geometry and font sizes do
not change. Automatic sparse-card shrinking is not part of the default policy.

- `data-size-policy="content-fit"`: explicitly allow intrinsic height and start
  alignment. It does not remove authored max-height or redefine layout topology.
- `data-size-policy="uniform"` or `data-uniform-group`: equalize direct peers'
  heights, not arbitrary cards or all column widths.
- `data-density-component` / `data-fit-box`: enable measured pressure relief.

Relief order is gap, then padding, then typography, with a fresh overflow check
after each step. Floors and font-fit opt-out are described in SKILL.md. Overrides
are logged with actual from/to values and reasons. Original styles are restored
before a repeat application; the same input must yield the same final geometry.

Connectors are recalculated after boxes settle. Mirror placement is only for
explicit paired absolute peers. Unannotated legacy lines are preserved. Automatic
semantic layout guessing, automatic topology fallback and count-based hub placement
are not part of this runtime.

## 1.1.0-rc3 runtime boundary

Ordinary navigation and export share `krissActivateSlide` / `krissSettleLayout` and the settled promise. Class/style activation, resize, font/image completion are observed. Changes during a settle trigger another revision. Source content overflow after this process blocks release; it is not only a warning. An empty decorative region may declare both `data-overflow-role="decoration"` and a nonempty `data-overflow-reason`; text-bearing content cannot use this exception. Known bundled legacy runtimes are removed by exact fingerprint, not arbitrary script matching. Unknown competing runtime definitions fail migration.

## Explicit size policy and idempotent reset

Legacy density-only reference CSS may retain its authored intrinsic-height rules,
but those rules do not apply when `data-size-policy` is explicit. Preserve,
content-fit and uniform are owned by the shared runtime. An explicit fixed-height
preserve box must not become intrinsic-height merely because a density label is
present. Padding/font relief still requires measured pressure.

A reset restores only properties actually changed from their remembered inline
value/priority. Reassigning unchanged CSSOM percentage strings loses internal
numeric precision in Chromium and previously caused presentation/export mismatch.
Do not normalize author positions or weaken the independent reopen comparison.
