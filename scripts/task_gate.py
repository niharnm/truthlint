#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import unicodedata
import uuid
from collections.abc import Iterable
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2
VALID_STATUSES = {"pending", "fix", "pass", "na", "blocked"}
DIRECT_EVIDENCE_KINDS = {
    "browser",
    "command",
    "file",
    "log",
    "manual",
    "runtime",
    "source",
    "test",
}
VALID_EVIDENCE_KINDS = DIRECT_EVIDENCE_KINDS | {"blocker", "observation", "reason"}
WEAK_EVIDENCE = {
    "complete",
    "done",
    "looks good",
    "ok",
    "passed",
    "verified",
    "works",
}
IGNORE_DIRS = {
    ".agents",
    ".claude",
    ".codex",
    ".eval",
    ".git",
    ".gemini",
    ".next",
    ".turbo",
    ".venv",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "vendor",
}
TEXT_SUFFIXES = {
    ".astro",
    ".css",
    ".go",
    ".html",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mdx",
    ".mjs",
    ".py",
    ".rb",
    ".rs",
    ".svelte",
    ".toml",
    ".ts",
    ".tsx",
    ".vue",
    ".yaml",
    ".yml",
}
MAX_FILES = 600
MAX_FILE_BYTES = 48_000
MAX_TOTAL_BYTES = 4_000_000

LOW_SIGNAL_DIRS = {
    "__fixtures__",
    "__mocks__",
    "__tests__",
    "docs",
    "examples",
    "fixtures",
    "mocks",
    "test",
    "tests",
}

NA_ALLOWED_IDS = {
    "A05",
    "A08",
    "A10",
    "A11",
    "A14",
    "A16",
    "A18",
    "A19",
    "A20",
    "A21",
    "A23",
    "B01",
    "B02",
    "B03",
    "B04",
    "B05",
    "B06",
    "B07",
    "B08",
    "B09",
    "B10",
    "B11",
    "B12",
    "B13",
    "B14",
    "B15",
    "B16",
    "CMT02",
    "CMT04",
    "E04",
    "G05",
    "G07",
    "P01",
    "P02",
    "P03",
    "P04",
    "P05",
    "P07",
    "P08",
    "P09",
    "P11",
    "Q04",
    "Q05",
    "W01",
    "W02",
    "W09",
    "W12",
    "W13",
    "W14",
    "W17",
    "W18",
    "W19",
    "W22",
}

PASS_KIND_REQUIREMENTS: dict[str, set[str]] = {
    "A01": {"browser", "command", "manual", "runtime", "test"},
    "A04": {"browser", "runtime", "test"},
    "U15": {"command", "test"},
    "U20": {"browser", "log", "runtime"},
    "U21": {"command", "runtime"},
    "U24": {"runtime", "test"},
    "W20": {"browser", "log", "runtime", "test"},
    "W21": {"browser", "command", "file", "test"},
    "P05": {"browser", "log", "runtime", "test"},
    "P06": {"browser", "command", "log", "runtime", "test"},
    "P07": {"browser", "log", "runtime", "test"},
    "P08": {"browser", "log", "runtime", "test"},
    "P09": {"browser", "runtime", "test"},
    "B16": {"browser", "runtime", "test"},
    "E04": {"log", "runtime", "source", "test"},
}
for game_check_index in range(1, 11):
    PASS_KIND_REQUIREMENTS[f"G{game_check_index:02d}"] = {
        "browser",
        "log",
        "runtime",
        "test",
    }


def entries(group: str, values: dict[str, str]) -> dict[str, dict[str, str]]:
    return {
        check_id: {"group": group, "label": label} for check_id, label in values.items()
    }


CHECKS: dict[str, dict[str, str]] = {}
CHECKS.update(
    entries(
        "control",
        {
            "C01": "Instruction, source, repository, and active-task context inventoried",
            "C02": "Every selected rule and checklist item assessed",
            "C03": "Every applicable gap fixed and reassessed",
            "C04": "Every not-applicable result has a concrete product or scope reason",
            "C05": "No facts, evidence, policies, proof, or results invented",
            "C06": "Instruction priority and authorization boundaries respected",
            "C07": "Assumptions and verifiable success criteria recorded",
            "C08": "Work continued until passed, reasoned not applicable, or genuinely blocked",
            "C09": "Product archetype and activated capabilities confirmed from direct evidence",
        },
    )
)
CHECKS.update(
    entries(
        "engineering",
        {
            "U01": "Relevant context, instructions, architecture, patterns, and tests inspected",
            "U02": "Request mode classified and mutations limited to authorized scope",
            "U03": "Complex work planned briefly and carried through",
            "U04": "Active state recovered after any context compaction",
            "U05": "Root cause or required behavior traced before changing code",
            "U06": "Smallest coherent change preserves unrelated behavior",
            "U07": "Correctness, clarity, maintainability, security, and behavior reviewed",
            "U08": "Types remain strict and errors remain explicit",
            "U09": "No unsafe casts, broad catches, silent failures, speculative fallbacks, or secrets",
            "U10": "Unrelated user changes preserved",
            "U11": "No destructive action, discarded change, amended commit, or deletion without authority",
            "U12": "Production dependency and public API, schema, or persistent-data changes authorized",
            "U13": "Implementation completed end to end",
            "U14": "Behavior changes have targeted tests when practical",
            "U15": "Relevant tests, lint, formatter, type checks, and build run",
            "U16": "Final diff inspected for bugs, regressions, security, and scope growth",
            "U17": "Verified facts, assumptions, blockers, and check results reported truthfully",
            "U18": "Comments and documentation are concise and public behavior docs are current",
            "U19": "Untouched code did not receive unrelated comments, docstrings, or annotations",
            "U20": "Raw logs, stack traces, browser console, and network evidence read before diagnosis",
            "U21": "Existing port ownership checked before starting a development server",
            "U22": "Assumptions stated and only a truly blocking high-risk question asked",
            "U23": "Only required files and lines changed without unrelated cleanup",
            "U24": "Bug reproduced or failing test added when practical, then fix verified",
            "U25": "Strong open-source implementations inspected when the decision warranted research",
            "U26": "Leading product behavior compared when user experience changed materially",
            "U27": "Relevant external patterns adapted without blind copying or unauthorized dependencies",
        },
    )
)
CHECKS.update(
    entries(
        "response",
        {
            "R01": "Response is concise, factual, specific, direct, and candid",
            "R02": "Every user-facing message satisfies the active local profile and communication rules",
            "R03": "Any missed mandatory communication rule triggered the configured recovery state machine",
            "R04": "Any replacement-task handoff is complete, sanitized, opened, and leaves the prior task unarchived",
            "R05": "The active local profile's recovery limit was respected",
            "R06": "Any task-creation or navigation failure was reported without a false success claim",
            "R07": "Unsafe, wasteful, or unsupported choices were critiqued plainly",
            "R08": "Review findings lead in severity order with file and line references",
            "R09": "Implementation report states changes, files, checks, assumptions, and blockers",
            "R10": "Whole files were not pasted unless requested",
            "R11": "Prohibited terms and dash characters were removed from responses and code comments",
            "R12": "Conversational preambles and trailing recaps were removed",
        },
    )
)
CHECKS.update(
    entries(
        "multi-agent",
        {
            "M01": "Independent large-task components delegated when parallel work materially helped",
            "M02": "Worker prompts contained task, objective, exact bounds, patterns, and output contract",
            "M03": "Live worker status table maintained while orchestration was active",
        },
    )
)
CHECKS.update(
    entries(
        "skills",
        {
            "S01": "Relevant specialized skills checked at the start of a new project or complex workflow",
            "S02": "Only applicable skills used and their required process followed",
            "S03": "Only task-created temporary skill files removed; installed and pre-existing skills preserved",
        },
    )
)
CHECKS.update(
    entries(
        "public-foundation",
        {
            "W01": "Custom 404 behavior",
            "W02": "Thank-you destination when a separate route adds value",
            "W03": "Unique page titles",
            "W04": "Route-specific meta descriptions",
            "W05": "Unique primary headings and logical heading order",
            "W06": "Correct canonical tags",
            "W07": "Correct rendered page source, semantics, hydration, and metadata",
            "W08": "Working internal links",
            "W09": "Breadcrumbs for useful route hierarchy",
            "W10": "Intentional robots.txt",
            "W11": "Valid sitemap.xml",
            "W12": "Accurate llms.txt when project policy requires it",
            "W13": "Structured data matches visible verified facts",
            "W14": "Local-business schema uses verified facts",
            "W15": "Social metadata and social share images",
            "W16": "Working favicon",
            "W17": "Custom production domain, HTTPS, redirects, and canonical host",
            "W18": "Search Console ownership and sitemap submission when operations are in scope",
            "W19": "Production source-map exposure follows approved policy and contains no secrets",
            "W20": "No unresolved application errors in the browser console",
            "W21": "Bitmap images have suitable format, dimensions, and byte size",
            "W22": "Print stylesheet when users reasonably print the content",
        },
    )
)
CHECKS.update(
    entries(
        "accessibility-interaction",
        {
            "A01": "Accessibility checked on every changed browser surface",
            "A02": "Colour contrast meets applicable thresholds",
            "A03": "Meaningful images have factual alt text and decorative images have empty alt text",
            "A04": "Forms work by keyboard",
            "A05": "Skip-to-content behavior when repeated navigation precedes document content",
            "A06": "Buttons have clear visible or accessible labels",
            "A07": "Icons follow the product system and have correct accessible treatment",
            "A08": "Mobile menus handle focus, close, scroll, resize, and route changes",
            "A09": "Pointer hover feedback has equivalent focus feedback",
            "A10": "Tooltips are used only when useful and work by pointer and keyboard",
            "A11": "Password fields have an accessible visibility toggle",
            "A12": "Forms have a tested success state",
            "A13": "Forms have specific tested error states and messages",
            "A14": "Hard-to-reverse actions have an accessible confirmation flow",
            "A15": "Async work has restrained loading feedback and reduced-motion support",
            "A16": "Back-to-top control when long pages materially benefit",
            "A17": "Sticky headers do not obstruct content, anchors, or focus",
            "A18": "Sticky mobile action when a confirmed conversion flow benefits",
            "A19": "Scroll progress when long-form content materially benefits",
            "A20": "Copy control when users copy code, links, addresses, or identifiers",
            "A21": "Dark-mode toggle when theming is supported",
            "A22": "Scroll motion is restrained, purposeful, and reduced-motion aware",
            "A23": "Site search when the corpus justifies it",
        },
    )
)
CHECKS.update(
    entries(
        "privacy-legal",
        {
            "P01": "Privacy policy reflects verified data practices when required",
            "P02": "Terms and conditions or terms of service use approved terms when required",
            "P03": "Refund or cancellation policy uses verified business terms when required",
            "P04": "Cookie policy reflects actual storage when required",
            "P05": "Cookie consent blocks nonessential activity and supports accept, reject, revoke, and persistence",
            "P06": "Tracking, cookies, storage, tag managers, and network requests inventoried",
            "P07": "Campaign attribution is permitted, minimized, disclosed, and tested",
            "P08": "Third-party embeds checked for privacy, security, accessibility, and failure behavior",
            "P09": "Form consent is purpose-specific, unbundled, and unselected",
            "P10": "Only data with a defined purpose is collected and retained",
            "P11": "Last-updated dates reflect verified revisions",
        },
    )
)
CHECKS.update(
    entries(
        "trust-content",
        {
            "B01": "Clear factual CTA appears above the fold on conversion pages",
            "B02": "Response-time promise uses an approved commitment",
            "B03": "Case studies use sourced work, outcomes, and permissions",
            "B04": "Five useful FAQs when the approved content plan requires that batch",
            "B05": "Reviews are real, sourced, and permitted; fake reviews removed",
            "B06": "Real-photo claims use approved authentic photos",
            "B07": "Maps and directions use a verified location or service area",
            "B08": "Tap-to-call uses a verified working number",
            "B09": "Opening hours are verified, including known exceptions",
            "B10": "Visible contact email is approved and working",
            "B11": "Social links point to approved working profiles",
            "B12": "About page and story use factual approved content",
            "B13": "Before-and-after gallery uses approved truthful comparison assets",
            "B14": "Distinct service pages have unique factual user value",
            "B15": "Five factual blog posts when the approved content plan requires that batch",
            "B16": "Submission flow, success state, thank-you behavior, retries, and duplicates work",
        },
    )
)
CHECKS.update(
    entries(
        "marketing-defaults",
        {
            "D01": "No default purple gradient without explicit product or brand direction",
            "D02": "No vague hero text",
            "D03": "No fake reviews",
            "D04": "No fake metrics",
            "D05": "No excessive scroll animation",
            "D06": "No default pill-shaped buttons without explicit product or brand direction",
            "D07": "No emoji used as interface icons without explicit direction",
            "D08": "No em dash or en dash characters in generated copy or comments",
            "D09": "No made-with-AI tag or assistant attribution without the user's request or a binding rule",
        },
    )
)
CHECKS.update(
    entries(
        "game",
        {
            "G01": "Core game loop start, play, outcome, restart, and exit paths work",
            "G02": "Declared keyboard, pointer, touch, and controller inputs work",
            "G03": "Focus enters and exits safely without accidental input capture",
            "G04": "Pause, resume, visibility, background, and focus-loss behavior preserves state",
            "G05": "Save, restore, invalid-state recovery, and reset work when persistence exists",
            "G06": "Slow, failed, cached, and repeated asset loads have correct behavior",
            "G07": "Audio mute, volume, persistence, autoplay, and focus behavior work when audio exists",
            "G08": "Supported viewports, pixel density, full screen, safe areas, and orientation work",
            "G09": "Motion and flashing are assessed and menus remain readable",
            "G10": "Frame behavior, memory, cleanup, console, and network health checked across restarts",
        },
    )
)
CHECKS.update(
    entries(
        "private-app",
        {
            "Q01": "Authentication sign-in, sign-out, expiry, recovery, refresh, and route guards work",
            "Q02": "Authorization boundaries hold for roles, tenants, ownership, and staff scopes",
            "Q03": "Loading, empty, error, and stale data states work",
            "Q04": "Delete, publish, charge, submit, and overwrite actions handle confirmation, retry, and idempotency",
            "Q05": "Meaningful edits handle navigation, refresh, conflicts, drafts, autosave, or warnings",
            "Q06": "Private routes have intentional authentication and crawler behavior",
        },
    )
)
CHECKS.update(
    entries(
        "community",
        {
            "CMT01": "Reporting, moderation, blocked content, and abuse feedback work",
            "CMT02": "Uploads enforce type, size, access, failure, and removal behavior",
            "CMT03": "Profile privacy defaults, audience controls, discovery, and deletion work",
            "CMT04": "Account block, mute, delete, export, recovery, and notification controls work when supported",
        },
    )
)
CHECKS.update(
    entries(
        "embedded",
        {
            "E01": "Embedded focus entry, exit, tab order, restoration, and trap prevention work",
            "E02": "Embedded resize, zoom, mobile viewport, overflow, and dynamic layout work",
            "E03": "Embedded loading, unavailable host data, network failure, retry, and feedback work",
            "E04": "Cross-window messages validate exact origins, payloads, and authorization",
            "E05": "Host-owned domain, navigation, metadata, and error behavior identified accurately",
        },
    )
)


