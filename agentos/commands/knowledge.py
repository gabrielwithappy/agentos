from __future__ import annotations

from pathlib import Path

import typer

from agentos.knowledge.schema import KnowledgeValidationError
from agentos.knowledge.search import search_documents
from agentos.knowledge.store import KnowledgeStore

app = typer.Typer(
    help="Store, publish, search, and cite project knowledge documents.",
    add_completion=False,
)


def _store(project: str | None) -> KnowledgeStore:
    return KnowledgeStore(Path(project).expanduser() if project else Path.cwd())


def _rel(store: KnowledgeStore, path: Path) -> str:
    try:
        return path.relative_to(store.root).as_posix()
    except ValueError:
        return path.as_posix()


def _handle_error(exc: Exception) -> None:
    typer.echo(str(exc), err=True)
    raise typer.Exit(2)


@app.command("inbox")
def inbox(project: str | None = typer.Option(None, "--project", help="Project root.")) -> None:
    """List draft documents waiting for review."""
    store = _store(project)
    try:
        documents = store.inbox_documents()
    except KnowledgeValidationError as exc:
        _handle_error(exc)
    if not documents:
        typer.echo("No inbox drafts found. Next: add Markdown drafts under docs/knowledge/inbox/.")
        return
    for document in documents:
        typer.echo(f"{_rel(store, document.path)} | {document.metadata.title} | {', '.join(document.metadata.tags)}")


@app.command("publish")
def publish(
    draft: str = typer.Argument(..., help="Draft markdown path under docs/knowledge/inbox."),
    category: str | None = typer.Option(None, "--category", help="Publish category: references, topics, or decisions."),
    project: str | None = typer.Option(None, "--project", help="Project root."),
) -> None:
    """Publish an inbox draft into an approved knowledge category."""
    store = _store(project)
    try:
        target = store.publish(draft, category=category)
    except KnowledgeValidationError as exc:
        _handle_error(exc)
    typer.echo(f"Published {_rel(store, target)}")


@app.command("update")
def update(
    doc: str = typer.Argument(..., help="Published knowledge markdown path."),
    summary: str | None = typer.Option(None, "--summary", help="Replace summary metadata."),
    text: str | None = typer.Option(None, "--text", help="Append body text."),
    project: str | None = typer.Option(None, "--project", help="Project root."),
) -> None:
    """Update summary metadata or append reviewed text."""
    store = _store(project)
    try:
        path = store.update(doc, summary=summary, body_append=text)
    except KnowledgeValidationError as exc:
        _handle_error(exc)
    typer.echo(f"Updated {_rel(store, path)}")


@app.command("deprecate")
def deprecate(
    doc: str = typer.Argument(..., help="Knowledge markdown path."),
    reason: str = typer.Option(..., "--reason", help="Why this knowledge is deprecated."),
    project: str | None = typer.Option(None, "--project", help="Project root."),
) -> None:
    """Mark a knowledge document deprecated without deleting evidence."""
    store = _store(project)
    try:
        path = store.deprecate(doc, reason=reason)
    except KnowledgeValidationError as exc:
        _handle_error(exc)
    typer.echo(f"Deprecated {_rel(store, path)}")


@app.command("list")
def list_documents(
    category: str | None = typer.Option(None, "--category", help="Filter by category."),
    status: str | None = typer.Option(None, "--status", help="Filter by status."),
    include_inbox: bool = typer.Option(False, "--include-inbox", help="Include inbox drafts."),
    project: str | None = typer.Option(None, "--project", help="Project root."),
) -> None:
    """List knowledge documents."""
    store = _store(project)
    try:
        documents = store.list_documents(include_inbox=include_inbox, category=category, status=status)
    except KnowledgeValidationError as exc:
        _handle_error(exc)
    if not documents:
        typer.echo("No knowledge documents found.")
        return
    for document in documents:
        typer.echo(
            f"{_rel(store, document.path)} | {document.metadata.status} | "
            f"{document.metadata.title} | {document.metadata.summary}"
        )


@app.command("search")
def search(
    query: str = typer.Argument(..., help="Keyword query."),
    category: str | None = typer.Option(None, "--category", help="Filter by category."),
    status: str | None = typer.Option(None, "--status", help="Filter by status."),
    project: str | None = typer.Option(None, "--project", help="Project root."),
) -> None:
    """Search title, summary, tags, and body text."""
    store = _store(project)
    try:
        documents = store.list_documents(include_inbox=False)
        results = search_documents(documents, query, category=category, status=status)
    except KnowledgeValidationError as exc:
        _handle_error(exc)
    if not results:
        typer.echo("No knowledge documents matched. Next: check docs/knowledge/inbox or broaden the keyword.")
        return
    for result in results:
        document = result.document
        typer.echo(
            f"{document.metadata.title} | {_rel(store, document.path)} | "
            f"{document.metadata.status}/{document.metadata.category} | "
            f"tags: {', '.join(document.metadata.tags)} | line {result.line_number}: {result.line}"
        )


@app.command("context")
def context(
    query: str = typer.Argument(..., help="Keyword query for a short cited bundle."),
    category: str | None = typer.Option(None, "--category", help="Filter by category."),
    status: str | None = typer.Option(None, "--status", help="Filter by status."),
    project: str | None = typer.Option(None, "--project", help="Project root."),
) -> None:
    """Return a short citation bundle with path and line evidence."""
    store = _store(project)
    try:
        documents = store.list_documents(include_inbox=False)
        results = search_documents(documents, query, category=category, status=status, limit=5)
    except KnowledgeValidationError as exc:
        _handle_error(exc)
    if not results:
        typer.echo("No knowledge context matched. Next: run agentos knowledge search with a broader keyword.")
        return
    typer.echo("Citation bundle")
    for result in results:
        document = result.document
        typer.echo(f"- {document.metadata.title}: {_rel(store, document.path)} line {result.line_number}")
        typer.echo(f"  {result.line}")
