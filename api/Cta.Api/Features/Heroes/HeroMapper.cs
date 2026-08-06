using System.Globalization;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace Cta.Api.Features.Heroes;

public static class HeroMapper
{
    public static HeroSummary Map(string id, string payloadJson, string? localizedName, bool hasPortrait,
        string? classificationJson, IReadOnlyDictionary<string, string> descriptions,
        IReadOnlyDictionary<string, List<Dictionary<string, string>>> parameters,
        IReadOnlyDictionary<string, List<AcquisitionDto>> acquisitions, ISet<string> portraitIds)
    {
        using var json = JsonDocument.Parse(payloadJson); var root = json.RootElement;
        string? Text(string name) => GetString(root, name);
        var raw = ObjectOrEmpty(root, "raw");
        string? RawText(string name) => GetString(raw, name)?.Trim() is { Length: > 0 } value ? value : null;
        var canonical = Text("canonical_name");
        using var classification = JsonDocument.Parse(classificationJson ?? "{}");
        var traits = root.TryGetProperty("traits", out var values)
            ? values.EnumerateArray().Select(x => x.GetString()).Where(x => x is not null).Select(x => x!).ToArray()
            : new[] { RawText("Ability1"), RawText("Ability2"), RawText("Ability3") }.Where(x => x is not null).Select(x => x!).ToArray();
        var traitDtos = traits.Select(code => new TraitDto(code, Humanize(code),
            FormatDescription(code, descriptions.GetValueOrDefault(code), parameters.GetValueOrDefault(id)))).ToArray();
        var heroAcquisition = acquisitions.GetValueOrDefault(id)?.ToList() ?? [];
        return new(id, localizedName ?? canonical ?? id, Text("class"), Text("tribe"), Text("element"), Text("damage_type"),
            Text("sex"), Text("mobility") ?? (IsFlag(RawText("Flying")) ? "flying" : "ground"), traitDtos,
            hasPortrait && portraitIds.Contains(id) ? $"/portraits/{Uri.EscapeDataString(id)}.png" : null,
            ObjectOrEmpty(root, "stats"), ObjectOrEmpty(root, "stat_semantics"), ObjectOrEmpty(root, "source_calculations"),
            root.TryGetProperty("passive", out var passive) ? passive.Clone() : JsonSerializer.SerializeToElement(new { code = RawText("SP4"), target = RawText("SP4 Target"), source_value = Scalar(RawText("SP4 Value")) }),
            root.TryGetProperty("progression", out var progression) ? progression.Clone() : JsonSerializer.SerializeToElement(new { base_stars = Scalar(RawText("BaseStars")), max_stars = Scalar(RawText("MaxStars")), rarity = Scalar(RawText("Rarity")), rarity_name = RarityName(RawText("Rarity")), factor_per_star = Scalar(RawText("Factor per Star")) }),
            root.TryGetProperty("progression_semantics", out var progressionSemantics) ? progressionSemantics.Clone() : ProgressionSemantics(RawText),
            root.TryGetProperty("availability", out var availability) ? availability.Clone() : JsonSerializer.SerializeToElement(new { dungeon = Flag(RawText("Dungeon")), shop = Flag(RawText("Shop")), event_available = Flag(RawText("Event")), epic_chest = Flag(RawText("ChestEpic")) }),
            root.TryGetProperty("legacy_availability", out var legacyAvailability) ? legacyAvailability.Clone() : LegacyAvailability(RawText),
            heroAcquisition, GetString(classification.RootElement, "kind") ?? "collectible",
            GetString(classification.RootElement, "owner_id"), canonical, raw);
    }

    public static string? GetString(JsonElement element, string name) => element.ValueKind == JsonValueKind.Object &&
        element.TryGetProperty(name, out var value) && value.ValueKind == JsonValueKind.String ? value.GetString() : null;
    public static JsonElement ObjectOrEmpty(JsonElement element, string name) => element.TryGetProperty(name, out var value) &&
        value.ValueKind == JsonValueKind.Object ? value.Clone() : JsonSerializer.SerializeToElement(new { });
    public static string Humanize(string value) => Regex.Replace(value, "([a-z])([A-Z])", "$1 $2");

    private static string? FormatDescription(string code, string? description, List<Dictionary<string, string>>? effects)
    {
        var effect = effects?.FirstOrDefault(x => x.TryGetValue("type", out var type) &&
            (code.Equals(type, StringComparison.OrdinalIgnoreCase) || code.StartsWith(type, StringComparison.OrdinalIgnoreCase)));
        if (description is null || effect is null) return description;
        foreach (var key in new[] { "value", "chance", "duration" })
            if (effect.TryGetValue(key, out var raw)) description = description.Replace($"{{{key}}}", Percent(raw));
        return description;
    }
    private static string Percent(string value) => double.TryParse(value, CultureInfo.InvariantCulture, out var number) && number is >= 0 and <= 1 ? (number * 100).ToString("0.##", CultureInfo.InvariantCulture) : value;
    private static bool IsFlag(string? value) => value?.ToLowerInvariant() is "1" or "x" or "true" or "yes";
    private static bool? Flag(string? value) => value is null ? null : IsFlag(value);
    private static object? Scalar(string? value) => value is null ? null : long.TryParse(value, out var integer) ? integer : double.TryParse(value, CultureInfo.InvariantCulture, out var number) ? number : value;
    private static string? RarityName(string? value) => value switch { "1" => "Common", "2" => "Rare", "3" => "Epic", "4" => "Legendary", _ => null };
    private static JsonElement ProgressionSemantics(Func<string, string?> raw)
    {
        var maximum = raw("MaxStars"); var rarity = raw("Rarity"); var rarityName = RarityName(rarity);
        return JsonSerializer.SerializeToElement(new
        {
            base_stars = new { value = Scalar(raw("BaseStars")), status = "unresolved", source_field = "BaseStars", meaning = (string?)null },
            max_stars = new { value = Scalar(maximum), status = maximum == "8" ? "strongly_supported" : "unresolved", source_field = "MaxStars", meaning = maximum == "8" ? "hero_evolution_cap" : null },
            rarity = new { value = Scalar(rarity), status = rarityName is null ? "unresolved" : "source_defined", source_field = "Rarity", meaning = rarityName is null ? null : "hero_rarity_tier", name = rarityName },
        });
    }
    private static JsonElement LegacyAvailability(Func<string, string?> raw) => JsonSerializer.SerializeToElement(new
    {
        dungeon = Legacy(raw("Dungeon"), "Dungeon"), shop = Legacy(raw("Shop"), "Shop"),
        @event = Legacy(raw("Event"), "Event"), epic_chest = Legacy(raw("ChestEpic"), "ChestEpic")
    });
    private static object Legacy(string? raw, string field) => new { value = Flag(raw), status = "legacy_unverified", source_field = field, source_path = "Heroes.csv" };
}
