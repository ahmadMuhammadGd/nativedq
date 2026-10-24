# Task: Standardize Repository Documentation Under `docs/`

## Objective

Audit and reorganize the repository's documentation so that **all project documentation lives under `docs/`**, following a consistent, maintainable structure.

Update existing documentation, create missing documents, fix internal links, and ensure that documentation accurately reflects the implementation and the core–adapter architecture.

The root `AGENTS.md` and root `README.md` are intentional exceptions:
- `AGENTS.md` contains concise, mandatory instructions for AI agents and links to the applicable standards in `docs/`.
- The root `README.md` serves as the project's public entry point, containing a brief overview, quick start, and links to detailed documentation.

Do not create additional documentation files outside these exceptions unless explicitly required by a tooling or publishing convention.

## 1. Inspect Before Modifying

Before making changes:

- Read the root `AGENTS.md` and existing documentation.
- Inspect the repository structure, package boundaries, public APIs, and `pyproject.toml` files.
- Identify every documentation file, including Markdown files, architecture diagrams, design documents, specifications, and contributor guides.
- Identify references to existing documentation throughout the repository.
- Determine which documents are outdated, duplicated, missing, or stored in inappropriate locations.

Do not move files blindly. Preserve useful content, consolidate duplicates where appropriate, and retain documentation required by tools or external platforms.

## 2. Required Documentation Structure

Organize documentation under `docs/` using this structure as a starting point. Adapt it to the repository's actual needs instead of creating empty or unnecessary directories.

```text
docs/
├── README.md
├── architecture/
│   ├── overview.md
│   └── core-adapter.md
├── standards/
│   ├── documentation.md
│   └── packaging.md
├── packages/
│   ├── core.md
│   ├── executor-spark35.md
│   └── artifact-iceberg.md
├── guides/
│   ├── installation.md
│   ├── usage.md
│   └── development.md
├── reference/
│   └── configuration.md
└── decisions/
```

Requirements:

- `docs/README.md` is the documentation index.
- `docs/architecture/` describes architectural decisions, component boundaries, and dependency direction.
- `docs/standards/` contains mandatory project conventions.
- `docs/packages/` documents individual packages, their responsibilities, public APIs, dependencies, and integration behavior.
- `docs/guides/` contains task-oriented instructions for installation, usage, and development.
- `docs/reference/` contains detailed technical reference material.
- `docs/decisions/` contains architecture decision records when needed.

Only create documents that have meaningful content and a clear purpose.

## 3. Package Documentation

Every Python package, including the core and each adapter, MUST have a corresponding document under `docs/packages/`.

For example:

- `packages/dqt-core/` → `docs/packages/core.md`
- `packages/dqt-executor-spark35/` → `docs/packages/executor-spark35.md`
- `packages/dqt-artifact-iceberg/` → `docs/packages/artifact-iceberg.md`

Each package document MUST cover the applicable sections:

1. Purpose and architectural role.
2. Responsibilities and explicit boundaries.
3. Installation and dependency requirements.
4. Public APIs and extension points.
5. Minimal usage examples.
6. Configuration and supported options.
7. Compatibility constraints.
8. Testing and development instructions.
9. Known limitations and unsupported behavior.

Document actual behavior. Do not invent APIs, configuration options, compatibility guarantees, or future capabilities.

## 4. Enforce the Documentation Location Rule

All project documentation MUST live under `docs/`, except for the root `AGENTS.md`, root `README.md`, and files that must exist elsewhere for repository tooling, packaging, licensing, or external platform conventions.

This includes documentation currently stored in:

- Package source directories.
- Individual package roots.
- Repository subdirectories.
- Agent task or prompt directories.
- Miscellaneous Markdown files outside `docs/`.

When documentation is found elsewhere:

1. Determine its purpose and whether it is still relevant.
2. Move it to an appropriate location under `docs/`.
3. Update references and links to the new location.
4. Consolidate duplicated content when safe.
5. Preserve required tool-specific files in their conventional locations when moving them would break functionality.

Do not relocate `pyproject.toml`, source code, tests, license files, or configuration files simply because they contain descriptive text.

## 5. Root README and AGENTS.md

### Root `README.md`

Keep it concise and focused on:

- Project purpose.
- Key capabilities.
- Quick-start instructions.
- High-level architecture.
- Links to `docs/README.md` and other relevant documentation.

Avoid duplicating the full technical documentation.

### Root `AGENTS.md`

Keep it concise and focused on instructions that agents must follow across tasks.

Include requirements that:

- `docs/` is the canonical location for project documentation.
- Agents must follow `docs/standards/documentation.md`.
- Package-specific documentation belongs in `docs/packages/`.
- Documentation must remain accurate and aligned with the implementation.
- Relevant documentation must be updated whenever code changes affect documented behavior.
- Agents must verify links and report validation limitations.

Do not copy the entire documentation standard into `AGENTS.md`.

## 6. Writing and Maintenance Standards

Follow these principles throughout the documentation:

- Use concise, technically precise language.
- Prefer actionable instructions and runnable examples.
- Use consistent terminology across the repository.
- Document public APIs and supported behavior rather than unstable internals.
- Explain the core–adapter dependency direction explicitly.
- Distinguish required dependencies from optional integrations.
- Use relative links for internal documentation where practical.
- Avoid redundant documents and duplicated explanations.
- Do not claim compatibility, standards compliance, or successful execution without evidence.
- Keep examples, commands, paths, and configuration aligned with the current codebase.

Create `docs/standards/documentation.md` containing the durable documentation rules established by this task.

## 7. Validate the Result

After reorganizing the documentation:

1. Search for Markdown and other documentation files outside the approved locations.
2. Verify that no required content was lost during moves or consolidation.
3. Check and repair internal relative links.
4. Update references in `AGENTS.md`, the root `README.md`, package metadata, and other relevant files.
5. Confirm that every Python package has a corresponding document in `docs/packages/`.
6. Verify that the documentation index links to the relevant documents.
7. Check for stale paths, duplicate content, empty documents, and broken references.
8. Ensure any documentation files retained outside `docs/` have a concrete tooling, packaging, licensing, or platform justification.

Use existing repository tools where available. If automated link checking is unavailable, perform reasonable static checks and state the limitations.

## 8. Constraints

- Preserve source code behavior and public APIs.
- Do not perform unrelated refactoring.
- Do not introduce unnecessary documentation frameworks or dependencies.
- Do not create empty placeholder documents merely to satisfy the proposed structure.
- Do not remove useful documentation before confirming that its content has been preserved.
- Do not move files whose locations are required by packaging, tooling, licensing, or platform conventions.
- Make the smallest coherent set of changes that achieves the objective.

## 9. Deliverables

At completion, report:

1. The final documentation directory structure.
2. Files moved, created, consolidated, or removed.
3. The rationale for any documentation retained outside `docs/`.
4. Links repaired and duplicate content eliminated.
5. Validation commands executed and their actual results.
6. Remaining gaps or checks that could not be completed.

**Execute the reorganization directly.** Do not stop after proposing a structure or listing recommendations. Inspect, modify, and validate the repository, and report the actual outcome.