# Adaptive Site Readiness Catalog

Read this file completely for website, web-app, browser-game, embedded-widget, SEO, accessibility, privacy, form, or launch work. Use [adaptive-classification.md](adaptive-classification.md) to select only applicable groups and routes.

Every selected item must end as `pass`, a concrete `na`, or `blocked`. An applicable missing item is `fix` until repaired and rechecked. Every result names one or more declared surface IDs. File existence alone is not proof. Prefer rendered output, browser behavior, network evidence, response metadata, tests, or deployment evidence.

Do not fabricate legal terms, facts, proof, content, or account state. Missing approved source material or external access is a blocker when the item is required.

## Public foundation and discovery

| ID | Requirement | Apply when | Evidence and remediation |
| --- | --- | --- | --- |
| W01 | Custom 404 page | The product owns public routable pages and error handling | Request a nonexistent route; verify useful copy and navigation; add or fix the owned error page |
| W02 | Thank-you page | A form or transaction needs a distinct destination | Submit the real flow and verify destination, state, duplicate handling, and analytics; an inline success state can be a valid `na` reason |
| W03 | Unique page titles | Public indexable pages | Inspect rendered titles across routes and fix duplicates or omissions |
| W04 | Meta descriptions | Public indexable pages | Inspect rendered metadata and write route-specific factual descriptions |
| W05 | Unique headings per page | Substantive public pages | Inspect one clear primary heading and a logical heading order |
| W06 | Canonical tags | Public indexable pages | Inspect rendered canonical URLs and validate host, path, query handling, and redirects |
| W07 | Proper page sources | Every owned browser surface | Validate rendered HTML, semantics, hydration output, metadata, and framework conventions |
| W08 | Internal links | Multi-page public surfaces | Crawl or exercise links and repair broken, orphaned, duplicate, or misleading paths |
| W09 | Breadcrumbs | Hierarchical routes benefit from location context | Verify visible trail, links, current-page state, and matching structured data |
| W10 | `robots.txt` | Owned public deployment | Fetch it and confirm intentional crawler rules and sitemap reference |
| W11 | `sitemap.xml` | Owned public indexable multi-page surface | Fetch and validate canonical, indexable URLs and freshness |
| W12 | `llms.txt` | Explicit request or project policy requires it | Fetch and validate accurate, non-secret content; otherwise record a project-specific `na` |
| W13 | Structured data | Visible content has a supported schema type | Inspect rendered JSON-LD and validate every field against visible verified facts |
| W14 | Local-business schema | A verified local or service-area business | Validate identity, address or area, hours, phone, and URLs; block on missing facts |
| W15 | Social sharing and share images | Public routes are intended for sharing | Inspect Open Graph and platform tags; verify absolute image URLs, dimensions, content, and previews |
| W16 | Site favicon | Public or production-ready surface | Verify browser icon, manifest references, formats, and response status |
| W17 | Custom domain | Team-owned production launch | Verify DNS, HTTPS, redirects, canonical host, and route behavior; missing account access is `blocked` |
| W18 | Google Search Console | Team-owned public indexable production site and operational setup is in scope | Verify ownership and sitemap submission; do not treat missing access as a code failure |
| W19 | Production source maps | Production frontend | Inspect deployed assets; prevent public secret or proprietary-source exposure; use approved private uploads when project policy needs debugging maps |
| W20 | Browser console errors | Tested routes and interactions | Inspect the real browser console and fix application errors; record known third-party noise separately |
| W21 | Compressed images | Bitmap media is served | Check intrinsic size, rendered size, bytes, format, and visible quality; resize, convert, or compress as needed |
| W22 | Print stylesheet | Users reasonably print the content | Test print preview and add focused print rules; otherwise give a concrete `na` reason |

## Accessibility and interaction

