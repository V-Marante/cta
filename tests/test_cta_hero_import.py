from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cta_importer.cta import HeroLibraryValidator, cta_parsers
from cta_importer.cta.heroes import passive
from cta_importer.cta.portraits import portrait_reference
from cta_importer.engine import ImportEngine, ImportRequest
from cta_importer.model import Severity, VersionInfo
from cta_importer.persistence import SQLiteRepository
from cta_importer.registry import ParserRegistry, ValidatorRegistry


HEROES = """Name,Key,Class,Tribe,Sex,Damage Type,Elemental,Atk,HP,Def,AtkRange,AtkReload,MoveSpeed,Ctk,CtkDmg,Resistance,Evade,BaseStars,MaxStars,POW,DPS
Ada,Ada,Ranger,Human,f,Phys,Fire,42,300,8,250,1.2,140,20,150,10,2,3,8,999,35
Bob,Bob,Knight,Orc,m,Magic,Water,30,500,20,100,2,90,5,100,30,0,2,8,850,15
"""

PERSOS = """<?xml version="1.0"?><characters>
  <character key="Ada" assets="AdaAsset" iconIdx="3"><skill>AdaArrow</skill><skill>GoneSkill</skill><ability>BobBlock</ability></character>
  <character key="Bob"><skill>BobBlock</skill></character>
</characters>"""

SKILLS = """<?xml version="1.0"?><skills>
  <skill key="AdaArrow" type="damage" name="Arrow"><spec atkPercent="2"/></skill>
  <skill key="BobBlock" type="buff" name="Block"><info>Canonical info</info></skill>
</skills>"""

PERSOS_EN = """<?xml version="1.0"?><characters><character key="Ada" name="Ada the Swift"/></characters>"""
SKILLS_EN = """<?xml version="1.0"?><skills><skill key="AdaArrow" name="Flame Arrow"><info>Deals fire damage.</info></skill></skills>"""
CONFIG_EN = """<?xml version="1.0"?><config>
  <group name="AbilityInfo"><value name="Evade">*{evade}%* chance to evade a hit</value></group>
  <group name="SkDesc"><value name="Arrow">Fires an arrow at an enemy</value></group>
</config>"""
CONFIG = """<?xml version="1.0"?><config>
  <group name="ChestTest"><value name="item" x="10" y="5">Medal_Ada</value></group>
  <group name="ChestLegendary"><value name="item" x="10" y="5">Bob</value></group>
  <group name="ChestHeroesPast"><value name="item" x="10" y="5">Ada</value></group>
  <group name="Crusade_Shop_Medals"><value name="item" x="10" y="500">Medal_Ada</value></group>
</config>"""
ITEMS_EN = """<?xml version="1.0"?><items><item key="ChestTest" name="Test Chest"/><item key="ChestLegendary" name="Legendary Chest"/><item key="ChestHeroesPast" name="Past Chest"/></items>"""


class CtaHeroImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "content"
        self.source.mkdir()
        for name, value in {"Heroes.csv": HEROES, "Persos.xml": PERSOS, "Skills.xml": SKILLS,
                            "Persos_en.xml": PERSOS_EN, "Skills_en.xml": SKILLS_EN, "Config_en.xml": CONFIG_EN,
                            "Config.xml": CONFIG, "Items_en.xml": ITEMS_EN}.items():
            (self.source / name).write_text(value, encoding="utf-8")
        self.repository = SQLiteRepository(self.root / "cta.sqlite")
        self.repository.migrate()

    def tearDown(self) -> None:
        self.repository.close()
        self.temp.cleanup()

    def test_imports_complete_hero_slice_with_provenance(self) -> None:
        engine = ImportEngine(self.repository, ParserRegistry(cta_parsers()), ValidatorRegistry([HeroLibraryValidator()]))
        result = engine.import_source(ImportRequest(self.source, VersionInfo("cta", "test")))

        self.assertEqual("succeeded", result.status)
        self.assertEqual(13, result.entity_count)  # plus one classification per hero
        hero = self.repository.connection.execute(
            "SELECT payload_json, source_path, source_record FROM entities WHERE import_id=? AND namespace='hero' AND entity_key='Ada'",
            (result.import_id,),
        ).fetchone()
        self.assertIn('"attack":42', hero["payload_json"])
        self.assertIn('"mobility":"ground"', hero["payload_json"])
        self.assertEqual("collectible", self.repository.connection.execute(
            "SELECT json_extract(payload_json, '$.kind') FROM entities WHERE import_id=? AND namespace='hero_classification' AND entity_key='Ada'", (result.import_id,)
        ).fetchone()[0])
        self.assertEqual("Heroes.csv", hero["source_path"])
        self.assertEqual("Ada", hero["source_record"])
        self.assertEqual(3, self.repository.connection.execute(
            "SELECT count(*) FROM relations WHERE import_id=? AND relation='character_skill' AND source_key='Ada'", (result.import_id,)
        ).fetchone()[0])
        relation_kinds = [row[0] for row in self.repository.connection.execute(
            "SELECT payload_json FROM relations WHERE import_id=? AND relation='character_skill' AND source_key='Ada' ORDER BY id", (result.import_id,)
        )]
        self.assertEqual(['{"kind":"skill"}', '{"kind":"skill"}', '{"kind":"ability"}'], relation_kinds)
        self.assertEqual("Ada the Swift", self.repository.connection.execute(
            "SELECT value FROM localizations WHERE import_id=? AND namespace='hero' AND entity_key='Ada' AND field='name'", (result.import_id,)
        ).fetchone()[0])
        self.assertEqual("*{evade}%* chance to evade a hit", self.repository.connection.execute(
            "SELECT value FROM localizations WHERE import_id=? AND namespace='ability' AND entity_key='Evade'", (result.import_id,)
        ).fetchone()[0])
        self.assertEqual("Test Chest", self.repository.connection.execute(
            "SELECT value FROM localizations WHERE import_id=? AND namespace='acquisition_source' AND entity_key='ChestTest'", (result.import_id,)
        ).fetchone()[0])
        self.assertEqual(3, self.repository.connection.execute(
            "SELECT count(*) FROM relations WHERE import_id=? AND relation='hero_acquisition' AND source_key='Ada'", (result.import_id,)
        ).fetchone()[0])
        self.assertEqual(1, self.repository.connection.execute(
            "SELECT count(*) FROM relations WHERE import_id=? AND relation='hero_acquisition' AND source_key='Bob' AND target_key='ChestLegendary'", (result.import_id,)
        ).fetchone()[0])
        past = self.repository.connection.execute(
            "SELECT payload_json FROM relations WHERE import_id=? AND relation='hero_acquisition' AND source_key='Ada' AND target_key='ChestHeroesPast'", (result.import_id,)
        ).fetchone()[0]
        self.assertIn('"current":false', past)
        crusade = self.repository.connection.execute(
            "SELECT payload_json FROM entities WHERE import_id=? AND namespace='acquisition_source' AND entity_key='Crusade_Shop_Medals'", (result.import_id,)
        ).fetchone()[0]
        self.assertIn('"kind":"shop"', crusade)
        self.assertIn('"name":"Crusade Shop"', crusade)
        portrait = self.repository.connection.execute(
            "SELECT payload_json FROM entities WHERE import_id=? AND namespace='portrait' AND lower(entity_key)='ada'", (result.import_id,)
        ).fetchone()[0]
        self.assertIn('"element_code":"FI"', portrait)
        self.assertIn('"frame_name":"GMI_FI_003.png"', portrait)
        self.assertIn('"atlas":"UIGuildMemberIcons0"', portrait)
        codes = {row[0] for row in self.repository.connection.execute("SELECT code FROM diagnostics WHERE import_id=?", (result.import_id,))}
        self.assertIn("unresolved_skill_reference", codes)
        self.assertIn("missing_portrait_reference", codes)
        self.assertIn("missing_localization_key", codes)

    def test_expanded_parser_versions_invalidate_older_imports(self) -> None:
        versions = {parser.descriptor.parser_id: parser.descriptor.parser_version for parser in cta_parsers()}
        self.assertEqual("1.5.0", versions["cta.heroes"])
        self.assertEqual("1.3.0", versions["cta.localization.en"])
        self.assertEqual("1.5.0", versions["cta.characters"])
        self.assertEqual("1.3.1", versions["cta.hero_acquisition"])

    def test_internal_fighter_class_maps_to_player_facing_brawler(self) -> None:
        (self.source / "Heroes.csv").write_text(HEROES.replace("Ranger,Human", "Fighter,Human", 1), encoding="utf-8")
        result = ImportEngine(self.repository, ParserRegistry(cta_parsers()), ValidatorRegistry([HeroLibraryValidator()])).import_source(
            ImportRequest(self.source, VersionInfo("cta", "job-name"))
        )
        payload = self.repository.connection.execute(
            "SELECT payload_json FROM entities WHERE import_id=? AND namespace='hero' AND entity_key='Ada'", (result.import_id,)
        ).fetchone()[0]
        self.assertIn('"class":"Brawler"', payload)
        self.assertIn('"source_class":"Fighter"', payload)
        self.assertIn('"base_stars":3', payload)
        self.assertIn('"max_stars":8', payload)

    def test_compact_portrait_mapping_is_deterministic(self) -> None:
        expected = {
            "Dark": "GMI_DA_001.png", "Earth": "GMI_EA_001.png", "Fire": "GMI_FI_001.png",
            "Light": "GMI_LI_001.png", "Water": "GMI_WA_001.png",
        }
        for element, frame in expected.items():
            with self.subTest(element=element):
                self.assertEqual(frame, portrait_reference(element, 1).frame_name)
        self.assertEqual("UIGuildMemberIcons1", portrait_reference("Water", 16).atlas_name)
        self.assertIsNone(portrait_reference("Neutral", 1))
        self.assertIsNone(portrait_reference("Earth", 33))
        self.assertIsNone(portrait_reference("Fire", None))

    def test_invalid_compact_portrait_index_is_diagnosed_without_guessing(self) -> None:
        (self.source / "Persos.xml").write_text(PERSOS.replace('<character key="Bob">', '<character key="Bob" assets="BobAsset" iconIdx="99">'), encoding="utf-8")
        result = ImportEngine(self.repository, ParserRegistry(cta_parsers()), ValidatorRegistry([HeroLibraryValidator()])).import_source(
            ImportRequest(self.source, VersionInfo("cta", "invalid-portrait"))
        )
        portrait = self.repository.connection.execute(
            "SELECT payload_json FROM entities WHERE import_id=? AND namespace='portrait' AND entity_key='Bob'", (result.import_id,)
        ).fetchone()[0]
        self.assertNotIn("frame_name", portrait)
        self.assertIn("invalid_compact_portrait_reference", {item.code for item in result.diagnostics})

    def test_case_only_identifiers_resolve_without_losing_raw_values(self) -> None:
        (self.source / "Persos.xml").write_text(PERSOS.replace('key="Ada"', 'key="aDa"').replace("AdaArrow", "adaarrow"), encoding="utf-8")
        result = ImportEngine(self.repository, ParserRegistry(cta_parsers()), ValidatorRegistry([HeroLibraryValidator()])).import_source(
            ImportRequest(self.source, VersionInfo("cta", "case-normalized"))
        )
        hero_relation = self.repository.connection.execute(
            "SELECT target_key,payload_json FROM relations WHERE import_id=? AND relation='hero_character' AND source_key='Ada'", (result.import_id,)
        ).fetchone()
        skill_relation = self.repository.connection.execute(
            "SELECT target_key,payload_json FROM relations WHERE import_id=? AND relation='character_skill' AND source_key='aDa' ORDER BY ordinal LIMIT 1", (result.import_id,)
        ).fetchone()
        self.assertEqual("aDa", hero_relation["target_key"])
        self.assertIn('"source_target_id":"Ada"', hero_relation["payload_json"])
        self.assertEqual("AdaArrow", skill_relation["target_key"])
        self.assertIn('"source_target_id":"adaarrow"', skill_relation["payload_json"])
        unresolved = [item.message for item in result.diagnostics if item.code == "unresolved_relation_target"]
        self.assertFalse(any("character:Ada" in message or "skill:adaarrow" in message for message in unresolved))

    def test_focused_passive_mapping_preserves_source_value(self) -> None:
        self.assertEqual({
            "code": "BuffHP", "target": "All", "source_value": 12.5,
            "name": "Buff HP", "description": "All team: +12.5% HP",
        }, passive("BuffHP", "All", "12.5"))

    def test_suffix_variant_classification_is_deterministic(self) -> None:
        lines = HEROES.splitlines()
        clone = lines[1].replace("Ada,Ada,", "Ada Clone,AdaClone,")
        (self.source / "Heroes.csv").write_text("\n".join((*lines, clone)) + "\n", encoding="utf-8")
        result = ImportEngine(self.repository, ParserRegistry(cta_parsers()), ValidatorRegistry([HeroLibraryValidator()])).import_source(
            ImportRequest(self.source, VersionInfo("cta", "variant"))
        )
        classification = self.repository.connection.execute(
            "SELECT payload_json FROM entities WHERE import_id=? AND namespace='hero_classification' AND entity_key='AdaClone'", (result.import_id,)
        ).fetchone()[0]
        self.assertIn('"kind":"summoned_variant"', classification)
        self.assertIn('"owner_id":"Ada"', classification)

    def test_duplicate_hero_ids_are_rejected(self) -> None:
        with (self.source / "Heroes.csv").open("a", encoding="utf-8") as stream:
            stream.write(HEROES.splitlines()[1] + "\n")
        result = ImportEngine(self.repository, ParserRegistry(cta_parsers()), ValidatorRegistry([HeroLibraryValidator()])).import_source(
            ImportRequest(self.source, VersionInfo("cta", "duplicate"), fail_on=Severity.ERROR)
        )
        self.assertEqual("rejected", result.status)
        self.assertIn("duplicate_hero_id", {item.code for item in result.diagnostics})


if __name__ == "__main__":
    unittest.main()
