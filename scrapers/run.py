"""Run scrapers and update data/latest.json + history.

Usage: python -m scrapers.run [institution ...]
A failing scraper keeps its last good rates and is marked stale.
"""
import sys
import traceback
from dataclasses import asdict
from datetime import datetime, timezone, timedelta

from .core import store
from .core.models import validate, to_dicts
from . import registry

SL_TZ = timezone(timedelta(hours=5, minutes=30))


def run(names: list[str]) -> int:
    now = datetime.now(SL_TZ)
    latest = store.load_json(store.LATEST, {"institutions": {}})
    failures = 0
    for name in names:
        mod = registry.load(name)
        inst = mod.INSTITUTION
        prev = latest["institutions"].get(inst.id, {})
        entry = {**asdict(inst), "checked_at": now.isoformat(timespec="seconds")}
        try:
            rates = to_dicts(validate(mod.scrape()))
            entry.update(status="ok", rates=rates, last_success=entry["checked_at"], error="")
            store.append_history(now.date().isoformat(), inst.id, rates)
            print(f"ok     {inst.id}: {', '.join(f'{r['tenure_months']}m={r['nominal_pct']}' for r in rates)}")
        except Exception as e:  # keep last good data
            failures += 1
            traceback.print_exc()
            has_old = bool(prev.get("rates"))
            entry.update(
                status="stale" if has_old else "no_data",
                rates=prev.get("rates", []),
                last_success=prev.get("last_success", ""),
                error=f"{type(e).__name__}: {e}"[:300],
            )
            print(f"FAILED {inst.id}: {entry['error']}")
        latest["institutions"][inst.id] = entry
    latest["updated_at"] = now.isoformat(timespec="seconds")
    store.save_json(store.LATEST, latest)
    return failures


if __name__ == "__main__":
    names = sys.argv[1:] or registry.available()
    failed = run(names)
    print(f"{len(names) - failed}/{len(names)} scrapers succeeded")
