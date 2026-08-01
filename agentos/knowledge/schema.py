from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


ALLOWED_CATEGORIES = {"references", "topics", "decisions"}
ALLOWED_STATUSES = {"draft", "published", "deprecated"}
REQUIRED_FIELDS = (
    "title",
    "status",
    "category",
    "source",
    "created_at",
    "updated_at",
    "tags",
    "summary",
    "citation",
)


class KnowledgeValidationError(ValueError):
    pass


@dataclass(frozen=True)
class KnowledgeMetadata:
    title: str
    status: str
    category: str
    source: str
    created_at: str
    updated_at: str
    tags: list[str]
    summary: str
    citation: str
    extra: dict[str, Any]


@dataclass(frozen=True)
class KnowledgeDocument:
    path: Path
    metadata: KnowledgeMetadata
    body: str
    raw: str


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        raise KnowledgeValidationError("Knowledge documents must start with YAML-style frontmatter.")
    try:
        _, frontmatter, body = text.split("---", 2)
    except ValueError as exc:
        raise KnowledgeValidationError("Knowledge document frontmatter must be closed with ---") from exc
    return _parse_frontmatter(frontmatter.strip("\n")), body.lstrip("\n")


def render_frontmatter(metadata: dict[str, Any], body: str) -> str:
    lines = ["---"]
    for key, value in metadata.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append("")
    lines.append(body.lstrip("\n"))
    return "\n".join(lines)


def parse_document(path: Path, text: str) -> KnowledgeDocument:
    data, body = split_frontmatter(text)
    missing = [field for field in REQUIRED_FIELDS if field not in data or data[field] in ("", [])]
    if missing:
        raise KnowledgeValidationError(f"Missing required metadata: {', '.join(missing)}")

    status = str(data["status"])
    category = str(data["category"])
    if status not in ALLOWED_STATUSES:
        raise KnowledgeValidationError(f"Invalid status: {status}. Allowed: {', '.join(sorted(ALLOWED_STATUSES))}")
    if category not in ALLOWED_CATEGORIES:
        raise KnowledgeValidationError(f"Invalid category: {category}. Allowed: {', '.join(sorted(ALLOWED_CATEGORIES))}")

    tags = data["tags"]
    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
    if not isinstance(tags, list) or not all(isinstance(tag, str) and tag.strip() for tag in tags):
        raise KnowledgeValidationError("Invalid tags: provide at least one tag string.")

    known = set(REQUIRED_FIELDS)
    extra = {key: value for key, value in data.items() if key not in known}
    metadata = KnowledgeMetadata(
        title=str(data["title"]),
        status=status,
        category=category,
        source=str(data["source"]),
        created_at=str(data["created_at"]),
        updated_at=str(data["updated_at"]),
        tags=[str(tag).strip() for tag in tags],
        summary=str(data["summary"]),
        citation=str(data["citation"]),
        extra=extra,
    )
    return KnowledgeDocument(path=path, metadata=metadata, body=body, raw=text)


def document_metadata_dict(document: KnowledgeDocument) -> dict[str, Any]:
    metadata = {
        "title": document.metadata.title,
        "status": document.metadata.status,
        "category": document.metadata.category,
        "source": document.metadata.source,
        "created_at": document.metadata.created_at,
        "updated_at": document.metadata.updated_at,
        "tags": document.metadata.tags,
        "summary": document.metadata.summary,
        "citation": document.metadata.citation,
    }
    metadata.update(document.metadata.extra)
    return metadata


def _parse_frontmatter(frontmatter: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_list_key: str | None = None
    for raw_line in frontmatter.splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if current_list_key and line.startswith("  - "):
            data[current_list_key].append(line[4:].strip())
            continue
        current_list_key = None
        if ":" not in line:
            raise KnowledgeValidationError(f"Invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise KnowledgeValidationError("Invalid frontmatter key.")
        if value == "":
            data[key] = []
            current_list_key = key
        else:
            data[key] = value.strip("'\"")
    return data
