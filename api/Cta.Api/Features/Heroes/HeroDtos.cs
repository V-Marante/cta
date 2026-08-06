using System.Text.Json;

namespace Cta.Api.Features.Heroes;

public sealed record TraitDto(string Code, string Name, string? Description);
public sealed record AcquisitionDto(string Id, string Name, string Kind, string? MedalId, bool Current);
public sealed record HeroSummary(string Id, string Name, string? Class, string? Tribe, string? Element, string? DamageType,
    string? Sex, string? Mobility, IReadOnlyList<TraitDto> Traits, string? PortraitUrl, JsonElement Stats,
    JsonElement Passive, JsonElement Progression, JsonElement Availability, IReadOnlyList<AcquisitionDto> Acquisition,
    string Classification, string? VariantOf, string? CanonicalName, JsonElement Raw);
public sealed record HeroPage(IEnumerable<HeroSummary> Items, int Total, int Page, int PageSize);
public sealed record HeroDetail(HeroSummary Hero, IEnumerable<SkillDto> Skills);
public sealed record SkillDto(string Id, string Name, string? Description, string? Type, JsonElement Components, JsonElement Raw);
public sealed record FilterOption(string Value, string Label);
public sealed record HeroFilters(IEnumerable<string> Classes, IEnumerable<string> Tribes, IEnumerable<string> Elements,
    IEnumerable<string> DamageTypes, IEnumerable<string> Rarities, IEnumerable<string> Mobilities,
    IEnumerable<string> Acquisitions, IEnumerable<FilterOption> Attributes);
