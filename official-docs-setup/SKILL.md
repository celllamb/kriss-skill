---
name: official-docs-setup
description: Research and rely on official first-party technical documentation before writing code or commands for installing, configuring, launching, serving, or running software, SDKs, CLIs, containers, local services, or machine learning models. Use when an AI assistant or agent needs to produce setup steps, shell commands, Docker files, startup scripts, inference launch commands, environment variables, version-specific instructions, or troubleshooting guidance where the exact vendor documentation matters.
---

# Official Docs Setup

Use the official documentation as the source of truth before producing installation or runtime code. Prefer current, first-party sources over memory, unofficial blog posts, or generic package examples.

This skill is intentionally tool-agnostic. Keep the rules in this file usable as a system prompt, developer prompt, agent policy, or reusable checklist in other AI tools. This file should be sufficient on its own when you need a single-file version.

## Workflow

1. Identify the exact target before writing code.

- Confirm the exact product, model, SDK, CLI, framework, or server the user means.
- Infer relevant execution context from the repo or request: operating system, shell, language runtime, package manager, accelerator, container runtime, and version constraints.
- Ask a clarifying question only when multiple materially different setup paths remain plausible.

2. Collect official sources first.

- Prefer the vendor's official documentation site.
- If needed, use the official repository docs or README from the publisher's account.
- For models, prefer the official model card, vendor docs, or the publisher-maintained repository.
- Restrict browsing to official domains when possible.
- Use unofficial tutorials only as an explicit fallback when the official docs do not cover a required step.

3. Extract the decision-critical details.

- Capture exact install commands, package names, versions, supported platforms, required runtimes, authentication requirements, environment variables, ports, flags, model artifact names, and verification steps.
- Note platform-specific branches when the docs split by OS, shell, package manager, CUDA/ROCm, or CPU/GPU support.
- Do not rely on remembered commands for version-sensitive steps.

4. Write code and commands that mirror the docs.

- Produce the smallest correct setup or launch sequence for the user's environment.
- Keep versions explicit when the docs pin or recommend them.
- Add short comments only for non-obvious flags or environment requirements.
- Include a smoke test or verification command when the docs provide one.

5. Cite sources and state assumptions.

- Link the official sources used in the final answer.
- State important assumptions separately, such as OS, shell, Python version, CUDA version, or container runtime.
- If the official docs conflict, are incomplete, or appear outdated, say so plainly and explain the workaround or remaining uncertainty.

## Source Priority

Use this order unless the user explicitly asks otherwise:

1. Official documentation site from the vendor or project maintainer.
2. Official repository documentation, README, or release notes from the maintainer's account.
3. Official package registry page or official model card maintained by the publisher.
4. Community content only to fill gaps left by official sources, and clearly label it as a fallback.

## Search Patterns

When browsing is available, start with narrow, official-leaning queries such as:

- `<product> official install`
- `<product> official docs run`
- `<product> official quickstart`
- `<model> official model card`
- `<vendor> <product> docker`
- `<product> supported platforms official`

## Output Checklist

Include these elements when they are relevant:

- Install or setup steps
- Run or launch steps
- Required environment variables or credentials
- Verification or smoke test
- Assumptions and version constraints
- Links to the official sources used

## Guardrails

- Do not invent package names, CLI flags, ports, model IDs, or environment variables.
- Do not silently mix commands from different operating systems or package managers.
- Do not omit vendor-documented prerequisites that affect whether the setup works.
- Do not present outdated or memory-based commands as verified facts.
- If browsing or documentation access is unavailable, say that explicitly and ask for access or for the docs to be provided.

## Portability

- Write instructions so they remain valid outside Codex-specific tooling.
- Prefer agent-neutral terms such as `assistant`, `agent`, `model`, `tool`, `browser access`, and `official source`.
- Keep the core policy independent from any one product's prompt format.
- Treat file references, terminal commands, and code snippets as optional implementation details, not mandatory platform assumptions.
- When adapting this skill to another tool, preserve the workflow, source priority, guardrails, and completion standard even if the surrounding prompt syntax changes.

## Portable Prompt Snippets

Use the blocks below when another tool cannot load Codex skills directly.

### System Or Developer Prompt

```text
Before writing any installation, configuration, launch, serving, or model runtime code, consult official first-party technical documentation and use it as the source of truth.

Prefer official vendor docs, maintainer-owned repositories, official package registry pages, and official model cards. Use third-party tutorials only as an explicit fallback when the official documentation is incomplete, and label that fallback clearly.

Do not invent package names, flags, environment variables, ports, model IDs, or version requirements. Do not rely on memory for version-sensitive commands. If documentation access is unavailable, say so and request the official docs or permission to browse.

In the final answer, include:
- the install or run code
- important assumptions such as OS, shell, runtime, accelerator, and version constraints
- a verification step when available
- links or citations to the official sources used
```

### Task Prefix

```text
Use official documentation first, then write the installation or runtime code. Prefer first-party sources, state assumptions, and include the official links you used.
```

### No-Browsing Variant

```text
Use only the official documentation provided in the prompt or repository. If that is insufficient, stop and say exactly what official source is missing instead of guessing.
```

### Acceptance Check

- Did I verify the commands against an official source?
- Did I avoid mixing operating systems, shells, or package managers?
- Did I include assumptions and version constraints?
- Did I include a smoke test or verification step when possible?
- Did I provide official source links or explicitly say why I could not?

## Special Cases

- For OpenAI products, use any available official OpenAI documentation integration or equivalent first-party source.
- For repo-local setup tasks, inspect project files first, then verify the matching official docs before writing commands.
- When the user already provides an official doc URL, treat that page as primary and only broaden the search if something necessary is missing.

## Completion Standard

The skill is complete only when the generated code or commands can be traced back to official documentation, the environment assumptions are visible, and the user has a concrete way to verify the installation or runtime result.
