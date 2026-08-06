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
        if (!heroAcquisition.Any(x => x.Current))
        {
            if (IsFlag(RawText("Dungeon"))) heroAcquisition.Add(new("Dungeon", "Dungeon", "game-mode", null, true));
            if (IsFlag(RawText("Shop"))) heroAcquisition.Add(new("Shop", "Shop", "shop", null, true));
            if (IsFlag(RawText("Event"))) heroAcquisition.Add(new("Event", "Event", "event", null, true));
            if (IsFlag(RawText("ChestEpic"))) heroAcquisition.Add(new("ChestHeroesEpic", "Epic Chest", "chest", null, true));
        }
        return new(id, localizedName ?? canonical ?? id, Text("class"), Text("tribe"), Text("element"), Text("damage_type"),
            Text("sex"), Text("mobility") ?? (IsFlag(RawText("Flying")) ? "flying" : "ground"), traitDtos,
            hasPortrait && portraitIds.Contains(id) ? $"/portraits/{Uri.EscapeDataString(id)}.png" : null,
            ObjectOrEmpty(root, "stats"), root.TryGetProperty("passive", out var passive) ? passive.Clone() : JsonSerializer.SerializeToElement(new { code = RawText("SP4"), target = RawText("SP4 Target"), source_value = Scalar(RawText("SP4 Value")) }),
            root.TryGetProperty("progression", out var progression) ? progression.Clone() : JsonSerializer.SerializeToElement(new { base_stars = Scalar(RawText("BaseStars")), max_stars = Scalar(RawText("MaxStars")), rarity = Scalar(RawText("Rarity")), rarity_name = RarityName(RawText("Rarity")), factor_per_star = Scalar(RawText("Factor per Star")) }),
            root.TryGetProperty("availability", out var availability) ? availability.Clone() : JsonSerializer.SerializeToElement(new { dungeon = Flag(RawText("Dungeon")), shop = Flag(RawText("Shop")), event_available = Flag(RawText("Event")), epic_chest = Flag(RawText("ChestEpic")) }),
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
}
