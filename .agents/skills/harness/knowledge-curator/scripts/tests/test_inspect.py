from __future__ import annotations
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from okf_evidence import load_and_verify
from okf_inspect import inspect_bundle


SCRIPTS_DIR = Path(__file__).parent.parent


def _make_bundle(tmpdir: str, files: dict[str, str]) -> str:
    root = Path(tmpdir) / 'bundle'
    root.mkdir()
    for rel, content in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding='utf-8')
    return str(root)


class TestEvidenceGate(unittest.TestCase):
    def test_load_and_verify_ok(self):
        data, err = load_and_verify(SCRIPTS_DIR)
        self.assertIsNone(err)
        self.assertIsNotNone(data)
        self.assertEqual(data['schema_version'], 1)

    def test_load_from_missing_dir(self):
        data, err = load_and_verify(Path('/tmp/__nonexistent__'))
        self.assertIsNone(data)
        self.assertEqual(err, 'evidence-missing')


class TestInspectMinimalValid(unittest.TestCase):
    def test_valid_bundle_no_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = _make_bundle(tmpdir, {
                'index.md': '# Index\n',
                'log.md': '# Log\n',
                'concepts/index.md': '# Concepts\n',
                'concepts/foo.md': '---\ntype: concept\n---\n# Foo\n',
            })
            data, _ = load_and_verify(SCRIPTS_DIR)
            result = inspect_bundle(bundle, evidence=data, evidence_digest=data['artifact_digest'])
            errors = [f for f in result['findings'] if f['severity'] == 'error']
            self.assertEqual(errors, [])

    def test_missing_root_log_is_warning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = _make_bundle(tmpdir, {
                'index.md': '# Index\n',
                'concepts/index.md': '# Concepts\n',
                'concepts/foo.md': '---\ntype: concept\n---\n# Foo\n',
            })
            data, _ = load_and_verify(SCRIPTS_DIR)
            result = inspect_bundle(bundle, evidence=data, evidence_digest=data['artifact_digest'])
            rule_ids = [f['rule_id'] for f in result['findings']]
            self.assertIn('missing-root-log', rule_ids)
            log_finding = next(f for f in result['findings'] if f['rule_id'] == 'missing-root-log')
            self.assertEqual(log_finding['severity'], 'warning')


class TestInspectTypeRequired(unittest.TestCase):
    def test_missing_type_is_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = _make_bundle(tmpdir, {
                'index.md': '# Index\n',
                'log.md': '# Log\n',
                'concepts/index.md': '# Concepts\n',
                'concepts/no-type.md': '---\ntitle: No Type\n---\n# No Type\n',
            })
            data, _ = load_and_verify(SCRIPTS_DIR)
            result = inspect_bundle(bundle, evidence=data, evidence_digest=data['artifact_digest'])
            rule_ids = [f['rule_id'] for f in result['findings']]
            self.assertIn('okf-type-missing', rule_ids)

    def test_empty_type_is_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = _make_bundle(tmpdir, {
                'index.md': '# Index\n',
                'log.md': '# Log\n',
                'concepts/index.md': '# Concepts\n',
                'concepts/empty-type.md': '---\ntype: \n---\n# Empty Type\n',
            })
            data, _ = load_and_verify(SCRIPTS_DIR)
            result = inspect_bundle(bundle, evidence=data, evidence_digest=data['artifact_digest'])
            rule_ids = [f['rule_id'] for f in result['findings']]
            self.assertIn('okf-type-missing', rule_ids)


class TestInspectMissingIndex(unittest.TestCase):
    def test_meaningful_dir_without_index_is_warning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = _make_bundle(tmpdir, {
                'index.md': '# Index\n',
                'log.md': '# Log\n',
                'concepts/foo.md': '---\ntype: concept\n---\n# Foo\n',
            })
            data, _ = load_and_verify(SCRIPTS_DIR)
            result = inspect_bundle(bundle, evidence=data, evidence_digest=data['artifact_digest'])
            rule_ids = [f['rule_id'] for f in result['findings']]
            self.assertIn('missing-index', rule_ids)
            idx_finding = next(f for f in result['findings'] if f['rule_id'] == 'missing-index')
            self.assertEqual(idx_finding['severity'], 'warning')

    def test_meaningful_dir_without_index_strict_is_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = _make_bundle(tmpdir, {
                'index.md': '# Index\n',
                'log.md': '# Log\n',
                'concepts/foo.md': '---\ntype: concept\n---\n# Foo\n',
            })
            data, _ = load_and_verify(SCRIPTS_DIR)
            result = inspect_bundle(bundle, strict=True, evidence=data, evidence_digest=data['artifact_digest'])
            rule_ids = [f['rule_id'] for f in result['findings']]
            self.assertIn('missing-index', rule_ids)
            idx_finding = next(f for f in result['findings'] if f['rule_id'] == 'missing-index')
            self.assertEqual(idx_finding['severity'], 'error')


if __name__ == '__main__':
    unittest.main()
