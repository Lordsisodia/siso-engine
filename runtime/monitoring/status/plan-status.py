#!/usr/bin/env python3
"""
Plan Run Status Tracker

Monitors plan/run progress:
- Decisions (target user, license policy)
- Artifact presence + size + mtime for each plan
- Memory step/compaction cadence
- Progress vs targets

No third-party dependencies.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PlanSpec:
    label: str
    plan_path: Path
    required_artifacts: tuple[str, ...]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_value(key: str, yaml_text: str) -> str | None:
    m = re.search(rf"^\s*{re.escape(key)}:\s*(.+?)\s*$", yaml_text, re.MULTILINE)
    if not m:
        return None
    raw = m.group(1).strip()
    if "#" in raw:
        raw = raw.split("#", 1)[0].strip()
    if raw.startswith('"') and raw.endswith('"') and len(raw) >= 2:
        raw = raw[1:-1]
    return raw.strip()


def fmt_dt(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.1f} MB"


def file_info(path: Path) -> tuple[str, str]:
    """Returns (size_str, mtime_str). If missing, returns ("MISSING", "")."""
    if not path.exists():
        return ("MISSING", "")
    st = path.stat()
    return (fmt_bytes(st.st_size), fmt_dt(st.st_mtime))


def count_step_files(plan_path: Path) -> int:
    steps_dir = plan_path / "context" / "steps"
    if not steps_dir.exists():
        return 0
    return len([
        p
        for p in steps_dir.iterdir()
        if p.is_file() and p.suffix == ".md" and p.name.lower() != "readme.md"
    ])


def count_compactions(plan_path: Path) -> int:
    comp_dir = plan_path / "context" / "compactions"
    if not comp_dir.exists():
        return 0
    return len([
        p
        for p in comp_dir.iterdir()
        if p.is_file() and p.suffix == ".md" and p.name.lower() != "readme.md"
    ])


def count_dir_files(dir_path: Path, *, suffix: str) -> int:
    if not dir_path.exists():
        return 0
    return len([p for p in dir_path.iterdir() if p.is_file() and p.suffix.lower() == suffix.lower()])


def pct(current: int, target: int) -> str:
    if target <= 0:
        return "n/a"
    return f"{min(100, round((current / target) * 100))}%"


def render_status(plan_path: Path) -> str:
    """Render status report for a plan."""
    plan_name = plan_path.name

    # Load config if exists
    cfg = plan_path / "artifacts" / "config.yaml"
    if cfg.exists():
        txt = read_text(cfg)
        target_user = parse_value("target_user", txt) or ""
        license_policy = parse_value("license_policy", txt) or ""
    else:
        target_user = ""
        license_policy = ""

    # Count artifacts
    artifacts_dir = plan_path / "artifacts"
    if artifacts_dir.exists():
        artifact_files = list(artifacts_dir.iterdir())
    else:
        artifact_files = []

    # Memory cadence
    steps = count_step_files(plan_path)
    compactions = count_compactions(plan_path)

    lines: list[str] = []
    lines.append(f"# Plan Status: {plan_name}")
    lines.append("")
    lines.append(f"- 📁 plan: `{plan_path}`")
    lines.append("")

    # Decisions
    if target_user or license_policy:
        lines.append("## 🎛️ Decisions")
        lines.append("")
        if target_user:
            lines.append(f"- 🎯 target: `{target_user}`")
        if license_policy:
            lines.append(f"- 📜 license: `{license_policy}`")
        lines.append("")

    # Memory
    lines.append("## 🧠 Memory")
    lines.append("")
    lines.append(f"- Context steps: `{steps}`")
    if compactions:
        lines.append(f"- Compactions: `{compactions}`")
    lines.append("")

    # Artifacts
    lines.append("## 📄 Artifacts")
    lines.append("")
    if artifact_files:
        for f in sorted(artifact_files):
            if f.is_file():
                size, mtime = file_info(f)
                lines.append(f"- ✅ `{f.name}` — {size} — {mtime}")
    else:
        lines.append("(no artifacts)")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Track plan/run progress")
    ap.add_argument("--plan", required=True, help="Path to plan directory")
    ap.add_argument("--write", action="store_true", help="Write to <plan>/artifacts/status.md")
    args = ap.parse_args()

    plan_path = Path(args.plan)
    if not plan_path.exists():
        print(f"ERROR: Plan not found: {plan_path}", file=sys.stderr)
        return 1

    report = render_status(plan_path)
    print(report)

    if args.write:
        out = plan_path / "artifacts" / "status.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report + "\n", encoding="utf-8")
        print("")
        print(f"Wrote: {out}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
