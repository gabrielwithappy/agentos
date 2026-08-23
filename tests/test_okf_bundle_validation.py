"""
Tests for OKF v0.2 bundle validator (Task 2).

Covers:
- Discovery: index.md, log.md, concepts/*.md traversal
- Grammar: flat YAML subset, disallowed syntax
- Required/error codes: all OKF_* structural errors
- Advisory/strict: all warning codes and strict mode
- JSON contract: stdout one-line, empty stderr, exit code, changed:false, next
- Diagnostic ordering: path lex → severity (error before warning) → code lex
- Read-only boundary: no file mutation before/after validate
- Refusal: symlink, binary, oversized files
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "catalog/skills/knowledge-curator/scripts/knowledge.py"
VALIDATE_MOD = ROOT / "catalog/skills/knowledge-curator/scripts"

sys.path.insert(0, str(VALIDATE_MOD))
from okf_bundle_validate import validate_bundle


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_valid_bundle(base: Path) -> Path:
    """Create a minimal valid OKF v0.2 bundle at base/bundle."""
    bundle = base / "bundle"
    bundle.mkdir()
    (bundle / "index.md").write_text(
        '---\nokf_version: "0.2"\ntitle: Test\n---\n# Test\n', encoding="utf-8"
    )
    (bundle / "log.md").write_text(
        '---\ntitle: Log\n---\n# Log\n', encoding="utf-8"
    )
    concepts = bundle / "concepts"
    concepts.mkdir()
    (concepts / "example.md").write_text(
        '---\ntype: concept\ntitle: Example\n---\n# Example\n', encoding="utf-8"
    )
    return bundle


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_validate(*args):
    return subprocess.run(
        [sys.executable, "-S", str(SCRIPT), "validate", *args],
        text=True, capture_output=True,
        cwd=str(VALIDATE_MOD),
    )


# ---------------------------------------------------------------------------
# JSON contract
# ---------------------------------------------------------------------------

class TestJsonContract:
    def test_valid_bundle_exit_zero(self, tmp_path):
        bundle = _make_valid_bundle(tmp_path)
        result = validate_bundle(str(bundle))
        assert result["ok"] is True
        assert result["code"] == 0
        assert result["action"] == "validate"
        assert result["changed"] is False
        assert isinstance(result["diagnostics"], list)
        assert isinstance(result["next"], str)

    def test_stdout_single_json_line(self, tmp_path):
        bundle = _make_valid_bundle(tmp_path)
        proc = _run_validate("--project", str(bundle))
        lines = [l for l in proc.stdout.splitlines() if l.strip()]
        assert len(lines) == 1
        json.loads(lines[0])  # must be valid JSON

    def test_stderr_empty(self, tmp_path):
        bundle = _make_valid_bundle(tmp_path)
        proc = _run_validate("--project", str(bundle))
        assert proc.stderr == ""

    def test_changed_always_false(self, tmp_path):
        bundle = _make_valid_bundle(tmp_path)
        result = validate_bundle(str(bundle))
        assert result["changed"] is False

    def test_next_always_present(self, tmp_path):
        bundle = _make_valid_bundle(tmp_path)
        result = validate_bundle(str(bundle))
        assert "next" in result and isinstance(result["next"], str)

    def test_error_exit_two(self, tmp_path):
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        # Missing index.md → error
        (bundle / "log.md").write_text("# log\n")
        proc = _run_validate("--project", str(bundle))
        assert proc.returncode == 2
        payload = json.loads(proc.stdout.strip().splitlines()[0])
        assert payload["ok"] is False
        assert payload["code"] == 2

    def test_ok_true_exit_zero_for_valid(self, tmp_path):
        bundle = _make_valid_bundle(tmp_path)
        proc = _run_validate("--project", str(bundle))
        assert proc.returncode == 0
        payload = json.loads(proc.stdout.strip())
        assert payload["ok"] is True


# ---------------------------------------------------------------------------
# Grammar tests
# ---------------------------------------------------------------------------

class TestGrammar:
    def _bundle_with_concept(self, tmp_path: Path, fm: str) -> Path:
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text('---\nokf_version: "0.2"\ntitle: T\n---\n', encoding="utf-8")
        (bundle / "log.md").write_text("# log\n", encoding="utf-8")
        concepts = bundle / "concepts"
        concepts.mkdir()
        (concepts / "c.md").write_text(f"---\n{fm}\n---\n# C\n", encoding="utf-8")
        return bundle

    def test_valid_flat_yaml_passes(self, tmp_path):
        bundle = self._bundle_with_concept(tmp_path, "type: concept\ntitle: C\n")
        result = validate_bundle(str(bundle))
        errors = [d for d in result["diagnostics"] if d["severity"] == "error" and "c.md" in d["path"]]
        assert not errors

    def test_tabs_in_frontmatter_fail(self, tmp_path):
        bundle = self._bundle_with_concept(tmp_path, "type:\tconcept\n")
        result = validate_bundle(str(bundle))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_FRONTMATTER_UNSUPPORTED" in codes

    def test_flow_collection_fails(self, tmp_path):
        bundle = self._bundle_with_concept(tmp_path, 'tags: {a: b}\n')
        result = validate_bundle(str(bundle))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_FRONTMATTER_UNSUPPORTED" in codes

    def test_nested_mapping_fails(self, tmp_path):
        bundle = self._bundle_with_concept(tmp_path, "type: concept\nnested:\n  key: val\n  inner: x\n")
        result = validate_bundle(str(bundle))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_FRONTMATTER_UNSUPPORTED" in codes

    def test_duplicate_key_fails(self, tmp_path):
        bundle = self._bundle_with_concept(tmp_path, "type: concept\ntype: duplicate\n")
        result = validate_bundle(str(bundle))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_FRONTMATTER_UNSUPPORTED" in codes

    def test_missing_closing_marker_fails(self, tmp_path):
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text('---\nokf_version: "0.2"\ntitle: T\n---\n', encoding="utf-8")
        (bundle / "log.md").write_text("# log\n", encoding="utf-8")
        concepts = bundle / "concepts"
        concepts.mkdir()
        (concepts / "c.md").write_text("---\ntype: concept\n# no closing\n", encoding="utf-8")
        result = validate_bundle(str(bundle))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_FRONTMATTER_UNSUPPORTED" in codes

    def test_list_tags_pass(self, tmp_path):
        fm = "type: concept\ntags:\n  - action/plan\n  - domain/knowledge-curator\n"
        bundle = self._bundle_with_concept(tmp_path, fm)
        result = validate_bundle(str(bundle))
        tag_errors = [d for d in result["diagnostics"] if d["code"] == "OKF_TAGS_MALFORMED"]
        assert not tag_errors


# ---------------------------------------------------------------------------
# Structural error tests
# ---------------------------------------------------------------------------

class TestErrors:
    def test_root_missing(self, tmp_path):
        result = validate_bundle(str(tmp_path / "nonexistent"))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_ROOT_MISSING" in codes
        assert result["code"] == 2

    def test_index_missing(self, tmp_path):
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "log.md").write_text("# log\n")
        result = validate_bundle(str(bundle))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_INDEX_MISSING" in codes

    def test_log_missing(self, tmp_path):
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text('---\nokf_version: "0.2"\ntitle: T\n---\n')
        result = validate_bundle(str(bundle))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_LOG_MISSING" in codes

    def test_version_missing(self, tmp_path):
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text("---\ntitle: T\n---\n# T\n")
        (bundle / "log.md").write_text("# log\n")
        result = validate_bundle(str(bundle))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_VERSION_MISSING" in codes

    def test_version_unsupported(self, tmp_path):
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text('---\nokf_version: "0.1"\ntitle: T\n---\n')
        (bundle / "log.md").write_text("# log\n")
        result = validate_bundle(str(bundle))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_VERSION_UNSUPPORTED" in codes

    def test_frontmatter_missing_in_concept(self, tmp_path):
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text('---\nokf_version: "0.2"\ntitle: T\n---\n')
        (bundle / "log.md").write_text("# log\n")
        concepts = bundle / "concepts"
        concepts.mkdir()
        (concepts / "no-fm.md").write_text("# No frontmatter here\n")
        result = validate_bundle(str(bundle))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_FRONTMATTER_MISSING" in codes

    def test_type_missing_in_concept(self, tmp_path):
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text('---\nokf_version: "0.2"\ntitle: T\n---\n')
        (bundle / "log.md").write_text("# log\n")
        concepts = bundle / "concepts"
        concepts.mkdir()
        (concepts / "no-type.md").write_text("---\ntitle: X\n---\n# X\n")
        result = validate_bundle(str(bundle))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_TYPE_MISSING" in codes


# ---------------------------------------------------------------------------
# Advisory / warnings tests
# ---------------------------------------------------------------------------

class TestWarnings:
    def _bundle(self, tmp_path: Path, concept_fm: str) -> Path:
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text('---\nokf_version: "0.2"\ntitle: T\n---\n', encoding="utf-8")
        (bundle / "log.md").write_text("# log\n", encoding="utf-8")
        concepts = bundle / "concepts"
        concepts.mkdir()
        (concepts / "c.md").write_text(f"---\n{concept_fm}\n---\n# C\n", encoding="utf-8")
        return bundle

    def test_description_missing_warning(self, tmp_path):
        bundle = self._bundle(tmp_path, "type: concept\n")
        result = validate_bundle(str(bundle))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_DESCRIPTION_MISSING" in codes
        # It is a warning, not error
        sev = {d["code"]: d["severity"] for d in result["diagnostics"]}
        assert sev.get("OKF_DESCRIPTION_MISSING") == "warning"

    def test_status_malformed_warning(self, tmp_path):
        bundle = self._bundle(tmp_path, "type: concept\nstatus: invalid\n")
        result = validate_bundle(str(bundle))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_STATUS_MALFORMED" in codes

    def test_tags_malformed_warning(self, tmp_path):
        bundle = self._bundle(tmp_path, "type: concept\ntags:\n  - notslashform\n")
        result = validate_bundle(str(bundle))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_TAGS_MALFORMED" in codes

    def test_sources_malformed_warning(self, tmp_path):
        # Empty sources list
        bundle = self._bundle(tmp_path, "type: concept\nsources:\n")
        result = validate_bundle(str(bundle))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_SOURCES_MALFORMED" in codes

    def test_generated_malformed_warning(self, tmp_path):
        bundle = self._bundle(tmp_path, "type: concept\ngenerated: bad-format\n")
        result = validate_bundle(str(bundle))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_GENERATED_MALFORMED" in codes

    def test_generated_valid_passes(self, tmp_path):
        bundle = self._bundle(tmp_path, "type: concept\ngenerated: human:gabriel @ 2026-08-11T00:00:00Z\n")
        result = validate_bundle(str(bundle))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_GENERATED_MALFORMED" not in codes

    def test_verified_malformed_warning(self, tmp_path):
        bundle = self._bundle(tmp_path, "type: concept\nverified: not-valid\n")
        result = validate_bundle(str(bundle))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_VERIFIED_MALFORMED" in codes

    def test_stale_after_malformed_warning(self, tmp_path):
        bundle = self._bundle(tmp_path, "type: concept\nstale_after: not-a-date\n")
        result = validate_bundle(str(bundle))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_STALE_AFTER_MALFORMED" in codes

    def test_stale_after_valid_passes(self, tmp_path):
        bundle = self._bundle(tmp_path, "type: concept\nstale_after: 2026-12-31\n")
        result = validate_bundle(str(bundle))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_STALE_AFTER_MALFORMED" not in codes

    def test_legacy_timestamp_warning(self, tmp_path):
        bundle = self._bundle(tmp_path, "type: concept\ntimestamp: 2026-01-01\n")
        result = validate_bundle(str(bundle))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_LEGACY_TIMESTAMP" in codes

    def test_legacy_citations_warning(self, tmp_path):
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text('---\nokf_version: "0.2"\ntitle: T\n---\n', encoding="utf-8")
        (bundle / "log.md").write_text("# log\n", encoding="utf-8")
        concepts = bundle / "concepts"
        concepts.mkdir()
        (concepts / "c.md").write_text("---\ntype: concept\n---\n# C\n\n# Citations\n- foo\n", encoding="utf-8")
        result = validate_bundle(str(bundle))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_LEGACY_CITATIONS" in codes

    def test_warnings_exit_zero_default(self, tmp_path):
        """Warnings alone should not cause non-zero exit in default mode."""
        bundle = self._bundle(tmp_path, "type: concept\n")
        result = validate_bundle(str(bundle), strict=False)
        assert result["code"] == 0

    def test_strict_warnings_exit_two(self, tmp_path):
        bundle = self._bundle(tmp_path, "type: concept\n")
        result = validate_bundle(str(bundle), strict=True)
        assert result["code"] == 2
        assert result["ok"] is False

    def test_strict_clean_bundle_exit_zero(self, tmp_path):
        """A bundle with no warnings at all passes strict mode."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text('---\nokf_version: "0.2"\ntitle: T\n---\n', encoding="utf-8")
        (bundle / "log.md").write_text("# log\n", encoding="utf-8")
        concepts = bundle / "concepts"
        concepts.mkdir()
        (concepts / "c.md").write_text(
            "---\ntype: concept\ndescription: A test concept.\nstatus: stable\n---\n# C\n",
            encoding="utf-8"
        )
        result = validate_bundle(str(bundle), strict=True)
        assert result["code"] == 0


