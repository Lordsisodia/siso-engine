# OSS Triage Rubric (quick scan)

Use this rubric when reviewing `artifacts/oss-ranked.md` and deciding what to put into:
- `.blackbox/oss-catalog/curation.json` (durable intent)
- `oss/entries/*.md` (deep notes for the top candidates)

This is intentionally lightweight: 3–10 minutes per repo.

## 1) Fit (most important)
- What platform primitive does this cover?
  - catalog, search, pricing/promotions, checkout, payments, tax, shipping, returns/RMA, OMS, WMS, PIM, CMS, auth, admin, analytics, etc.
- Does it match our stack and integration surface (API-first, webhooks, data model)?
- Is it “a library we can embed” vs “a full product we’d have to operate”?

## 2) Licensing (hard gate)
- Prefer permissive (MIT/Apache-2.0/BSD).
- Flag for review: GPL/AGPL/copyleft, “fair-code”, Commons Clause, unknown/no license.
- Treat GitHub license metadata as best-effort; verify before adoption.

## 3) Project health (risk signal)
- Recent activity: last push / releases / open PRs.
- Bus factor: how many maintainers, contributor diversity.
- Issue hygiene: response time, stale issues, roadmap clarity.

## 4) Adoption + ecosystem
- Stars and forks (weak but useful).
- Docs quality: quickstart, integration guides, examples.
- Compatibility: SDKs, APIs, data stores, supported runtimes.

## 5) Security + compliance posture (risk signal)
- Known CVEs / security policy / responsible disclosure.
- Dependency footprint (how big is the transitive tree).
- Authentication/authorization model if it handles sensitive flows.

## 6) “POC in 1–2 days” test
- What is the smallest integration slice that proves value?
- What measurable outcome indicates success?
  - e.g. “can create an order and compute shipping+tax”, “can index + query catalog”, “can run in our infra”

## Suggested curation statuses
- `triage`: looks promising, needs scan
- `deepen`: deeper evaluation planned (write notes, integration plan)
- `poc`: timeboxed POC is scoped or in progress
- `adopt`: strong candidate; integrate when ready
- `watch`: revisit later
- `reject`: explicitly not suitable

