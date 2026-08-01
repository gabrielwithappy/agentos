from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from agentos.cli import app


runner = CliRunner()


def _draft(root: Path, name: str = "search-contract.md") -> Path:
    path = root / "docs" / "knowledge" / "inbox" / name
    path.parent.mkdir(parents=True)
    path.write_text(
        """---
title: Search Contract
status: draft
category: topics
source: manual
created_at: 2026-08-01
updated_at: 2026-08-01
tags:
  - knowledge
  - search
summary: Reusable keyword search rules.
citation: docs/source.md#search
---

# Search Contract

Keyword search returns path and line evidence.

## Usage

Use knowledge context before citing durable research.
""",
        encoding="utf-8",
    )
    return path


def test_search_returns_path_title_tags_and_line_evidence(tmp_path):
    draft = _draft(tmp_path)
    publish = runner.invoke(app, ["knowledge", "publish", str(draft), "--category", "topics", "--project", str(tmp_path)])
    assert publish.exit_code == 0

    result = runner.invoke(app, ["knowledge", "search", "keyword", "--project", str(tmp_path)])

    assert result.exit_code == 0
    assert "Search Contract" in result.stdout
    assert "docs/knowledge/topics/search-contract.md" in result.stdout
    assert "knowledge, search" in result.stdout
    assert "line" in result.stdout


def test_search_supports_multiple_keywords_and_filters(tmp_path):
    draft = _draft(tmp_path)
    assert runner.invoke(app, ["knowledge", "publish", str(draft), "--category", "topics", "--project", str(tmp_path)]).exit_code == 0

    ok = runner.invoke(app, ["knowledge", "search", "keyword context", "--category", "topics", "--status", "published", "--project", str(tmp_path)])
    miss = runner.invoke(app, ["knowledge", "search", "keyword", "--category", "decisions", "--project", str(tmp_path)])

    assert ok.exit_code == 0
    assert "Search Contract" in ok.stdout
    assert miss.exit_code == 0
    assert "No knowledge documents matched" in miss.stdout


def test_cli_lifecycle_and_context_bundle(tmp_path):
    draft = _draft(tmp_path)

    inbox = runner.invoke(app, ["knowledge", "inbox", "--project", str(tmp_path)])
    assert inbox.exit_code == 0
    assert "search-contract.md" in inbox.stdout

    published = runner.invoke(app, ["knowledge", "publish", str(draft), "--category", "topics", "--project", str(tmp_path)])
    assert published.exit_code == 0
    assert "Published" in published.stdout

    doc = tmp_path / "docs" / "knowledge" / "topics" / "search-contract.md"
    updated = runner.invoke(app, ["knowledge", "update", str(doc), "--summary", "Updated search summary.", "--project", str(tmp_path)])
    assert updated.exit_code == 0
    assert "Updated" in updated.stdout

    listed = runner.invoke(app, ["knowledge", "list", "--project", str(tmp_path)])
    assert listed.exit_code == 0
    assert "Updated search summary." in listed.stdout

    context = runner.invoke(app, ["knowledge", "context", "durable research", "--project", str(tmp_path)])
    assert context.exit_code == 0
    assert "Citation bundle" in context.stdout
    assert "docs/knowledge/topics/search-contract.md" in context.stdout
    assert "line" in context.stdout

    deprecated = runner.invoke(app, ["knowledge", "deprecate", str(doc), "--reason", "superseded", "--project", str(tmp_path)])
    assert deprecated.exit_code == 0
    assert "Deprecated" in deprecated.stdout
    assert "status: deprecated" in doc.read_text(encoding="utf-8")


def test_cli_errors_are_safe_for_empty_or_invalid_knowledge(tmp_path):
    empty = runner.invoke(app, ["knowledge", "search", "missing", "--project", str(tmp_path)])
    assert empty.exit_code == 0
    assert "No knowledge documents matched" in empty.stdout

    bad = tmp_path / "docs" / "knowledge" / "inbox" / "bad.md"
    bad.parent.mkdir(parents=True)
    bad.write_text("---\ntitle: Bad\n---\n\nbody", encoding="utf-8")
    result = runner.invoke(app, ["knowledge", "publish", str(bad), "--project", str(tmp_path)])
    assert result.exit_code == 2
    assert "Missing required metadata" in result.stderr


def test_cli_help_lists_expected_commands():
    result = runner.invoke(app, ["knowledge", "--help"])

    assert result.exit_code == 0
    for command in ["inbox", "publish", "update", "deprecate", "list", "search", "context"]:
        assert command in result.stdout
