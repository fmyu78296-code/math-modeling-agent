"""Portable tests using synthetic metadata; no private papers are required."""
import copy
import csv
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import reference_bridge as bridge
from tools.reference_bridge import (load_catalog, metadata_differences, public_row,
                                    reconcile, verify_archive, verify_local_files)


class ReferenceBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="synthetic-refs-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        refs = self.root / "refs"
        refs.mkdir()
        rows = []
        hashes = {}
        for source_id, topic in (("C01", "C"), ("C02", "C"), ("D01", "D")):
            relative = f"refs/synthetic-{source_id}.txt"
            path = self.root / relative
            path.write_text(f"Synthetic test fixture {source_id}. Not a paper.\n",
                            encoding="utf-8")
            hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
            row = {field: "" for field in bridge.FIELDS}
            row.update(source_id=source_id, topic=topic,
                       title=f"Synthetic reference {source_id}",
                       authors="Test Fixture", year="2026", venue="Synthetic",
                       doi=f"10.0000/synthetic-{source_id.lower()}",
                       url=f"https://example.invalid/reference/{source_id.lower()}",
                       accessed_at="2026-10-09", access_level="synthetic",
                       verification_status="unverified",
                       local_file=relative, local_text="", kind="test_fixture",
                       relation="", notes="Synthetic fixture, not scientific evidence")
            rows.append(row)
        fields = (*bridge.FIELDS, "topic", "local_file", "local_text", "kind", "relation")
        with (refs / "catalog.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        (refs / "file_hashes.json").write_text(json.dumps(hashes), encoding="utf-8")
        patcher = patch.multiple(bridge, ROOT=self.root,
                                 CATALOG=refs / "catalog.csv",
                                 HASHES=refs / "file_hashes.json")
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_local_catalog_and_hashes(self):
        c, d = load_catalog("C"), load_catalog("D")
        self.assertEqual((len(c), len(d)), (2, 1))
        self.assertEqual(len(verify_archive()), 3)
        verify_local_files(c + d)
        self.assertEqual({row["source_id"] for row in c}, {"C01", "C02"})

    def test_existing_doi_retains_local_id(self):
        local = public_row(load_catalog("C")[0])
        incoming = copy.deepcopy(local)
        incoming.update(source_id="found-1",
                        doi="https://doi.org/10.0000/SYNTHETIC-C01")
        merged, events = reconcile("C", [incoming])
        self.assertEqual(len(merged), 2)
        self.assertEqual(events[0][:3], ("matched", "found-1", "C01"))
        self.assertEqual(metadata_differences(incoming, local), [])

    def test_new_and_conflicting_doi_are_reviewable(self):
        new = {field: "" for field in public_row(load_catalog("C")[0])}
        new.update(source_id="agent-1", title="Synthetic new method", year="2026",
                   doi="10.0000/synthetic-new", verification_status="verified")
        collision = copy.deepcopy(new)
        collision.update(source_id="agent-2", title=load_catalog("C")[0]["title"],
                         doi="10.0000/synthetic-different")
        merged, events = reconcile("C", [new, collision])
        self.assertEqual(len(merged), 4)
        self.assertEqual(events[0][0], "new_unreviewed")
        self.assertEqual(events[1][0], "possible_title_conflict")
        self.assertEqual(merged[2]["verification_status"], "partially_verified")

    def test_changed_archived_file_is_rejected(self):
        (self.root / "refs/synthetic-C01.txt").write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "archived source hash changed"):
            verify_archive()


if __name__ == "__main__":
    unittest.main()
