using System.Text.Json;
using Cta.Api.Configuration;
using Cta.Api.Data;

namespace Cta.Api.Features.Heroes;

public sealed class HeroRepository(SqliteConnectionFactory connections, ImportSelector imports, RepositoryPaths paths)
{
    private readonly HashSet<string> _portraitIds = Directory.Exists(paths.HeroIconRoot)
        ? Directory.EnumerateFiles(paths.HeroIconRoot, "*.png").Select(Path.GetFileNameWithoutExtension).Where(x => x is not null).Select(x => x!).ToHashSet(StringComparer.OrdinalIgnoreCase)
        : new(StringComparer.OrdinalIgnoreCase);

    public Task<string?> LatestImportAsync() => imports.LatestSuccessfulAsync();

    public async Task<List<HeroSummary>> LoadHeroesAsync(string importId)
    {
        await using var db = await connections.OpenAsync();
        var descriptions = await LocalizationMap(db, importId, "ability", "description");
        var parameters = await AbilityParameters(db, importId);
        var acquisitions = await Acquisitions(db, importId);
        await using var command = db.CreateCommand();
        command.CommandText = """
          SELECT h.entity_key, h.payload_json,
            (SELECT value FROM localizations l WHERE l.import_id=h.import_id AND l.namespace='hero' AND lower(l.entity_key)=lower(h.entity_key) AND l.locale='en' AND l.field='name' LIMIT 1),
            EXISTS(SELECT 1 FROM entities p WHERE p.import_id=h.import_id AND p.namespace='portrait' AND lower(p.entity_key)=lower(h.entity_key)),
            (SELECT payload_json FROM entities c WHERE c.import_id=h.import_id AND c.namespace='hero_classification' AND lower(c.entity_key)=lower(h.entity_key) LIMIT 1)
          FROM entities h WHERE h.import_id=$import AND h.namespace='hero'
          """;
        command.Parameters.AddWithValue("$import", importId);
        var result = new List<HeroSummary>();
        await using var rows = await command.ExecuteReaderAsync();
        while (await rows.ReadAsync()) result.Add(HeroMapper.Map(rows.GetString(0), rows.GetString(1), rows.IsDBNull(2) ? null : rows.GetString(2),
            rows.GetBoolean(3), rows.IsDBNull(4) ? null : rows.GetString(4), descriptions, parameters, acquisitions, _portraitIds));
        return result;
    }

    public async Task<List<SkillDto>> LoadSkillsAsync(string importId, string heroId)
    {
        await using var db = await connections.OpenAsync();
        var descriptions = await LocalizationMap(db, importId, "skill_description", "description");
        await using var command = db.CreateCommand();
        command.CommandText = """
          SELECT s.entity_key, s.payload_json,
            (SELECT value FROM localizations l WHERE l.import_id=s.import_id AND l.namespace='skill' AND l.entity_key=s.entity_key AND l.locale='en' AND l.field='name'),
            (SELECT value FROM localizations l WHERE l.import_id=s.import_id AND l.namespace='skill' AND l.entity_key=s.entity_key AND l.locale='en' AND l.field='description')
          FROM relations r JOIN entities s ON s.import_id=r.import_id AND s.namespace='skill' AND lower(s.entity_key)=lower(r.target_key)
          WHERE r.import_id=$import AND r.relation='character_skill' AND lower(r.source_key)=lower($hero) AND coalesce(json_extract(r.payload_json, '$.kind'), 'skill')='skill' ORDER BY r.ordinal
          """;
        command.Parameters.AddWithValue("$import", importId); command.Parameters.AddWithValue("$hero", heroId);
        var result = new List<SkillDto>();
        await using var rows = await command.ExecuteReaderAsync();
        while (await rows.ReadAsync())
        {
            using var json = JsonDocument.Parse(rows.GetString(1)); var root = json.RootElement;
            var canonical = HeroMapper.GetString(root, "canonical_name");
            var description = rows.IsDBNull(3) ? null : rows.GetString(3);
            if (description is null && root.TryGetProperty("components", out var parts))
            {
                var reference = HeroMapper.GetString(parts.EnumerateArray().FirstOrDefault(x => HeroMapper.GetString(x, "kind") == "info"), "text");
                description = reference?.StartsWith("SkDesc_", StringComparison.Ordinal) == true ? descriptions.GetValueOrDefault(reference[7..]) : reference;
            }
            result.Add(new(rows.GetString(0), rows.IsDBNull(2) ? canonical ?? HeroMapper.Humanize(rows.GetString(0)) : rows.GetString(2), description,
                HeroMapper.GetString(root, "type"), root.GetProperty("components").Clone(), root.GetProperty("attributes").Clone()));
        }
        return result;
    }

