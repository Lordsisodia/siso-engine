# GitHub Search Queries — Returns / RMA (v3, low-stars, less topic strict)
#
# Goal: find OSS implementations of returns/RMA/store credit flows.
# Strategy: accept a lower star floor (returns OSS tends to be niche), but keep queries
# “implementation-shaped” to avoid generic programming "return" hits.
#
# Recommended run settings:
# - `--min-stars 5` (or 25 if you’re getting too much noise)
# - `--include-archived` (returns repos are often abandoned)
# - `--no-derived-queries` (lane-only)
# - use a strict `--exclude-regex` for coursework/portfolios/templates

## Topic signals (no topic:ecommerce; too strict in practice)

# Topic-list style: expands into `topic:<token>` queries automatically.
- `return-portal`, `returns-portal`, `reverse-logistics`, `return-label`

## Shopify-centric (apps/portals/label + store credit vocabulary)

- `"return portal" shopify`
- `"returns portal" shopify`
- `"return label" shopify`
- `"exchange" shopify "store credit"`
- `"store credit" shopify returns`

## Cross-platform e-commerce primitives (RMA lifecycle vocabulary)

- `"return portal" ecommerce`
- `"returns management" ecommerce`
- `"reverse logistics" ecommerce`
- `"store credit" returns ecommerce`
- `"return label" ecommerce`
- `"return merchandise authorization" ecommerce`
- `"rma" ecommerce returns`

## Other ecosystems (often where OSS returns modules exist)

- `"magento2" rma`
- `"magento 2" rma`
- `"woocommerce" returns plugin`
- `"spree" rma`
- `"solidus" store credit`
- `"saleor" returns`
