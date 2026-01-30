# Competitor feature map (clipboard/CSV import focused, derived-query compatible)
#
# This file is shaped for `.blackbox/scripts/research/generate_oss_query_bank.py`:
# - headings MUST look like: "### 2.x ..."
# - bullets under headings become query seeds

### 2.7 Admin UX: Import & Bulk Edit
- csv import ui with error reporting
- paste from excel to grid
- tsv clipboard parsing
- header mapping for imports
- row selection + apply-to-selected
- bulk edit preview + confirmation

### 2.8 Validation & Data Coercion
- schema validation for csv rows
- row and column error reporting
- type coercion (date number currency boolean)
- zod preprocess transform

