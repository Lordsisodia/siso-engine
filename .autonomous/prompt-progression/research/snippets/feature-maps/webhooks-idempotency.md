# Competitor feature map (webhooks + idempotency, derived-query compatible)
#
# Shaped for `.blackbox/scripts/research/generate_oss_query_bank.py`:
# - headings MUST look like: "### 2.x ..."
# - bullets under headings become query seeds

### 2.5 Automation & Integrations
- webhook ingestion
- webhook signature verification
- webhook retries
- webhook deduplication
- idempotency keys
- at least once processing
- dead letter queue

### 2.8 Data Integrity, Audit & Safety
- idempotent consumers
- outbox pattern
- event deduplication
- replay protection

