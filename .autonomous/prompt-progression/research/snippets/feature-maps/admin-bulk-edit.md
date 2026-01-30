# Competitor feature map (admin bulk-edit focused, derived-query compatible)
#
# This file is shaped for `.blackbox/scripts/research/generate_oss_query_bank.py`:
# - headings MUST look like: "### 2.x ..."
# - bullets under headings become query seeds

### 2.7 Admin UX & Selection + Actions
- actions toolbar for selected rows
- row selection model (shift select, select all across pages)
- indeterminate checkbox selection
- apply changes to selected items
- apply-to-selected modal with preview
- saved views (filters + sort + search persistence)
- column filters
- datagrid filtering

### 2.8 Data Integrity, Undo & Audit
- undo redo for bulk edits
- optimistic updates with rollback
- audit log for admin actions
- change history per record

### 2.9 Query State & Search
- url query params state management
- filter state url sync
- faceted filtering
- debounced search input
