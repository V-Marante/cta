using System.Text.Json;
using Microsoft.Data.Sqlite;
using Microsoft.Extensions.FileProviders;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddCors(options => options.AddDefaultPolicy(policy =>
    policy.WithOrigins(builder.Configuration["WebOrigin"] ?? "http://localhost:5173").AllowAnyHeader().AllowAnyMethod()));
var app = builder.Build();
app.UseCors();

var repositoryRoot = FindRepositoryRoot(builder.Environment.ContentRootPath);
var database = ResolvePath(builder.Configuration["Database"] ?? "extracted/cta.sqlite", repositoryRoot);
if (!File.Exists(database))
    throw new FileNotFoundException($"Importer database not found at '{database}'. Run the importer first or set Database to an existing SQLite file.", database);

var portraitSetting = builder.Configuration["HeroIconRoot"] ?? "generated/hero-icons";
var portraits = ResolvePath(portraitSetting, repositoryRoot);

var portraitIds = Directory.Exists(portraits)
    ? Directory.EnumerateFiles(portraits, "*.png").Select(path => Path.GetFileNameWithoutExtension(path)!).ToHashSet(StringComparer.OrdinalIgnoreCase)
    : new HashSet<string>(StringComparer.OrdinalIgnoreCase);
if (Directory.Exists(portraits))
    app.UseStaticFiles(new StaticFileOptions { FileProvider = new PhysicalFileProvider(portraits), RequestPath = "/portraits" });
if (portraitIds.Count > 0)
    app.Logger.LogInformation("Loaded {Count} hero portraits from {PortraitRoot}", portraitIds.Count, portraits);
else
    app.Logger.LogInformation("No small hero icons found at {PortraitRoot}; hero names will be used instead.", portraits);

app.MapGet("/api/heroes", async (string? search, string? @class, string? tribe, string? element,
    string? damageType, string? rarity, string? mobility, string? acquisition, string? attribute,
    string? classification, bool includeNonCollectible = false, int page = 1, int pageSize = 48) =>
{
    page = Math.Max(page, 1);
    pageSize = Math.Clamp(pageSize, 1, 250);
    await using var db = Open(database);
    var importId = await LatestImport(db);
    if (importId is null) return Results.Ok(new HeroPage([], 0, page, pageSize));
    var heroes = await LoadHeroes(db, importId, portraitIds);
    var filtered = heroes.Where(hero =>
        (includeNonCollectible || hero.Classification == "collectible") && Match(hero.Classification, classification) &&
        Match(hero.Class, @class) && Match(hero.Tribe, tribe) && Match(hero.Element, element) &&
        Match(hero.DamageType, damageType) && Match(hero.Mobility, mobility) && Match(JsonText(hero.Progression, "rarity_name"), rarity) &&
        (string.IsNullOrWhiteSpace(acquisition) || hero.Acquisition.Any(x => x.Current && (Match(x.Id, acquisition) || Match(x.Name, acquisition)))) &&
        (string.IsNullOrWhiteSpace(attribute) || hero.Traits.Any(x => Match(x.Code, attribute))) &&
        (string.IsNullOrWhiteSpace(search) ||
        hero.Name.Contains(search, StringComparison.OrdinalIgnoreCase) || hero.Id.Contains(search, StringComparison.OrdinalIgnoreCase)))
        .OrderBy(hero => hero.Name).ToList();
    return Results.Ok(new HeroPage(filtered.Skip((page - 1) * pageSize).Take(pageSize), filtered.Count, page, pageSize));
});

app.MapGet("/api/heroes/filters", async () =>
{
    await using var db = Open(database);
    var importId = await LatestImport(db);
    var heroes = importId is null ? [] : await LoadHeroes(db, importId, portraitIds);
    return Results.Ok(new {
        classes = Values(heroes.Select(x => x.Class)), tribes = Values(heroes.Select(x => x.Tribe)),
        elements = Values(heroes.Select(x => x.Element)), damageTypes = Values(heroes.Select(x => x.DamageType)),
        rarities = Values(heroes.Select(x => JsonText(x.Progression, "rarity_name"))),
        mobilities = Values(heroes.Select(x => x.Mobility)),
        acquisitions = Values(heroes.SelectMany(x => x.Acquisition.Where(a => a.Current).Select(a => a.Name))),
        attributes = heroes.SelectMany(x => x.Traits).GroupBy(x => x.Code).Select(x => new { value = x.Key, label = x.First().Name }).OrderBy(x => x.label),
        classifications = Values(heroes.Select(x => x.Classification))
    });
});

