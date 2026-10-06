# Source checks and saved-project maintenance

Run these commands from the repository root.

Optional checks against public citation services:

```bash
python scripts/check_sources.py --output docs/source-check.json
```

This command makes network requests to public sources without sending user videos or invoking paid AI services. The [saved sample report](source-check.json) records successful checks on October 2, 2026; it does not establish corpus-wide matching accuracy.

To repair source links in saved projects:

```bash
python scripts/refresh_source_links.py          # Preview only
python scripts/refresh_source_links.py --apply  # Save resolved links
```

Link repairs preserve transcript text, translations, grades, and review decisions, and do not retranscribe or retranslate videos.