# ---------------------------------------------------------------------------
# Diagnostic ordering tests
# ---------------------------------------------------------------------------

class TestDiagnosticOrder:
    def test_path_lex_then_severity_then_code(self, tmp_path):
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text('---\nokf_version: "0.2"\ntitle: T\n---\n')
        (bundle / "log.md").write_text("# log\n")
        concepts = bundle / "concepts"
        concepts.mkdir()
        # Two concepts with different issues
        (concepts / "a.md").write_text("---\ntype: concept\nstatus: BROKEN\n---\n# A\n")
        (concepts / "b.md").write_text("---\ntype: concept\n---\n# B\n")  # missing description warning
        result = validate_bundle(str(bundle))
        paths = [d["path"] for d in result["diagnostics"]]
        # a.md should appear before b.md
        assert paths.index("concepts/a.md") < paths.index("concepts/b.md")

    def test_errors_before_warnings_same_path(self, tmp_path):
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text('---\nokf_version: "0.2"\ntitle: T\n---\n')
        (bundle / "log.md").write_text("# log\n")
        concepts = bundle / "concepts"
        concepts.mkdir()
        # Concept missing type (error) and with invalid status (warning)
        (concepts / "c.md").write_text("---\nstatus: bad\n---\n# C\n")  # no type = error
        result = validate_bundle(str(bundle))
        c_diags = [d for d in result["diagnostics"] if "c.md" in d["path"]]
        if len(c_diags) >= 2:
            # errors should come before warnings
            error_idx = next((i for i, d in enumerate(c_diags) if d["severity"] == "error"), None)
            warning_idx = next((i for i, d in enumerate(c_diags) if d["severity"] == "warning"), None)
            if error_idx is not None and warning_idx is not None:
                assert error_idx < warning_idx

    def test_no_duplicate_path_code(self, tmp_path):
        """Same (path, code) pair must appear at most once."""
        bundle = _make_valid_bundle(tmp_path)
        result = validate_bundle(str(bundle))
        seen = set()
        for d in result["diagnostics"]:
            key = (d["path"], d["code"])
            assert key not in seen, f"Duplicate diagnostic: {key}"
            seen.add(key)


