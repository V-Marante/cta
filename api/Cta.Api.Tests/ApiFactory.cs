using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Data.Sqlite;
using Microsoft.Extensions.Configuration;
using System.Text.Json;

namespace Cta.Api.Tests;

public sealed class ApiFactory : WebApplicationFactory<Program>
{
    public ApiFactory(string gameId = "cta", bool withUiIcon = false, bool withHeroIcon = false)
    {
        Database = Path.Combine(Path.GetTempPath(), $"cta-api-{Guid.NewGuid():N}.sqlite");
        UiIconRoot = Path.Combine(Path.GetTempPath(), $"cta-api-icons-{Guid.NewGuid():N}");
        HeroIconRoot = Path.Combine(Path.GetTempPath(), $"cta-api-portraits-{Guid.NewGuid():N}");
        GameId = gameId;
        if (withUiIcon)
        {
            Directory.CreateDirectory(Path.Combine(UiIconRoot, "elements"));
            File.WriteAllBytes(Path.Combine(UiIconRoot, "elements", "fire.png"),
                Convert.FromBase64String("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M/wHwAF/gL+3MxZ5wAAAABJRU5ErkJggg=="));
        }
        if (withHeroIcon)
        {
            Directory.CreateDirectory(HeroIconRoot);
            File.WriteAllBytes(Path.Combine(HeroIconRoot, "Alpha.png"),
                Convert.FromBase64String("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M/wHwAF/gL+3MxZ5wAAAABJRU5ErkJggg=="));
        }
        CreateSchema();
    }

    public string Database { get; }
    public string GameId { get; }
    public string UiIconRoot { get; }
    public string HeroIconRoot { get; }

    protected override void ConfigureWebHost(IWebHostBuilder builder) => builder.ConfigureAppConfiguration((_, config) =>
        config.AddInMemoryCollection(new Dictionary<string, string?> { ["Database"] = Database, ["GameId"] = GameId,
            ["HeroIconRoot"] = HeroIconRoot, ["UiIconRoot"] = UiIconRoot }));

    public void Seed(string importId, string gameId, string finishedAt, params HeroSeed[] heroes)
    {
        using var db = Open();
        Execute(db, "INSERT INTO import_runs(id,game_id,status,finished_at) VALUES($id,$game,'succeeded',$finished)", ("$id", importId), ("$game", gameId), ("$finished", finishedAt));
        foreach (var hero in heroes)
        {
            var payload = JsonSerializer.Serialize(new { canonical_name = hero.Name, @class = hero.Class, tribe = hero.Tribe,
                element = hero.Element, damage_type = hero.DamageType, sex = "f", mobility = hero.Mobility,
                traits = new[] { hero.Attribute }, stats = new { attack = 42, critical_chance = 0, power = 999 },
                stat_semantics = new { attack = new { value = 42, status = "source_defined", source_field = "Atk", label = "ATK", meaning = "base_attack_damage", unit = "points" }, power = new { value = 999, status = "unresolved", source_field = "POW", label = "Raw POW", meaning = (string?)null, unit = "source_score" } },
                source_calculations = new { factor_per_star = new { value = (double?)null, status = "unresolved", source_field = "Factor per Star", meaning = (string?)null } }, passive = new { },
                progression = new { base_stars = 3, max_stars = 8, rarity_name = hero.Rarity },
                progression_semantics = new { base_stars = new { value = 3, status = "unresolved", source_field = "BaseStars", meaning = (string?)null } },
                availability = new { shop = true }, legacy_availability = new { shop = new { value = true, status = "legacy_unverified", source_field = "Shop", source_path = "Heroes.csv" } }, raw = new { } });
            Entity(db, importId, "hero", hero.Id, payload);
            Entity(db, importId, "hero_classification", hero.Id, JsonSerializer.Serialize(new { kind = hero.Classification, owner_id = (string?)null }));
            Localize(db, importId, "hero", hero.Id, "name", hero.Name);
            if (hero.Acquisition is not null)
            {
                Entity(db, importId, "acquisition_source", hero.Acquisition, $$"""{"source_id":"{{hero.Acquisition}}","kind":"chest"}""");
                Localize(db, importId, "acquisition_source", hero.Acquisition, "name", hero.Acquisition);
                Execute(db, "INSERT INTO relations(import_id,relation,source_key,target_key,ordinal,payload_json) VALUES($i,'hero_acquisition',$h,$a,0,'{\"current\":true,\"medal_id\":\"Medal_Test\"}')", ("$i", importId), ("$h", hero.Id), ("$a", hero.Acquisition));
            }
        }
    }

