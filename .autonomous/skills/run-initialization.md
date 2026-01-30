# Skill: Run Initialization

**Purpose:** Create a new run folder with all required documentation files
**Trigger:** At the start of every Legacy execution loop
**Input:** Task ID (optional - if continuing previous task)
**Output:** Path to new run folder

---

## Procedure

### Step 1: Determine Run Number

```bash
# Find highest existing run number
ls runs/ | grep "run-" | sort -V | tail -1
# Next run = highest + 1
```

### Step 2: Create Run Folder

```bash
mkdir -p runs/run-NNNN
```

### Step 3: Copy Templates

Copy from `runs/run-TEMPLATE/`:
- `THOUGHTS.md` → `runs/run-NNNN/THOUGHTS.md`
- `DECISIONS.md` → `runs/run-NNNN/DECISIONS.md`
- `ASSUMPTIONS.md` → `runs/run-NNNN/ASSUMPTIONS.md`
- `LEARNINGS.md` → `runs/run-NNNN/LEARNINGS.md`

### Step 4: Initialize THOUGHTS.md

Fill in header:
- **Started:** Current timestamp
- **Task:** Task ID being worked (or "TBD" if selecting)
- **Status:** in_progress

### Step 5: Update Timeline

Append to `timeline/README.md`:
```markdown
| Time | Run | Task | Action | Status |
|------|-----|------|--------|--------|
| [HH:MM] | run-NNNN | [Task] | Started | In Progress |
```

### Step 6: Check for Review

If run number is divisible by 5:
- Trigger first principles review
- Document in `timeline/reviews/review-NNNN.md`

---

## Verification

- [ ] Run folder exists: `runs/run-NNNN/`
- [ ] All 4 template files present
- [ ] THOUGHTS.md has correct header
- [ ] Timeline updated
- [ ] Run number is sequential

---

## Example

```
Initializing run-0017...
✓ Created runs/run-0017/
✓ Copied template files
✓ Updated THOUGHTS.md header
✓ Appended to timeline
Run 0017 ready for execution
```

---

## Error Handling

**If run folder already exists:**
- Log error
- Increment number and retry
- Document collision in DECISIONS.md

**If template files missing:**
- Create minimal files
- Log assumption about template structure
- Continue with reduced documentation

