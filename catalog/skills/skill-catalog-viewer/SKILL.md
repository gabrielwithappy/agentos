---
name: skill-catalog-viewer
description: Generate a self-contained HTML page that helps users browse the AgentOS skill catalog. Use this skill whenever the user asks to list, compare, inspect, or show skill descriptions from catalog/skills/catalog.json or the repository's SKILL.md files.
---

# Skill Catalog Viewer

Create a static HTML catalog from the repository's registered skills.

## Usage

Run the bundled generator from the repository root:

```bash
python3 catalog/skills/skill-catalog-viewer/scripts/generate_html.py \
  --output /tmp/agentos-skill-catalog/index.html
```

The default catalog is `catalog/skills/catalog.json` under the repository
root. Use `--root` for a fixture or another checked-out copy, and `--catalog`
to select a catalog path relative to that root. The output is an independent
`index.html`; it does not require a web server, JavaScript package, stylesheet
package, network, or API key.

## Result

The page contains a searchable list with each registered skill's name,
summary, triggers, source path, and the safe `description` field from its
`SKILL.md` frontmatter when available. It intentionally does not copy the
arbitrary Markdown body into the generated page.

## Safety and errors

- Read only entries declared in `catalog.json` and only their `SKILL.md` files.
- Resolve every catalog and source path beneath `--root`; reject absolute paths
  and symlinks that escape the root with a non-zero exit. Stale catalog entries
  without a `SKILL.md` are reported and omitted from the page.
- Escape all values before inserting them into HTML.
- Never fetch network resources or expose environment variables, credentials,
  or arbitrary files.
- If generation fails, keep any existing output untouched and report the
  actionable path or catalog error on stderr.
