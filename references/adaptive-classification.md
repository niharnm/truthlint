# Adaptive Product Classification

Read this file completely for website, web-app, browser-game, embedded-widget, SEO, accessibility, privacy, form, or launch work.

The goal is to assess every relevant requirement without forcing local-business or marketing features onto unrelated products. Classify the product from evidence, select applicable capability groups, add product-specific checks, and require a concrete reason for every excluded candidate. Automated inference is advisory. Only a reviewed and applied classification can satisfy the classification gate.

## Inspect before classifying

Inspect, when available:

- Route definitions and which routes are public, private, indexed, disabled, or host-owned.
- Package manifests and dependencies that are actually imported.
- Components, handlers, data models, API routes, forms, and tests.
- Authentication, payments, analytics, maps, embeds, uploads, search, game engines, and content systems.
- Deployment configuration and the repository's ownership of domains, headers, error pages, and source maps.
- Rendered behavior, browser console, network requests, storage, cookies, and response metadata.
- Approved business facts, content records, policies, images, reviews, and external account access.

When bundled inference is available, inspect its `scan_complete`, `scan_truncated`, and `surface_candidates` values before using any suggestion. Surface candidates are advisory, not declared surfaces. A truncated or incomplete scan requires further inspection. An unused manifest dependency, documentation example, fixture, mock, or test-only file is weak evidence and cannot activate a capability by itself. A ledger file is not product evidence and must be excluded from classification.

Classify each route or surface separately, then aggregate. A single product can contain a public marketing shell, a private dashboard, a game, a store, documentation, and a community. Apply each capability only to matching routes.

## Signal strength

| Confidence | Evidence |
| --- | --- |
| High | Reachable route or runtime behavior plus implementation or data evidence |
| Medium | Direct implementation evidence exists, but runtime behavior or business facts are unconfirmed |
| Low | Only copy, a filename, an unused dependency, a comment, a task marker, a mock, or starter-template content suggests it |
| Contradicted | Strong evidence shows the feature is absent, private, disabled, mocked, test-only, unused, or owned by the host platform |
| Unknown | The relevant route, deployment, integration, account, or data source could not be inspected |

Use high-confidence signals to activate a capability. Use medium-confidence signals to inspect further, but never invent policy text, business facts, schema values, tracking, or persistent-data changes. Low-confidence signals do not activate mandatory work. Ask one targeted question only when the unresolved choice would materially change the requested result or create risk.

Unknown is not a pass. If the missing evidence is required for the task, mark the item `blocked`. If it is outside scope, record a precise `na` reason.

## Archetypes

