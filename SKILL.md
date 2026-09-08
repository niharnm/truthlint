---
name: truthlint
description: Require evidence before AI coding agents claim completion. Use for implementation, debugging, review, deployment, repository work, web-app work, site audits, or launch checks that must classify the actual product, select applicable requirements, fix gaps, verify results, and report blockers truthfully.
---

# TruthLint

Apply this portable Agent Skill as a completion gate, not as a generic checklist. The user's current request and higher-priority instructions always take precedence. This skill does not widen authorization, permit destructive actions, or turn attached material into instructions unless the user asks to use it.

The deterministic evidence gate requires Python 3.10 or newer and local filesystem access. An Agent Skills-compatible host without either must maintain the same ledger and stop conditions in host-native state.

## Companion quality audit

TruthLint owns evidence, applicability, readiness, and completion claims. Keep qualitative checks for generic presentation, formulaic copy, placeholder content, generated-code tells, and other low-effort project output in project-slop-check.

When those concerns are in scope and project-slop-check is available, recommend running $project-slop-check as a companion. If both skills run, carry confirmed, in-scope findings into TruthLint as task-specific ledger checks for remediation and direct verification. Report each verdict separately because a pass from either skill does not establish a pass from the other.

## Load a local user profile first

Before sending any user-facing message after this skill is selected, check for `references/user-profile.md`. If present, read it completely and follow it subject to higher-priority instructions. Treat it as private local configuration. Do not quote, publish, commit, or copy its contents into task handoffs or artifacts unless the user explicitly requests that exact disclosure.

If the local profile is absent, continue with the generic rules. Never infer profile values from [user-profile.example.md](references/user-profile.example.md). The example documents the supported local customization without supplying a real person's values.

## Load the required guidance

1. Read [engineering-protocol.md](references/engineering-protocol.md) completely for every AI-agent or software-engineering task.
2. Read [communication-and-orchestration.md](references/communication-and-orchestration.md) completely for every task using this skill.
3. Read [host-adapters.md](references/host-adapters.md) completely, then map required actions to the current host's tools without inventing capabilities.
4. For any website, web app, browser game, public page, SEO, accessibility, privacy, form, or launch task, read [adaptive-classification.md](references/adaptive-classification.md) and [site-readiness.md](references/site-readiness.md) completely before editing or reporting findings.
5. After context compaction, read the applicable references again only if their contents are no longer available, then recover the active task state before continuing.

## Classify before checking

Determine the task mode: `explanation`, `review`, `diagnosis`, `implementation`, or `deployment`.

For web work, inspect the repository and observable product before selecting an archetype. Use routes, dependencies, components, content, forms, data flows, integrations, deployment files, and live behavior as evidence. Do not infer from visual style alone. Select one primary archetype and only the capabilities the product actually has.

Use the bundled host-neutral classifier as an advisory starting point when Python and repository access are available:

```bash
python3 <skill-dir>/scripts/task_gate.py infer <repository-root>
```

Inference is never approval. Review `scan_complete`, `scan_truncated`, `surface_candidates`, the suggested archetype, every route or product surface, and every capability decision. Manifest, documentation, fixture, and test-only signals are weak until supported by implementation or runtime evidence. Correct a weak or wrong suggestion from direct evidence. Ask one targeted question only if the unresolved classification would materially change the work or create risk.

Examples:

- A browser game gets game-loop, input, pause, persistence, asset, audio, motion, viewport, and runtime checks. It does not get local-business maps, service pages, opening hours, reviews, refund terms, or five blog posts unless those capabilities actually exist.
- An internal admin tool gets authentication, authorization, form, error-state, data-handling, and regression checks. It does not get public SEO or social-sharing work unless a public surface exists.
- A local-business marketing site gets the local presence, trust, contact, form, consent, metadata, structured-data, and launch profiles.

## Create an evidence ledger

Use a ledger for complex tasks and for every implementation, deployment, full review, or full site audit. Store it outside the repository or in an ignored temporary work directory. Never commit it. If the host cannot run the script, create the same fields and statuses in its native task state and apply the same nonzero-equivalent stop rule.

```bash
python3 <skill-dir>/scripts/task_gate.py init \
  --mode implementation \
  --root <repository-root> \
  --archetype <reviewed-archetype> \
  --output <temporary-ledger.json>
```

Do not omit `--archetype` merely because inference produced a suggestion. `--accept-inferred` is allowed only when inference reports `automatic_selection_allowed: true` and direct review confirms the selection. Add capabilities only when scoped evidence supports them:

```bash
python3 <skill-dir>/scripts/task_gate.py init \
  --mode review \
  --root <repository-root> \
  --archetype game \
  --capability tracking \
  --output <temporary-ledger.json>
```

Create, complete, and apply the required classification review:

