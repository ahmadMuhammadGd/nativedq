# Documentation standard

These rules are mandatory for project documentation. They apply to code,
configuration, examples, and documentation changes.

## Canonical location

- All project documentation lives under `docs/`.
- The only Markdown files allowed outside `docs/` are:
  - the root `README.md` (public entry point and links);
  - the root `AGENTS.md` (instructions for AI agents);
  - files required by tooling, packaging, licensing, or external platform
    conventions.
- Agent task briefs under `agents/` are tooling inputs executed by the agent
  harness, not project documentation. Do not add project documentation there.
- Do not place documentation in package roots or source directories. Package
  documentation belongs in `docs/packages/`.

## Structure

```text
docs/
├── README.md            documentation index and navigation
├── architecture/        system design, boundaries, dependency direction
├── standards/           mandatory project conventions (this directory)
├── packages/            one document per Python package
├── guides/              installation, usage, development instructions
├── reference/           detailed technical reference
└── decisions/           architecture decision records, when needed
```

Create directories and documents only when they have real content. Do not add
empty placeholders. Add `docs/decisions/` only when a decision requires a
durable rationale.

## Package documents

Every Python package in `packages/` must have a corresponding document in
`docs/packages/`, named after the package without its prefix:

- `packages/nativedq-core/` → `docs/packages/core.md`
- `packages/nativedq-executor-spark35/` → `docs/packages/executor-spark35.md`
- A new package requires its document in the same change.

Each package document covers, where applicable:

1. Purpose and architectural role.
2. Responsibilities and explicit boundaries.
3. Installation and dependency requirements, including extras.
4. Public APIs and extension points.
5. Minimal, runnable usage examples.
6. Configuration and supported options.
7. Compatibility constraints (Python, core, engine versions).
8. Testing and development commands.
9. Known limitations and unsupported behavior.

Document what the code does. Do not invent APIs, configuration options, or
compatibility guarantees.

## Writing rules

- Use concise, technically precise language and consistent terminology.
- Prefer actionable instructions and runnable commands.
- Document supported public behavior rather than unstable internals.
- State the core-to-adapter dependency direction explicitly where relevant.
- Distinguish required dependencies from optional integrations and extras.
- Use relative links for internal documents and verify them after moves.
- Avoid duplicated documents; link to the authoritative document instead.
- Do not claim standards compliance or successful execution without evidence.
- Keep examples, commands, paths, and configuration synchronized with the code.

## Maintenance

- Update documentation whenever a code change alters documented behavior,
  public APIs, configuration, installation, compatibility, or supported
  features.
- When moving or renaming a document, update every reference and check the
  affected links.
- When consolidating documents, preserve their useful content before removing
  the old file.
- Keep the index in `docs/README.md` accurate: every document should be
  reachable from it.
- Keep the root `README.md` brief and link to `docs/README.md` instead of
  duplicating detailed documentation.
- Keep `AGENTS.md` focused on cross-task agent instructions and link to the
  applicable standards in `docs/`.

## Validation

Before finishing a documentation change:

1. Search for Markdown files outside the approved locations.
2. Check relative links resolve to existing files.
3. Confirm every package has a document in `docs/packages/`.
4. Confirm `docs/README.md` links to each document.
5. Check for stale paths, empty files, and duplicated explanations.
6. Report any check that could not be executed.
