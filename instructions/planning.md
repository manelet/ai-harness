# Planning and specifications

Use the pinned Superpowers workflow for planning, design, and specification requests. The installer also exposes the vendored skills to the native skill directories of Codex and Claude Code.

All paths below are relative to this source file in the harness. Resolve them there, not against the project being planned.

## Workflow

1. Read and follow `../vendor/superpowers/skills/brainstorming/SKILL.md` when turning an idea into a design or spec. Inspect the target project, clarify material unknowns, compare approaches where useful, and write a concrete design.
2. Read and follow `../vendor/superpowers/skills/writing-plans/SKILL.md` when turning an approved spec or sufficiently clear requirements into an implementation plan. Include exact files, independently verifiable tasks, acceptance criteria, and relevant validation commands.
3. Review artifacts for contradictions, ungrounded assumptions, missing requirements, and ambiguous tasks. Clearly identify unresolved facts; never invent them to eliminate a placeholder.

Save artifacts in the **target project**, not automatically in this harness:

- Specs: `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`.
- Plans: `docs/superpowers/plans/YYYY-MM-DD-<topic>.md`.

Use an existing project convention or a user-requested location instead when applicable. If the user explicitly asks for a spec file, create one even when upstream would classify the change as bounded and omit the document. Link each plan to its spec.

## Integration boundaries

- Apply these skills to planning and spec work. Do not introduce a mandatory brainstorming ceremony for every unrelated, already-authorized small edit.
- Keep conversation concise; include enough detail in the artifacts to make them useful to an implementer.
- Follow the user's current scope, existing authorization, and `security.md` over conflicting upstream workflow defaults. Do not repeat approvals already given for the same scope.
- A planning-only request ends with the requested artifacts. It does not authorize implementation, commits, deployment, or subagent execution. Obtain the necessary user direction before starting a new phase; prepare the concrete artifact before asking for its review.
- The upstream execution skills named in plan headers and handoffs are not bundled here. Do not claim they are installed or emit a mandatory dependency on them. Describe the handoff using the available client capabilities and the authorized workflow instead.
- Upstream visual-companion files are preserved for completeness. Do not start their scripts or optional browser service automatically; inspect them before any explicitly requested use.
- If a bundled skill cannot be read, report the missing file rather than silently claiming to use Superpowers.
