# GitHub Search Queries — Admin bulk ops (v1)
#
# Goal: find OSS primitives for admin/bulk-edit tooling:
# - selection models + action bars (“apply to selected”)
# - table filter state + saved views + URL sync
# - optimistic updates + undo/redo
# - spreadsheet-like bulk edit: clipboard paste + cell editors + validation
#
# Recommended run settings:
# - `--min-stars 100` (drop to 50 if too sparse)
# - `--no-derived-queries` (lane-only)
# - add `--exclude-regex` for portfolios/templates

## Selection models + “apply to selected” UX
- `tanstack table row selection example`
- `tanstack table select all across pages`
- `tanstack table indeterminate checkbox`
- `shift click selection react table`
- `selected rows toolbar react`
- `apply to selected modal react`
- `multi select actions toolbar react`

## Table filters + saved views + URL sync
- `"tanstack table" saved views`
- `"tanstack table" column filters hook`
- `"tanstack table" url search params`
- `persist table state localstorage react`
- `saved views filter state react`
- `admin filters url query params react`
- `search params state admin table react`

## Optimistic updates + undo/redo (admin safe edits)
- `react query optimistic update rollback`
- `tanstack query optimistic update helper`
- `optimistic updates undo redo`
- `react undo redo hook`
- `command pattern undo redo javascript`
- `mutation queue hook react`
- `queue mutations react hook`

## Spreadsheet-like bulk edit (clipboard + validation)
- `react data grid cell editor`
- `react grid clipboard copy paste`
- `clipboard paste table react`
- `spreadsheet component react editable`
- `react spreadsheet copy paste`
- `arrow key navigation grid react`
- `roving tabindex grid react`
- `data grid validation react`
- `highlight invalid cells react`

## TSV / clipboard parsing + type coercion utilities
- `excel paste tsv parser javascript`
- `tab separated clipboard parser typescript`
- `clipboard tsv parse normalize`
- `parse tab delimited text typescript`
- `zod preprocess csv`
- `zod coerce number`
- `zod coerce date`