    private static async Task<Dictionary<string, string>> LocalizationMap(Microsoft.Data.Sqlite.SqliteConnection db, string importId, string ns, string field)
    {
        await using var command = db.CreateCommand();
        command.CommandText = "SELECT entity_key,value FROM localizations WHERE import_id=$import AND namespace=$namespace AND locale='en' AND field=$field";
        command.Parameters.AddWithValue("$import", importId); command.Parameters.AddWithValue("$namespace", ns); command.Parameters.AddWithValue("$field", field);
        var result = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        await using var rows = await command.ExecuteReaderAsync(); while (await rows.ReadAsync()) result[rows.GetString(0)] = rows.GetString(1);
        return result;
    }

    private static async Task<Dictionary<string, List<Dictionary<string, string>>>> AbilityParameters(Microsoft.Data.Sqlite.SqliteConnection db, string importId)
    {
        await using var command = db.CreateCommand(); command.CommandText = "SELECT r.source_key,s.payload_json FROM relations r JOIN entities s ON s.import_id=r.import_id AND s.namespace='skill' AND lower(s.entity_key)=lower(r.target_key) WHERE r.import_id=$import AND r.relation='character_skill' AND json_extract(r.payload_json,'$.kind')='ability'"; command.Parameters.AddWithValue("$import", importId);
        var result = new Dictionary<string, List<Dictionary<string, string>>>(StringComparer.OrdinalIgnoreCase);
        await using var rows = await command.ExecuteReaderAsync(); while (await rows.ReadAsync()) { using var json = JsonDocument.Parse(rows.GetString(1)); if (!result.TryGetValue(rows.GetString(0), out var effects)) result[rows.GetString(0)] = effects = []; foreach (var component in json.RootElement.GetProperty("components").EnumerateArray().Where(x => HeroMapper.GetString(x, "kind") == "effect")) effects.Add(component.GetProperty("attributes").EnumerateObject().ToDictionary(x => x.Name, x => x.Value.GetString() ?? "", StringComparer.OrdinalIgnoreCase)); }
        return result;
    }

    private static async Task<Dictionary<string, List<AcquisitionDto>>> Acquisitions(Microsoft.Data.Sqlite.SqliteConnection db, string importId)
    {
        await using var command = db.CreateCommand(); command.CommandText = "SELECT r.source_key,r.target_key,r.payload_json,coalesce(l.value,r.target_key) FROM relations r LEFT JOIN localizations l ON l.import_id=r.import_id AND l.namespace='acquisition_source' AND l.entity_key=r.target_key AND l.locale='en' AND l.field='name' WHERE r.import_id=$import AND r.relation='hero_acquisition'"; command.Parameters.AddWithValue("$import", importId);
        var result = new Dictionary<string, List<AcquisitionDto>>(StringComparer.OrdinalIgnoreCase);
        await using var rows = await command.ExecuteReaderAsync(); while (await rows.ReadAsync()) { using var json = JsonDocument.Parse(rows.GetString(2)); if (!result.TryGetValue(rows.GetString(0), out var sources)) result[rows.GetString(0)] = sources = []; sources.Add(new(rows.GetString(1), rows.GetString(3), "chest", HeroMapper.GetString(json.RootElement, "medal_id"), !json.RootElement.TryGetProperty("current", out var current) || current.ValueKind != JsonValueKind.False)); }
        return result;
    }
}