app.MapGet("/api/heroes/{id}", async (string id) =>
{
    await using var db = Open(database);
    var importId = await LatestImport(db);
    if (importId is null) return Results.NotFound();
    var hero = (await LoadHeroes(db, importId, portraitIds)).FirstOrDefault(x => x.Id.Equals(id, StringComparison.OrdinalIgnoreCase));
    if (hero is null) return Results.NotFound();
    var skills = await LoadSkills(db, importId, hero.Id);
    return Results.Ok(new HeroDetail(hero, skills));
});

app.MapGet("/api/heroes/{id}/skills", async (string id) =>
{
    await using var db = Open(database);
    var importId = await LatestImport(db);
    return importId is null ? Results.NotFound() : Results.Ok(await LoadSkills(db, importId, id));
});

app.MapGet("/health", () => Results.Ok(new { status = "ok" }));
app.Run();

static SqliteConnection Open(string path)
{
    var db = new SqliteConnection($"Data Source={path};Mode=ReadOnly");
    db.Open();
    return db;
}

static string ResolvePath(string path, string repositoryRoot) =>
    Path.GetFullPath(Path.IsPathRooted(path) ? path : Path.Combine(repositoryRoot, path));

static string FindRepositoryRoot(string start)
{
    for (var directory = new DirectoryInfo(start); directory is not null; directory = directory.Parent)
        if (File.Exists(Path.Combine(directory.FullName, "pyproject.toml")))
            return directory.FullName;
    return Directory.GetCurrentDirectory();
}

static async Task<string?> LatestImport(SqliteConnection db)
{
    await using var cmd = db.CreateCommand();
    cmd.CommandText = "SELECT id FROM import_runs WHERE status='succeeded' ORDER BY finished_at DESC LIMIT 1";
    return await cmd.ExecuteScalarAsync() as string;
}

