from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from cta_importer.cta.classification import classify_heroes
from cta_importer.model import SourceArtifact


class CtaClassificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.artifact = SourceArtifact(root, "Persos.xml", 0, "synthetic")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_all_classification_categories_have_evidence(self) -> None:
        rows = {key: self.row() for key in (
            "Collectible", "Uncertain", "Enemy", "Npc", "Owner", "OwnerClone", "OwnerBerserk", "Cosmetic", "Werewolf"
        )}
        nodes = ET.fromstring("""<characters>
          <character key="Collectible" assets="Hero" iconIdx="1"><skill>A</skill><skill>B</skill><skill>C</skill></character>
          <character key="Uncertain" assets="Legacy"><skill>A</skill></character>
          <character key="Enemy"><module /></character>
          <character key="Npc" />
          <character key="Owner" assets="Owner" iconIdx="2"><skill>A</skill><skill>B</skill><skill>C</skill></character>
          <character key="OwnerClone" assets="Owner" />
          <character key="OwnerBerserk" assets="Owner" />
          <character key="Cosmetic" assets="Skin" skinOwner="Owner" />
          <character key="Werewolf" assets="Wolf" iconIdx="3"><skill>A</skill><skill>B</skill><skill>C</skill></character>
        </characters>""")
        characters = {(node.get("key") or "").lower(): node for node in nodes.findall("character")}
        entities, _ = classify_heroes(rows, characters, {"collectible": ("ChestTest",), "owner": ("ChestTest",), "werewolf": ("ChestHLW",)}, self.artifact)
        payloads = {item.key: item.payload for item in entities}
        expected = {
            "Collectible": "collectible", "Uncertain": "uncertain", "Enemy": "enemy", "Npc": "npc",
            "OwnerClone": "summoned_variant", "OwnerBerserk": "transformed_variant",
            "Cosmetic": "cosmetic_variant", "Werewolf": "non_collectible",
        }
        for key, kind in expected.items():
            self.assertEqual(kind, payloads[key]["kind"])
            self.assertTrue(payloads[key]["evidence"])
            self.assertIn(payloads[key]["confidence"], {"low", "medium", "high"})
        self.assertEqual("Owner", payloads["Cosmetic"]["owner_id"])
        self.assertEqual("Owner", payloads["OwnerClone"]["owner_id"])

    def test_no_icon_and_no_acquisition_is_uncertain(self) -> None:
        rows = {key: self.row() for key in ("ArthusKnight", "GreenArcher", "IceGolem", "MummyGiant", "Rolexo", "SkeletonArcher", "ViForky", "ViLokt", "ViRagnar", "VuTNTbomb")}
        root = ET.Element("characters")
        for key in rows:
            node = ET.SubElement(root, "character", key=key, assets=key)
            ET.SubElement(node, "skill").text = "Attack"
        entities, _ = classify_heroes(rows, {node.get("key", "").lower(): node for node in root}, {}, self.artifact)
        self.assertEqual({"uncertain"}, {item.payload["kind"] for item in entities})

    @staticmethod
    def row() -> dict[str, str]:
        return {"Dungeon": "0", "Shop": "0", "Event": "0", "ChestEpic": "0", "Ability1": "", "Ability2": "", "Ability3": ""}


if __name__ == "__main__":
    unittest.main()
