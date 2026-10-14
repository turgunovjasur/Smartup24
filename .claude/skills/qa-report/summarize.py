"""Allure xom natijalaridan (``*-result.json``) markdown xulosa chiqaradi.

Faqat fayllarda BOR ma'lumotni sanaydi — hech narsa taxmin qilinmaydi.
Bir test bir necha marta yozilgan bo'lsa (historyId bir xil), eng oxirgisi olinadi.

    python .claude/skills/qa-report/summarize.py [results_dir]
"""
import glob
import json
import os
import sys
from collections import Counter
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

STATUS_UZ = {
    "passed": "o'tdi",
    "failed": "yiqildi (assertion)",
    "broken": "buzildi (xato/timeout)",
    "skipped": "o'tkazildi",
    "unknown": "noma'lum",
}


def _failed_step(steps):
    """Yiqilgan eng ichki qadam nomi (``@qa_action`` qadamlari)."""
    for step in steps or []:
        if step.get("status") in ("failed", "broken"):
            return _failed_step(step.get("steps")) or step.get("name")
    return None


def _first_line(text, limit=200):
    line = (text or "").strip().splitlines()[0] if (text or "").strip() else ""
    return line[:limit]


def main():
    results_dir = sys.argv[1] if len(sys.argv) > 1 else "test-results/allure-results"
    files = glob.glob(os.path.join(results_dir, "*-result.json"))
    if not files:
        print(f"Natija topilmadi: {results_dir} ichida *-result.json yo'q.")
        return

    latest = {}
    for path in files:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError) as exc:
            print(f"O'qib bo'lmadi: {path} ({exc})")
            continue
        key = data.get("historyId") or data.get("fullName") or path
        if key not in latest or data.get("stop", 0) > latest[key].get("stop", 0):
            latest[key] = data

    tests = sorted(latest.values(), key=lambda d: d.get("start", 0))
    counts = Counter(t.get("status", "unknown") for t in tests)
    starts = [t["start"] for t in tests if t.get("start")]
    stops = [t["stop"] for t in tests if t.get("stop")]

    print(f"## Natija — {results_dir}")
    if starts and stops:
        begin = datetime.fromtimestamp(min(starts) / 1000)
        minutes = (max(stops) - min(starts)) / 60000
        print(f"Boshlangan: {begin:%Y-%m-%d %H:%M} | Davomiyligi: {minutes:.1f} daq | Jami: {len(tests)}")
    print()
    print("| Status | Soni |")
    print("|--------|------|")
    for status in ("passed", "failed", "broken", "skipped", "unknown"):
        if counts.get(status):
            print(f"| {status} — {STATUS_UZ[status]} | {counts[status]} |")

    bad = [t for t in tests if t.get("status") in ("failed", "broken")]
    if bad:
        print()
        print("### Yiqilganlar")
        print("| Test | Status | Yiqilgan qadam | Xato (1-qator) |")
        print("|------|--------|----------------|----------------|")
        for t in bad:
            details = t.get("statusDetails") or {}
            name = t.get("fullName") or t.get("name")
            step = _failed_step(t.get("steps")) or "-"
            msg = _first_line(details.get("message")).replace("|", "\\|")
            print(f"| {name} | {t['status']} | {step} | {msg} |")

    skipped = [t for t in tests if t.get("status") == "skipped"]
    if skipped:
        print()
        print("### O'tkazilganlar / xfail")
        for t in skipped:
            reason = _first_line((t.get("statusDetails") or {}).get("message"))
            print(f"- {t.get('fullName') or t.get('name')} — {reason or 'sabab yozilmagan'}")


if __name__ == "__main__":
    main()