static async Task<List<HeroSummary>> LoadHeroes(SqliteConnection db, string importId, HashSet<string> portraitIds)
{
    var abilityDescriptions = await LoadLocalizationMap(db, importId, "ability", "description");
    var abilityParameters = await LoadAbilityParameters(db, importId);
    var acquisitions = await LoadAcquisitions(db, importId);
    await using var cmd = db.CreateCommand();
    cmd.CommandText = """
      SELECT h.entity_key, h.payload_json,
        (SELECT value FROM localizations l WHERE l.import_id=h.import_id AND l.namespace='hero'
          AND lower(l.entity_key)=lower(h.entity_key) AND l.locale='en' AND l.field='name' LIMIT 1) localized_name,
        EXISTS(SELECT 1 FROM entities p WHERE p.import_id=h.import_id AND p.namespace='portrait'
          AND lower(p.entity_key)=lower(h.entity_key)) has_portrait,
        (SELECT payload_json FROM entities c WHERE c.import_id=h.import_id AND c.namespace='hero_classification'
          AND lower(c.entity_key)=lower(h.entity_key) LIMIT 1) classification_json
      FROM entities h WHERE h.import_id=$import AND h.namespace='hero'
      """;
    cmd.Parameters.AddWithValue("$import", importId);
    var result = new List<HeroSummary>();
    await using var rows = await cmd.ExecuteReaderAsync();
    while (await rows.ReadAsync())
    {
        using var json = JsonDocument.Parse(rows.GetString(1));
        var root = json.RootElement;
        string? Text(string name) => root.TryGetProperty(name, out var value) && value.ValueKind == JsonValueKind.String ? value.GetString() : null;
        var raw = ObjectOrEmpty(root, "raw");
        string? RawText(string name) => raw.TryGetProperty(name, out var value) && value.ValueKind == JsonValueKind.String && !string.IsNullOrWhiteSpace(value.GetString()) ? value.GetString()!.Trim() : null;
        var id = rows.GetString(0);
        var canonical = Text("canonical_name");
        var name = rows.IsDBNull(2) ? canonical ?? id : rows.GetString(2);
        using var classificationDocument = JsonDocument.Parse(rows.IsDBNull(4) ? "{}" : rows.GetString(4));
        var classificationRoot = classificationDocument.RootElement;
        var classificationKind = GetPropertyOrNull(classificationRoot, "kind") ?? "collectible";
        var ownerId = GetPropertyOrNull(classificationRoot, "owner_id");
        var traits = root.TryGetProperty("traits", out var traitValues)
            ? traitValues.EnumerateArray().Select(x => x.GetString()!).Where(x => x is not null)
                .Select(code => new TraitDto(code, Humanize(code), FormatTraitDescription(code, abilityDescriptions.GetValueOrDefault(code), abilityParameters.GetValueOrDefault(id)))).ToArray()
            : new[] { RawText("Ability1"), RawText("Ability2"), RawText("Ability3") }.Where(x => x is not null)
                .Select(code => new TraitDto(code!, Humanize(code!), FormatTraitDescription(code!, abilityDescriptions.GetValueOrDefault(code!), abilityParameters.GetValueOrDefault(id)))).ToArray();
        var mobility = Text("mobility") ?? (IsSourceFlag(RawText("Flying")) ? "flying" : "ground");
        var passive = root.TryGetProperty("passive", out var passiveValue) ? passiveValue.Clone() : JsonSerializer.SerializeToElement(new {
            code = RawText("SP4"), target = RawText("SP4 Target"), source_value = SourceScalar(RawText("SP4 Value"))
        });
        var progression = root.TryGetProperty("progression", out var progressionValue) ? progressionValue.Clone() : JsonSerializer.SerializeToElement(new {
            base_stars = SourceScalar(RawText("BaseStars")), max_stars = SourceScalar(RawText("MaxStars")),
            rarity = SourceScalar(RawText("Rarity")), rarity_name = RarityName(RawText("Rarity")), factor_per_star = SourceScalar(RawText("Factor per Star"))
        });
        var availability = root.TryGetProperty("availability", out var availabilityValue) ? availabilityValue.Clone() : JsonSerializer.SerializeToElement(new {
            dungeon = SourceFlag(RawText("Dungeon")), shop = SourceFlag(RawText("Shop")),
            event_available = SourceFlag(RawText("Event")), epic_chest = SourceFlag(RawText("ChestEpic"))
        });
        var heroAcquisition = acquisitions.GetValueOrDefault(id) ?? [];
        if (!heroAcquisition.Any(source => source.Current))
        {
            if (IsSourceFlag(RawText("Dungeon"))) heroAcquisition.Add(new("Dungeon", "Dungeon", "game-mode", null, true));
            if (IsSourceFlag(RawText("Shop"))) heroAcquisition.Add(new("Shop", "Shop", "shop", null, true));
            if (IsSourceFlag(RawText("Event"))) heroAcquisition.Add(new("Event", "Event", "event", null, true));
            if (IsSourceFlag(RawText("ChestEpic"))) heroAcquisition.Add(new("ChestHeroesEpic", "Epic Chest", "chest", null, true));
        }
        result.Add(new HeroSummary(id, name, Text("class"), Text("tribe"), Text("element"), Text("damage_type"),
            Text("sex"), mobility, traits,
            rows.GetBoolean(3) && portraitIds.Contains(id) ? $"/portraits/{Uri.EscapeDataString(id)}.png" : null,
            ObjectOrEmpty(root, "stats"), passive, progression, availability,
            heroAcquisition, classificationKind, ownerId, canonical, raw));
    }
    return result;
}

static async Task<Dictionary<string, List<Dictionary<string, string>>>> LoadAbilityParameters(SqliteConnection db, string importId)
{
    await using var cmd = db.CreateCommand();
    cmd.CommandText = """
      SELECT r.source_key, s.payload_json FROM relations r
      JOIN entities s ON s.import_id=r.import_id AND s.namespace='skill' AND lower(s.entity_key)=lower(r.target_key)
      WHERE r.import_id=$import AND r.relation='character_skill' AND json_extract(r.payload_json, '$.kind')='ability'
      """;
    cmd.Parameters.AddWithValue("$import", importId);
    var result = new Dictionary<string, List<Dictionary<string, string>>>(StringComparer.OrdinalIgnoreCase);
    await using var rows = await cmd.ExecuteReaderAsync();
    while (await rows.ReadAsync())
    {
        using var json = JsonDocument.Parse(rows.GetString(1));
        if (!result.TryGetValue(rows.GetString(0), out var effects)) result[rows.GetString(0)] = effects = [];
        foreach (var component in json.RootElement.GetProperty("components").EnumerateArray().Where(x => x.GetProperty("kind").GetString() == "effect"))
            effects.Add(component.GetProperty("attributes").EnumerateObject().ToDictionary(x => x.Name, x => x.Value.GetString() ?? "", StringComparer.OrdinalIgnoreCase));
    }
    return result;
}