| ID | Requirement | Apply when | Evidence and remediation |
| --- | --- | --- | --- |
| A01 | Accessibility | Every changed browser surface | Run relevant automated checks plus keyboard and screen-reader-oriented inspection; fix failures in scope |
| A02 | Colour contrast | Visible text, controls, focus states, and meaningful graphics | Measure against the applicable WCAG thresholds and correct design tokens or states |
| A03 | Alt text on images | Images exist | Add factual alt text to meaningful images and empty alt text to decorative images |
| A04 | Keyboard-friendly forms | Forms exist | Complete, correct, and submit each flow without a pointer; fix order, focus, labels, and announcements |
| A05 | Skip-to-content link | Repeated navigation precedes document content | Verify first-focus behavior, visible focus, target focus, and no obstruction |
| A06 | Clear button labels | Buttons exist | Replace vague names and give icon-only controls an accessible name |
| A07 | Proper icons | Icons exist | Use the established icon system; verify meaning, consistency, contrast, and accessible names where needed |
| A08 | Mobile menus | Navigation collapses on small screens | Test open, close, focus order, Escape, outside action if supported, scroll locking, resize, and route change |
| A09 | Hover states | Pointer-interactive controls exist | Add clear hover feedback and an equivalent focus indication |
| A10 | Rich tooltips | Unfamiliar controls need explanation | Prefer visible labels; when needed, verify pointer and keyboard access, dismissal, and readable content |
| A11 | Password-visibility toggle | Password fields exist | Add an accessible stateful control that preserves value, focus, and selection |
| A12 | Form success state | Forms exist | Test specific feedback, focus handling, cleared or preserved data, and repeat submission |
| A13 | Form error state and message | Forms exist | Test field, network, and server failures with specific visible and announced messages |
| A14 | Confirmation modals | A destructive or hard-to-reverse action exists | Test initial focus, focus containment, Escape, cancel, confirm, and focus restoration |
| A15 | Loading animations | Users wait for asynchronous work | Provide restrained progress feedback, prevent duplicate actions, and support reduced motion |
| A16 | Back-to-top button | Long pages make it materially useful | Test keyboard access, focus destination, and reduced motion; otherwise record `na` |
| A17 | Sticky headers | Long navigation-heavy pages benefit | Test obstruction, anchors, small screens, focus visibility, and content height |
| A18 | Sticky mobile CTA | A confirmed mobile conversion flow benefits | Test safe areas, keyboard overlap, obstruction, route state, and dismissal if applicable |
| A19 | Scroll progress bar | Long-form reading or staged content benefits | Test accuracy, resize, dynamic content, and reduced motion; otherwise record `na` |
| A20 | Copy button | Users copy code, links, addresses, or identifiers | Test success, permission failure, repeated actions, and clear feedback |
| A21 | Dark-mode toggle | Product supports themes or the request requires one | Test initial system preference, persistence, contrast, all states, and no flash |
| A22 | Scroll-motion restraint | Motion appears in the changed surface | Remove excessive motion; preserve only purposeful, interruptible behavior with reduced-motion support |
| A23 | Site search | The searchable corpus is large enough to justify it | Test relevant results, no-result and error states, keyboard use, query URLs, and indexing policy |

For a canvas game, use reliable focus entry and exit instead of assuming a document skip link is the correct control.

## Privacy, legal, consent, and data handling