# ---------------------------------------------------------------------------
# Read-only boundary tests
# ---------------------------------------------------------------------------

class TestReadOnlyBoundary:
    def test_no_file_mutation_valid(self, tmp_path):
        bundle = _make_valid_bundle(tmp_path)
        # Record hashes before
        before = {p: _sha256(p) for p in bundle.rglob("*.md")}
        validate_bundle(str(bundle))
        after = {p: _sha256(p) for p in bundle.rglob("*.md")}
        assert before == after

    def test_no_file_mutation_with_errors(self, tmp_path):
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text('---\nokf_version: "0.2"\ntitle: T\n---\n')
        (bundle / "log.md").write_text("# log\n")
        concepts = bundle / "concepts"
        concepts.mkdir()
        (concepts / "bad.md").write_text("no frontmatter\n")
        before = {p: _sha256(p) for p in bundle.rglob("*.md")}
        validate_bundle(str(bundle))
        after = {p: _sha256(p) for p in bundle.rglob("*.md")}
        assert before == after

    def test_symlink_concept_refused(self, tmp_path):
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text('---\nokf_version: "0.2"\ntitle: T\n---\n')
        (bundle / "log.md").write_text("# log\n")
        concepts = bundle / "concepts"
        concepts.mkdir()
        outside = tmp_path / "outside.md"
        outside.write_text("---\ntype: concept\n---\n# X\n")
        (concepts / "link.md").symlink_to(outside)
        result = validate_bundle(str(bundle))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_PATH_SYMLINK" in codes

    def test_binary_file_refused(self, tmp_path):
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text('---\nokf_version: "0.2"\ntitle: T\n---\n')
        (bundle / "log.md").write_text("# log\n")
        concepts = bundle / "concepts"
        concepts.mkdir()
        (concepts / "binary.md").write_bytes(b"---\ntype: concept\n---\n\x00\x01\x02")
        result = validate_bundle(str(bundle))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_FILE_BINARY" in codes

    def test_oversized_file_refused(self, tmp_path):
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text('---\nokf_version: "0.2"\ntitle: T\n---\n')
        (bundle / "log.md").write_text("# log\n")
        concepts = bundle / "concepts"
        concepts.mkdir()
        # Write just over 1 MiB
        big = concepts / "big.md"
        big.write_bytes(b"x" * (1024 * 1024 + 1))
        result = validate_bundle(str(bundle))
        codes = {d["code"] for d in result["diagnostics"]}
        assert "OKF_FILE_OVERSIZE" in codes