static async Task<Dictionary<string, List<AcquisitionDto>>> LoadAcquisitions(SqliteConnection db, string importId)
{
    await using var cmd = db.CreateCommand();
    cmd.CommandText = """
      SELECT r.source_key, r.target_key, r.payload_json, coalesce(l.value, r.target_key)
      FROM relations r LEFT JOIN localizations l ON l.import_id=r.import_id AND l.namespace='acquisition_source'
        AND l.entity_key=r.target_key AND l.locale='en' AND l.field='name'
      WHERE r.import_id=$import AND r.relation='hero_acquisition'
      """;
    cmd.Parameters.AddWithValue("$import", importId);
    var result = new Dictionary<string, List<AcquisitionDto>>(StringComparer.OrdinalIgnoreCase);
    await using var rows = await cmd.ExecuteReaderAsync();
    while (await rows.ReadAsync())
    {
        using var json = JsonDocument.Parse(rows.GetString(2)); var payload = json.RootElement;
        if (!result.TryGetValue(rows.GetString(0), out var sources)) result[rows.GetString(0)] = sources = [];
        sources.Add(new(rows.GetString(1), rows.GetString(3), "chest", GetPropertyOrNull(payload, "medal_id"),
            !payload.TryGetProperty("current", out var current) || current.ValueKind != JsonValueKind.False));
    }
    return result;
}

static string? FormatTraitDescription(string code, string? description, List<Dictionary<string, string>>? effects)
{
    if (description is null || effects is null) return description;
    var effect = effects.FirstOrDefault(x => x.TryGetValue("type", out var type) &&
        (code.Equals(type, StringComparison.OrdinalIgnoreCase) || code.StartsWith(type, StringComparison.OrdinalIgnoreCase)));
    if (effect is null) return description;
    foreach (var key in new[] { "value", "chance", "duration" })
        if (effect.TryGetValue(key, out var raw)) description = description.Replace($"{{{key}}}", PercentParameter(raw));
    return description;
}

static string PercentParameter(string value) => double.TryParse(value, System.Globalization.CultureInfo.InvariantCulture, out var number) && number is >= 0 and <= 1
    ? (number * 100).ToString("0.##", System.Globalization.CultureInfo.InvariantCulture) : value;

static string? RarityName(string? value) => value switch { "1" => "Common", "2" => "Rare", "3" => "Epic", "4" => "Legendary", _ => null };

static async Task<List<SkillDto>> LoadSkills(SqliteConnection db, string importId, string heroId)
{
    var descriptions = await LoadLocalizationMap(db, importId, "skill_description", "description");
    await using var cmd = db.CreateCommand();
    cmd.CommandText = """
      SELECT s.entity_key, s.payload_json,
        (SELECT value FROM localizations l WHERE l.import_id=s.import_id AND l.namespace='skill' AND l.entity_key=s.entity_key AND l.locale='en' AND l.field='name') name,
        (SELECT value FROM localizations l WHERE l.import_id=s.import_id AND l.namespace='skill' AND l.entity_key=s.entity_key AND l.locale='en' AND l.field='description') description
      FROM relations r JOIN entities s ON s.import_id=r.import_id AND s.namespace='skill' AND lower(s.entity_key)=lower(r.target_key)
      WHERE r.import_id=$import AND r.relation='character_skill' AND lower(r.source_key)=lower($hero)
        AND coalesce(json_extract(r.payload_json, '$.kind'), 'skill')='skill'
      ORDER BY r.ordinal
      """;
    cmd.Parameters.AddWithValue("$import", importId); cmd.Parameters.AddWithValue("$hero", heroId);
    var result = new List<SkillDto>();
    await using var rows = await cmd.ExecuteReaderAsync();
    while (await rows.ReadAsync())
    {
        using var json = JsonDocument.Parse(rows.GetString(1)); var root = json.RootElement;
        var canonical = root.TryGetProperty("canonical_name", out var n) && n.ValueKind == JsonValueKind.String ? n.GetString() : null;
        var description = rows.IsDBNull(3) ? null : rows.GetString(3);
        if (description is null && root.TryGetProperty("components", out var parts))
        {
            var reference = GetPropertyOrNull(parts.EnumerateArray().FirstOrDefault(x => x.GetProperty("kind").GetString() == "info"), "text");
            if (reference is not null && reference.StartsWith("SkDesc_", StringComparison.Ordinal))
                description = descriptions.GetValueOrDefault(reference[7..]);
            else if (!string.IsNullOrWhiteSpace(reference))
                description = reference;
        }
        result.Add(new(rows.GetString(0), rows.IsDBNull(2) ? canonical ?? Humanize(rows.GetString(0)) : rows.GetString(2),
            description, root.TryGetProperty("type", out var t) ? t.GetString() : null,
            root.GetProperty("components").Clone(), root.GetProperty("attributes").Clone()));
    }
    return result;
}