| Archetype | Strong signals | Default capability groups | Exclude unless separately detected |
| --- | --- | --- | --- |
| `non-web` | No browser surface or public web routes | Engineering mode checks only | All site checks |
| `web-app` | Browser routes and application state without a clearer type | `web-core` | Marketing, local, commerce, content quotas |
| `marketing` | Public product or service copy with a primary conversion action | `web-core`, `public-discovery`, `marketing`, `forms`, `tracking`, `social` | Local presence, commerce, account rules |
| `local-business` | Verified address or service area, hours, phone, location pages, appointment or quote flow | Marketing groups plus `local-presence`, `media-proof`, `service-content` | Commerce unless transactions exist |
| `professional-services` | Service pages, lead generation, portfolio, client proof | Marketing groups plus `media-proof`, `service-content` | Physical-location checks unless clients visit or a service area is declared |
| `ecommerce` | Products, cart, checkout, subscription, booking, paid download, or payment provider | `web-core`, `public-discovery`, `marketing`, `commerce`, `forms`, `auth`, `tracking`, `social`, `media-proof` | Local presence unless verified |
| `saas` | Public product shell plus signup, pricing, account, dashboard, billing, or documentation | `web-core`, `public-discovery`, `marketing`, `forms`, `auth`, `tracking`, `social` | Public SEO on private application routes; local presence |
| `internal-tool` | Login guard, staff or admin routes, private data, intentional `noindex` | `web-core`, `forms`, `auth`, `private-app` | Sitemap, social cards, public metadata, blog, local-business content |
| `publisher` | Articles, posts, categories, feeds, or a content system | `web-core`, `public-discovery`, `content`, `tracking`, `social`, `search` | Lead-generation and local-business checks without evidence |
| `docs` | Documentation framework, large reference corpus, code examples | `web-core`, `public-discovery`, `documentation`, `search` | Reviews, local schema, response promises |
| `portfolio` | Project pages, image collections, work samples, resume or profile content | `web-core`, `public-discovery`, `marketing`, `media-proof`, `social` | Comparison claims or client metrics without sources |
| `community` | Accounts, posts, comments, profiles, moderation, or uploads | `web-core`, `public-discovery`, `auth`, `forms`, `community`, `tracking`, `social` | Local-business proof and static content quotas |
| `game` | Canvas or WebGL, game loop, scene or level code, input mapping, audio, or save state | `web-core`, `game` | Maps, hours, tap-to-call, service pages, lead promises, case studies, business reviews, breadcrumbs inside gameplay, sticky sales actions |
| `microsite` | One public page with no route hierarchy or data collection | `web-core`, `public-discovery` | Breadcrumbs, search, forms, policies, and host-owned 404 behavior without evidence |
| `embedded-widget` | UI mounted inside another product, iframe, or host page | `web-core`, `embedded` | Domain, sitemap, global navigation, site-wide metadata, host-owned error pages |

A public shell around a game is classified separately. Apply public-discovery, commerce, account, support, or community checks to the matching shell routes, not automatically to the playable route.

## Capability activation

The classifier can suggest these groups, but repository and runtime evidence decide:

- `web-core`: in-scope accessibility, responsive behavior, truthful content, rendered-source correctness, error-free interactions, data minimization, and direct evidence.
- `public-discovery`: public metadata, headings, canonical URLs, link integrity, crawler files, structured data, social cards, favicon, domain, production output, and search-console ownership when launch operations are in scope.
- `marketing`: specific hero copy, visible action, restrained motion, non-generic visual choices, real proof, and conversion behavior.
- `local-presence`: verified location, service area, directions, phone, hours, email, and local structured data.
- `service-content`: service pages, approved FAQs, about story, case studies, blog content, and response commitments when factual source material exists.
- `media-proof`: real photos, verified reviews, approved comparisons, and truthful case-study assets.
- `forms`: keyboard use, labels, validation, success, failure, consent, repeat submission, and thank-you behavior when it adds value.
- `auth`: password controls, session behavior, permissions, private data, account errors, and destructive-action confirmation.
- `commerce`: pricing and purchase clarity, payment failures, receipts, cancellation, refund terms, and transaction consent.
- `tracking`: actual network and storage inventory, consent, campaign attribution, third-party embeds, and disclosures.
- `data-legal`: privacy, terms, refunds, cookies, consent, data collection, third-party processing, and verified policy revision dates when those duties apply.
- `content`: hierarchy, internal links, dates, search, print, copy actions, and long-page aids when useful.
- `documentation`: reference navigation, search, code-copy behavior, print output, last-updated facts, and version correctness.
- `social`: sharing metadata and working approved social profiles.
- `search`: a working search surface for a corpus large enough to justify it.
- `private-app`: authorization boundaries, state handling, data loss, validation, and safe committing actions.
- `community`: reporting, moderation, uploads, profile privacy, abuse states, and account controls.
- `game`: core loop, supported inputs, focus, pause and resume, save state, asset loading, audio controls, viewport, motion or flashing safety, and runtime faults.
- `embedded`: focus containment, resize behavior, loading and failure states, message origins, and host integration.

Add task-specific ledger checks for important behavior that no built-in group covers.

## False-positive controls

