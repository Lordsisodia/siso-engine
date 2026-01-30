# Usage

## Create a run (recommended)

```bash
./docs/.blackbox/scripts/new-run.sh "feedback-batch-001" --owner shaun
```

This creates a run folder and sets it as active in `docs/.blackbox/.runs/ACTIVE_RUN`.

## Add feedback

Edit:

- `docs/.blackbox/.runs/<run>/inbox.md`

## Create per-issue folders (inside active run)

```bash
node docs/.blackbox/bin/blackbox.mjs new "Fix profile save button disabled" --domain ui --priority p1 --owner triage-agent
```

## Where outputs go

- Grouping output: `docs/.blackbox/.runs/<run>/grouping.md`
- Handoffs: `docs/.blackbox/.runs/<run>/handoffs/`
- Per-issue artifacts: `docs/.blackbox/.runs/<run>/issues/<issue>/`

