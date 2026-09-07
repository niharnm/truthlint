# Contributing to TruthLint

TruthLint should remain portable, evidence-gated, and selective about which checks apply.

## Before opening a change

- Search existing issues and keep the proposal tied to an observed failure or missing behavior.
- Do not add a check solely because it is a general preference. State which task mode, product archetype, capability, and surface make it applicable.
- Do not add vendor-specific required behavior to the core workflow.
- Do not include private profiles, credentials, generated ledgers, or repository data in a report or fixture.

## Development setup

TruthLint requires Python 3.10 or newer. Runtime code uses only the standard library.

```sh
python3 -m unittest -v scripts/test_task_gate.py
uvx ruff==0.16.6 check .
uvx ruff==0.16.6 format --check .
uvx --from skills-ref==0.1.1 agentskills validate "$PWD"
```

## Pull requests

A behavior change should include:

- A focused explanation of the observed problem.
- A regression test that fails before the change and passes after it.
- Passing unit tests, Ruff checks, and Agent Skills validation.
- Updated public documentation when behavior changes.
- No unrelated formatting, refactoring, dependencies, or private data.

Classifier changes should test both the intended signal and a nearby false positive. Gate changes should test the valid path and the expected rejection path.

By contributing, you agree that your contribution is licensed under the MIT License.
