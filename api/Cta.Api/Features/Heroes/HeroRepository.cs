using System.Text.Json;
using System.Text.RegularExpressions;
using System.Collections.Concurrent;
using Cta.Api.Configuration;
using Cta.Api.Data;

namespace Cta.Api.Features.Heroes;

public sealed class HeroRepository(SqliteConnectionFactory connections, ImportSelector imports, RepositoryPaths paths)
{
    private readonly ConcurrentDictionary<string, Lazy<Task<IReadOnlyList<HeroSummary>>>> _heroes = new(StringComparer.Ordinal);
    private readonly ConcurrentDictionary<(string ImportId, string HeroId), Lazy<Task<IReadOnlyList<SkillDto>>>> _skills = new();
    private readonly HashSet<string> _portraitIds = Directory.Exists(paths.HeroIconRoot)
        ? Directory.EnumerateFiles(paths.HeroIconRoot, "*.png").Select(Path.GetFileNameWithoutExtension).Where(x => x is not null).Select(x => x!).ToHashSet(StringComparer.OrdinalIgnoreCase)
        : new(StringComparer.OrdinalIgnoreCase);

    public Task<string?> LatestImportAsync() => imports.LatestSuccessfulAsync();

    public Task<IReadOnlyList<HeroSummary>> LoadHeroesAsync(string importId) =>
        _heroes.GetOrAdd(importId, key => new(() => ReadHeroesAsync(key), LazyThreadSafetyMode.ExecutionAndPublication)).Value;

    private async Task<IReadOnlyList<HeroSummary>> ReadHeroesAsync(string importId)
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

    public Task<IReadOnlyList<SkillDto>> LoadSkillsAsync(string importId, string heroId) =>
        _skills.GetOrAdd((importId, heroId.ToUpperInvariant()), key =>
            new(() => ReadSkillsAsync(key.ImportId, heroId), LazyThreadSafetyMode.ExecutionAndPublication)).Value;

