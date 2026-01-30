# Feature maps (derived-query seeds)

Purpose:
- Store small “competitor feature map” markdowns that are shaped to be consumed by:
  - `docs/.blackbox/scripts/research/generate_oss_query_bank.py`
- These files intentionally live in a **committed** location (not `.blackbox/.local/`) because they are reusable research inputs.

Format rules (important):
- Headings MUST look like: `### 2.x ...`
- Bullets under headings become query seeds for derived GitHub search query banks.

Where these get used:
- `docs/.blackbox/scripts/start-oss-discovery-cycle.sh` can generate a derived query bank from a feature map:
  - it calls `generate_oss_query_bank.py --feature-map <path> --out <out.md>`

Notes:
- Keep these short; treat them as “query seed packs”, not full product specs.
- If a feature map becomes a real product scope, promote it into `docs/05-planning/` as a proper planning doc.