COMMON_IDS = [
    *[f"C{index:02d}" for index in range(1, 10)],
    *[f"R{index:02d}" for index in range(1, 13)],
    *[f"S{index:02d}" for index in range(1, 4)],
    "D03",
    "D04",
    "D08",
    "D09",
]

MODE_IDS: dict[str, list[str]] = {
    "explanation": ["U01", "U02", "U04", "U17", "U22"],
    "review": [
        "U01",
        "U02",
        "U03",
        "U04",
        "U05",
        "U06",
        "U07",
        "U08",
        "U09",
        "U10",
        "U16",
        "U17",
        "U18",
        "U20",
        "U21",
        "U22",
        "U23",
        "U25",
        "U26",
        "U27",
        "M01",
        "M02",
        "M03",
    ],
    "diagnosis": [
        "U01",
        "U02",
        "U03",
        "U04",
        "U05",
        "U06",
        "U07",
        "U09",
        "U10",
        "U17",
        "U20",
        "U21",
        "U22",
        "U23",
        "U24",
        "U25",
        "U27",
        "M01",
        "M02",
        "M03",
    ],
    "implementation": [
        *[f"U{index:02d}" for index in range(1, 28)],
        "M01",
        "M02",
        "M03",
    ],
    "deployment": [
        *[f"U{index:02d}" for index in range(1, 28)],
        "M01",
        "M02",
        "M03",
    ],
}

CAPABILITY_GROUPS: dict[str, list[str]] = {
    "web-core": [
        "W07",
        "W20",
        "W21",
        "A01",
        "A02",
        "A03",
        "A05",
        "A06",
        "A07",
        "A08",
        "A09",
        "P06",
        "P10",
        "D03",
        "D04",
        "D08",
        "D09",
    ],
    "public-discovery": [
        "W01",
        "W03",
        "W04",
        "W05",
        "W06",
        "W08",
        "W09",
        "W10",
        "W11",
        "W12",
        "W13",
        "W15",
        "W16",
        "W17",
        "W18",
        "W19",
        "W20",
        "W21",
    ],
    "marketing": [
        "B01",
        "B03",
        "B04",
        "B05",
        "B06",
        "B12",
        "A18",
        "A22",
        "D01",
        "D02",
        "D05",
        "D06",
        "D07",
    ],
    "local-presence": ["W14", "B07", "B08", "B09", "B10"],
    "service-content": ["B02", "B03", "B04", "B12", "B14", "B15", "P02", "P11"],
    "media-proof": ["B03", "B05", "B06", "B13"],
    "forms": ["W02", "A04", "A12", "A13", "P01", "P09", "P10", "B16"],
    "auth": [
        "A11",
        "A12",
        "A13",
        "A14",
        "P01",
        "P02",
        "P04",
        "P10",
        "P11",
        "Q01",
        "Q02",
        "Q06",
    ],
    "commerce": [
        "W02",
        "P01",
        "P02",
        "P03",
        "P04",
        "P05",
        "P09",
        "P10",
        "P11",
        "B16",
        "Q04",
    ],
    "tracking": ["P01", "P04", "P05", "P06", "P07", "P08", "P10", "P11"],
    "data-legal": [*[f"P{index:02d}" for index in range(1, 12)]],
    "content": [
        "W09",
        "W11",
        "W12",
        "W22",
        "A16",
        "A17",
        "A19",
        "A20",
        "A23",
        "P11",
        "B15",
    ],
    "documentation": ["W09", "W22", "A10", "A16", "A17", "A19", "A20", "A23", "P11"],
    "social": ["W15", "B11"],
    "search": ["A23"],
    "private-app": ["A14", "A15", "Q01", "Q02", "Q03", "Q04", "Q05", "Q06"],
    "community": ["P01", "P02", "P08", "P10", "CMT01", "CMT02", "CMT03", "CMT04"],
    "game": [*[f"G{index:02d}" for index in range(1, 11)], "P06", "P10"],
    "embedded": [*[f"E{index:02d}" for index in range(1, 6)], "P06", "P08", "P10"],
    "interaction-extras": [
        "A10",
        "A14",
        "A15",
        "A16",
        "A17",
        "A19",
        "A20",
        "A21",
        "A22",
    ],
}

ARCHETYPE_DEFAULTS: dict[str, list[str]] = {
    "non-web": [],
    "web-app": ["web-core"],
    "marketing": [
        "web-core",
        "public-discovery",
        "marketing",
        "forms",
        "tracking",
        "social",
    ],
    "local-business": [
        "web-core",
        "public-discovery",
        "marketing",
        "forms",
        "tracking",
        "social",
        "local-presence",
        "media-proof",
        "service-content",
    ],
    "professional-services": [
        "web-core",
        "public-discovery",
        "marketing",
        "forms",
        "tracking",
        "social",
        "media-proof",
        "service-content",
    ],
    "ecommerce": [
        "web-core",
        "public-discovery",
        "marketing",
        "commerce",
        "forms",
        "auth",
        "tracking",
        "social",
        "media-proof",
    ],
    "saas": [
        "web-core",
        "public-discovery",
        "marketing",
        "forms",
        "auth",
        "tracking",
        "social",
    ],
    "internal-tool": ["web-core", "forms", "auth", "private-app"],
    "publisher": [
        "web-core",
        "public-discovery",
        "content",
        "tracking",
        "social",
        "search",
    ],
    "docs": ["web-core", "public-discovery", "documentation", "search"],
    "portfolio": ["web-core", "public-discovery", "marketing", "media-proof", "social"],
    "community": [
        "web-core",
        "public-discovery",
        "auth",
        "forms",
        "community",
        "tracking",
        "social",
    ],
    "game": ["web-core", "game"],
    "microsite": ["web-core", "public-discovery"],
    "embedded-widget": ["web-core", "embedded"],
}

SURFACE_REQUIRED_CAPABILITIES: dict[str, list[str]] = {
    "non-web": [],
    "web-app": ["web-core"],
    "marketing": ["web-core", "public-discovery", "marketing"],
    "local-business": ["web-core", "public-discovery", "marketing", "local-presence"],
    "professional-services": [
        "web-core",
        "public-discovery",
        "marketing",
        "service-content",
    ],
    "ecommerce": ["web-core", "public-discovery", "commerce"],
    "saas": ["web-core", "public-discovery"],
    "internal-tool": ["web-core", "auth", "private-app"],
    "publisher": ["web-core", "public-discovery", "content"],
    "docs": ["web-core", "public-discovery", "documentation"],
    "portfolio": ["web-core", "public-discovery", "marketing", "media-proof"],
    "community": ["web-core", "auth", "community"],
    "game": ["web-core", "game"],
    "microsite": ["web-core", "public-discovery"],
    "embedded-widget": ["web-core", "embedded"],
}


ARCHETYPE_SIGNALS: dict[str, list[tuple[str, int]]] = {
    "game": [
        ('"phaser"', 9),
        ("@pixi/", 9),
        ("babylonjs", 9),
        ("playcanvas", 9),
        ("/scenes/", 5),
        ("/levels/", 5),
        ("gamestate", 5),
        ("game loop", 5),
        ("sprite", 2),
        ("requestanimationframe", 1),
        ("webgl", 2),
    ],
    "local-business": [
        ("localbusiness", 9),
        ("opening hours", 5),
        ("service area", 5),
        ("maps.google", 4),
        ("book appointment", 4),
        ("directions", 2),
        ("tel:", 1),
    ],
    "ecommerce": [
        ("shopify", 8),
        ("medusajs", 8),
        ("/checkout", 7),
        ("/cart", 6),
        ("stripe", 4),
        ("order confirmation", 4),
        ("product variant", 4),
    ],
    "saas": [
        ("/dashboard", 5),
        ("subscription", 4),
        ("billing", 3),
        ("workspace", 2),
        ("organization", 1),
        ("clerk", 3),
        ("auth0", 3),
    ],
    "internal-tool": [
        ("backoffice", 8),
        ("internal tool", 8),
        ("staff-only", 7),
        ("/admin", 4),
        ("admin/", 3),
        ("noindex", 1),
    ],
    "publisher": [
        ("/blog/", 5),
        ("/posts/", 5),
        ("contentful", 5),
        ("sanity", 4),
        ("article", 1),
        ("author", 1),
    ],
    "docs": [
        ("docusaurus", 9),
        ("nextra", 9),
        ("vitepress", 9),
        ("mkdocs", 9),
        ("/docs/", 4),
        (".mdx", 2),
        ("documentation", 1),
    ],
    "portfolio": [
        ("portfolio", 6),
        ("/projects/", 4),
        ("resume", 3),
        ("curriculum vitae", 5),
        ("case study", 2),
    ],
    "community": [
        ("moderation", 6),
        ("user-generated", 7),
        ("/comments/", 5),
        ("report abuse", 5),
        ("/profiles/", 3),
        ("upload", 1),
    ],
    "embedded-widget": [
        ("postmessage", 5),
        ("messageevent", 4),
        ("iframe", 2),
        ("widget", 2),
        ("embed", 1),
    ],
    "professional-services": [
        ("consulting", 5),
        ("agency", 4),
        ("our services", 3),
        ("case studies", 3),
        ("contact us", 1),
    ],
    "marketing": [
        ("/landing/", 4),
        ("buy game", 4),
        ("hero", 2),
        ("call to action", 3),
        ("testimonial", 2),
        ("pricing", 2),
        ("faq", 1),
    ],
}

