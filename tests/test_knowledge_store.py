from __future__ import annotations

from pathlib import Path

import pytest

from agentos.knowledge.schema import KnowledgeValidationError, parse_document
from agentos.knowledge.store import KnowledgeStore


VALID_DRAFT = """---
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
"""


def test_schema_accepts_required_metadata():
    doc = parse_document(Path("docs/knowledge/inbox/search-contract.md"), VALID_DRAFT)

    assert doc.metadata.title == "Search Contract"
    assert doc.metadata.status == "draft"
    assert doc.metadata.category == "topics"
    assert doc.metadata.tags == ["knowledge", "search"]
    assert doc.body.startswith("# Search Contract")


@pytest.mark.parametrize(
    "field",
    ["title", "status", "category", "source", "created_at", "updated_at", "summary", "citation"],
)
def test_schema_rejects_missing_required_metadata(field: str):
    text = VALID_DRAFT.replace(f"{field}: ", f"missing_{field}: ", 1)

    with pytest.raises(KnowledgeValidationError, match=field):
        parse_document(Path("draft.md"), text)


def test_schema_rejects_invalid_status_and_category():
    with pytest.raises(KnowledgeValidationError, match="status"):
        parse_document(Path("draft.md"), VALID_DRAFT.replace("status: draft", "status: queued"))

    with pytest.raises(KnowledgeValidationError, match="category"):
        parse_document(Path("draft.md"), VALID_DRAFT.replace("category: topics", "category: inbox"))


def test_lifecycle_publishes_and_deprecates_draft(tmp_path):
    root = tmp_path
    draft = root / "docs" / "knowledge" / "inbox" / "search-contract.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(VALID_DRAFT, encoding="utf-8")
    store = KnowledgeStore(root)

    published = store.publish(draft, category="topics")

    assert published == root / "docs" / "knowledge" / "topics" / "search-contract.md"
    assert not draft.exists()
    doc = parse_document(published, published.read_text(encoding="utf-8"))
    assert doc.metadata.status == "published"
    assert doc.metadata.category == "topics"

    deprecated = store.deprecate(published, reason="superseded")
    deprecated_text = deprecated.read_text(encoding="utf-8")
    assert "status: deprecated" in deprecated_text
    assert "deprecated_reason: superseded" in deprecated_text


def test_lifecycle_rejects_path_traversal(tmp_path):
    root = tmp_path
    outside = tmp_path.parent / "outside.md"
    outside.write_text(VALID_DRAFT, encoding="utf-8")
    store = KnowledgeStore(root)

    with pytest.raises(KnowledgeValidationError, match="docs/knowledge"):
        store.publish(outside, category="topics")

    draft = root / "docs" / "knowledge" / "inbox" / "x.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(VALID_DRAFT, encoding="utf-8")
    with pytest.raises(KnowledgeValidationError, match="category"):
        store.publish(draft, category="../topics")


def test_list_documents_includes_published_and_inbox(tmp_path):
    root = tmp_path
    inbox = root / "docs" / "knowledge" / "inbox" / "draft.md"
    topic = root / "docs" / "knowledge" / "topics" / "published.md"
    inbox.parent.mkdir(parents=True)
    topic.parent.mkdir(parents=True)
    inbox.write_text(VALID_DRAFT, encoding="utf-8")
    topic.write_text(
        VALID_DRAFT.replace("status: draft", "status: published").replace("title: Search Contract", "title: Published"),
        encoding="utf-8",
    )

    docs = KnowledgeStore(root).list_documents(include_inbox=True)

    assert [doc.path.name for doc in docs] == ["draft.md", "published.md"]
