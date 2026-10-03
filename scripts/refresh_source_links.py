"""Repair saved citation URLs only; no transcription or paid-model requests.

Run without --apply to preview changes. Active or concurrently edited projects
are skipped. Canonical text, translations, grades and review flags stay intact.
"""
import argparse
import copy
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


def refresh_source(source, kind):
    result = copy.deepcopy(source)
    if kind == "hadith":
        reference = result.get("verification")
        if reference and reference.get("provider") == "Dorar":
            result["verification"] = server.resolve_dorar_reference(reference, reference.get("arabic", "")[:100])
        elif "dorar.net" in server.urllib.parse.urlsplit(result.get("url", "")).netloc:
            result = server.resolve_dorar_reference(result, result.get("arabic", "")[:100])
    elif kind == "quran" and result.get("explanation_status") != "available" and result.get("explanation_url"):
        result["explanation_index_url"] = result.pop("explanation_url")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    server.initialize_db()
    with server.db() as con:
        rows = con.execute("SELECT id,status,updated,segments FROM projects").fetchall()
    changed, direct, fallback, skipped = 0, 0, 0, 0
    for row in rows:
        if row["status"] == "processing":
            skipped += 1
            continue
        segments = json.loads(row["segments"])
        before = copy.deepcopy(segments)
        for segment in segments:
            if not segment.get("source"):
                continue
            segment["source"] = refresh_source(segment["source"], segment.get("type"))
            reference = segment["source"].get("verification") or segment["source"]
            direct += reference.get("link_status") == "direct"
            fallback += reference.get("link_status") == "search_only"
        if segments == before:
            continue
        if args.apply:
            with server.LOCK, server.db() as con:
                count = con.execute("UPDATE projects SET segments=?,updated=? WHERE id=? AND updated=? AND status!='processing'",
                    (json.dumps(segments, ensure_ascii=False), time.time(), row["id"], row["updated"])).rowcount
            if not count:
                skipped += 1
                continue
        changed += 1
    print(json.dumps({"applied": args.apply, "changed_projects": changed, "direct_records": direct,
                      "search_fallbacks": fallback, "skipped_projects": skipped}))


if __name__ == "__main__":
    main()