WEB_SIGNALS: list[tuple[str, int]] = [
    ('"next"', 4),
    ('"react"', 3),
    ('"vue"', 3),
    ('"svelte"', 3),
    ('"astro"', 3),
    ('"vite"', 2),
    ('"@angular/', 4),
    ('"remix', 3),
    ("<html", 4),
    ("next.config", 4),
    ("vite.config", 3),
]

CAPABILITY_SIGNALS: dict[str, list[tuple[str, int]]] = {
    "public-discovery": [
        ("/landing/", 4),
        ("<h1", 2),
        ("robots.txt", 6),
        ("sitemap.xml", 6),
        ("<title", 3),
    ],
    "marketing": [
        ("/landing/", 4),
        ("<h1", 2),
        ("buy game", 4),
        ("get started", 3),
        ("book now", 3),
    ],
    "forms": [("<form", 4), ("usesubmit", 3), ("formdata", 3), ("contact form", 4)],
    "auth": [
        ("next-auth", 6),
        ("auth0", 6),
        ("clerk", 6),
        ("supabase.auth", 5),
        ("password", 2),
    ],
    "commerce": [
        ("stripe", 5),
        ("shopify", 7),
        ("/checkout", 6),
        ("/cart", 5),
        ("payment", 2),
    ],
    "tracking": [
        ("posthog", 6),
        ("gtag(", 5),
        ("google analytics", 5),
        ("segment", 4),
        ("plausible", 4),
    ],
    "data-legal": [
        ("privacy policy", 5),
        ("terms of service", 5),
        ("terms and conditions", 5),
        ("cookie policy", 5),
        ("refund policy", 4),
    ],
    "local-presence": [
        ("localbusiness", 8),
        ("opening hours", 4),
        ("service area", 4),
        ("maps.google", 3),
    ],
    "service-content": [
        ("our services", 4),
        ("case studies", 3),
        ("book appointment", 4),
    ],
    "media-proof": [
        ("before and after", 5),
        ("before-after", 5),
        ("testimonials", 3),
        ("gallery", 2),
    ],
    "content": [
        ("/blog/", 4),
        ("/posts/", 4),
        ("contentful", 4),
        ("sanity", 3),
        (".mdx", 2),
    ],
    "documentation": [
        ("docusaurus", 8),
        ("nextra", 8),
        ("vitepress", 8),
        ("mkdocs", 8),
        ("/docs/", 3),
    ],
    "search": [
        ("algolia", 6),
        ("typesense", 6),
        ("meilisearch", 6),
        ("site search", 4),
        ("searchparams", 1),
    ],
    "social": [
        ("og:image", 4),
        ("opengraph", 3),
        ("twitter:card", 4),
        ("social links", 3),
    ],
    "community": [
        ("moderation", 5),
        ("user-generated", 6),
        ("report abuse", 5),
        ("/comments/", 4),
    ],
    "game": [
        ("phaser", 8),
        ("@pixi/", 8),
        ("babylonjs", 8),
        ("gamestate", 5),
        ("/scenes/", 4),
    ],
    "embedded": [("postmessage", 5), ("messageevent", 4), ("iframe", 2), ("widget", 2)],
    "interaction-extras": [
        ("dark mode", 2),
        ("tooltip", 2),
        ("copy button", 3),
        ("scroll progress", 4),
    ],
}

ARCHETYPE_PRIORITY = [
    "game",
    "ecommerce",
    "local-business",
    "community",
    "internal-tool",
    "docs",
    "publisher",
    "saas",
    "embedded-widget",
    "professional-services",
    "portfolio",
    "marketing",
]

