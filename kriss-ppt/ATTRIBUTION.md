# Attribution

This skill is adapted from **Kuneosu/make-slide**:

- Repository: https://github.com/Kuneosu/make-slide
- License: MIT
- Upstream copyright: Copyright (c) 2026 kuneosu

Substantial workflow/specification concepts retained from the upstream project include:

- input-mode and outline workflow;
- single-file HTML presentation model;
- keyboard/touch navigation, progress, counter, fullscreen, and popup speaker notes;
- HTML specification;
- the upstream project's HTML-first visual-fidelity goal (the screenshot exporter itself is **not** retained as the delivery implementation).

Modifications in this derivative:

- all theme choices removed;
- KRISS theme made mandatory and bundled locally;
- 25 KRISS canonical presentation patterns substituted for upstream theme/layout selection;
- output fixed to HTML + PPTX;
- PPTX conversion replaced with a browser-measured, editable native DOM-to-PowerPoint translator plus visual parity QA;
- KRISS-specific design/quality rules added.
