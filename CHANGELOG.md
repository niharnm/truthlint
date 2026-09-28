# Changelog

All notable changes to TruthLint are documented here.

## [Unreleased]

### Added

- Six conditional launch-risk checks: audience-age decisions and age screening (P12), third-party font and asset requests before consent (P13), session replay and input capture (P14), commercial email sender, postal address, and unsubscribe duties (P15), automatic-renewal disclosure and cancellation (P16), and a designated copyright agent for hosted user content (P17).

### Changed

- `data-legal` now selects P01 through P17. P13 joins `web-core`, P12 and P15 join `auth`, P15 joins `forms`, P14 joins `tracking`, P16 joins `commerce`, and P17 joins `community`.
- Common session replay SDKs now count as `tracking` signals during inference.
- In-progress ledgers that select an affected capability must be recreated because their required check sets changed.

## [0.1.0] - 2026-09-07

### Added

- Portable Agent Skill instructions for implementation, review, diagnosis, explanation, and deployment work.
- Adaptive classification across 15 product archetypes and 20 capability groups.
- A 160-check catalog covering engineering work, browser products, accessibility, privacy, commerce, games, private applications, communities, and embedded widgets.
- A schema 2 evidence ledger with scoped surfaces, direct evidence, custom checks, and fail-closed validation.
- Bounded repository inference with weak-signal controls and symlink-safe scanning.
- Local profile support through an ignored configuration file.
- Python 3.10+ unit tests and Agent Skills validation.

[Unreleased]: https://github.com/niharnm/truthlint/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/niharnm/truthlint/releases/tag/v0.1.0
