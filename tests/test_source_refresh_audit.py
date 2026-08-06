import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


class SourceRefreshAuditTests(unittest.TestCase):
    def test_reconciles_synthetic_apk_listing_patch_and_canonical_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "bluestacks"
            for relative in ("apk", "logs", "shared-data/cache/content", "shared-data/cache/patch"):
                (root / relative).mkdir(parents=True, exist_ok=True)
            apk = root / "apk/base.apk"
            apk.write_bytes(b"synthetic apk")
            apk_hash = hashlib.sha256(apk.read_bytes()).hexdigest()
            (root / "logs/com.godzilab.idlerpg.apk-sha256.txt").write_text(
                f"{apk_hash}  samples/bluestacks/apk/base.apk\n", encoding="utf-8"
            )
            (root / "logs/com.godzilab.idlerpg.dumpsys-package.txt").write_text(
                "versionCode=200821 minSdk=23\nversionName=2.0.821\n", encoding="utf-8"
            )
            names = ("Heroes.csv", "Persos.xml", "Skills.xml", "Items.xml", "Config.xml", "Config_en.xml")
            patch = root / "shared-data/cache/patch/refresh.bin"
            with zipfile.ZipFile(patch, "w") as archive:
                for name in names:
                    value = f"synthetic {name}".encode()
                    (root / "shared-data/cache/content" / name).write_bytes(value)
                    archive.writestr(name, value)
            listed = [f"/sdcard/Android/data/com.godzilab.idlerpg/cache/content/{name}" for name in names]
            listed.append("/sdcard/Android/data/com.godzilab.idlerpg/cache/patch/refresh.bin")
            (root / "logs/com.godzilab.idlerpg.shared-files.txt").write_text("\n".join(listed) + "\n", encoding="utf-8")
            output = Path(directory) / "audit.json"
            result = subprocess.run(
                [sys.executable, "scripts/audit-cta-source-refresh.py", str(root), str(output)],
                check=True, capture_output=True, text=True,
            )
            summary = json.loads(result.stdout)
            audit = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("2.0.821 (200821)", summary["version"])
            self.assertTrue(audit["apk_hashes_match_record"])
            self.assertEqual([], audit["listed_but_missing"])
            self.assertEqual([], audit["materialized_but_unlisted"])
            self.assertTrue(all(row["matching_patch_bundles"] == ["refresh.bin"] for row in audit["canonical_sources"]))


if __name__ == "__main__":
    unittest.main()