| ID | Requirement | Apply when | Evidence and remediation |
| --- | --- | --- | --- |
| P01 | Privacy policy page | Personal data, analytics, tracking, embeds, accounts, transactions, or applicable rules require it | Inventory actual practices and use approved text; block rather than invent terms |
| P02 | Terms and conditions or terms-of-service page | Accounts, transactions, services, subscriptions, uploads, licensing, or usage rules create a need | Use approved terms only; never generate business commitments from guesses |
| P03 | Refund or cancellation policy | Refundable payment, booking, subscription, or purchase exists | Use verified business policy and test where users encounter it; missing terms are `blocked` |
| P04 | Cookies policy | Cookies or similar storage make it applicable | Inventory actual storage and use approved disclosures |
| P05 | Cookie consent and simple banner | Nonessential storage or tracking requires consent | Block nonessential activity before consent; test accept, reject, revoke, persistence, and accessibility |
| P06 | Tracking audit | Every browser product | Inspect source, tag managers, cookies, storage, and network requests; document verified absence when none exists |
| P07 | UTM tracking | Campaign attribution exists and consent rules permit it | Test capture, retention, disclosure, minimization, canonical URLs, and removal where no longer needed |
| P08 | Third-party embeds | External embeds exist | Check privacy, consent, security, accessibility, performance, and failure behavior |
| P09 | Form consent | A form collects personal data or marketing permission | Add purpose-specific, unbundled, unselected consent and link approved policy text |
| P10 | Collect only necessary data | Forms, accounts, analytics, tracking, uploads, or storage exist | Map each field and event to a purpose; remove collection and retention without a defined need |
| P11 | Last-updated date | Policies or time-sensitive informational pages exist | Use a verified revision date; never insert today's date as a guess |

A checklist does not prove legal compliance. Report legal review as unverified unless qualified review actually occurred.

## Trust, conversion, local business, and content

| ID | Requirement | Apply when | Evidence and remediation |
| --- | --- | --- | --- |
| B01 | Clear CTA above the fold | Conversion-focused landing route | Verify at target breakpoints and make the action specific and truthful |
| B02 | Response-time promise | Business has an approved service commitment | Display only confirmed wording and timing; otherwise mark `blocked` or `na` |
| B03 | Case-studies section | Approved case-study material supports the route goal | Use sourced work, outcomes, and permissions; never invent results |
| B04 | FAQ section with five FAQs | Explicit request, approved content plan, or established site standard calls for five useful questions | Add exactly five sourced answers; do not add filler or invent business facts |
| B05 | Real reviews and removal of fake reviews | Reviews appear or are requested | Verify provenance and permission; remove fabricated reviews without exception |
| B06 | Real photos | Authentic people, place, work, or product proof fits the route | Use approved assets; never call generated or stock imagery real |
| B07 | Maps and directions | A physical location or visitable service area matters | Verify address, route links, consent behavior, fallback, and mobile use |
| B08 | Tap-to-call number | The business accepts calls | Use a verified number and test the `tel:` link on supported devices |
| B09 | Opening hours | Physical or scheduled service has hours | Use verified standard and special hours; do not guess holiday behavior |
| B10 | Visible contact email | Email is an approved support or sales channel | Use a verified address and test the link and visible text |
| B11 | Working social links | Approved profiles exist | Verify destination, ownership, target behavior, and accessible labels |
| B12 | About page and story | Organizational context supports trust or orientation | Use factual approved content and working internal links |
| B13 | Before-and-after gallery | Approved truthful comparison assets exist | Verify consent, matching context, labels, ordering, and no misleading edits |
| B14 | Page per service | Distinct services have enough unique factual content and user or search value | Avoid thin duplicate pages; block on missing source material |
| B15 | Five blog posts | Explicit request, approved launch plan, or established content standard calls for five factual posts | Use approved topics and source material; do not invent expertise or claims |
| B16 | Working success and thank-you flow | Forms or transactions exist | Test submission, success, thank-you behavior, analytics, retries, and duplicate handling |

## Default exclusions for marketing surfaces

| ID | Requirement | Enforcement |
| --- | --- | --- |
| D01 | No default purple gradient | Do not add one unless the user or the established brand explicitly requires it |
| D02 | No vague hero text | Replace it with specific factual value, audience, and action |
| D03 | No fake reviews | Never add them and remove any found; no exception |
| D04 | No fake metrics | Never add them and remove unsupported numbers; no exception |
| D05 | No excessive scroll animation | Remove heavy or decorative motion unless explicitly required and accessible |
| D06 | No default pill-shaped buttons | Follow the established design system or an explicit request instead |
| D07 | No emoji used as interface icons | Use the established icon system unless the user explicitly requests emoji |
| D08 | No em dash or en dash characters | Rewrite generated copy and comments with permitted punctuation |
| D09 | No made-with-AI tag or assistant attribution | Never add it unless the user explicitly requests it or a binding rule requires it |