INFERENCE_FIELDS = {
    "archetype_evidence",
    "archetype_scores",
    "automatic_selection_allowed",
    "byte_limit_reached",
    "bytes_scanned",
    "capability_candidates",
    "capability_evidence",
    "capability_scores",
    "confidence",
    "file_limit_reached",
    "files_scanned",
    "needs_review",
    "root",
    "scan_complete",
    "scan_truncated",
    "selected_archetype",
    "selected_capabilities",
    "surface_candidates",
    "truncated_files",
    "unreadable_files",
    "web_evidence",
    "web_score",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def document_kind(rel: str) -> str:
    path = Path(rel)
    parts = {part.lower() for part in path.parts}
    name = path.name.lower()
    if name in {"package.json", "pyproject.toml", "cargo.toml", "gemfile"}:
        return "manifest"
    if parts & LOW_SIGNAL_DIRS or re.search(r"(?:^|[._-])(test|spec)(?:[._-]|$)", name):
        return "test-or-fixture"
    if name.startswith("readme") or path.suffix.lower() in {".md", ".mdx"}:
        return "documentation"
    return "source"


def collect_documents(root: Path) -> tuple[list[tuple[str, str, str]], dict[str, Any]]:
    documents: list[tuple[str, str, str]] = []
    file_count = 0
    total_bytes = 0
    file_limit_reached = False
    byte_limit_reached = False
    truncated_files: list[str] = []
    unreadable_files: list[str] = []
    for current, directories, files in os.walk(root):
        directories[:] = sorted(
            directory
            for directory in directories
            if directory not in IGNORE_DIRS
            and not (Path(current) / directory).is_symlink()
        )
        for name in sorted(files):
            if file_count >= MAX_FILES:
                file_limit_reached = True
                break
            if total_bytes >= MAX_TOTAL_BYTES:
                byte_limit_reached = True
                break
            path = Path(current) / name
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                continue
            if name.endswith("ledger.json") or name in {
                "classification-review.json",
                "yarn.lock",
                "package-lock.json",
                "pnpm-lock.yaml",
            }:
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES and name not in {
                "Dockerfile",
                "Gemfile",
                "Procfile",
            }:
                continue
            try:
                with path.open("rb") as handle:
                    raw = handle.read(MAX_FILE_BYTES + 1)
            except (OSError, PermissionError):
                if len(unreadable_files) < 20:
                    unreadable_files.append(rel)
                continue
            if path.suffix.lower() == ".json":
                try:
                    possible_gate_file = json.loads(raw.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    possible_gate_file = None
                if isinstance(possible_gate_file, dict):
                    ledger_signature = {
                        "schema_version",
                        "mode",
                        "archetype",
                        "capabilities",
                        "checks",
                    }
                    review_signature = {
                        "primary_archetype",
                        "surfaces",
                        "capabilities",
                        "confirmation",
                    }
                    if (
                        ledger_signature.issubset(possible_gate_file)
                        or set(possible_gate_file) == review_signature
                    ):
                        continue
            if len(raw) > MAX_FILE_BYTES:
                if len(truncated_files) < 20:
                    truncated_files.append(rel)
                raw = raw[:MAX_FILE_BYTES]
            if total_bytes + len(raw) > MAX_TOTAL_BYTES:
                remaining = MAX_TOTAL_BYTES - total_bytes
                if remaining <= 0:
                    byte_limit_reached = True
                    break
                if len(truncated_files) < 20 and rel not in truncated_files:
                    truncated_files.append(rel)
                raw = raw[:remaining]
                byte_limit_reached = True
            file_count += 1
            total_bytes += len(raw)
            documents.append(
                (rel, raw.decode("utf-8", errors="ignore"), document_kind(rel))
            )
            if byte_limit_reached:
                break
        if file_limit_reached or byte_limit_reached:
            break
    scan_truncated = file_limit_reached or byte_limit_reached or bool(truncated_files)
    scan_complete = not scan_truncated and not unreadable_files
    return documents, {
        "files_scanned": file_count,
        "bytes_scanned": total_bytes,
        "scan_truncated": scan_truncated,
        "scan_complete": scan_complete,
        "file_limit_reached": file_limit_reached,
        "byte_limit_reached": byte_limit_reached,
        "truncated_files": truncated_files,
        "unreadable_files": unreadable_files,
    }


def signal_weight(weight: int, kind: str) -> int:
    if kind == "source":
        return weight
    if kind == "manifest":
        return min(3, max(1, (weight + 2) // 3))
    return 1


def score_signals(
    documents: list[tuple[str, str, str]],
    signals: dict[str, list[tuple[str, int]]],
) -> tuple[dict[str, int], dict[str, list[str]]]:
    scores = {name: 0 for name in signals}
    evidence: dict[str, list[str]] = {name: [] for name in signals}
    contributions: dict[str, dict[str, int]] = {name: {} for name in signals}
    for rel, content, kind in documents:
        haystack = f"/{rel.lower()}\n{content.lower()}"
        for name, patterns in signals.items():
            for pattern, weight in patterns:
                if pattern in haystack:
                    contribution = signal_weight(weight, kind)
                    previous = contributions[name].get(pattern, 0)
                    if contribution > previous:
                        scores[name] += contribution - previous
                        contributions[name][pattern] = contribution
                    item = f"{rel} [{kind}]: {pattern}"
                    if item not in evidence[name] and len(evidence[name]) < 8:
                        evidence[name].append(item)
    return scores, evidence


def score_web(documents: list[tuple[str, str, str]]) -> tuple[int, list[str]]:
    score = 0
    evidence: list[str] = []
    contributions: dict[str, int] = {}
    for rel, content, kind in documents:
        haystack = f"/{rel.lower()}\n{content.lower()}"
        for pattern, weight in WEB_SIGNALS:
            if pattern in haystack:
                contribution = signal_weight(weight, kind)
                previous = contributions.get(pattern, 0)
                if contribution > previous:
                    score += contribution - previous
                    contributions[pattern] = contribution
                item = f"{rel} [{kind}]: {pattern}"
                if item not in evidence and len(evidence) < 8:
                    evidence.append(item)
    return score, evidence


def infer_surface_candidates(
    documents: list[tuple[str, str, str]],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for rel, content, kind in documents:
        if kind != "source":
            continue
        haystack = f"/{rel.lower()}\n{content.lower()}"
        archetypes: dict[str, list[str]] = {}
        capabilities: dict[str, list[str]] = {}
        for archetype, patterns in ARCHETYPE_SIGNALS.items():
            matches = [
                pattern
                for pattern, weight in patterns
                if weight >= 3 and pattern in haystack
            ]
            if sum(weight for pattern, weight in patterns if pattern in matches) >= 4:
                archetypes[archetype] = matches
        for capability, patterns in CAPABILITY_SIGNALS.items():
            matches = [
                pattern
                for pattern, weight in patterns
                if weight >= 2 and pattern in haystack
            ]
            if sum(weight for pattern, weight in patterns if pattern in matches) >= 4:
                capabilities[capability] = matches
        if not archetypes and not capabilities:
            continue
        lowered = rel.lower()
        if any(
            token in lowered
            for token in ("/landing/", "/pages/", "/public/", "app/page", "index.")
        ):
            visibility = "public-candidate"
        elif any(
            token in lowered for token in ("/admin/", "/dashboard/", "/internal/")
        ):
            visibility = "private-candidate"
        else:
            visibility = "unknown"
        surface_id = re.sub(r"[^a-z0-9]+", "-", rel.lower()).strip("-")[:48]
        candidates.append(
            {
                "id": surface_id or "source",
                "source": rel,
                "visibility_candidate": visibility,
                "archetype_candidates": sorted(archetypes),
                "capability_candidates": sorted(capabilities),
                "evidence": {
                    "archetypes": archetypes,
                    "capabilities": capabilities,
                },
            }
        )
    return candidates[:40]


def select_archetype(scores: dict[str, int], web_score: int) -> tuple[str, str, bool]:
    ranked = sorted(
        scores.items(),
        key=lambda item: (-item[1], ARCHETYPE_PRIORITY.index(item[0])),
    )
    top_name, top_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0
    if top_score < 4:
        if web_score >= 3:
            return "web-app", "low", True
        return "non-web", "low", False
    margin = top_score - second_score
    if top_score >= 8 and margin >= 3:
        return top_name, "high", False
    return top_name, "medium", margin <= 2


def infer_repository(root: Path) -> dict[str, Any]:
    resolved = root.resolve()
    if not resolved.is_dir():
        raise ValueError(f"Repository root is not a directory: {resolved}")
    documents, scan = collect_documents(resolved)
    archetype_scores, archetype_evidence = score_signals(documents, ARCHETYPE_SIGNALS)
    capability_scores, capability_evidence = score_signals(
        documents, CAPABILITY_SIGNALS
    )
    web_score, web_evidence = score_web(documents)
    surface_candidates = infer_surface_candidates(documents)
    archetype, confidence, needs_review = select_archetype(archetype_scores, web_score)
    capabilities = set(ARCHETYPE_DEFAULTS[archetype])
    for capability, score in capability_scores.items():
        if score >= 4:
            capabilities.add(capability)
    if archetype == "non-web":
        capabilities = {
            capability
            for capability in capabilities
            if capability not in CAPABILITY_GROUPS
        }
    if not scan["scan_complete"]:
        confidence = "low"
        needs_review = True
    capability_candidates = sorted(
        capability for capability, score in capability_scores.items() if score > 0
    )
    secondary_surface = any(
        candidate_archetype != archetype
        for surface in surface_candidates
        for candidate_archetype in surface["archetype_candidates"]
    )
    if secondary_surface or (
        archetype == "game"
        and ({"marketing", "public-discovery"} & set(capability_candidates))
    ):
        needs_review = True
    return {
        "root": str(resolved),
        **scan,
        "selected_archetype": archetype,
        "confidence": confidence,
        "needs_review": needs_review,
        "automatic_selection_allowed": scan["scan_complete"]
        and confidence == "high"
        and not needs_review,
        "web_score": web_score,
        "web_evidence": web_evidence,
        "archetype_scores": archetype_scores,
        "archetype_evidence": {
            name: items for name, items in archetype_evidence.items() if items
        },
        "capability_scores": capability_scores,
        "capability_evidence": {
            name: items for name, items in capability_evidence.items() if items
        },
        "capability_candidates": capability_candidates,
        "selected_capabilities": sorted(capabilities),
        "surface_candidates": surface_candidates,
    }


def empty_evidence() -> dict[str, Any]:
    return {
        "kind": None,
        "target": "",
        "observed": "",
        "capability_unavailable": None,
        "scope_ids": [],
    }


def check_record(check_id: str, sources: list[str]) -> dict[str, Any]:
    definition = CHECKS[check_id]
    return {
        "id": check_id,
        "group": definition["group"],
        "label": definition["label"],
        "sources": sources,
        "status": "pending",
        "evidence": empty_evidence(),
        "updated_at": None,
    }


def selected_check_sources(mode: str, capabilities: list[str]) -> dict[str, list[str]]:
    selected: dict[str, set[str]] = {}

    def include(check_ids: Iterable[str], source: str) -> None:
        for check_id in check_ids:
            selected.setdefault(check_id, set()).add(source)

    include(COMMON_IDS, "common")
    include(MODE_IDS[mode], f"mode:{mode}")
    for capability in capabilities:
        include(CAPABILITY_GROUPS[capability], f"capability:{capability}")
    return {check_id: sorted(sources) for check_id, sources in sorted(selected.items())}


def definition_fingerprint(
    mode: str,
    archetype: str,
    capabilities: list[str],
    sources: dict[str, list[str]],
) -> str:
    definitions = {
        check_id: {
            **CHECKS[check_id],
            "sources": check_sources,
        }
        for check_id, check_sources in sources.items()
    }
    canonical = json.dumps(
        {
            "schema_version": SCHEMA_VERSION,
            "mode": mode,
            "archetype": archetype,
            "capabilities": capabilities,
            "definitions": definitions,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def empty_classification_review(archetype: str) -> dict[str, Any]:
    return {
        "status": "pending",
        "primary_archetype": archetype,
        "surfaces": [],
        "capabilities": {
            capability: {
                "decision": "pending",
                "scopes": [],
                "evidence": empty_evidence(),
                "updated_at": None,
            }
            for capability in sorted(CAPABILITY_GROUPS)
        },
        "confirmation": empty_evidence(),
        "inference_disposition": {
            "decision": "pending",
            "direct_evidence": empty_evidence(),
            "reason": empty_evidence(),
            "updated_at": None,
        },
        "updated_at": None,
    }


def build_ledger(
    mode: str,
    archetype: str,
    capabilities: list[str],
    classification: dict[str, Any] | None,
) -> dict[str, Any]:
    if mode not in MODE_IDS:
        raise ValueError(f"Unknown mode: {mode}")
    if archetype not in ARCHETYPE_DEFAULTS:
        raise ValueError(f"Unknown archetype: {archetype}")
    normalized_capabilities = sorted(set(capabilities))
    unknown = sorted(set(normalized_capabilities) - set(CAPABILITY_GROUPS))
    if unknown:
        raise ValueError(f"Unknown capabilities: {', '.join(unknown)}")
    missing_defaults = sorted(
        set(ARCHETYPE_DEFAULTS[archetype]) - set(normalized_capabilities)
    )
    if missing_defaults:
        raise ValueError(
            f"Archetype {archetype} requires default capabilities: {', '.join(missing_defaults)}"
        )
    selected = selected_check_sources(mode, normalized_capabilities)
    checks = {
        check_id: check_record(check_id, sources)
        for check_id, sources in selected.items()
    }
    now = utc_now()
    return {
        "schema_version": SCHEMA_VERSION,
        "ledger_id": str(uuid.uuid4()),
        "created_at": now,
        "updated_at": now,
        "mode": mode,
        "archetype": archetype,
        "capabilities": normalized_capabilities,
        "classification": classification,
        "classification_review": empty_classification_review(archetype),
        "definition_fingerprint": definition_fingerprint(
            mode, archetype, normalized_capabilities, selected
        ),
        "required_check_ids": sorted(selected),
        "custom_check_ids": [],
        "checks": checks,
    }


def write_json(path: Path, payload: dict[str, Any], overwrite: bool = True) -> None:
    path = path.resolve()
    if path.exists() and not overwrite:
        raise ValueError(f"Refusing to overwrite existing ledger: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def load_ledger(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Ledger not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Ledger is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Ledger schema version is missing or unsupported")
    return payload


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or "T" not in value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def timestamp_is_valid(value: Any) -> bool:
    return parse_timestamp(value) is not None


def validate_timestamp_bounds(
    subject: str,
    value: Any,
    created_at: datetime | None,
    updated_at: datetime | None,
) -> str | None:
    parsed = parse_timestamp(value)
    if parsed is None or created_at is None or updated_at is None:
        return None
    if parsed < created_at:
        return f"{subject}: timestamp is earlier than ledger creation"
    if parsed > updated_at:
        return f"{subject}: timestamp is later than the ledger update time"
    if parsed > datetime.now(timezone.utc) + timedelta(minutes=5):
        return f"{subject}: timestamp is implausibly in the future"
    return None


def is_sorted_unique_text_list(value: Any) -> bool:
    return (
        isinstance(value, list)
        and all(isinstance(item, str) for item in value)
        and value == sorted(set(value))
    )


def visible_text(value: str) -> str:
    return "".join(
        character
        for character in value
        if not character.isspace()
        and not unicodedata.category(character).startswith(("C", "Z"))
    )


def validate_evidence(subject: str, status: str, evidence: Any) -> list[str]:
    errors: list[str] = []
    expected_fields = {
        "kind",
        "target",
        "observed",
        "capability_unavailable",
        "scope_ids",
    }
    if not isinstance(evidence, dict):
        return [f"{subject}: evidence must be an object"]
    fields = set(evidence)
    if fields != expected_fields:
        missing = sorted(expected_fields - fields)
        extra = sorted(fields - expected_fields)
        if missing:
            errors.append(
                f"{subject}: evidence is missing fields: {', '.join(missing)}"
            )
        if extra:
            errors.append(f"{subject}: evidence has unknown fields: {', '.join(extra)}")
        return errors
    kind = evidence.get("kind")
    target = evidence.get("target")
    observed = evidence.get("observed")
    capability_unavailable = evidence.get("capability_unavailable")
    scope_ids = evidence.get("scope_ids")
    if status == "pending":
        if (
            kind is not None
            or target != ""
            or observed != ""
            or capability_unavailable is not None
            or scope_ids != []
        ):
            errors.append(f"{subject}: pending evidence must be empty")
        return errors
    if kind not in VALID_EVIDENCE_KINDS:
        errors.append(f"{subject}: invalid evidence kind {kind!r}")
    visible_target = visible_text(target) if isinstance(target, str) else ""
    if (
        len(visible_target) < 3
        or sum(character.isalnum() for character in visible_target) < 2
    ):
        errors.append(
            f"{subject}: evidence target must identify a file, route, command, behavior, or scope"
        )
    if not isinstance(observed, str):
        errors.append(f"{subject}: observed result must be text")
    else:
        normalized = observed.strip().lower().rstrip(".")
        visible_observed = visible_text(observed)
        observed_words = re.findall(r"[^\W_]+", observed, flags=re.UNICODE)
        if (
            len(visible_observed) < 12
            or sum(character.isalnum() for character in visible_observed) < 6
            or len(observed_words) < 2
            or normalized in WEAK_EVIDENCE
        ):
            errors.append(f"{subject}: observed result is too vague")
        if status == "na" and normalized in {
            "n/a",
            "na",
            "not needed",
            "not applicable",
            "irrelevant",
            "none",
        }:
            errors.append(f"{subject}: not-applicable reason is too vague")
    if not isinstance(capability_unavailable, bool):
        errors.append(f"{subject}: capability_unavailable must be true or false")
    if not is_sorted_unique_text_list(scope_ids) or not scope_ids:
        errors.append(f"{subject}: scope_ids must be a nonempty sorted unique list")
    if status == "pass":
        if kind not in DIRECT_EVIDENCE_KINDS:
            errors.append(f"{subject}: pass requires a direct evidence kind")
        if capability_unavailable is not False:
            errors.append(f"{subject}: pass cannot claim an unavailable capability")
    elif status == "fix":
        if kind not in DIRECT_EVIDENCE_KINDS | {"observation"}:
            errors.append(f"{subject}: fix requires direct or observation evidence")
        if capability_unavailable is not False:
            errors.append(f"{subject}: fix cannot claim an unavailable capability")
    elif status == "na":
        if kind != "reason":
            errors.append(f"{subject}: not applicable requires reason evidence")
        if capability_unavailable is not False:
            errors.append(
                f"{subject}: not applicable cannot claim an unavailable capability"
            )
    elif status == "blocked" and kind != "blocker":
        errors.append(f"{subject}: blocked requires blocker evidence")
    return errors


def validate_inference(classification: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(classification, dict):
        return ["Ledger classification must be an object or null"]
    if set(classification) != INFERENCE_FIELDS:
        missing = sorted(INFERENCE_FIELDS - set(classification))
        extra = sorted(set(classification) - INFERENCE_FIELDS)
        if missing:
            errors.append(
                f"Ledger classification is missing fields: {', '.join(missing)}"
            )
        if extra:
            errors.append(
                f"Ledger classification has unknown fields: {', '.join(extra)}"
            )
        return errors
    if (
        not isinstance(classification["root"], str)
        or not Path(classification["root"]).is_absolute()
        or not visible_text(classification["root"])
    ):
        errors.append("Ledger classification root must be an absolute visible path")
    for field in ("files_scanned", "bytes_scanned", "web_score"):
        if type(classification[field]) is not int or classification[field] < 0:
            errors.append(
                f"Ledger classification {field} must be a nonnegative integer"
            )
    for field in (
        "scan_complete",
        "scan_truncated",
        "file_limit_reached",
        "byte_limit_reached",
        "needs_review",
        "automatic_selection_allowed",
    ):
        if type(classification[field]) is not bool:
            errors.append(f"Ledger classification {field} must be true or false")
    for field in ("truncated_files", "unreadable_files", "web_evidence"):
        if not isinstance(classification[field], list) or not all(
            isinstance(item, str) for item in classification[field]
        ):
            errors.append(f"Ledger classification {field} must be a text list")
    expected_scan_complete = (
        not classification["scan_truncated"] and not classification["unreadable_files"]
    )
    if (
        type(classification["scan_complete"]) is bool
        and classification["scan_complete"] != expected_scan_complete
    ):
        errors.append(
            "Ledger classification scan completeness is internally inconsistent"
        )
    if classification["scan_truncated"] != (
        classification["file_limit_reached"]
        or classification["byte_limit_reached"]
        or bool(classification["truncated_files"])
    ):
        errors.append(
            "Ledger classification truncation fields are internally inconsistent"
        )
    if classification["confidence"] not in {"low", "medium", "high"}:
        errors.append("Ledger classification confidence is invalid")
    archetype = classification["selected_archetype"]
    if archetype not in ARCHETYPE_DEFAULTS:
        errors.append("Ledger classification contains an unknown selected archetype")
    selected_capabilities = classification["selected_capabilities"]
    if not is_sorted_unique_text_list(selected_capabilities) or not set(
        selected_capabilities
    ).issubset(CAPABILITY_GROUPS):
        errors.append("Ledger classification contains invalid selected capabilities")
    elif archetype in ARCHETYPE_DEFAULTS and not set(
        ARCHETYPE_DEFAULTS[archetype]
    ).issubset(selected_capabilities):
        errors.append("Ledger classification omits selected archetype defaults")
    candidates = classification["capability_candidates"]
    if not is_sorted_unique_text_list(candidates) or not set(candidates).issubset(
        CAPABILITY_GROUPS
    ):
        errors.append("Ledger classification contains invalid capability candidates")
    archetype_scores = classification["archetype_scores"]
    archetype_scores_valid = (
        isinstance(archetype_scores, dict)
        and set(archetype_scores) == set(ARCHETYPE_SIGNALS)
        and all(
            type(score) is int and score >= 0 for score in archetype_scores.values()
        )
    )
    if not archetype_scores_valid:
        errors.append(
            "Ledger classification archetype scores do not match the classifier schema"
        )
    capability_scores = classification["capability_scores"]
    capability_scores_valid = (
        isinstance(capability_scores, dict)
        and set(capability_scores) == set(CAPABILITY_SIGNALS)
        and all(
            type(score) is int and score >= 0 for score in capability_scores.values()
        )
    )
    if not capability_scores_valid:
        errors.append(
            "Ledger classification capability scores do not match the classifier schema"
        )
    for field, allowed_keys in (
        ("archetype_evidence", set(ARCHETYPE_SIGNALS)),
        ("capability_evidence", set(CAPABILITY_SIGNALS)),
    ):
        evidence = classification[field]
        if (
            not isinstance(evidence, dict)
            or not set(evidence).issubset(allowed_keys)
            or not all(
                isinstance(items, list) and all(isinstance(item, str) for item in items)
                for items in evidence.values()
            )
        ):
            errors.append(f"Ledger classification {field} is invalid")
    surface_candidates = classification["surface_candidates"]
    surface_candidates_valid = isinstance(surface_candidates, list)
    if not isinstance(surface_candidates, list):
        errors.append("Ledger classification surface candidates must be a list")
    else:
        expected_surface_fields = {
            "id",
            "source",
            "visibility_candidate",
            "archetype_candidates",
            "capability_candidates",
            "evidence",
        }
        for index, surface in enumerate(surface_candidates):
            if not isinstance(surface, dict) or set(surface) != expected_surface_fields:
                errors.append(
                    f"Ledger classification surface candidate {index} is invalid"
                )
                surface_candidates_valid = False
                continue
            candidate_id = surface["id"]
            if (
                not isinstance(candidate_id, str)
                or not candidate_id
                or len(candidate_id) > 48
                or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", candidate_id)
            ):
                errors.append(
                    f"Ledger classification surface candidate {index} has an invalid id"
                )
                surface_candidates_valid = False
            source = surface["source"]
            if (
                not isinstance(source, str)
                or not visible_text(source)
                or not any(character.isalnum() for character in visible_text(source))
            ):
                errors.append(
                    f"Ledger classification surface candidate {index} has an invalid source"
                )
                surface_candidates_valid = False
            if surface["visibility_candidate"] not in {
                "public-candidate",
                "private-candidate",
                "unknown",
            }:
                errors.append(
                    f"Ledger classification surface candidate {index} has an invalid visibility"
                )
                surface_candidates_valid = False
            if not is_sorted_unique_text_list(
                surface["archetype_candidates"]
            ) or not set(surface["archetype_candidates"]).issubset(ARCHETYPE_DEFAULTS):
                errors.append(
                    f"Ledger classification surface candidate {index} has invalid archetypes"
                )
                surface_candidates_valid = False
            if not is_sorted_unique_text_list(
                surface["capability_candidates"]
            ) or not set(surface["capability_candidates"]).issubset(CAPABILITY_GROUPS):
                errors.append(
                    f"Ledger classification surface candidate {index} has invalid capabilities"
                )
                surface_candidates_valid = False
            candidate_evidence = surface["evidence"]
            if (
                not isinstance(candidate_evidence, dict)
                or set(candidate_evidence) != {"archetypes", "capabilities"}
                or not isinstance(candidate_evidence.get("archetypes"), dict)
                or not isinstance(candidate_evidence.get("capabilities"), dict)
            ):
                errors.append(
                    f"Ledger classification surface candidate {index} has invalid evidence"
                )
                surface_candidates_valid = False
            else:
                evidence_groups = (
                    (
                        "archetypes",
                        surface["archetype_candidates"],
                        set(ARCHETYPE_SIGNALS),
                    ),
                    (
                        "capabilities",
                        surface["capability_candidates"],
                        set(CAPABILITY_SIGNALS),
                    ),
                )
                for evidence_name, candidate_names, allowed_names in evidence_groups:
                    evidence_items = candidate_evidence[evidence_name]
                    if (
                        not is_sorted_unique_text_list(candidate_names)
                        or not set(evidence_items).issubset(allowed_names)
                        or set(evidence_items) != set(candidate_names)
                        or not all(
                            isinstance(matches, list)
                            and bool(matches)
                            and all(
                                isinstance(match, str) and bool(visible_text(match))
                                for match in matches
                            )
                            for matches in evidence_items.values()
                        )
                    ):
                        errors.append(
                            f"Ledger classification surface candidate {index} has invalid {evidence_name} evidence"
                        )
                        surface_candidates_valid = False

    scores_can_be_replayed = (
        archetype_scores_valid
        and capability_scores_valid
        and type(classification["web_score"]) is int
        and classification["web_score"] >= 0
    )
    if scores_can_be_replayed:
        expected_archetype, expected_confidence, expected_needs_review = (
            select_archetype(archetype_scores, classification["web_score"])
        )
        if classification["scan_complete"] is False:
            expected_confidence = "low"
            expected_needs_review = True
        expected_candidates = sorted(
            capability for capability, score in capability_scores.items() if score > 0
        )
        expected_capabilities = set(ARCHETYPE_DEFAULTS[expected_archetype])
        expected_capabilities.update(
            capability for capability, score in capability_scores.items() if score >= 4
        )
        if expected_archetype == "non-web":
            expected_capabilities = set()
        if surface_candidates_valid:
            secondary_surface = any(
                candidate_archetype != expected_archetype
                for surface in surface_candidates
                for candidate_archetype in surface["archetype_candidates"]
            )
            if secondary_surface or (
                expected_archetype == "game"
                and {"marketing", "public-discovery"} & set(expected_candidates)
            ):
                expected_needs_review = True
        if classification["selected_archetype"] != expected_archetype:
            errors.append(
                "Ledger classification selected archetype does not match its scores"
            )
        if classification["confidence"] != expected_confidence:
            errors.append("Ledger classification confidence does not match its scores")
        if classification["capability_candidates"] != expected_candidates:
            errors.append(
                "Ledger classification capability candidates do not match their scores"
            )
        if classification["selected_capabilities"] != sorted(expected_capabilities):
            errors.append(
                "Ledger classification selected capabilities do not match their scores"
            )
        if (
            surface_candidates_valid
            and classification["needs_review"] != expected_needs_review
        ):
            errors.append(
                "Ledger classification review state does not match its evidence"
            )
    expected_automatic = (
        classification["scan_complete"] is True
        and classification["confidence"] == "high"
        and classification["needs_review"] is False
    )
    if classification["automatic_selection_allowed"] != expected_automatic:
        errors.append("Ledger classification automatic-selection state is inconsistent")
    if not classification["scan_complete"] and classification["confidence"] != "low":
        errors.append("Incomplete classification scans must have low confidence")
    return errors


def validate_classification_review(payload: dict[str, Any], errors: list[str]) -> None:
    review = payload.get("classification_review")
    if not isinstance(review, dict):
        errors.append("classification_review must be an object")
        return
    expected_fields = {
        "status",
        "primary_archetype",
        "surfaces",
        "capabilities",
        "confirmation",
        "inference_disposition",
        "updated_at",
    }
    if set(review) != expected_fields:
        errors.append("classification_review fields do not match the schema")
        return
    status = review.get("status")
    if status not in {"pending", "pass"}:
        errors.append("classification_review status must be pending or pass")
        return
    if review.get("primary_archetype") != payload.get("archetype"):
        errors.append(
            "classification_review primary archetype does not match the ledger"
        )
    capabilities = review.get("capabilities")
    if not isinstance(capabilities, dict) or set(capabilities) != set(
        CAPABILITY_GROUPS
    ):
        errors.append(
            "classification_review must contain every capability decision exactly once"
        )
        return
    if status == "pending":
        if review.get("surfaces") != [] or review.get("updated_at") is not None:
            errors.append(
                "pending classification_review must not contain surfaces or an update time"
            )
        errors.extend(
            validate_evidence(
                "classification_review confirmation",
                "pending",
                review.get("confirmation"),
            )
        )
        disposition = review.get("inference_disposition")
        if not isinstance(disposition, dict) or set(disposition) != {
            "decision",
            "direct_evidence",
            "reason",
            "updated_at",
        }:
            errors.append(
                "pending inference_disposition fields do not match the schema"
            )
        else:
            if (
                disposition.get("decision") != "pending"
                or disposition.get("updated_at") is not None
            ):
                errors.append("pending inference_disposition must remain unresolved")
            errors.extend(
                validate_evidence(
                    "inference_disposition direct evidence",
                    "pending",
                    disposition.get("direct_evidence"),
                )
            )
            errors.extend(
                validate_evidence(
                    "inference_disposition reason", "pending", disposition.get("reason")
                )
            )
        for capability, decision in capabilities.items():
            if not isinstance(decision, dict) or set(decision) != {
                "decision",
                "scopes",
                "evidence",
                "updated_at",
            }:
                errors.append(
                    f"classification_review {capability}: fields do not match the schema"
                )
                continue
            if decision.get("decision") != "pending":
                errors.append(
                    f"classification_review {capability}: pending review was modified"
                )
                continue
            if decision.get("scopes") != [] or decision.get("updated_at") is not None:
                errors.append(
                    f"classification_review {capability}: pending decision must be empty"
                )
            errors.extend(
                validate_evidence(
                    f"classification_review {capability}",
                    "pending",
                    decision.get("evidence"),
                )
            )
        return

    if not timestamp_is_valid(review.get("updated_at")):
        errors.append("classification_review pass requires a valid update time")
    errors.extend(
        validate_evidence(
            "classification_review confirmation", "pass", review.get("confirmation")
        )
    )
    surfaces = review.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        errors.append(
            "classification_review pass requires at least one route or product surface"
        )
        return
    surface_ids: set[str] = set()
    surface_archetypes: dict[str, str] = {}
    primary_found = False
    for index, surface in enumerate(surfaces):
        subject = f"classification_review surface {index}"
        if not isinstance(surface, dict) or set(surface) != {
            "id",
            "path",
            "archetype",
            "visibility",
            "evidence",
            "updated_at",
        }:
            errors.append(f"{subject}: fields do not match the schema")
            continue
        surface_id = surface.get("id")
        if not isinstance(surface_id, str) or not re.fullmatch(
            r"[a-z][a-z0-9_-]{1,31}", surface_id
        ):
            errors.append(
                f"{subject}: id must be 2 to 32 lowercase letters, digits, underscores, or hyphens"
            )
        elif surface_id in surface_ids:
            errors.append(f"{subject}: duplicate id {surface_id}")
        else:
            surface_ids.add(surface_id)
            if surface.get("archetype") in ARCHETYPE_DEFAULTS:
                surface_archetypes[surface_id] = surface["archetype"]
        surface_path = surface.get("path")
        if not isinstance(surface_path, str) or (
            surface_path not in {"/", "."}
            and (
                len(visible_text(surface_path)) < 1
                or not any(
                    character.isalnum() for character in visible_text(surface_path)
                )
            )
        ):
            errors.append(f"{subject}: path must not be empty")
        if surface.get("archetype") not in ARCHETYPE_DEFAULTS:
            errors.append(f"{subject}: unknown archetype {surface.get('archetype')!r}")
        if surface.get("archetype") == payload.get("archetype"):
            primary_found = True
        if surface.get("visibility") not in {
            "public",
            "private",
            "embedded",
            "non-web",
        }:
            errors.append(f"{subject}: visibility is invalid")
        if not timestamp_is_valid(surface.get("updated_at")):
            errors.append(f"{subject}: update time is invalid")
        surface_evidence = surface.get("evidence")
        errors.extend(validate_evidence(subject, "pass", surface_evidence))
        if isinstance(surface_evidence, dict) and surface_evidence.get("scope_ids") != [
            surface_id
        ]:
            errors.append(
                f"{subject}: evidence scope_ids must contain only its surface id"
            )
    if not primary_found:
        errors.append(
            "classification_review surfaces do not include the primary archetype"
        )

    confirmation = review.get("confirmation")
    if isinstance(confirmation, dict) and confirmation.get("scope_ids") != sorted(
        surface_ids
    ):
        errors.append("classification_review confirmation must cover every surface")

    payload_capabilities = payload.get("capabilities")
    selected_capabilities = (
        set(payload_capabilities)
        if isinstance(payload_capabilities, list)
        and all(isinstance(capability, str) for capability in payload_capabilities)
        else set()
    )
    disposition = review.get("inference_disposition")
    if not isinstance(disposition, dict) or set(disposition) != {
        "decision",
        "direct_evidence",
        "reason",
        "updated_at",
    }:
        errors.append("inference_disposition fields do not match the schema")
    else:
        classification = payload.get("classification")
        if classification is None:
            expected_disposition = "not-run"
        else:
            inferred_capabilities = (
                set(classification.get("selected_capabilities", []))
                if isinstance(classification, dict)
                and is_sorted_unique_text_list(
                    classification.get("selected_capabilities")
                )
                else set()
            )
            inference_changed = (
                not isinstance(classification, dict)
                or classification.get("selected_archetype") != payload.get("archetype")
                or not inferred_capabilities.issubset(selected_capabilities)
            )
            expected_disposition = "overridden" if inference_changed else "accepted"
        if disposition.get("decision") != expected_disposition:
            errors.append(f"inference_disposition must be {expected_disposition}")
        if not timestamp_is_valid(disposition.get("updated_at")):
            errors.append("inference_disposition update time is invalid")
        direct_evidence = disposition.get("direct_evidence")
        errors.extend(
            validate_evidence(
                "inference_disposition direct evidence", "pass", direct_evidence
            )
        )
        if isinstance(direct_evidence, dict) and direct_evidence.get(
            "scope_ids"
        ) != sorted(surface_ids):
            errors.append(
                "inference_disposition direct evidence must cover every surface"
            )
        reason_status = "pending" if expected_disposition == "accepted" else "na"
        reason = disposition.get("reason")
        errors.extend(
            validate_evidence("inference_disposition reason", reason_status, reason)
        )
        if (
            reason_status == "na"
            and isinstance(reason, dict)
            and reason.get("scope_ids") != sorted(surface_ids)
        ):
            errors.append("inference_disposition reason must cover every surface")
        if isinstance(classification, dict):
            disposition_text = " ".join(
                str(item)
                for evidence in (direct_evidence, reason)
                if isinstance(evidence, dict)
                for item in (evidence.get("target", ""), evidence.get("observed", ""))
            ).lower()
            inferred_capabilities = set(
                classification.get("selected_capabilities", [])
                if is_sorted_unique_text_list(
                    classification.get("selected_capabilities")
                )
                else []
            )
            removed_capabilities = sorted(inferred_capabilities - selected_capabilities)
            if expected_disposition == "overridden":
                for capability in removed_capabilities:
                    if capability.lower() not in disposition_text:
                        errors.append(
                            "inference_disposition evidence omits removed inferred "
                            f"capability {capability}"
                        )

            reviewed_archetypes = set(surface_archetypes.values())
            for index, candidate in enumerate(
                classification.get("surface_candidates", [])
                if isinstance(classification.get("surface_candidates"), list)
                else []
            ):
                if not isinstance(candidate, dict):
                    continue
                candidate_archetypes = candidate.get("archetype_candidates")
                candidate_capabilities = candidate.get("capability_candidates")
                archetype_covered = is_sorted_unique_text_list(
                    candidate_archetypes
                ) and bool(set(candidate_archetypes) & reviewed_archetypes)
                capability_covered = (
                    not candidate_archetypes
                    and is_sorted_unique_text_list(candidate_capabilities)
                    and bool(set(candidate_capabilities) & selected_capabilities)
                )
                source = candidate.get("source")
                candidate_id = candidate.get("id")
                explicitly_overridden = expected_disposition == "overridden" and any(
                    isinstance(identifier, str)
                    and identifier.lower() in disposition_text
                    for identifier in (source, candidate_id)
                )
                if (
                    not archetype_covered
                    and not capability_covered
                    and not explicitly_overridden
                ):
                    errors.append(
                        "classification_review omits material inferred surface candidate "
                        f"{index}: {source!r}"
                    )
    for capability, decision in capabilities.items():
        subject = f"classification_review {capability}"
        if not isinstance(decision, dict) or set(decision) != {
            "decision",
            "scopes",
            "evidence",
            "updated_at",
        }:
            errors.append(f"{subject}: fields do not match the schema")
            continue
        expected_decision = (
            "active" if capability in selected_capabilities else "rejected"
        )
        if decision.get("decision") != expected_decision:
            errors.append(f"{subject}: expected decision {expected_decision}")
        scopes = decision.get("scopes")
        if not is_sorted_unique_text_list(scopes) or not scopes:
            errors.append(f"{subject}: scopes must contain at least one surface id")
        elif not set(scopes).issubset(surface_ids):
            errors.append(f"{subject}: scopes contain an unknown surface id")
        if not timestamp_is_valid(decision.get("updated_at")):
            errors.append(f"{subject}: update time is invalid")
        evidence_status = "pass" if expected_decision == "active" else "na"
        decision_evidence = decision.get("evidence")
        errors.extend(validate_evidence(subject, evidence_status, decision_evidence))
        if (
            isinstance(decision_evidence, dict)
            and decision_evidence.get("scope_ids") != scopes
        ):
            errors.append(
                f"{subject}: evidence scope_ids must match its declared scopes"
            )

    for surface_id, surface_archetype in surface_archetypes.items():
        for capability in SURFACE_REQUIRED_CAPABILITIES[surface_archetype]:
            decision = capabilities.get(capability)
            if not isinstance(decision, dict):
                continue
            if decision.get("decision") != "active" or surface_id not in decision.get(
                "scopes", []
            ):
                errors.append(
                    f"classification_review surface {surface_id}: {surface_archetype} requires "
                    f"active capability {capability} on that surface"
                )


def validate_ledger(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_top_fields = {
        "schema_version",
        "ledger_id",
        "created_at",
        "updated_at",
        "mode",
        "archetype",
        "capabilities",
        "classification",
        "classification_review",
        "definition_fingerprint",
        "required_check_ids",
        "custom_check_ids",
        "checks",
    }
    if not isinstance(payload, dict):
        return ["Ledger must be an object"]
    if set(payload) != expected_top_fields:
        missing = sorted(expected_top_fields - set(payload))
        extra = sorted(set(payload) - expected_top_fields)
        if missing:
            errors.append(f"Ledger is missing fields: {', '.join(missing)}")
        if extra:
            errors.append(f"Ledger has unknown fields: {', '.join(extra)}")
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append("Ledger schema version is missing or unsupported")
    try:
        uuid.UUID(str(payload.get("ledger_id")))
    except (ValueError, AttributeError):
        errors.append("Ledger id is missing or invalid")
    created_at = parse_timestamp(payload.get("created_at"))
    updated_at = parse_timestamp(payload.get("updated_at"))
    if created_at is None or updated_at is None:
        errors.append("Ledger creation and update times must be valid timestamps")
    else:
        if updated_at < created_at:
            errors.append("Ledger update time is earlier than its creation time")
        if created_at > datetime.now(timezone.utc) + timedelta(minutes=5):
            errors.append("Ledger creation time is implausibly in the future")
        if updated_at > datetime.now(timezone.utc) + timedelta(minutes=5):
            errors.append("Ledger update time is implausibly in the future")
    mode = payload.get("mode")
    archetype = payload.get("archetype")
    capabilities = payload.get("capabilities")
    if mode not in MODE_IDS:
        errors.append(f"Unknown ledger mode: {mode!r}")
    if archetype not in ARCHETYPE_DEFAULTS:
        errors.append(f"Unknown ledger archetype: {archetype!r}")
    if not is_sorted_unique_text_list(capabilities):
        errors.append("Ledger capabilities must be a sorted unique list")
        normalized_capabilities: list[str] = []
    else:
        normalized_capabilities = capabilities
        unknown_capabilities = sorted(set(capabilities) - set(CAPABILITY_GROUPS))
        if unknown_capabilities:
            errors.append(
                f"Unknown ledger capabilities: {', '.join(unknown_capabilities)}"
            )
    review_for_defaults = payload.get("classification_review")
    review_is_applied = (
        isinstance(review_for_defaults, dict)
        and review_for_defaults.get("status") == "pass"
    )
    if archetype in ARCHETYPE_DEFAULTS and not review_is_applied:
        missing_defaults = sorted(
            set(ARCHETYPE_DEFAULTS[archetype]) - set(normalized_capabilities)
        )
        if missing_defaults:
            errors.append(
                f"Ledger omits archetype defaults: {', '.join(missing_defaults)}"
            )
    classification = payload.get("classification")
    if classification is not None:
        errors.extend(validate_inference(classification))

    expected_sources: dict[str, list[str]] = {}
    if mode in MODE_IDS and all(
        capability in CAPABILITY_GROUPS for capability in normalized_capabilities
    ):
        expected_sources = selected_check_sources(mode, normalized_capabilities)
    expected_required_ids = sorted(expected_sources)
    if payload.get("required_check_ids") != expected_required_ids:
        errors.append("Required check ids do not match mode and capabilities")
    if mode in MODE_IDS and archetype in ARCHETYPE_DEFAULTS and expected_sources:
        expected_fingerprint = definition_fingerprint(
            mode, archetype, normalized_capabilities, expected_sources
        )
        if payload.get("definition_fingerprint") != expected_fingerprint:
            errors.append(
                "Ledger definition fingerprint does not match its selected profile"
            )
    custom_ids = payload.get("custom_check_ids")
    if not is_sorted_unique_text_list(custom_ids):
        errors.append("Custom check ids must be a sorted unique list")
        normalized_custom_ids: list[str] = []
    else:
        normalized_custom_ids = custom_ids
        for check_id in custom_ids:
            if not isinstance(check_id, str) or not re.fullmatch(
                r"[A-Z][A-Z0-9_-]{2,31}", check_id
            ):
                errors.append(f"Invalid custom check id: {check_id!r}")
            if check_id in CHECKS:
                errors.append(
                    f"Custom check id collides with a built-in check: {check_id}"
                )
    checks = payload.get("checks")
    if not isinstance(checks, dict):
        errors.append("Ledger checks must be an object")
        return errors
    expected_check_ids = set(expected_required_ids) | set(normalized_custom_ids)
    actual_check_ids = set(checks)
    if not checks:
        errors.append("Ledger checks must not be empty")
    missing_checks = sorted(expected_check_ids - actual_check_ids)
    extra_checks = sorted(actual_check_ids - expected_check_ids)
    if missing_checks:
        errors.append(f"Ledger is missing required checks: {', '.join(missing_checks)}")
    if extra_checks:
        errors.append(f"Ledger contains undeclared checks: {', '.join(extra_checks)}")
    for key, value in checks.items():
        if not isinstance(value, dict):
            errors.append(f"{key}: check record is not an object")
            continue
        expected_record_fields = {
            "id",
            "group",
            "label",
            "sources",
            "status",
            "evidence",
            "updated_at",
        }
        if set(value) != expected_record_fields:
            errors.append(f"{key}: record fields do not match the schema")
            continue
        if value.get("id") != key:
            errors.append(f"{key}: record id does not match key")
        if key in CHECKS:
            if (
                value.get("group") != CHECKS[key]["group"]
                or value.get("label") != CHECKS[key]["label"]
            ):
                errors.append(f"{key}: built-in group or label was modified")
            if value.get("sources") != expected_sources.get(key):
                errors.append(f"{key}: sources do not match mode and capabilities")
        elif key in normalized_custom_ids:
            if not isinstance(value.get("group"), str) or not value["group"].strip():
                errors.append(f"{key}: custom group must not be empty")
            if not isinstance(value.get("label"), str) or not value["label"].strip():
                errors.append(f"{key}: custom label must not be empty")
            if value.get("sources") != ["custom"]:
                errors.append(f"{key}: custom sources must equal ['custom']")
        status = value.get("status")
        if status not in VALID_STATUSES:
            errors.append(f"{key}: invalid status {status!r}")
        else:
            if status == "na" and key in CHECKS and key not in NA_ALLOWED_IDS:
                errors.append(f"{key}: this invariant cannot be marked not applicable")
            if status == "na" and key in normalized_custom_ids:
                errors.append(
                    f"{key}: a custom requirement cannot be marked not applicable"
                )
            errors.extend(validate_evidence(key, status, value.get("evidence")))
            evidence = value.get("evidence")
            if (
                status == "pass"
                and key in PASS_KIND_REQUIREMENTS
                and isinstance(evidence, dict)
                and evidence.get("kind") not in PASS_KIND_REQUIREMENTS[key]
            ):
                allowed = ", ".join(sorted(PASS_KIND_REQUIREMENTS[key]))
                errors.append(f"{key}: pass evidence kind must be one of {allowed}")
            if status == "pending" and value.get("updated_at") is not None:
                errors.append(f"{key}: pending check must not have an update time")
            if status != "pending" and not timestamp_is_valid(value.get("updated_at")):
                errors.append(f"{key}: resolved check requires a valid update time")
            if status != "pending":
                timestamp_error = validate_timestamp_bounds(
                    key, value.get("updated_at"), created_at, updated_at
                )
                if timestamp_error:
                    errors.append(timestamp_error)
    validate_classification_review(payload, errors)
    review = payload.get("classification_review")
    c09 = checks.get("C09")
    if isinstance(review, dict) and isinstance(c09, dict):
        if review.get("status") == "pending" and c09.get("status") != "pending":
            errors.append(
                "C09 can only be resolved by applying a complete classification review"
            )
        if review.get("status") == "pending":
            prematurely_resolved = sorted(
                check_id
                for check_id, record in checks.items()
                if isinstance(record, dict) and record.get("status") != "pending"
            )
            if prematurely_resolved:
                errors.append(
                    "Checks cannot be resolved before classification review: "
                    + ", ".join(prematurely_resolved)
                )
        if review.get("status") == "pass":
            if c09.get("status") != "pass" or c09.get("evidence") != review.get(
                "confirmation"
            ):
                errors.append("C09 must match the applied classification confirmation")
            surfaces = review.get("surfaces")
            decisions = review.get("capabilities")
            if isinstance(surfaces, list) and isinstance(decisions, dict):
                surface_ids = {
                    surface.get("id")
                    for surface in surfaces
                    if isinstance(surface, dict) and isinstance(surface.get("id"), str)
                }
                for check_id, record in checks.items():
                    if (
                        not isinstance(record, dict)
                        or record.get("status") == "pending"
                    ):
                        continue
                    evidence = record.get("evidence")
                    if (
                        not isinstance(evidence, dict)
                        or not isinstance(evidence.get("scope_ids"), list)
                        or not all(
                            isinstance(scope, str) for scope in evidence["scope_ids"]
                        )
                    ):
                        continue
                    evidence_scopes = set(evidence["scope_ids"])
                    if not evidence_scopes.issubset(surface_ids):
                        errors.append(
                            f"{check_id}: evidence references an unknown surface"
                        )
                    for source in record.get("sources", []):
                        if not isinstance(source, str) or not source.startswith(
                            "capability:"
                        ):
                            continue
                        capability = source.removeprefix("capability:")
                        decision = decisions.get(capability)
                        if (
                            not isinstance(decision, dict)
                            or not isinstance(decision.get("scopes"), list)
                            or not all(
                                isinstance(scope, str) for scope in decision["scopes"]
                            )
                        ):
                            continue
                        missing_scopes = sorted(
                            set(decision["scopes"]) - evidence_scopes
                        )
                        if missing_scopes:
                            errors.append(
                                f"{check_id}: evidence omits {capability} surfaces: "
                                + ", ".join(missing_scopes)
                            )
            if review.get("status") == "pass":
                timestamp_items: list[tuple[str, Any]] = [
                    ("classification_review", review.get("updated_at")),
                ]
                review_surfaces = review.get("surfaces")
                for surface in (
                    review_surfaces if isinstance(review_surfaces, list) else []
                ):
                    if isinstance(surface, dict):
                        timestamp_items.append(
                            (
                                f"classification_review surface {surface.get('id')}",
                                surface.get("updated_at"),
                            )
                        )
                review_capabilities = review.get("capabilities")
                for capability, decision in (
                    review_capabilities.items()
                    if isinstance(review_capabilities, dict)
                    else []
                ):
                    if isinstance(decision, dict):
                        timestamp_items.append(
                            (
                                f"classification_review {capability}",
                                decision.get("updated_at"),
                            )
                        )
                disposition = review.get("inference_disposition")
                if isinstance(disposition, dict):
                    timestamp_items.append(
                        ("inference_disposition", disposition.get("updated_at"))
                    )
                for subject, value in timestamp_items:
                    timestamp_error = validate_timestamp_bounds(
                        subject, value, created_at, updated_at
                    )
                    if timestamp_error:
                        errors.append(timestamp_error)
    return errors


def require_valid_ledger(payload: dict[str, Any]) -> None:
    errors = validate_ledger(payload)
    if errors:
        raise ValueError("Ledger validation failed: " + "; ".join(errors))


def command_infer(args: argparse.Namespace) -> int:
    result = infer_repository(Path(args.root))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def command_init(args: argparse.Namespace) -> int:
    classification: dict[str, Any] | None = None
    if args.root:
        classification = infer_repository(Path(args.root))
    accept_inferred = bool(getattr(args, "accept_inferred", False))
    if args.archetype and accept_inferred:
        raise ValueError("Use either --archetype or --accept-inferred, not both")
    if classification is None and not args.archetype:
        raise ValueError("Specify --archetype when no repository root is inspected")
    if classification is not None and not args.archetype:
        if not accept_inferred:
            raise ValueError(
                "Inference is advisory. Review it, then provide --archetype, or use "
                "--accept-inferred only when automatic_selection_allowed is true"
            )
        if not classification["automatic_selection_allowed"]:
            raise ValueError(
                "The inferred classification is not safe to accept automatically; "
                "inspect direct evidence and provide --archetype"
            )
    archetype = args.archetype or classification["selected_archetype"]
    capabilities = set(ARCHETYPE_DEFAULTS[archetype])
    if classification is not None:
        capabilities.update(classification["selected_capabilities"])
    capabilities.update(args.capability)
    unknown = sorted(
        capability for capability in capabilities if capability not in CAPABILITY_GROUPS
    )
    if unknown:
        raise ValueError(f"Unknown capabilities: {', '.join(unknown)}")
    ledger = build_ledger(args.mode, archetype, sorted(capabilities), classification)
    write_json(Path(args.output), ledger, overwrite=args.force)
    print(f"Created ledger: {Path(args.output).resolve()}")
    print(f"Mode: {args.mode}")
    print(f"Archetype: {archetype}")
    print(f"Capabilities: {', '.join(sorted(capabilities)) or 'none'}")
    print(f"Checks: {len(ledger['checks'])}")
    print(
        "Classification review: pending; create and apply the review file before recording C09."
    )
    return 0


def command_add(args: argparse.Namespace) -> int:
    path = Path(args.ledger)
    payload = load_ledger(path)
    require_valid_ledger(payload)
    check_id = args.id.strip().upper()
    if not re.fullmatch(r"[A-Z][A-Z0-9_-]{2,31}", check_id):
        raise ValueError(
            "Custom check id must be 3 to 32 uppercase letters, digits, underscores, or hyphens"
        )
    if check_id in payload["checks"]:
        raise ValueError(f"Check already exists: {check_id}")
    if check_id in CHECKS:
        raise ValueError(f"Custom check id collides with a built-in check: {check_id}")
    label = args.label.strip()
    group = args.group.strip()
    if not label or not group:
        raise ValueError("Custom check label and group must not be empty")
    payload["checks"][check_id] = {
        "id": check_id,
        "group": group,
        "label": label,
        "sources": ["custom"],
        "status": "pending",
        "evidence": empty_evidence(),
        "updated_at": None,
    }
    payload["custom_check_ids"] = sorted([*payload["custom_check_ids"], check_id])
    payload["updated_at"] = utc_now()
    require_valid_ledger(payload)
    write_json(path, payload)
    print(f"Added {check_id}: {label}")
    return 0


def command_record(args: argparse.Namespace) -> int:
    path = Path(args.ledger)
    payload = load_ledger(path)
    require_valid_ledger(payload)
    if payload["classification_review"]["status"] != "pass":
        raise ValueError(
            "Apply a complete classification review before recording check results"
        )
    check_id = args.id.strip().upper()
    if check_id not in payload["checks"]:
        raise ValueError(f"Unknown check id: {check_id}")
    if check_id == "C09":
        raise ValueError(
            "C09 can only be resolved by applying a complete classification review"
        )
    if args.status == "pending":
        if (
            args.kind
            or args.target
            or args.observed
            or args.capability_unavailable is not None
            or getattr(args, "scope", [])
        ):
            raise ValueError("Pending status does not accept evidence fields")
        evidence = empty_evidence()
        updated_at = None
    else:
        if (
            not args.kind
            or not args.target
            or not args.observed
            or args.capability_unavailable is None
        ):
            raise ValueError(
                "Resolved status requires --kind, --target, --observed, and --capability-unavailable"
            )
        evidence = {
            "kind": args.kind,
            "target": args.target.strip(),
            "observed": args.observed.strip(),
            "capability_unavailable": args.capability_unavailable == "yes",
            "scope_ids": sorted(set(getattr(args, "scope", []))),
        }
        evidence_errors = validate_evidence(check_id, args.status, evidence)
        if evidence_errors:
            raise ValueError("; ".join(evidence_errors))
        updated_at = utc_now()
    record = payload["checks"][check_id]
    record["status"] = args.status
    record["evidence"] = evidence
    record["updated_at"] = updated_at
    payload["updated_at"] = utc_now()
    require_valid_ledger(payload)
    write_json(path, payload)
    print(f"Recorded {check_id} as {args.status}")
    return 0


def command_classification_template(args: argparse.Namespace) -> int:
    payload = load_ledger(Path(args.ledger))
    require_valid_ledger(payload)
    review = payload["classification_review"]
    if review["status"] == "pass":
        surfaces = [
            {key: value for key, value in surface.items() if key != "updated_at"}
            for surface in review["surfaces"]
        ]
        decisions = {
            capability: {
                key: value for key, value in decision.items() if key != "updated_at"
            }
            for capability, decision in review["capabilities"].items()
        }
        confirmation = review["confirmation"]
        inference_disposition = {
            key: value
            for key, value in review["inference_disposition"].items()
            if key != "updated_at"
        }
    else:
        surfaces = [
            {
                "id": "replace-me",
                "path": "replace-me",
                "archetype": payload["archetype"],
                "visibility": "replace-me",
                "evidence": empty_evidence(),
            }
        ]
        decisions = {
            capability: {
                "decision": "active"
                if capability in payload["capabilities"]
                else "rejected",
                "scopes": ["replace-me"],
                "evidence": empty_evidence(),
            }
            for capability in sorted(CAPABILITY_GROUPS)
        }
        confirmation = empty_evidence()
        classification = payload.get("classification")
        if classification is None:
            disposition_decision = "not-run"
        elif classification.get("selected_archetype") == payload["archetype"]:
            disposition_decision = "accepted"
        else:
            disposition_decision = "overridden"
        inference_disposition = {
            "decision": disposition_decision,
            "direct_evidence": empty_evidence(),
            "reason": empty_evidence(),
        }
    template = {
        "primary_archetype": payload["archetype"],
        "surfaces": surfaces,
        "capabilities": decisions,
        "confirmation": confirmation,
        "inference_disposition": inference_disposition,
    }
    write_json(Path(args.output), template, overwrite=args.force)
    print(f"Created classification review template: {Path(args.output).resolve()}")
    return 0


def command_apply_classification(args: argparse.Namespace) -> int:
    path = Path(args.ledger)
    payload = load_ledger(path)
    require_valid_ledger(payload)
    try:
        raw = json.loads(Path(args.review).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Classification review not found: {args.review}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Classification review is not valid JSON: {exc}") from exc
    expected_fields = {
        "primary_archetype",
        "surfaces",
        "capabilities",
        "confirmation",
        "inference_disposition",
    }
    if not isinstance(raw, dict) or set(raw) != expected_fields:
        raise ValueError(
            "Classification review fields do not match the template schema"
        )
    now = utc_now()
    raw_surfaces = raw.get("surfaces")
    surfaces: Any = raw_surfaces
    if isinstance(raw_surfaces, list):
        surfaces = []
        for surface in raw_surfaces:
            if not isinstance(surface, dict):
                surfaces.append(surface)
                continue
            normalized_surface = {**surface, "updated_at": now}
            evidence = surface.get("evidence")
            if isinstance(evidence, dict):
                normalized_surface["evidence"] = {
                    **evidence,
                    "scope_ids": [surface.get("id")],
                }
            surfaces.append(normalized_surface)
    surface_ids = (
        sorted(
            surface.get("id")
            for surface in surfaces
            if isinstance(surface, dict) and isinstance(surface.get("id"), str)
        )
        if isinstance(surfaces, list)
        else []
    )
    raw_decisions = raw.get("capabilities")
    if not isinstance(raw_decisions, dict) or set(raw_decisions) != set(
        CAPABILITY_GROUPS
    ):
        raise ValueError(
            "Classification review must decide every capability exactly once"
        )
    active_capabilities: list[str] = []
    for capability, decision in raw_decisions.items():
        if not isinstance(decision, dict) or decision.get("decision") not in {
            "active",
            "rejected",
        }:
            raise ValueError(
                f"Classification review has an invalid decision for {capability}"
            )
        if decision["decision"] == "active":
            active_capabilities.append(capability)
    active_capabilities.sort()
    decisions: Any = raw_decisions
    decisions = {}
    for capability, decision in raw_decisions.items():
        normalized_decision = {**decision, "updated_at": now}
        evidence = decision.get("evidence")
        if isinstance(evidence, dict):
            scopes = decision.get("scopes")
            normalized_decision["evidence"] = {
                **evidence,
                "scope_ids": (
                    sorted(scopes)
                    if isinstance(scopes, list)
                    and all(isinstance(scope, str) for scope in scopes)
                    else scopes
                ),
            }
        decisions[capability] = normalized_decision
    confirmation = raw.get("confirmation")
    if isinstance(confirmation, dict):
        confirmation = {**confirmation, "scope_ids": surface_ids}
    raw_disposition = raw.get("inference_disposition")
    inference_disposition: Any = raw_disposition
    if isinstance(raw_disposition, dict):
        inference_disposition = {**raw_disposition, "updated_at": now}
        direct_evidence = raw_disposition.get("direct_evidence")
        if isinstance(direct_evidence, dict):
            inference_disposition["direct_evidence"] = {
                **direct_evidence,
                "scope_ids": surface_ids,
            }
        reason = raw_disposition.get("reason")
        if isinstance(reason, dict) and raw_disposition.get("decision") != "accepted":
            inference_disposition["reason"] = {**reason, "scope_ids": surface_ids}
    review = {
        "status": "pass",
        "primary_archetype": raw.get("primary_archetype"),
        "surfaces": surfaces,
        "capabilities": decisions,
        "confirmation": confirmation,
        "inference_disposition": inference_disposition,
        "updated_at": now,
    }
    selected_sources = selected_check_sources(payload["mode"], active_capabilities)
    current_checks = payload["checks"]
    rebuilt_checks = {
        check_id: current_checks.get(check_id, check_record(check_id, sources))
        for check_id, sources in selected_sources.items()
    }
    for check_id in payload["custom_check_ids"]:
        rebuilt_checks[check_id] = current_checks[check_id]
    for check_id, sources in selected_sources.items():
        rebuilt_checks[check_id]["sources"] = sources
    payload["capabilities"] = active_capabilities
    payload["required_check_ids"] = sorted(selected_sources)
    payload["definition_fingerprint"] = definition_fingerprint(
        payload["mode"], payload["archetype"], active_capabilities, selected_sources
    )
    payload["checks"] = dict(sorted(rebuilt_checks.items()))
    payload["classification_review"] = review
    c09 = payload["checks"]["C09"]
    c09["status"] = "pass"
    c09["evidence"] = confirmation
    c09["updated_at"] = now
    payload["updated_at"] = now
    require_valid_ledger(payload)
    write_json(path, payload)
    print(f"Applied classification review: {Path(args.review).resolve()}")
    return 0


def status_counts(payload: dict[str, Any]) -> dict[str, int]:
    counts = {status: 0 for status in sorted(VALID_STATUSES)}
    checks = payload.get("checks")
    if not isinstance(checks, dict):
        return counts
    for record in checks.values():
        status = record.get("status") if isinstance(record, dict) else None
        if status in counts:
            counts[status] += 1
    return counts


def print_unresolved(payload: dict[str, Any]) -> None:
    checks = payload.get("checks")
    if not isinstance(checks, dict):
        return
    for check_id, record in sorted(checks.items()):
        if not isinstance(record, dict):
            continue
        status = record.get("status")
        if status in {"pending", "fix", "blocked"}:
            evidence = record.get("evidence")
            observed = evidence.get("observed") if isinstance(evidence, dict) else ""
            print(
                f"[{status.upper()}] {check_id} {record.get('label')}: "
                f"{observed or 'no evidence recorded'}"
            )


def command_check(args: argparse.Namespace) -> int:
    payload = load_ledger(Path(args.ledger))
    errors = validate_ledger(payload)
    if errors:
        print("Ledger validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2
    counts = status_counts(payload)
    unresolved = counts["pending"] + counts["fix"] + counts["blocked"]
    print(
        "Gate summary: "
        + ", ".join(
            f"{status}={counts[status]}"
            for status in ["pass", "na", "fix", "pending", "blocked"]
        )
    )
    if unresolved:
        print_unresolved(payload)
        return 1
    print("Gate passed with no unresolved checks.")
    return 0


def command_summary(args: argparse.Namespace) -> int:
    payload = load_ledger(Path(args.ledger))
    errors = validate_ledger(payload)
    counts = status_counts(payload)
    print(f"Mode: {payload.get('mode')}")
    print(f"Archetype: {payload.get('archetype')}")
    capabilities = payload.get("capabilities")
    capability_text = (
        ", ".join(capabilities)
        if isinstance(capabilities, list)
        and all(isinstance(item, str) for item in capabilities)
        else "<invalid>"
    )
    print(f"Capabilities: {capability_text or 'none'}")
    print("Statuses: " + ", ".join(f"{key}={value}" for key, value in counts.items()))
    if errors:
        print("Validation errors:")
        for error in errors:
            print(f"- {error}")
    print_unresolved(payload)
    return 2 if errors else 0


def command_catalog(_: argparse.Namespace) -> int:
    print("Archetypes:")
    for archetype, capabilities in ARCHETYPE_DEFAULTS.items():
        print(f"- {archetype}: {', '.join(capabilities) or 'engineering checks only'}")
    print("Capabilities:")
    for capability, check_ids in CAPABILITY_GROUPS.items():
        print(f"- {capability}: {', '.join(check_ids)}")
    print("Checks:")
    for check_id, check in sorted(CHECKS.items()):
        print(f"- {check_id} [{check['group']}]: {check['label']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="task_gate.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    infer_parser = subparsers.add_parser(
        "infer", help="Inspect a repository and suggest an archetype and capabilities"
    )
    infer_parser.add_argument("root")
    infer_parser.set_defaults(handler=command_infer)

    init_parser = subparsers.add_parser("init", help="Create a task evidence ledger")
    init_parser.add_argument("--mode", choices=sorted(MODE_IDS), required=True)
    init_parser.add_argument("--root")
    init_parser.add_argument("--archetype", choices=sorted(ARCHETYPE_DEFAULTS))
    init_parser.add_argument("--accept-inferred", action="store_true")
    init_parser.add_argument(
        "--capability", action="append", default=[], choices=sorted(CAPABILITY_GROUPS)
    )
    init_parser.add_argument("--output", required=True)
    init_parser.add_argument("--force", action="store_true")
    init_parser.set_defaults(handler=command_init)

    add_parser = subparsers.add_parser("add", help="Add a task-specific check")
    add_parser.add_argument("ledger")
    add_parser.add_argument("--id", required=True)
    add_parser.add_argument("--group", required=True)
    add_parser.add_argument("--label", required=True)
    add_parser.set_defaults(handler=command_add)

    record_parser = subparsers.add_parser("record", help="Record one check result")
    record_parser.add_argument("ledger")
    record_parser.add_argument("id")
    record_parser.add_argument("status", choices=sorted(VALID_STATUSES))
    record_parser.add_argument("--kind", choices=sorted(VALID_EVIDENCE_KINDS))
    record_parser.add_argument("--target")
    record_parser.add_argument("--observed")
    record_parser.add_argument("--capability-unavailable", choices=["yes", "no"])
    record_parser.add_argument("--scope", action="append", default=[])
    record_parser.set_defaults(handler=command_record)

    template_parser = subparsers.add_parser(
        "classification-template",
        help="Create the required route and capability review template",
    )
    template_parser.add_argument("ledger")
    template_parser.add_argument("--output", required=True)
    template_parser.add_argument("--force", action="store_true")
    template_parser.set_defaults(handler=command_classification_template)

    apply_classification_parser = subparsers.add_parser(
        "apply-classification",
        help="Validate and apply a completed route and capability review",
    )
    apply_classification_parser.add_argument("ledger")
    apply_classification_parser.add_argument("review")
    apply_classification_parser.set_defaults(handler=command_apply_classification)

    check_parser = subparsers.add_parser(
        "check", help="Fail if checks are invalid or unresolved"
    )
    check_parser.add_argument("ledger")
    check_parser.set_defaults(handler=command_check)

    summary_parser = subparsers.add_parser(
        "summary", help="Print ledger status and unresolved checks"
    )
    summary_parser.add_argument("ledger")
    summary_parser.set_defaults(handler=command_summary)

    catalog_parser = subparsers.add_parser(
        "catalog", help="List archetypes, capabilities, and check ids"
    )
    catalog_parser.set_defaults(handler=command_catalog)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.handler(args))
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"File error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