static async Task<Dictionary<string, string>> LoadLocalizationMap(SqliteConnection db, string importId, string namespaceName, string field)
{
    await using var cmd = db.CreateCommand();
    cmd.CommandText = "SELECT entity_key, value FROM localizations WHERE import_id=$import AND namespace=$namespace AND locale='en' AND field=$field";
    cmd.Parameters.AddWithValue("$import", importId); cmd.Parameters.AddWithValue("$namespace", namespaceName); cmd.Parameters.AddWithValue("$field", field);
    var result = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
    await using var rows = await cmd.ExecuteReaderAsync();
    while (await rows.ReadAsync()) result[rows.GetString(0)] = rows.GetString(1);
    return result;
}

static string? GetPropertyOrNull(JsonElement element, string name) =>
    element.ValueKind == JsonValueKind.Object && element.TryGetProperty(name, out var value) && value.ValueKind == JsonValueKind.String ? value.GetString() : null;

static JsonElement ObjectOrEmpty(JsonElement element, string name) =>
    element.TryGetProperty(name, out var value) && value.ValueKind == JsonValueKind.Object ? value.Clone() : JsonSerializer.SerializeToElement(new { });

static bool IsSourceFlag(string? value) => value?.ToLowerInvariant() is "1" or "x" or "true" or "yes";
static bool? SourceFlag(string? value) => value is null ? null : IsSourceFlag(value);
static object? SourceScalar(string? value) => value is null ? null : long.TryParse(value, out var integer) ? integer : double.TryParse(value, out var number) ? number : value;

static string Humanize(string value) => System.Text.RegularExpressions.Regex.Replace(value, "([a-z])([A-Z])", "$1 $2");

static bool Match(string? value, string? filter) => string.IsNullOrWhiteSpace(filter) || string.Equals(value, filter, StringComparison.OrdinalIgnoreCase);
static string? JsonText(JsonElement element, string name) => GetPropertyOrNull(element, name);
static IEnumerable<string> Values(IEnumerable<string?> values) => values.Where(x => !string.IsNullOrWhiteSpace(x)).Select(x => x!).Distinct(StringComparer.OrdinalIgnoreCase).Order();

record HeroSummary(string Id, string Name, string? Class, string? Tribe, string? Element, string? DamageType,
    string? Sex, string? Mobility, IEnumerable<TraitDto> Traits, string? PortraitUrl, JsonElement Stats,
    JsonElement Passive, JsonElement Progression, JsonElement Availability, IEnumerable<AcquisitionDto> Acquisition,
    string Classification, string? VariantOf, string? CanonicalName, JsonElement Raw);
record TraitDto(string Code, string Name, string? Description);
record AcquisitionDto(string Id, string Name, string Kind, string? MedalId, bool Current);
record HeroPage(IEnumerable<HeroSummary> Items, int Total, int Page, int PageSize);
record HeroDetail(HeroSummary Hero, IEnumerable<SkillDto> Skills);
record SkillDto(string Id, string Name, string? Description, string? Type, JsonElement Components, JsonElement Raw);

public partial class Program { }
