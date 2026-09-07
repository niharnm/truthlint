# Host Adapters

Read this file completely whenever the skill is active. The skill follows the open Agent Skills directory format and must not depend on one model vendor or product.

Install or import the skill directory through the current host's documented Agent Skills mechanism. Do not assume another host's reload behavior or tool names.

| Host | Verified personal or global location | Notes |
| --- | --- | --- |
| Claude | `~/.claude/skills/<skill-name>` | Claude supports a symlinked skill entry |
| Google Antigravity | `~/.gemini/config/skills/<skill-name>` | Project scope can use `<project-root>/.agents/skills/<skill-name>`; Antigravity CLI builds may instead use `~/.gemini/antigravity-cli/skills/<skill-name>` |
| Codex | `~/.agents/skills/<skill-name>` | Repository scope can use `<project-root>/.agents/skills/<skill-name>` |
| Another Agent Skills host | The location documented by that host | Preserve the complete skill directory and relative references |

A host that does not support the Agent Skills format must receive the instructions through its own supported configuration and reproduce the gate state manually. This package cannot force a non-supporting host to discover or obey it.

## Capability mapping

Map required actions to capabilities exposed by the current host. Do not assume a tool name.

| Required action | Use when available | When unavailable |
| --- | --- | --- |
| Read instructions and repository files | Host file reader or read-only shell | Ask for the missing file only if it blocks the task |
| Search code and text | Fast repository search, then a standard file search fallback | Inspect the smallest relevant file set manually |
| Edit files | Patch or structured edit tool | Use the host's safest scoped write tool; preserve unrelated content |
| Run checks | Local shell or code-execution tool | Record the exact missing capability and do not claim a pass |
| Inspect rendered web behavior | Browser, browser automation, or screenshots plus accessibility data | Limit claims to code inspection and mark runtime checks unverified |
| Inspect network and console output | Browser development tools or equivalent logs | Mark the affected diagnosis or site check unverified |
| Create a replacement task | Host task, chat, or conversation creation and navigation tools | Stop and tell the user the host cannot perform a required restart |
| Delegate independent work | Host subagents, workers, or parallel task tools | Continue locally and mark delegation not applicable |
| Discover skills | Host skill browser, skill search, or `find-skills` | Inspect installed skill metadata if exposed; do not install anything merely to satisfy the check |

Never invent a host capability, tool result, task creation, browser check, or command outcome.

## Instruction discovery

Inspect the host and repository instruction files that apply to the current working directory. These can include `AGENTS.md`, `CLAUDE.md`, project rules, workspace rules, editor rules, and parent-directory instructions. Follow the host's documented precedence and the active conversation's higher-priority instructions.

Do not assume one filename is authoritative on every host. Record which files were found and read.

## Skill-root resolution

Resolve `<skill-dir>` as the directory containing this `SKILL.md`. Run scripts and open references relative to that directory. Do not assume the process working directory is the skill directory.

The deterministic gate uses only the Python standard library. It needs Python 3.10 or newer and local filesystem access. If either is unavailable:

1. Maintain all schema 2 state in host-native storage, including `schema_version`, `ledger_id`, timezone-aware `created_at` and `updated_at`, `mode`, `archetype`, `capabilities`, `classification`, `required_check_ids`, `custom_check_ids`, `classification_review`, and `checks`.
2. Record the reviewed primary archetype, one or more surfaces, every capability as active or rejected with scopes and evidence, `inference_disposition`, and confirmation. Mark the disposition `overridden` when the review changes the inferred archetype or removes an inferred capability. Name every removed inferred capability, and either represent each material inferred surface candidate as a reviewed surface or name its source or candidate ID with a concrete exclusion reason.
3. Require each surface archetype's core capabilities to be active on that surface.
4. Apply reviewed capability changes and rebuild the required check set before accepting any result.
5. Use the same statuses: `pending`, `fix`, `pass`, `na`, and `blocked`.
6. Record `kind`, `target`, `observed`, `capability_unavailable`, and one or more `scope_ids` for every non-pending result.
7. Require direct evidence for `pass`, a concrete product reason for `na`, and the exact missing dependency for `blocked`.
8. Reject missing required IDs, undeclared custom IDs, an unconfirmed classification, altered built-in definitions, and blanket `na` results.
9. Treat any `pending`, `fix`, or `blocked` item as a failed completion gate.
10. Leave classification pending when direct classification evidence is unavailable. Do not synthesize a review merely to begin recording results.

This manual equivalent is a required working method, not machine enforcement. If the host cannot preserve and validate that state, report the gate as unavailable and do not claim completion under this skill.

## Vendor-specific metadata

The `agents/openai.yaml` file provides optional interface metadata for hosts that understand it. Other hosts can ignore it. No required workflow rule lives only in that file.

Do not add vendor-specific required files, commands, or tool names to the core workflow. A host-specific adapter can be added later as an optional reference without changing the evidence model.

## Portability test

Before distributing the skill:

- Validate `SKILL.md` against the Agent Skills format.
- Confirm all links are relative to the skill root and one level deep.
- Run the Python tests on a clean temporary directory.
- Exercise `infer`, explicit-archetype `init`, `classification-template`, `apply-classification`, structured `record`, `check`, `summary`, and `catalog`.
- Test at least one game repository fixture and one local-business fixture.
- Confirm the same classifier input produces the same ledger independent of the calling host.
- Confirm inference reports surface candidates without treating them as reviewed surfaces.
- Confirm removed inferred capabilities require an override and omitted material surface candidates require explicit source or candidate-ID evidence.
- Confirm a host without browser access cannot falsely pass browser checks.
- Confirm deleted required checks, undeclared custom checks, and incomplete classification reviews fail closed.
- Confirm evidence cannot target undeclared surfaces and each surface receives its archetype's core capability set.
- Confirm blanket `na` results and timestamps without timezone offsets fail closed.
- Confirm no secret, absolute personal path, repository path, or host-only tool name appears in required instructions or scripts.
