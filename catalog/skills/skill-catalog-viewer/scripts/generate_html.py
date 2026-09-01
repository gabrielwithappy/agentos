#!/usr/bin/env python3
"""Generate a safe, self-contained HTML view of the AgentOS skill catalog."""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


class CatalogError(ValueError):
    """Raised when catalog input violates the generator contract."""


def _inside(path: Path, root: Path, label: str) -> Path:
    candidate = path.absolute().resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise CatalogError(f"{label} escapes root: {path}") from exc
    return candidate


def _frontmatter_description(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CatalogError(f"cannot read skill file {path}: {exc}") from exc
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            break
        if line.startswith("description:"):
            value = line.split(":", 1)[1].strip()
            if value in {">", "|", ">-", "|-", ">+", "|+"}:
                folded: list[str] = []
                for continuation in lines[index + 1 :]:
                    if continuation.strip() == "---":
                        break
                    folded.append(continuation.strip())
                return " ".join(part for part in folded if part)
            return value.strip("'\"")
    return ""


def _load_entries(root: Path, catalog_path: Path) -> list[dict[str, Any]]:
    if not catalog_path.is_file() or catalog_path.is_symlink():
        raise CatalogError(f"catalog is missing or not a regular file: {catalog_path}")
    try:
        data = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"invalid catalog {catalog_path}: {exc}") from exc
    entries = data.get("skills") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        raise CatalogError("catalog must contain a skills list")

    result: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            raise CatalogError("each catalog skill must have a name")
        source = entry.get("source_path")
        if not isinstance(source, str) or not source:
            raise CatalogError(f"skill {entry['name']} has no source_path")
        source_dir = _inside(root / source, root, f"source_path for {entry['name']}")
        skill_file = _inside(source_dir / "SKILL.md", root, f"SKILL.md for {entry['name']}")
        if not source_dir.is_dir() or not skill_file.is_file():
            print(f"warning: skipping {entry['name']}; SKILL.md is missing", file=sys.stderr)
            continue
        if source_dir.is_symlink() or skill_file.is_symlink():
            raise CatalogError(f"source for {entry['name']} is not a regular skill directory")
        result.append({
            "name": entry["name"],
            "summary": entry.get("summary", ""),
            "triggers": entry.get("triggers", []),
            "category": entry.get("category", "optional"),
            "source_path": source,
            "description": _frontmatter_description(skill_file),
        })
    return sorted(result, key=lambda item: item["name"].casefold())


def _text(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value) if value is not None else ""


def _render(entries: list[dict[str, Any]]) -> str:
    cards = []
    for item in entries:
        cards.append(
            '<article class="skill" data-search="{search}">'
            "<h2>{name}</h2><p class=\"summary\">{summary}</p>"
            "<p><strong>Category:</strong> {category}</p>"
            "<p><strong>Triggers:</strong> {triggers}</p>"
            "<p><strong>Source:</strong> <code>{source}</code></p>"
            "<details><summary>Description</summary><p>{description}</p></details>"
            "</article>".format(
                search=html.escape(" ".join(str(v) for v in item.values()).casefold(), quote=True),
                name=html.escape(_text(item["name"])),
                summary=html.escape(_text(item["summary"])),
                category=html.escape(_text(item["category"])),
                triggers=html.escape(_text(item["triggers"])),
                source=html.escape(_text(item["source_path"])),
                description=html.escape(_text(item["description"])),
            )
        )
    body = "\n".join(cards) or '<p id="empty">No skills found.</p>'
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>AgentOS Skill Catalog</title>
<style>
body{font:16px/1.5 system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#17202a;background:#f7f8fa}
header,.skill{background:white;border:1px solid #d9dee5;border-radius:10px;padding:1rem 1.25rem;margin:1rem 0;box-shadow:0 1px 2px #0000000d}
h1{margin-top:0} input{width:100%;box-sizing:border-box;padding:.7rem;border:1px solid #aeb7c2;border-radius:6px;font-size:1rem}
.summary{font-size:1.05rem}.skill h2{margin:.1rem 0}.skill[hidden]{display:none} code{color:#34495e}
</style></head>
<body><header><h1>AgentOS Skill Catalog</h1>
<p>Browse registered skills and their safe frontmatter descriptions.</p>
<label for="search">Search skills</label><input id="search" type="search" placeholder="name, summary, trigger..." autocomplete="off">
<p id="count"></p></header><main id="skills">""" + body + """</main>
<script>
const input=document.querySelector('#search'), cards=[...document.querySelectorAll('.skill')], count=document.querySelector('#count');
function filter(){const q=input.value.toLowerCase().trim();let n=0;for(const card of cards){const show=!q||card.dataset.search.includes(q);card.hidden=!show;if(show)n++;}count.textContent=`${n} skill${n===1?'':'s'} shown`;} input.addEventListener('input',filter);filter();
</script></body></html>
"""


def generate(root: Path, catalog: Path, output: Path) -> None:
    entries = _load_entries(root, catalog)
    output_parent = output.parent
    output_parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{output.name}.", dir=output_parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(_render(entries))
        os.replace(temporary, output)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def main() -> int:
    repo_root = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repo_root)
    parser.add_argument("--catalog", type=Path, default=Path("catalog/skills/catalog.json"))
    parser.add_argument("--output", type=Path, default=Path("index.html"))
    args = parser.parse_args()
    root = args.root.absolute().resolve()
    output = args.output if args.output.is_absolute() else Path.cwd() / args.output
    try:
        catalog = _inside(args.catalog if args.catalog.is_absolute() else root / args.catalog, root, "catalog")
        generate(root, catalog, output)
    except CatalogError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: cannot write {output}: {exc}", file=sys.stderr)
        return 2
    print(f"Generated {output} ({output.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
