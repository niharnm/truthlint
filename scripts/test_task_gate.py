#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).with_name("task_gate.py")
SPEC = importlib.util.spec_from_file_location("task_gate", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load task_gate.py")
task_gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(task_gate)


class TaskGateTests(unittest.TestCase):
    def make_repo(
        self, files: dict[str, str]
    ) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        for rel, content in files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return temporary, root

    def evidence(
        self,
        kind: str = "test",
        target: str = "isolated test fixture",
        observed: str = "Observed the expected result in the isolated fixture",
        capability_unavailable: bool = False,
        scope_ids: list[str] | None = None,
    ) -> dict[str, object]:
        return {
            "kind": kind,
            "target": target,
            "observed": observed,
            "capability_unavailable": capability_unavailable,
            "scope_ids": ["primary"] if scope_ids is None else scope_ids,
        }

    def passing_kind(self, check_id: str) -> str:
        allowed = task_gate.PASS_KIND_REQUIREMENTS.get(check_id)
        return min(allowed) if allowed else "test"

    def classification_review(
        self,
        ledger: dict[str, object],
        hybrid: bool = False,
    ) -> dict[str, object]:
        archetype = str(ledger["archetype"])
        if hybrid:
            surfaces = [
                {
                    "id": "landing",
                    "path": "/",
                    "archetype": "marketing",
                    "visibility": "public",
                    "evidence": self.evidence(
                        "source",
                        "src/landing/page.tsx",
                        "The root route is a public marketing surface",
                        scope_ids=["landing"],
                    ),
                },
                {
                    "id": "play",
                    "path": "/play",
                    "archetype": archetype,
                    "visibility": "public",
                    "evidence": self.evidence(
                        "source",
                        "src/scenes/LevelOne.ts",
                        "The play route contains the primary game surface",
                        scope_ids=["play"],
                    ),
                },
            ]
        else:
            visibility = "non-web" if archetype == "non-web" else "public"
            surfaces = [
                {
                    "id": "primary",
                    "path": "repository" if archetype == "non-web" else "/",
                    "archetype": archetype,
                    "visibility": visibility,
                    "evidence": self.evidence(
                        "source",
                        "repository root",
                        "The inspected source confirms the selected primary archetype",
                        scope_ids=["primary"],
                    ),
                },
            ]
        surface_ids = [surface["id"] for surface in surfaces]
        selected = set(ledger["capabilities"])
        decisions: dict[str, dict[str, object]] = {}
        for capability in sorted(task_gate.CAPABILITY_GROUPS):
            active = capability in selected
            if hybrid and capability == "game":
                scopes = ["play"]
            elif hybrid and capability in {"marketing", "public-discovery"}:
                scopes = ["landing"]
            else:
                scopes = surface_ids
            decisions[capability] = {
                "decision": "active" if active else "rejected",
                "scopes": scopes,
                "evidence": self.evidence(
                    "source" if active else "reason",
                    f"capability:{capability}",
                    (
                        f"Direct repository evidence activates {capability} for these surfaces"
                        if active
                        else f"No repository behavior requires {capability} on the assessed surfaces"
                    ),
                    scope_ids=scopes,
                ),
            }
        classification = ledger["classification"]
        if classification is None:
            disposition_decision = "not-run"
        elif classification["selected_archetype"] == archetype and set(
            classification["selected_capabilities"]
        ).issubset(selected):
            disposition_decision = "accepted"
        else:
            disposition_decision = "overridden"
        removed_capabilities = (
            sorted(set(classification["selected_capabilities"]) - selected)
            if classification is not None
            else []
        )
        inferred_sources = (
            sorted(
                candidate["source"]
                for candidate in classification["surface_candidates"]
            )
            if classification is not None
            else []
        )
        disposition_reason = (
            task_gate.empty_evidence()
            if disposition_decision == "accepted"
            else self.evidence(
                "reason",
                "inference decision",
                (
                    "Repository inference was not run because the archetype was supplied directly"
                    if disposition_decision == "not-run"
                    else (
                        "Direct surface evidence supersedes the inferred selection; removed "
                        + ", ".join(removed_capabilities or ["no capabilities"])
                        + "; reviewed "
                        + ", ".join(inferred_sources or ["repository sources"])
                    )
                ),
                scope_ids=surface_ids,
            )
        )
        return {
            "primary_archetype": archetype,
            "surfaces": surfaces,
            "capabilities": decisions,
            "confirmation": self.evidence(
                "manual",
                "route and capability review",
                "Reviewed each product surface and every capability decision",
                scope_ids=surface_ids,
            ),
            "inference_disposition": {
                "decision": disposition_decision,
                "direct_evidence": self.evidence(
                    "source",
                    "repository surface review",
                    "Direct source inspection confirms the final archetype selection",
                    scope_ids=surface_ids,
                ),
                "reason": disposition_reason,
            },
        }

    def complete_classification(
        self,
        ledger: dict[str, object],
        hybrid: bool = False,
    ) -> None:
        raw = self.classification_review(ledger, hybrid)
        now = task_gate.utc_now()
        surfaces = [{**surface, "updated_at": now} for surface in raw["surfaces"]]
        decisions = {
            capability: {**decision, "updated_at": now}
            for capability, decision in raw["capabilities"].items()
        }
        review = {
            "status": "pass",
            "primary_archetype": raw["primary_archetype"],
            "surfaces": surfaces,
            "capabilities": decisions,
            "confirmation": raw["confirmation"],
            "inference_disposition": {
                **raw["inference_disposition"],
                "updated_at": now,
            },
            "updated_at": now,
        }
        ledger["classification_review"] = review
        ledger["checks"]["C09"]["status"] = "pass"
        ledger["checks"]["C09"]["evidence"] = raw["confirmation"]
        ledger["checks"]["C09"]["updated_at"] = now
        ledger["updated_at"] = now

    def resolve_all_checks(self, ledger: dict[str, object]) -> None:
        self.complete_classification(ledger)
        for check_id, record in ledger["checks"].items():
            if check_id == "C09":
                continue
            record["status"] = "pass"
            record["evidence"] = self.evidence(
                self.passing_kind(check_id),
                f"fixture:{check_id}",
                f"Verified check {check_id} in the isolated test fixture",
                scope_ids=["primary"],
            )
            record["updated_at"] = task_gate.utc_now()
        ledger["updated_at"] = task_gate.utc_now()

    def test_catalog_lists_every_check(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(task_gate.command_catalog(Namespace()), 0)
        check_lines = output.getvalue().split("Checks:\n", 1)[1].splitlines()
        catalog_ids = {line.split(" ", 2)[1] for line in check_lines}
        self.assertEqual(catalog_ids, set(task_gate.CHECKS))

    def test_game_inference_avoids_business_checks(self) -> None:
        temporary, root = self.make_repo(
            {
                "package.json": '{"dependencies":{"phaser":"4.0.0","vite":"7.0.0"}}',
                "src/scenes/LevelOne.ts": "export class GameState { sprite = 'player'; }",
            }
        )
        self.addCleanup(temporary.cleanup)
        result = task_gate.infer_repository(root)
        self.assertEqual(result["selected_archetype"], "game")
        ledger = task_gate.build_ledger(
            "review",
            result["selected_archetype"],
            result["selected_capabilities"],
            result,
        )
        self.assertIn("G01", ledger["checks"])
        self.assertIn("P06", ledger["checks"])
        self.assertNotIn("B07", ledger["checks"])
        self.assertNotIn("B15", ledger["checks"])
        self.assertNotIn("P03", ledger["checks"])

    def test_local_business_inference_selects_local_checks(self) -> None:
        temporary, root = self.make_repo(
            {
                "package.json": '{"dependencies":{"next":"16.0.0","react":"20.0.0"}}',
                "app/page.tsx": (
                    "const schema = 'LocalBusiness'; const hours = 'Opening Hours'; "
                    "const area = 'Service Area'; const map = 'maps.google.com';"
                ),
            }
        )
        self.addCleanup(temporary.cleanup)
        result = task_gate.infer_repository(root)
        self.assertEqual(result["selected_archetype"], "local-business")
        ledger = task_gate.build_ledger(
            "implementation",
            result["selected_archetype"],
            result["selected_capabilities"],
            result,
        )
        self.assertIn("W14", ledger["checks"])
        self.assertIn("B07", ledger["checks"])
        self.assertIn("B14", ledger["checks"])
        self.assertNotIn("P03", ledger["checks"])

    def test_explicit_archetype_keeps_inferred_capabilities_for_review(self) -> None:
        temporary, root = self.make_repo(
            {
                "package.json": '{"dependencies":{"phaser":"4.0.0","vite":"7.0.0"}}',
                "src/scenes/Main.ts": "export const GameState = {};",
            }
        )
        self.addCleanup(temporary.cleanup)
        ledger_path = root / "ledger.json"
        args = Namespace(
            root=str(root),
            archetype="non-web",
            capability=[],
            mode="review",
            output=str(ledger_path),
            force=False,
        )
        with redirect_stdout(io.StringIO()):
            self.assertEqual(task_gate.command_init(args), 0)
        payload = json.loads(ledger_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["capabilities"], ["game", "web-core"])
        self.assertIn("G01", payload["checks"])

        manual_path = root / "manual-ledger.json"
        args.root = None
        args.output = str(manual_path)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(task_gate.command_init(args), 0)
        payload = json.loads(manual_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["capabilities"], [])
        self.assertNotIn("G01", payload["checks"])

    def test_not_applicable_requires_specific_evidence(self) -> None:
        ledger = task_gate.build_ledger("explanation", "non-web", [], None)
        ledger["checks"]["C01"]["status"] = "na"
        ledger["checks"]["C01"]["evidence"] = self.evidence(
            "reason",
            "task scope",
            "not needed",
        )
        ledger["checks"]["C01"]["updated_at"] = task_gate.utc_now()
        errors = task_gate.validate_ledger(ledger)
        self.assertTrue(any("too vague" in error for error in errors))

    def test_fail_closed_rejects_missing_top_level_fields_and_empty_checks(
        self,
    ) -> None:
        payload = {"schema_version": task_gate.SCHEMA_VERSION, "checks": {}}
        errors = task_gate.validate_ledger(payload)
        self.assertTrue(any("missing fields" in error.lower() for error in errors))
        self.assertTrue(any("must not be empty" in error for error in errors))

    def test_fail_closed_rejects_deleted_or_undeclared_checks(self) -> None:
        deleted = task_gate.build_ledger("explanation", "non-web", [], None)
        deleted["checks"].pop("C01")
        errors = task_gate.validate_ledger(deleted)
        self.assertTrue(
            any("missing required checks: C01" in error for error in errors)
        )

        undeclared = task_gate.build_ledger("explanation", "non-web", [], None)
        undeclared["checks"]["G01"] = task_gate.check_record("G01", ["custom"])
        errors = task_gate.validate_ledger(undeclared)
        self.assertTrue(any("undeclared checks: G01" in error for error in errors))

    def test_fail_closed_rejects_modified_builtin_definition_and_sources(self) -> None:
        ledger = task_gate.build_ledger("explanation", "non-web", [], None)
        ledger["checks"]["C01"]["label"] = "A different requirement"
        ledger["checks"]["C02"]["sources"] = ["custom"]
        errors = task_gate.validate_ledger(ledger)
        self.assertTrue(
            any(
                "C01: built-in group or label was modified" in error for error in errors
            )
        )
        self.assertTrue(any("C02: sources do not match" in error for error in errors))

    def test_structured_evidence_rejects_strings_weak_results_and_wrong_kinds(
        self,
    ) -> None:
        ledger = task_gate.build_ledger("explanation", "non-web", [], None)
        record = ledger["checks"]["C01"]
        record["status"] = "pass"
        record["evidence"] = "Verified in a test"
        record["updated_at"] = task_gate.utc_now()
        errors = task_gate.validate_ledger(ledger)
        self.assertTrue(
            any("C01: evidence must be an object" in error for error in errors)
        )

        record["evidence"] = self.evidence("test", "fixture:C01", "ok")
        errors = task_gate.validate_ledger(ledger)
        self.assertTrue(
            any("C01: observed result is too vague" in error for error in errors)
        )

        record["evidence"] = self.evidence(
            "reason",
            "fixture:C01",
            "A reason alone cannot prove that this check passed",
        )
        errors = task_gate.validate_ledger(ledger)
        self.assertTrue(
            any(
                "C01: pass requires a direct evidence kind" in error for error in errors
            )
        )

    def test_classification_check_cannot_be_resolved_without_full_review(self) -> None:
        ledger = task_gate.build_ledger("explanation", "non-web", [], None)
        record = ledger["checks"]["C09"]
        record["status"] = "pass"
        record["evidence"] = self.evidence()
        record["updated_at"] = task_gate.utc_now()
        errors = task_gate.validate_ledger(ledger)
        self.assertTrue(any("C09 can only be resolved" in error for error in errors))

    def test_blanket_not_applicable_rejected_for_pass_only_invariants(self) -> None:
        ledger = task_gate.build_ledger("explanation", "non-web", [], None)
        self.complete_classification(ledger)
        invariant_ids = sorted(
            set(ledger["checks"]) - task_gate.NA_ALLOWED_IDS - {"C09"}
        )
        for check_id, record in ledger["checks"].items():
            if check_id == "C09":
                continue
            record["status"] = "na"
            record["evidence"] = self.evidence(
                "reason",
                f"fixture:{check_id}",
                f"The blanket attempt marks check {check_id} as not applicable",
                scope_ids=["primary"],
            )
            record["updated_at"] = task_gate.utc_now()
        ledger["updated_at"] = task_gate.utc_now()
        errors = task_gate.validate_ledger(ledger)
        for check_id in invariant_ids:
            self.assertTrue(
                any(
                    f"{check_id}: this invariant cannot be marked not applicable"
                    in error
                    for error in errors
                )
            )

    def test_custom_requirement_cannot_be_marked_not_applicable(self) -> None:
        ledger = task_gate.build_ledger("explanation", "non-web", [], None)
        ledger["custom_check_ids"] = ["X01"]
        ledger["checks"]["X01"] = {
            "id": "X01",
            "group": "task",
            "label": "The user-requested behavior is implemented",
            "sources": ["custom"],
            "status": "pending",
            "evidence": task_gate.empty_evidence(),
            "updated_at": None,
        }
        self.resolve_all_checks(ledger)
        ledger["checks"]["X01"]["status"] = "na"
        ledger["checks"]["X01"]["evidence"] = self.evidence(
            "reason",
            "user request",
            "The requested behavior was declared outside the current scope",
            scope_ids=["primary"],
        )
        ledger["checks"]["X01"]["updated_at"] = task_gate.utc_now()
        ledger["updated_at"] = task_gate.utc_now()
        errors = task_gate.validate_ledger(ledger)
        self.assertTrue(
            any(
                "X01: a custom requirement cannot be marked not applicable" in error
                for error in errors
            )
        )

    def test_mismatched_inference_requires_completed_override_disposition(self) -> None:
        temporary, root = self.make_repo(
            {
                "package.json": '{"dependencies":{"phaser":"4.0.0","vite":"7.0.0"}}',
                "src/scenes/LevelOne.ts": "export class GameState { sprite = 'player'; }",
            }
        )
        self.addCleanup(temporary.cleanup)
        inference = task_gate.infer_repository(root)
        ledger = task_gate.build_ledger("review", "non-web", [], inference)
        self.complete_classification(ledger)
        self.assertEqual(task_gate.validate_ledger(ledger), [])

        ledger["classification_review"]["inference_disposition"] = {
            "decision": "pending",
            "direct_evidence": task_gate.empty_evidence(),
            "reason": task_gate.empty_evidence(),
            "updated_at": None,
        }
        errors = task_gate.validate_ledger(ledger)
        self.assertTrue(
            any("inference_disposition must be overridden" in error for error in errors)
        )
        self.assertTrue(
            any(
                "inference_disposition update time is invalid" in error
                for error in errors
            )
        )

    def test_game_surface_cannot_reject_game_capability(self) -> None:
        ledger = task_gate.build_ledger(
            "review",
            "game",
            task_gate.ARCHETYPE_DEFAULTS["game"],
            None,
        )
        self.complete_classification(ledger)
        decision = ledger["classification_review"]["capabilities"]["game"]
        decision["decision"] = "rejected"
        decision["evidence"] = self.evidence(
            "reason",
            "capability:game",
            "The attempted review rejects game behavior on the play surface",
            scope_ids=["primary"],
        )
        errors = task_gate.validate_ledger(ledger)
        self.assertTrue(
            any(
                "classification_review game: expected decision active" in error
                for error in errors
            )
        )
        self.assertTrue(
            any("game requires active capability game" in error for error in errors)
        )

    def test_game_check_evidence_must_cover_play_scope(self) -> None:
        capabilities = sorted(
            {
                *task_gate.ARCHETYPE_DEFAULTS["game"],
                "marketing",
                "public-discovery",
            }
        )
        ledger = task_gate.build_ledger("review", "game", capabilities, None)
        self.complete_classification(ledger, hybrid=True)
        self.assertEqual(task_gate.validate_ledger(ledger), [])
        now = task_gate.utc_now()
        record = ledger["checks"]["G01"]
        record["status"] = "pass"
        record["evidence"] = self.evidence(
            "test",
            "landing route test",
            "The landing route ran but the play route was not examined",
            scope_ids=["landing"],
        )
        record["updated_at"] = now
        ledger["updated_at"] = now
        errors = task_gate.validate_ledger(ledger)
        self.assertTrue(
            any("G01: evidence omits game surfaces: play" in error for error in errors)
        )

    def test_paid_game_shell_cannot_be_removed_without_explicit_override(self) -> None:
        temporary, root = self.make_repo(
            {
                "package.json": (
                    '{"dependencies":{"phaser":"4.0.0","vite":"7.0.0",'
                    '"stripe":"20.0.0"}}'
                ),
                "src/scenes/Level.ts": "export class GameState { sprite = 'player'; }",
                "src/landing/page.tsx": "export default () => <h1>Buy game</h1>;",
                "src/checkout/page.tsx": "const stripe = 'stripe'; const payment = 'payment';",
            }
        )
        self.addCleanup(temporary.cleanup)
        inference = task_gate.infer_repository(root)
        self.assertEqual(inference["selected_archetype"], "game")
        self.assertTrue(
            {"commerce", "marketing", "public-discovery"}.issubset(
                inference["selected_capabilities"]
            )
        )
        ledger = task_gate.build_ledger(
            "review",
            inference["selected_archetype"],
            inference["selected_capabilities"],
            inference,
        )
        review = self.classification_review(ledger)
        retained = {"game", "web-core"}
        for capability, decision in review["capabilities"].items():
            if capability in retained:
                continue
            decision["decision"] = "rejected"
            decision["scopes"] = ["primary"]
            decision["evidence"] = self.evidence(
                "reason",
                f"capability:{capability}",
                f"The review rejects inferred capability {capability} on this surface",
                scope_ids=["primary"],
            )
        review["inference_disposition"] = {
            "decision": "overridden",
            "direct_evidence": self.evidence(
                "source",
                "repository review",
                "Direct source inspection supports the reduced game-only classification",
                scope_ids=["primary"],
            ),
            "reason": self.evidence(
                "reason",
                "inference override",
                "The public shell was excluded from the final classification",
                scope_ids=["primary"],
            ),
        }
        ledger_path = root / ".eval" / "ledger.json"
        review_path = root / ".eval" / "review.json"
        task_gate.write_json(ledger_path, ledger, overwrite=False)
        task_gate.write_json(review_path, review, overwrite=False)
        with self.assertRaises(ValueError) as caught:
            task_gate.command_apply_classification(
                Namespace(ledger=str(ledger_path), review=str(review_path))
            )
        message = str(caught.exception)
        self.assertIn(
            "inference_disposition evidence omits removed inferred capability commerce",
            message,
        )
        self.assertIn(
            "classification_review omits material inferred surface candidate",
            message,
        )

    def test_zero_width_paths_targets_and_observations_are_rejected(self) -> None:
        zero_width = "\u200b\u200c\u2060"
        target_errors = task_gate.validate_evidence(
            "X01",
            "pass",
            self.evidence(
                "test", zero_width, "Observed a concrete passing test result"
            ),
        )
        self.assertTrue(
            any("evidence target must identify" in error for error in target_errors)
        )
        observed_errors = task_gate.validate_evidence(
            "X01",
            "pass",
            self.evidence("test", "fixture:X01", zero_width),
        )
        self.assertTrue(
            any("observed result is too vague" in error for error in observed_errors)
        )

        ledger = task_gate.build_ledger("explanation", "non-web", [], None)
        self.complete_classification(ledger)
        ledger["classification_review"]["surfaces"][0]["path"] = zero_width
        errors = task_gate.validate_ledger(ledger)
        self.assertTrue(any("path must not be empty" in error for error in errors))

    def test_punctuation_padding_does_not_make_evidence_meaningful(self) -> None:
        ledger = task_gate.build_ledger("explanation", "non-web", [], None)
        self.resolve_all_checks(ledger)
        ledger["checks"]["C01"]["evidence"].update(
            target="a!!",
            observed="a!!!!!!!!!!!",
        )
        errors = task_gate.validate_ledger(ledger)
        self.assertTrue(
            any("C01: evidence target must identify" in error for error in errors)
        )
        self.assertTrue(
            any("C01: observed result is too vague" in error for error in errors)
        )

    def test_partial_inference_object_is_rejected(self) -> None:
        temporary, root = self.make_repo(
            {
                "package.json": '{"dependencies":{"phaser":"4.0.0","vite":"7.0.0"}}',
                "src/scenes/LevelOne.ts": "export class GameState { sprite = 'player'; }",
            }
        )
        self.addCleanup(temporary.cleanup)
        partial = task_gate.infer_repository(root)
        partial.pop("surface_candidates")
        ledger = task_gate.build_ledger(
            "review",
            partial["selected_archetype"],
            partial["selected_capabilities"],
            partial,
        )
        errors = task_gate.validate_ledger(ledger)
        self.assertTrue(
            any(
                "Ledger classification is missing fields: surface_candidates" in error
                for error in errors
            )
        )

    def test_malformed_inference_surface_candidate_fields_are_rejected(self) -> None:
        temporary, root = self.make_repo(
            {
                "package.json": '{"dependencies":{"phaser":"4.0.0","vite":"7.0.0"}}',
                "src/scenes/LevelOne.ts": "export class GameState { sprite = 'player'; }",
            }
        )
        self.addCleanup(temporary.cleanup)
        inference = task_gate.infer_repository(root)
        candidate = inference["surface_candidates"][0]
        candidate.update(
            id=None,
            source=None,
            visibility_candidate=None,
            evidence=None,
        )
        errors = task_gate.validate_inference(inference)
        for expected in (
            "invalid id",
            "invalid source",
            "invalid visibility",
            "invalid evidence",
        ):
            self.assertTrue(any(expected in error for error in errors))

    def test_inference_selection_must_match_its_scores(self) -> None:
        temporary, root = self.make_repo(
            {
                "package.json": '{"dependencies":{"phaser":"4.0.0","vite":"7.0.0"}}',
                "src/scenes/LevelOne.ts": "export class GameState { sprite = 'player'; }",
            }
        )
        self.addCleanup(temporary.cleanup)
        inference = task_gate.infer_repository(root)
        inference["archetype_scores"] = {
            archetype: 0 for archetype in task_gate.ARCHETYPE_SIGNALS
        }
        inference["capability_scores"] = {
            capability: 0 for capability in task_gate.CAPABILITY_SIGNALS
        }
        inference["capability_candidates"] = []
        errors = task_gate.validate_inference(inference)
        self.assertTrue(
            any(
                "selected archetype does not match its scores" in error
                for error in errors
            )
        )
        self.assertTrue(
            any(
                "selected capabilities do not match their scores" in error
                for error in errors
            )
        )

    def test_date_only_and_future_ledger_timestamps_are_rejected(self) -> None:
        date_only = task_gate.build_ledger("explanation", "non-web", [], None)
        date_only["created_at"] = "2026-09-07"
        date_only["updated_at"] = "2026-09-07"
        errors = task_gate.validate_ledger(date_only)
        self.assertTrue(any("must be valid timestamps" in error for error in errors))

        future = task_gate.build_ledger("explanation", "non-web", [], None)
        future["updated_at"] = (
            datetime.now(timezone.utc) + timedelta(hours=1)
        ).isoformat()
        errors = task_gate.validate_ledger(future)
        self.assertTrue(
            any(
                "Ledger update time is implausibly in the future" in error
                for error in errors
            )
        )

    def test_source_check_ids_remain_complete(self) -> None:
        expected = {
            *{f"W{index:02d}" for index in range(1, 23)},
            *{f"A{index:02d}" for index in range(1, 24)},
            *{f"P{index:02d}" for index in range(1, 12)},
            *{f"B{index:02d}" for index in range(1, 17)},
            *{f"D{index:02d}" for index in range(1, 10)},
        }
        self.assertTrue(expected.issubset(task_gate.CHECKS))

    def test_all_profiles_reference_known_capabilities_and_checks(self) -> None:
        for capabilities in task_gate.ARCHETYPE_DEFAULTS.values():
            self.assertTrue(set(capabilities).issubset(task_gate.CAPABILITY_GROUPS))
        for check_ids in task_gate.CAPABILITY_GROUPS.values():
            self.assertTrue(set(check_ids).issubset(task_gate.CHECKS))
        for check_ids in task_gate.MODE_IDS.values():
            self.assertTrue(set(check_ids).issubset(task_gate.CHECKS))

    def test_cross_cutting_checks_are_reachable_from_required_profiles(self) -> None:
        self.assertIn("A05", task_gate.CAPABILITY_GROUPS["web-core"])
        self.assertIn("P01", task_gate.CAPABILITY_GROUPS["forms"])
        self.assertIn("P02", task_gate.CAPABILITY_GROUPS["service-content"])
        self.assertIn("P04", task_gate.CAPABILITY_GROUPS["auth"])
        self.assertIn("P11", task_gate.CAPABILITY_GROUPS["service-content"])
        self.assertIn("W22", task_gate.CAPABILITY_GROUPS["content"])
        self.assertEqual(
            set(task_gate.CAPABILITY_GROUPS["data-legal"]),
            {f"P{index:02d}" for index in range(1, 12)},
        )
        self.assertIn("data-legal", task_gate.CAPABILITY_SIGNALS)
        for check_id in ("D03", "D04", "D08", "D09"):
            self.assertIn(check_id, task_gate.COMMON_IDS)
            self.assertIn(
                check_id,
                task_gate.build_ledger("explanation", "non-web", [], None)["checks"],
            )
        self.assertNotIn("file", task_gate.PASS_KIND_REQUIREMENTS["A01"])
        self.assertNotIn("source", task_gate.PASS_KIND_REQUIREMENTS["A01"])
        self.assertIn("U03", task_gate.MODE_IDS["review"])
        self.assertIn("U21", task_gate.MODE_IDS["review"])
        self.assertIn("U03", task_gate.MODE_IDS["diagnosis"])
        for check_id in ("M01", "M02", "M03"):
            self.assertIn(check_id, task_gate.MODE_IDS["diagnosis"])

    def test_interactive_and_privacy_checks_require_runtime_capable_evidence(
        self,
    ) -> None:
        for check_id in ("A04", "P05", "P06", "P07", "P08", "P09", "B16"):
            allowed = task_gate.PASS_KIND_REQUIREMENTS[check_id]
            self.assertTrue(allowed & {"browser", "command", "log", "runtime", "test"})
            self.assertNotIn("file", allowed)
            self.assertNotIn("source", allowed)

    def test_data_legal_signals_activate_the_full_policy_check_set(self) -> None:
        temporary, root = self.make_repo(
            {
                "package.json": '{"dependencies":{"next":"16.0.0","react":"20.0.0"}}',
                "app/privacy/page.tsx": "export default function PrivacyPolicy() { return 'Privacy policy'; }",
            }
        )
        self.addCleanup(temporary.cleanup)
        inference = task_gate.infer_repository(root)
        self.assertIn("data-legal", inference["selected_capabilities"])
        ledger = task_gate.build_ledger(
            "review",
            inference["selected_archetype"],
            inference["selected_capabilities"],
            inference,
        )
        for index in range(1, 12):
            self.assertIn(f"P{index:02d}", ledger["checks"])

    def test_repeated_fixture_mentions_do_not_create_a_game_false_positive(
        self,
    ) -> None:
        files = {
            "package.json": '{"dependencies":{"next":"16.0.0","react":"20.0.0"}}',
        }
        for index in range(20):
            files[f"tests/case_{index}.ts"] = (
                '{"dependency":"phaser","sprite":"sprite"}'
            )
        temporary, root = self.make_repo(files)
        self.addCleanup(temporary.cleanup)
        result = task_gate.infer_repository(root)
        self.assertEqual(result["selected_archetype"], "web-app")
        self.assertLess(result["archetype_scores"]["game"], 4)
        self.assertNotIn("game", result["selected_capabilities"])

    def test_truncated_scan_forces_manual_review(self) -> None:
        temporary, root = self.make_repo(
            {
                "a.ts": "export const first = true;",
                "b.ts": "export const second = true;",
            }
        )
        self.addCleanup(temporary.cleanup)
        with patch.object(task_gate, "MAX_FILES", 1):
            result = task_gate.infer_repository(root)
        self.assertTrue(result["scan_truncated"])
        self.assertFalse(result["scan_complete"])
        self.assertEqual(result["confidence"], "low")
        self.assertTrue(result["needs_review"])
        self.assertFalse(result["automatic_selection_allowed"])

    def test_inference_skips_symlinked_files_and_directories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "repo"
            root.mkdir()
            external_file = base / "external-game.py"
            external_file.write_text(
                "import phaser\nsprite = 'player'\nclass GameState: pass\n",
                encoding="utf-8",
            )
            external_directory = base / "external-source"
            external_directory.mkdir()
            (external_directory / "checkout.tsx").write_text(
                "export const Checkout = () => 'Buy now with Stripe';\n",
                encoding="utf-8",
            )
            try:
                (root / "linked.py").symlink_to(external_file)
                (root / "linked-directory").symlink_to(
                    external_directory,
                    target_is_directory=True,
                )
            except OSError as exc:
                self.skipTest(f"Symlinks unavailable on this platform: {exc}")

            result = task_gate.infer_repository(root)

            self.assertEqual(result["files_scanned"], 0)
            self.assertEqual(result["selected_archetype"], "non-web")
            self.assertEqual(result["archetype_scores"]["game"], 0)
            self.assertEqual(result["capability_scores"]["commerce"], 0)
            self.assertEqual(result["surface_candidates"], [])

    def test_rescan_is_stable_and_ignores_its_own_ledger(self) -> None:
        temporary, root = self.make_repo(
            {
                "package.json": '{"dependencies":{"phaser":"4.0.0","vite":"7.0.0"}}',
                "src/scenes/LevelOne.ts": "export class GameState { sprite = 'player'; }",
            }
        )
        self.addCleanup(temporary.cleanup)
        first = task_gate.infer_repository(root)
        (root / "task-ledger.json").write_text(
            json.dumps({"misleading": "LocalBusiness checkout dashboard"}),
            encoding="utf-8",
        )
        second = task_gate.infer_repository(root)
        self.assertEqual(first, second)

    def test_hybrid_game_and_marketing_routes_activate_both_check_sets(self) -> None:
        temporary, root = self.make_repo(
            {
                "package.json": '{"dependencies":{"phaser":"4.0.0","vite":"7.0.0"}}',
                "src/scenes/LevelOne.ts": "export class GameState { sprite = 'player'; }",
                "src/landing/page.tsx": "export default () => <><h1>Buy game</h1></>;",
            }
        )
        self.addCleanup(temporary.cleanup)
        result = task_gate.infer_repository(root)
        self.assertEqual(result["selected_archetype"], "game")
        self.assertIn("game", result["selected_capabilities"])
        self.assertIn("marketing", result["selected_capabilities"])
        self.assertIn("public-discovery", result["selected_capabilities"])
        self.assertTrue(result["needs_review"])
        self.assertFalse(result["automatic_selection_allowed"])
        ledger = task_gate.build_ledger(
            "review",
            result["selected_archetype"],
            result["selected_capabilities"],
            result,
        )
        self.assertIn("G01", ledger["checks"])
        self.assertIn("B01", ledger["checks"])
        self.assertIn("W01", ledger["checks"])

    def test_completion_gate_fails_then_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.json"
            ledger = task_gate.build_ledger("explanation", "non-web", [], None)
            task_gate.write_json(path, ledger, overwrite=False)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(
                    task_gate.command_check(Namespace(ledger=str(path))), 1
                )
            payload = task_gate.load_ledger(path)
            self.resolve_all_checks(payload)
            task_gate.write_json(path, payload)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(
                    task_gate.command_check(Namespace(ledger=str(path))), 0
                )

    def test_complete_cli_flow_with_hybrid_routes_and_custom_check(self) -> None:
        temporary, root = self.make_repo(
            {
                "package.json": '{"dependencies":{"phaser":"4.0.0","vite":"7.0.0"}}',
                "src/scenes/LevelOne.ts": "export class GameState { sprite = 'player'; }",
                "src/landing/page.tsx": "export default () => <><h1>Buy game</h1></>;",
            }
        )
        self.addCleanup(temporary.cleanup)
        ledger_path = root / ".eval" / "task-ledger.json"
        review_path = root / ".eval" / "classification-review.json"
        init_args = Namespace(
            root=str(root),
            archetype="game",
            accept_inferred=False,
            capability=["marketing", "public-discovery"],
            mode="implementation",
            output=str(ledger_path),
            force=False,
        )
        with redirect_stdout(io.StringIO()):
            self.assertEqual(task_gate.command_init(init_args), 0)
            self.assertEqual(
                task_gate.command_add(
                    Namespace(
                        ledger=str(ledger_path),
                        id="X01",
                        group="task",
                        label="The requested game purchase path works",
                    )
                ),
                0,
            )
        ledger = task_gate.load_ledger(ledger_path)
        review = self.classification_review(ledger, hybrid=True)
        task_gate.write_json(review_path, review, overwrite=False)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(
                task_gate.command_apply_classification(
                    Namespace(
                        ledger=str(ledger_path),
                        review=str(review_path),
                    )
                ),
                0,
            )

        ledger = task_gate.load_ledger(ledger_path)
        for check_id in ledger["checks"]:
            if check_id == "C09":
                continue
            with redirect_stdout(io.StringIO()):
                self.assertEqual(
                    task_gate.command_record(
                        Namespace(
                            ledger=str(ledger_path),
                            id=check_id,
                            status="pass",
                            kind=self.passing_kind(check_id),
                            target=f"fixture:{check_id}",
                            observed=f"Verified check {check_id} in the complete command flow",
                            capability_unavailable="no",
                            scope=["landing", "play"],
                        )
                    ),
                    0,
                )
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(
                task_gate.command_check(Namespace(ledger=str(ledger_path))), 0
            )
        self.assertIn("Gate passed with no unresolved checks", output.getvalue())


if __name__ == "__main__":
    unittest.main()
