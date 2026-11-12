# CPUSH

Interactive readings, source detectives, and review activities for CPUSH, organized by unit and chapter.

**Start at [`index.html`](index.html)**, the course hub that links to every page.

## Updating the hub

After adding or renaming pages, rebuild the index:

```bash
python3 tools/build_index.py
```

The script scans every `unit-*/<chapter>/*.html` page. When you add a new unit folder, add its title and colors to `UNITS` at the top of `tools/build_index.py`.
