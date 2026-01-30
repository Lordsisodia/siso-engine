# GitHub Search Queries — Returns-only (v2, topic-qualified)
#
# Goal: focus on RMA/returns/store-credit primitives with less noise.
# Strategy: prefer `topic:` and explicit returns vocabulary; avoid generic "script"/"agreement"/"whitepaper" patterns.

## Topic-qualified returns/RMA (best signal when present)
- `topic:rma topic:ecommerce`
- `topic:returns topic:ecommerce`
- `topic:reverse-logistics topic:ecommerce`
- `topic:return-portal topic:ecommerce`

## Shopify returns apps / portals (narrower)
- `"return portal" "shopify app"`
- `"returns" "shopify app" "store credit"`
- `"exchange" "shopify app" "store credit"`

## Store credit primitives
- `"store credit" "returns" ecommerce`
- `"store credit" refund exchange`

## RMA workflow primitives
- `"rma" "return reason" taxonomy`
- `"return request" "rma number"`
- `"return received" inspection restock`