    private async Task<IReadOnlyList<SkillDto>> ReadSkillsAsync(string importId, string heroId)
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
            var resolved = ResolveDescription(description, root.GetProperty("components"));
            result.Add(new(rows.GetString(0), rows.IsDBNull(2) ? canonical ?? HeroMapper.Humanize(rows.GetString(0)) : rows.GetString(2), resolved.Text,
                description, JsonSerializer.SerializeToElement(resolved.Parameters), resolved.Unresolved,
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
        await using var command = db.CreateCommand(); command.CommandText = """
          SELECT r.source_key,r.target_key,r.payload_json,
            coalesce(l.value,json_extract(a.payload_json,'$.name'),r.target_key),
            coalesce(json_extract(a.payload_json,'$.kind'),'chest'), r.source_path, r.source_record
          FROM relations r
          LEFT JOIN localizations l ON l.import_id=r.import_id AND l.namespace='acquisition_source' AND l.entity_key=r.target_key AND l.locale='en' AND l.field='name'
          LEFT JOIN entities a ON a.import_id=r.import_id AND a.namespace='acquisition_source' AND a.entity_key=r.target_key
          WHERE r.import_id=$import AND r.relation='hero_acquisition'
          """; command.Parameters.AddWithValue("$import", importId);
        var result = new Dictionary<string, List<AcquisitionDto>>(StringComparer.OrdinalIgnoreCase);
        await using var rows = await command.ExecuteReaderAsync(); while (await rows.ReadAsync()) { using var json = JsonDocument.Parse(rows.GetString(2)); if (!result.TryGetValue(rows.GetString(0), out var sources)) result[rows.GetString(0)] = sources = []; var currentValue = !json.RootElement.TryGetProperty("current", out var current) || current.ValueKind != JsonValueKind.False; sources.Add(new(rows.GetString(1), rows.GetString(3), rows.GetString(4), HeroMapper.GetString(json.RootElement, "medal_id"), currentValue, HeroMapper.GetString(json.RootElement, "evidence_type") ?? "explicit_configuration", HeroMapper.GetString(json.RootElement, "status") ?? (currentValue ? "current" : "historical"), HeroMapper.GetString(json.RootElement, "source_path") ?? (rows.IsDBNull(5) ? null : rows.GetString(5)), HeroMapper.GetString(json.RootElement, "source_record") ?? (rows.IsDBNull(6) ? null : rows.GetString(6)))); }
        return result;
    }

    private static DescriptionResolution ResolveDescription(string? template, JsonElement components)
    {
        if (template is null) return new(null, new(), []);
        var parts = components.EnumerateArray().ToArray();
        string? Attribute(string kind, string name) => parts.Where(x => HeroMapper.GetString(x, "kind") == kind)
            .Select(x => x.TryGetProperty("attributes", out var attributes) ? HeroMapper.GetString(attributes, name) : null)
            .FirstOrDefault(x => x is not null);
        string? Effect(string type, string name) => parts.Where(x => HeroMapper.GetString(x, "kind") == "effect")
            .Where(x => x.TryGetProperty("attributes", out var attributes) && HeroMapper.GetString(attributes, "type") == type)
            .Select(x => HeroMapper.GetString(x.GetProperty("attributes"), name)).FirstOrDefault(x => x is not null);
        var values = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        void Add(string key, string? value, string? suffix = null) { if (value is not null) values[key] = value + suffix; }
        var durationCandidates = new[] { Attribute("effect", "duration"), Attribute("spec", "time"), Attribute("spec", "effectDuration") }
            .Where(x => x is not null).Distinct().ToArray();
        if (durationCandidates.Length == 1) Add("duration", durationCandidates[0], " seconds");
        Add("durationEffect", Attribute("effect", "duration"), " seconds");
        Add("chance", Percentage(Attribute("spec", "chance")));
        Add("hpPercent", Percentage(Attribute("spec", "hpPercent")));
        Add("healthRegen", Percentage(Effect("healthRegen", "value")));
        Add("dodge", Effect("dodge", "value"));
        Add("numProjectiles", Attribute("spec", "count"));
        var hitCount = parts.Count(x => HeroMapper.GetString(x, "kind") == "hit"); if (hitCount > 0) values["hits"] = hitCount.ToString();
        var effectType = Attribute("effect", "type"); if (effectType is not null && effectType != "random") values["effect"] = HeroMapper.Humanize(effectType);
        var effectValue = Attribute("spec", "effectValue");
        if (effectValue is not null && double.TryParse(effectValue, System.Globalization.CultureInfo.InvariantCulture, out var effectNumber) && effectNumber is >= 0 and <= 1)
            values["effectValue"] = (effectNumber * 100).ToString("0.##", System.Globalization.CultureInfo.InvariantCulture);
        var placeholders = Regex.Matches(template, "\\{([A-Za-z][A-Za-z0-9]*)\\}").Select(x => x.Groups[1].Value).Distinct(StringComparer.OrdinalIgnoreCase).ToArray();
        foreach (var key in values.Keys.Where(key => !placeholders.Contains(key, StringComparer.OrdinalIgnoreCase)).ToArray()) values.Remove(key);
        var text = template; foreach (var (key, value) in values) text = text.Replace($"{{{key}}}", value, StringComparison.OrdinalIgnoreCase);
        return new(text, values, placeholders.Where(x => !values.ContainsKey(x) && !x.Equals("element", StringComparison.OrdinalIgnoreCase)).ToArray());
    }

    private static string? Percentage(string? raw) => double.TryParse(raw, System.Globalization.CultureInfo.InvariantCulture, out var value)
        ? (value * 100).ToString("0.##", System.Globalization.CultureInfo.InvariantCulture) : null;
    private sealed record DescriptionResolution(string? Text, Dictionary<string, string> Parameters, IReadOnlyList<string> Unresolved);
}