    public void SeedSkill(string importId, string heroId)
    {
        using var db = Open();
        Entity(db, importId, "skill", "TestSkill", "{\"canonical_name\":\"Fallback Skill\",\"type\":\"damage\",\"attributes\":{},\"components\":[{\"kind\":\"info\",\"attributes\":{},\"attribute_semantics\":{},\"text\":\"SkDesc_Test\"},{\"kind\":\"spec\",\"attributes\":{\"time\":\"5\",\"cooldown\":\"0\"},\"attribute_semantics\":{\"cooldown\":{\"raw_value\":\"0\",\"value\":0,\"display_value\":0,\"status\":\"strongly_supported\",\"meaning\":\"duration\",\"unit\":\"seconds\",\"source_attribute\":\"cooldown\"}},\"text\":null}]}");
        Localize(db, importId, "skill_description", "Test", "description", "Works for {duration}.");
        Execute(db, "INSERT INTO relations(import_id,relation,source_key,target_key,ordinal,payload_json) VALUES($i,'character_skill',$h,'TestSkill',0,'{\"kind\":\"skill\"}')", ("$i", importId), ("$h", heroId));
    }

    public void SeedPortraitReference(string importId, string heroId)
    {
        using var db = Open();
        Entity(db, importId, "portrait", heroId, $$"""{"source_id":"{{heroId}}","frame_name":"GMI_FI_001.png"}""");
    }

    private void CreateSchema()
    {
        using var db = Open();
        Execute(db, """
          CREATE TABLE import_runs(id TEXT PRIMARY KEY,game_id TEXT,status TEXT,finished_at TEXT);
          CREATE TABLE entities(import_id TEXT,namespace TEXT,entity_key TEXT,payload_json TEXT);
          CREATE TABLE localizations(import_id TEXT,namespace TEXT,entity_key TEXT,locale TEXT,field TEXT,value TEXT);
          CREATE TABLE relations(import_id TEXT,relation TEXT,source_key TEXT,target_key TEXT,ordinal INTEGER,payload_json TEXT,source_path TEXT,source_record TEXT);
          """);
    }
    private SqliteConnection Open() { var db = new SqliteConnection($"Data Source={Database}"); db.Open(); return db; }
    private static void Entity(SqliteConnection db, string importId, string ns, string key, string json) => Execute(db, "INSERT INTO entities VALUES($i,$n,$k,$j)", ("$i", importId), ("$n", ns), ("$k", key), ("$j", json));
    private static void Localize(SqliteConnection db, string importId, string ns, string key, string field, string value) => Execute(db, "INSERT INTO localizations VALUES($i,$n,$k,'en',$f,$v)", ("$i", importId), ("$n", ns), ("$k", key), ("$f", field), ("$v", value));
    private static void Execute(SqliteConnection db, string sql, params (string, object)[] values) { using var command = db.CreateCommand(); command.CommandText = sql; foreach (var (name, value) in values) command.Parameters.AddWithValue(name, value); command.ExecuteNonQuery(); }

    protected override void Dispose(bool disposing) { base.Dispose(disposing); if (File.Exists(Database)) File.Delete(Database); if (Directory.Exists(UiIconRoot)) Directory.Delete(UiIconRoot, true); if (Directory.Exists(HeroIconRoot)) Directory.Delete(HeroIconRoot, true); }
}

public sealed record HeroSeed(string Id, string Name, string Class = "Ranger", string Tribe = "Human", string Element = "Fire",
    string DamageType = "Physical", string Mobility = "ground", string Rarity = "Epic", string Attribute = "Evade",
    string Classification = "collectible", string? Acquisition = "Test Chest");
