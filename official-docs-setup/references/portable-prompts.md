# Portable Prompts

Use these templates when you want the same behavior in tools other than Codex.

## System Or Developer Prompt

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

## Task Prefix

```text
Use official documentation first, then write the installation or runtime code. Prefer first-party sources, state assumptions, and include the official links you used.
```

## No-Browsing Variant

```text
Use only the official documentation provided in the prompt or repository. If that is insufficient, stop and say exactly what official source is missing instead of guessing.
```

## Acceptance Check

Use this quick checklist before returning an answer:

- Did I verify the commands against an official source?
- Did I avoid mixing operating systems, shells, or package managers?
- Did I include assumptions and version constraints?
- Did I include a smoke test or verification step when possible?
- Did I provide official source links or explicitly say why I could not?