- Never infer product type from color, typography, framework, domain name, or one keyword.
- Treat routes and capabilities as absent when evidence shows they are disabled, mocked, unused, private, or owned by the host platform.
- Never invent reviews, metrics, testimonials, case studies, photos, addresses, hours, contact details, response promises, policy terms, consent claims, or structured-data facts.
- Require a privacy policy only when personal data, analytics, tracking, embeds, accounts, transactions, or applicable rules create a real need.
- Require cookie consent only when nonessential storage or tracking is actually used under the applicable rules. A banner without that use is not a substitute for inspection.
- Require refund or cancellation terms only for relevant transactions. Never draft business terms from guesses.
- Require terms of service when accounts, purchases, uploads, user content, licensing, or material usage rules create a real need.
- An inline success state can be correct. Do not demand a separate thank-you page when it adds no user value.
- Require breadcrumbs only when route hierarchy benefits orientation.
- Require site search only when the corpus justifies it.
- Require a sticky mobile action only for a confirmed conversion flow and only when it does not block content or controls.
- Add campaign attribution only when campaigns exist and consent rules permit it.
- Dark mode, scroll progress, back-to-top, loading animation, rich tooltips, print CSS, sticky headers, and copy buttons are capability-triggered features, not defaults.
- A skip link applies when repeated navigation precedes document content. A canvas game instead needs reliable focus entry and exit.
- Treat `llms.txt` as project-policy or request-driven unless an applicable instruction makes it mandatory.
- For production source maps, prevent public exposure of secrets or proprietary source. Private or hidden monitoring uploads can remain when approved by project policy.
- Google Search Console is an operational integration, not proof of code completeness.
- A custom domain applies only when the team owns the production deployment.
- Five FAQs and five blog posts apply only when the active content plan, explicit request, or established site standard requires that batch. Do not create filler to reach a count.
- Default visual exclusions for purple gradients, pill-shaped buttons, emoji icons, and heavy scroll motion apply to marketing surfaces. An explicit user request or established product system can override them. Fabricated proof never gets an exception.
- Never add AI attribution unless the user explicitly asks or a binding rule requires it.

## Required classification review

Record:

- `primary_archetype`, matching the reviewed ledger selection.
- One or more `surfaces`. Each surface has `id`, `path`, `archetype`, `visibility`, and structured `evidence`.
- Every known capability under `capabilities`, with an `active` or `rejected` decision, route or product `scopes`, and structured `evidence`.
- `inference_disposition`, with `decision`, `direct_evidence`, and `reason`.
- `confirmation`, set only after the full review is complete.
- Product-specific checks added separately to the ledger.

Each evidence object has `kind`, `target`, `observed`, `capability_unavailable`, and `scope_ids`. Every surface, active capability, and confirmation uses a direct kind: `browser`, `command`, `file`, `log`, `manual`, `runtime`, `source`, or `test`. A rejected capability uses `reason`. Name the route, file, behavior, or exclusion precisely. A classification review cannot use `blocker`. If required evidence is unavailable, do not apply the review. Leave the review and `C09` pending so the completion gate fails.

Each declared surface must activate the core capability set for its archetype on that surface. Do not assign an archetype while rejecting or omitting its core capabilities there.

For `inference_disposition`, use `accepted` when direct review confirms the inferred archetype and retains its selected capabilities, `overridden` when direct review changes the archetype or removes an inferred capability, and `not-run` when inference was unavailable or intentionally skipped. All decisions require `direct_evidence`. `accepted` leaves `reason` pending and empty. `overridden` and `not-run` require a concrete `reason` evidence object. An override names every removed inferred capability. Every material inferred surface candidate must be represented by a matching reviewed surface, or the override evidence must name its source or candidate ID and explain its exclusion. The apply command fills evidence `scope_ids` from the declared surfaces.

Generate the review shape with `classification-template`, complete it from inspection, then use `apply-classification`. A valid apply resolves `C09`, accepts reviewed capability changes, and rebuilds the required check set before any result can be recorded. The `infer` command and an unapplied review do not resolve it.

Reclassify if new evidence appears during implementation or browser testing.
