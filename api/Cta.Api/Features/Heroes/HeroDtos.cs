using System.Text.Json;

namespace Cta.Api.Features.Heroes;

public sealed record TraitDto(string Code, string Name, string? Description);
public sealed record AcquisitionDto(string Id, string Name, string Kind, string? MedalId, bool Current,
    string EvidenceType, string Status, string? SourcePath, string? SourceRecord);
public sealed record HeroSummary(string Id, string Name, string? Class, string? Tribe, string? Element, string? DamageType,
    string? Sex, string? Mobility, IReadOnlyList<TraitDto> Traits, string? PortraitUrl, JsonElement Stats, JsonElement StatSemantics,
    JsonElement SourceCalculations,
    JsonElement Passive, JsonElement Progression, JsonElement ProgressionSemantics, JsonElement Availability,
    JsonElement LegacyAvailability, IReadOnlyList<AcquisitionDto> Acquisition,
    string Classification, string? VariantOf, string? CanonicalName, JsonElement Raw);
public sealed record HeroPage(IEnumerable<HeroSummary> Items, int Total, int Page, int PageSize);
public sealed record HeroDetail(HeroSummary Hero, IEnumerable<SkillDto> Skills);
public sealed record SkillDto(string Id, string Name, string? Description, string? DescriptionTemplate,
    JsonElement DescriptionParameters, IReadOnlyList<string> UnresolvedPlaceholders,
    string? Type, JsonElement Components, JsonElement Raw);
public sealed record FilterOption(string Value, string Label);
public sealed record HeroFilters(IEnumerable<string> Classes, IEnumerable<string> Tribes, IEnumerable<string> Elements,
    IEnumerable<string> DamageTypes, IEnumerable<string> Rarities, IEnumerable<string> Mobilities,
    IEnumerable<string> Acquisitions, IEnumerable<FilterOption> Attributes);
public sealed record HealthResponse(string Status);