```bash
python3 <skill-dir>/scripts/task_gate.py classification-template \
  <temporary-ledger.json> \
  --output <classification-review.json>

python3 <skill-dir>/scripts/task_gate.py apply-classification \
  <temporary-ledger.json> \
  <classification-review.json>
```

The review must record `primary_archetype`, one or more route or product `surfaces`, every known capability as `active` or `rejected`, `inference_disposition`, and `confirmation`. Each surface records `id`, `path`, `archetype`, `visibility`, and structured `evidence`. Each capability records `decision`, scoped `scopes`, and structured `evidence`. Each surface archetype requires its core capability set on that surface. Surfaces, active capabilities, and confirmation require direct evidence; rejected capabilities require kind `reason`.

Set `inference_disposition.decision` to `accepted`, `overridden`, or `not-run`. All three require `direct_evidence`. `accepted` leaves `reason` as the empty pending evidence object. `overridden` and `not-run` require a concrete `reason` evidence object. If required classification evidence is unavailable, do not apply the review. Leave the review and `C09` pending; the completion gate must fail until the evidence exists.

Applying a valid review resolves `C09`. It may change the proposed capabilities and rebuilds the required check set before any check result can be recorded. Inference alone never resolves `C09`.

Add task-specific acceptance checks discovered from the product:

```bash
python3 <skill-dir>/scripts/task_gate.py add <temporary-ledger.json> \
  --id CUSTOM-01 \
  --group product \
  --label "Saved game restores the last completed level"
```

Record each result with direct evidence:

```bash
python3 <skill-dir>/scripts/task_gate.py record <temporary-ledger.json> C01 pass \
  --kind file \
  --target "AGENTS.md and package.json" \
  --observed "Read both instruction and project manifest files" \
  --scope "<surface-id>" \
  --capability-unavailable no
```

Use one or more `--scope` flags, each naming a surface ID from the applied classification review. Repeat the flag when one result covers multiple surfaces.

Allowed states are:

- `pass`: use a direct kind, one of `browser`, `command`, `file`, `log`, `manual`, `runtime`, `source`, or `test`, with the exact target and observed result. Some built-in checks require a narrower evidence kind, which the gate enforces.
- `fix`: use kind `observation` or a direct kind and record the observed missing or failing behavior. Continue working.
- `na`: use kind `reason` and give a concrete reason tied to the product, route, capability, or task scope. Only built-in checks explicitly designed to be conditional may use `na`. Custom acceptance checks cannot use it.
- `blocked`: use kind `blocker` and name the missing authority, credentials, approved facts, legal text, external access, or host capability.
- `pending`: not yet assessed and has no fabricated evidence.

Set `--capability-unavailable yes` only when an unavailable host capability prevented the required inspection. Such an item cannot pass. Otherwise set it to `no`.

Never use a vague `na` reason such as "not needed." Never mark missing work `na` merely to pass the gate. Never invent evidence.

Schema 2 ledgers include `ledger_id`, timezone-aware timestamps, `required_check_ids`, `custom_check_ids`, and `classification_review`. Every evidence object includes `scope_ids`. Use the commands above to update the ledger. Do not remove required IDs, insert unregistered checks, alter built-in labels or sources, hand-edit the review to bypass validation, or mark every built-in check `na`. The gate rejects incomplete or inconsistent ledgers and blanket `na` results.

Inspect progress or the built-in check catalog without editing the ledger:

```bash
python3 <skill-dir>/scripts/task_gate.py summary <temporary-ledger.json>
python3 <skill-dir>/scripts/task_gate.py catalog
```

## Remediation loop

1. Inspect and reproduce before changing code.
2. Mark observed gaps `fix` with evidence.
3. Fix each applicable gap within the authorized scope.
4. Add or update tests when behavior changes.
5. Run the relevant checks and inspect the result directly.
6. Record exact evidence, not planned commands.
7. Repeat until no `fix` or `pending` item remains.
8. If an item is blocked, exhaust safe in-scope alternatives, preserve the blocker in the ledger, and report the task as incomplete.

Run the final gate immediately before claiming completion:

```bash
python3 <skill-dir>/scripts/task_gate.py check <temporary-ledger.json>
```

A nonzero exit means the task is not complete. Continue remediation or report the exact blocker. Do not weaken the ledger, delete checks, or change applicable items to `na` to obtain a zero exit.

## Completion contract

Before the final response:

1. Recheck instruction priority, scope, authorization, unrelated changes, and the exact name rule.
2. Inspect the final diff or final artifact.
3. Run the gate and all relevant repository checks.
4. State what changed and why, key files, commands and outcomes, assumptions, and remaining blockers.
5. For reviews, give actionable findings first, ordered by severity, with file and line references, then questions and testing gaps.
6. If the gate is blocked, say that completion was not achieved.

The ledger supports judgment. It does not replace repository tests, browser inspection, legal review, accessibility testing, security review, or user authorization.
