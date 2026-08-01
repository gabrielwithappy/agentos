from __future__ import annotations

from dataclasses import dataclass

from agentos.knowledge.schema import KnowledgeDocument


@dataclass(frozen=True)
class SearchResult:
    document: KnowledgeDocument
    line_number: int
    line: str


def search_documents(
    documents: list[KnowledgeDocument],
    query: str,
    *,
    category: str | None = None,
    status: str | None = None,
    limit: int = 10,
) -> list[SearchResult]:
    terms = [term.casefold() for term in query.split() if term.strip()]
    if not terms:
        return []
    results: list[SearchResult] = []
    for document in documents:
        if category and document.metadata.category != category:
            continue
        if status and document.metadata.status != status:
            continue
        haystack = "\n".join(
            [
                document.metadata.title,
                document.metadata.summary,
                " ".join(document.metadata.tags),
                document.body,
            ]
        ).casefold()
        if not all(term in haystack for term in terms):
            continue
        line_number, line = _best_line(document, terms)
        results.append(SearchResult(document=document, line_number=line_number, line=line))
        if len(results) >= limit:
            break
    return results


def _best_line(document: KnowledgeDocument, terms: list[str]) -> tuple[int, str]:
    body_lines = document.body.splitlines()
    for index, line in enumerate(body_lines, start=1):
        folded = line.casefold()
        if any(term in folded for term in terms):
            return index, line.strip()
    return 1, document.metadata.summary