D03, D04, D08, and D09 apply to every product. D01, D02, D05, D06, and D07 apply to marketing surfaces and should not override an explicit game or product art direction.

## Game checks

| ID | Requirement | Evidence and remediation |
| --- | --- | --- |
| G01 | Core loop | Exercise start, play, success or failure, restart, and exit paths |
| G02 | Supported inputs | Test declared keyboard, pointer, touch, and controller mappings without assuming unsupported devices |
| G03 | Focus and page integration | Test focus entry and exit, browser shortcuts, scroll prevention, and accidental input capture |
| G04 | Pause, resume, and visibility | Test pause, tab switching, backgrounding, focus loss, and resumption without state corruption |
| G05 | Save, restore, and reset | Test persistence versioning, invalid state, reset, and recovery where saving exists |
| G06 | Asset loading and failure | Test slow, failed, cached, and repeated loads with actionable feedback |
| G07 | Audio controls | Test mute, volume, persistence, autoplay restrictions, and focus changes where audio exists |
| G08 | Viewport and orientation | Test supported sizes, pixel density, full-screen transitions, safe areas, and orientation behavior |
| G09 | Motion and flashing safety | Check flashing, camera motion, reduced-motion options where feasible, and readable non-game menus |
| G10 | Runtime health | Inspect frame behavior, memory growth, console errors, network failures, and cleanup across restarts |

## Private app, community, and embedded checks

| ID | Requirement | Apply when | Evidence and remediation |
| --- | --- | --- | --- |
| Q01 | Authentication state | Private or account routes exist | Test sign-in, sign-out, expiry, recovery, refresh, and protected-route behavior |
| Q02 | Authorization boundaries | Roles, tenants, ownership, or staff scopes exist | Test allowed and denied actions at server and client boundaries |
| Q03 | Loading, empty, error, and stale states | Data-backed application views exist | Exercise each state without dummy fallbacks or hidden errors |
| Q04 | Destructive and committing actions | Actions can delete, publish, charge, submit, or overwrite | Test confirmation where needed, idempotency, retry, cancellation, and recovery |
| Q05 | Data-loss prevention | Users edit meaningful state | Test navigation, refresh, conflict, draft, autosave, or warning behavior as applicable |
| Q06 | Private-route indexing | Private routes exist | Verify authentication and intentional crawler or metadata behavior |
| CMT01 | Reporting and moderation | User-generated content exists | Test reporting, blocked content, moderator actions, feedback, and abuse paths |
| CMT02 | Upload safety and errors | User uploads exist | Test type, size, malformed input, access, storage failure, and removal |
| CMT03 | Profile privacy | Public or private profiles exist | Verify defaults, audience controls, discovery, and deletion behavior |
| CMT04 | Account controls | Community accounts exist | Test block, mute, delete, export, recovery, and notification settings as applicable |
| E01 | Focus containment | Embedded widget | Test entry, exit, tab order, host focus restoration, and no keyboard trap |
| E02 | Resize and host layout | Embedded widget | Test host width, height, zoom, mobile viewport, overflow, and dynamic content |
| E03 | Loading and failure | Embedded widget | Test unavailable host data, network failure, retries, and actionable host feedback |
| E04 | Message origins | Cross-window messaging exists | Validate exact origins, payload shape, authorization, and failure handling |
| E05 | Host ownership | Host supplies domain, navigation, or metadata | Record those site-wide checks as host-owned rather than pretending the widget passed them |

## Final site report

Report selected archetypes and capabilities, then group results as:

1. Applicable items fixed and verified.
2. Applicable items still blocked, with the exact missing input or access.
3. Candidate items marked `na`, each with a route or capability reason.
4. Commands, browser checks, tests, and deployment checks actually run.

Do not claim the full site is ready when only the changed component was inspected.
