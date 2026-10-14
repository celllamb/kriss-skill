# KRISS Canonical Slide Types

The KRISS theme uses 25 canonical patterns. The patterns below are the only layout vocabulary for generated slides. Variants may be used only when they remain recognizably within the canonical pattern and preserve KRISS design rules.

## A. Framing / Branding

### 1. Cover
Opening slide with title, subtitle, presenter/institution/date. Keep title inside the cover safe zone and away from the decorative motif.

### 2. Agenda / Overview
Numbered sections or 3–5 topic overview blocks.

### 3. Section / Closing
Use the same branding family for section transitions or the final thank-you/contact slide.

## B. Explanation / Comparison

### 4. Standard Text + Figure
Left text + right figure/diagram, or equivalent balanced composition. Default explanatory research slide.

### 5. Overview / Portfolio Cards
3–6 structured cards for research areas, work packages, services, roles, or portfolio overview. Use **compact** cards for heading + one-line content; use equal-height cards only when comparison across cards matters.

### 6. Comparison / Decision Matrix
Use for method A vs B, benchmark cards, feature matrices, or dense comparison tables.

### 7. Problem / Transformation
Use for Problem→Solution or AS-IS→TO-BE. Make causal or transformation logic explicit.

## C. Process / Strategy

### 8. Roadmap / Staged Strategy
Year plan, phased roadmap, chevron flow, maturity stages, or staged execution strategy.

### 9. Workflow / Process
Horizontal workflow as default; branching flowchart as a variant when decision logic is important. For 4–6 short steps (heading + up to two brief lines), use the **compact** workflow variant with content-height boxes and vertical centering. Do not stretch short workflow cards to fill the content area.

### 10. Cycle / Lifecycle
Closed-loop process: plan→execute→validate→review, lifecycle, feedback loop, or iterative quality cycle.

### 11. System Architecture / Relationship Structure
Semantic family for systems, services, resources, data, interfaces, boundaries, and their relationships. **Do not assume a radial hub.** First determine the information topology, then select H01–H06 from `architecture-visual-variants.html`: symmetric peers → H01; grouped ecosystem → H02; bridge/boundary → H03; hierarchy/layers → H04; four responsibility domains → H05; inner/outer ecosystem → H06.

### 12. Process / Requirements Ecosystem
End-to-end process with surrounding requirements, constraints, quality checks, outputs, or stakeholders.

### 13. Strategy / Impact Framework
4-axis strategy, vision/mission/role framework, expected impact, or institutional strategy structure. Use compact strategy cards when each axis contains only a short phrase; reserve larger cards for multi-item axes.

### 14. Goal Hierarchy
Vision → final goal → subgoals → outputs/KPIs. Use for proposals, programs, transformation initiatives, and strategic plans.

### 15. Organization / Governance Chart
Steering body → teams/committees → support/advisory/partner units.

## D. Evidence / Data

### 16. Data Result 2-Column
Two linked result panels, e.g. plot + table, method + validation, result A + result B.

### 17. Multi-Panel Results
Three or more analysis panels with a single synthesis statement.

### 18. Dense Technical / Experimental Data
For high-density technical datasets such as measurements, event logs, case metadata, method/system comparisons, or detailed result tables.

### 19. Evidence Image Mosaic
Multiple images, plots, diagrams, screenshots, or visual evidence panels with short labels and a single interpretation hierarchy.

### 20. Screenshot + Explainer
Software, database, website, instrument UI, or workflow screenshot with explanatory callouts.

## E. Technical / Quality / Organization

### 21. Technical Walkthrough / Code + Terminal
Code/status output, before-after prompt/code, step-by-step command sequence, or terminal-driven demonstration.

### 22. Quality / Performance Framework
Required/excluded markers, accuracy/completeness/consistency/performance metrics, validation criteria, or quality checklist.

### 23. Safety / Permission Matrix
Do/don't, allowed/prohibited, risk/control, permission/sandbox/approval, or operational safety rules.

### 24. People / Team Profile
One or two people per slide with photo, role, expertise, contribution, and role goal.

### 25. KPI / Survey Dashboard
Market size, growth rate, survey responses, ranked preferences, KPI cards, donut/bar charts, or compact decision dashboard. KPI metric blocks are **compact by default**; allocate extra space to charts or interpretation rather than blank card interiors.

## Pattern Selection Rules

1. Pick the pattern that best matches the information structure, not the prettiest pattern.
2. Prefer Standard Text + Figure for ordinary explanation instead of forcing a special layout.
3. Prefer Data Result / Multi-Panel / Dense Technical patterns when evidence is the main message.
4. Use Strategy / Goal / Roadmap patterns only when hierarchy, sequence, or execution logic is genuine.
5. Do not create a new standalone pattern when an existing pattern can express the content as a variant.
6. Preserve the title bar, safe areas, KRISS palette, spacing, and typography hierarchy from `reference.html`.
7. After selecting the pattern, select its density variant (`compact`, `standard`, `expanded`) from `density-guide.md`; the canonical pattern does not imply fixed component height.
