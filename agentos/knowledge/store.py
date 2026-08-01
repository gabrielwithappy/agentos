from __future__ import annotations

from datetime import date
from pathlib import Path

from agentos.knowledge.schema import (
    ALLOWED_CATEGORIES,
    KnowledgeDocument,
    KnowledgeValidationError,
    document_metadata_dict,
    parse_document,
    render_frontmatter,
)


class KnowledgeStore:
    def __init__(self, root: Path | str | None = None) -> None:
        self.root = Path(root or Path.cwd()).resolve()
        self.knowledge_dir = self.root / "docs" / "knowledge"

    def ensure_dirs(self) -> None:
        for name in ("inbox", "references", "topics", "decisions"):
            (self.knowledge_dir / name).mkdir(parents=True, exist_ok=True)

    def inbox_documents(self) -> list[KnowledgeDocument]:
        return self._documents_in(self.knowledge_dir / "inbox")

    def list_documents(
        self,
        *,
        include_inbox: bool = False,
        category: str | None = None,
        status: str | None = None,
    ) -> list[KnowledgeDocument]:
        folders = ["references", "topics", "decisions"]
        if include_inbox:
            folders.insert(0, "inbox")
        documents: list[KnowledgeDocument] = []
        for folder in folders:
            documents.extend(self._documents_in(self.knowledge_dir / folder))
        if category:
            documents = [doc for doc in documents if doc.metadata.category == category]
        if status:
            documents = [doc for doc in documents if doc.metadata.status == status]
        return sorted(documents, key=lambda doc: doc.path.relative_to(self.root).as_posix())

    def publish(self, draft_path: Path | str, *, category: str | None = None) -> Path:
        self.ensure_dirs()
        source = self._resolve_inside_knowledge(draft_path)
        if not self._is_relative_to(source, self.knowledge_dir / "inbox"):
            raise KnowledgeValidationError("Draft must be inside docs/knowledge/inbox before publish.")
        document = parse_document(source, source.read_text(encoding="utf-8"))
        target_category = category or document.metadata.category
        if target_category not in ALLOWED_CATEGORIES:
            raise KnowledgeValidationError(f"Invalid category: {target_category}")
        metadata = document_metadata_dict(document)
        metadata["status"] = "published"
        metadata["category"] = target_category
        metadata["updated_at"] = date.today().isoformat()
        target = self._safe_target(target_category, source.name)
        if target.exists():
            raise KnowledgeValidationError(f"Target already exists: {target.relative_to(self.root)}")
        target.write_text(render_frontmatter(metadata, document.body), encoding="utf-8")
        source.unlink()
        return target

    def update(self, doc_path: Path | str, *, summary: str | None = None, body_append: str | None = None) -> Path:
        path = self._resolve_inside_knowledge(doc_path)
        document = parse_document(path, path.read_text(encoding="utf-8"))
        metadata = document_metadata_dict(document)
        if summary:
            metadata["summary"] = summary
        metadata["updated_at"] = date.today().isoformat()
        body = document.body
        if body_append:
            body = body.rstrip() + "\n\n" + body_append.strip() + "\n"
        path.write_text(render_frontmatter(metadata, body), encoding="utf-8")
        return path

    def deprecate(self, doc_path: Path | str, *, reason: str) -> Path:
        path = self._resolve_inside_knowledge(doc_path)
        document = parse_document(path, path.read_text(encoding="utf-8"))
        metadata = document_metadata_dict(document)
        metadata["status"] = "deprecated"
        metadata["updated_at"] = date.today().isoformat()
        metadata["deprecated_reason"] = reason
        path.write_text(render_frontmatter(metadata, document.body), encoding="utf-8")
        return path

    def _documents_in(self, folder: Path) -> list[KnowledgeDocument]:
        if not folder.exists():
            return []
        documents: list[KnowledgeDocument] = []
        for path in sorted(folder.glob("*.md")):
            documents.append(parse_document(path, path.read_text(encoding="utf-8")))
        return documents

    def _safe_target(self, category: str, filename: str) -> Path:
        if category not in ALLOWED_CATEGORIES:
            raise KnowledgeValidationError(f"Invalid category: {category}")
        if Path(filename).name != filename:
            raise KnowledgeValidationError("Target filename must not contain path separators.")
        target = (self.knowledge_dir / category / filename).resolve()
        if not self._is_relative_to(target, self.knowledge_dir / category):
            raise KnowledgeValidationError("Publish target must stay inside docs/knowledge.")
        return target

    def _resolve_inside_knowledge(self, path: Path | str) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        resolved = candidate.resolve()
        if not self._is_relative_to(resolved, self.knowledge_dir):
            raise KnowledgeValidationError("Path must stay inside docs/knowledge.")
        if not resolved.is_file():
            raise KnowledgeValidationError(f"Knowledge document not found: {path}")
        return resolved

    @staticmethod
    def _is_relative_to(path: Path, parent: Path) -> bool:
        try:
            path.resolve().relative_to(parent.resolve())
            return True
        except ValueError:
            return False
