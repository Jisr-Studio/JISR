"""Opt-in live checks of public citation services; no paid APIs or user media."""
import hashlib
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


def check_sources():
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "checks": []}
    samples = [
        ("Quranpedia", lambda: server.lookup_quran(2, 222, "إن الله يحب التوابين ويحب المتطهرين"), ("arabic", "english", "translator")),
        ("HadeethEnc", lambda: server.lookup_hadith("65004", "الطهور شطر الإيمان"), ("arabic", "english", "narrator", "grade", "attribution", "explanation")),
    ]
    def dorar_sample():
        segment = {"ar": "الطهور شطر الإيمان", "en": "Draft for review", "candidate": {"hadith_query": "الطهور شطر الإيمان"}}
        if not server.verify_hadith(segment):
            raise ValueError("No complete source match returned")
        return segment["source"]
    samples.append(("Dorar", dorar_sample, ("arabic", "narrator", "grade", "attribution")))
    samples.append(("Dorar tafsir", lambda: server.lookup_tafsir(2, 222), ("explanation", "explanation_scope", "explanation_source", "surah_name")))
    samples.append(("Al-Jamhara bilingual term", lambda: server.lookup_term("الاجتهاد"), ("term", "definition_ar", "english_term", "definition_en", "english_url")))
    samples.append(("Al-Jamhara ablution term", lambda: server.lookup_term("الوضوء"), ("term", "definition_ar", "url")))
    def automatic_hadith():
        spoken = "من توضأ فأحسن الوضوء خرجت خطاياه"
        segment = {"ar": spoken, "en": "Draft for review", "candidate": {"kind": "hadith", "hadith_query": spoken}}
        if not server.verify_hadith(segment):
            raise ValueError("No Hadith match returned")
        source = segment["source"]
        if source.get("translation_status") != "sourced" or source.get("translation_lookup_status") != "matched":
            raise ValueError("No unique sourced translation returned")
        return source
    samples.append(("Automatic Dorar + HadeethEnc match", automatic_hadith, ("english", "explanation", "verification", "translation_url")))
    for name, lookup, fields in samples:
        result = {"service": name, "ok": False}
        try:
            with patch.dict(server.os.environ, {"GEMINI_API_KEY": ""}):
                source = lookup()
            missing = [field for field in fields if not source.get(field)]
            if missing:
                raise ValueError("Missing source fields: " + ", ".join(missing))
            result.update(ok=True, url=source.get("url") or source["explanation_url"], available_fields=sorted(source))
            for field in ("translation_status", "translation_lookup_status", "alignment_status"):
                if field in source:
                    result[field] = source[field]
            for field in ("arabic", "english", "explanation", "definition_ar", "definition_en"):
                if source.get(field):
                    result[field + "_sha256"] = hashlib.sha256(source[field].encode()).hexdigest()
        except Exception as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"
        report["checks"].append(result)
    report["ok"] = all(item["ok"] for item in report["checks"])
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Save the timestamped check report as JSON")
    args = parser.parse_args()
    report = check_sources()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2))
    sys.exit(0 if report["ok"] else 1)
