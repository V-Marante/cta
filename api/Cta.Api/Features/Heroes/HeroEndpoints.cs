using System.Text.Json;

namespace Cta.Api.Features.Heroes;

public static class HeroEndpoints
{
    public static IEndpointRouteBuilder MapHeroEndpoints(this IEndpointRouteBuilder app)
    {
        app.MapGet("/api/heroes", List).WithName("ListHeroes").Produces<HeroPage>();
        app.MapGet("/api/heroes/filters", Filters).WithName("GetHeroFilters").Produces<HeroFilters>();
        app.MapGet("/api/heroes/{id}", Detail).WithName("GetHero").Produces<HeroDetail>().Produces(StatusCodes.Status404NotFound);
        app.MapGet("/api/heroes/{id}/skills", Skills).WithName("GetHeroSkills").Produces<IReadOnlyList<SkillDto>>().Produces(StatusCodes.Status404NotFound);
        return app;
    }

    private static async Task<IResult> List(HeroRepository repository, string? search, string? @class, string? tribe,
        string? element, string? damageType, string? rarity, string? mobility, string? acquisition, string? attribute,
        int page = 1, int pageSize = 48)
    {
        page = Math.Max(page, 1); pageSize = Math.Clamp(pageSize, 1, 250);
        var importId = await repository.LatestImportAsync();
        if (importId is null) return Results.Ok(new HeroPage([], 0, page, pageSize));
        var filtered = (await repository.LoadHeroesAsync(importId)).Where(hero =>
            hero.Classification == "collectible" &&
            Match(hero.Class, @class) && Match(hero.Tribe, tribe) && Match(hero.Element, element) && Match(hero.DamageType, damageType) &&
            Match(hero.Mobility, mobility) && Match(JsonText(hero.Progression, "rarity_name"), rarity) &&
            (string.IsNullOrWhiteSpace(acquisition) || hero.Acquisition.Any(x => x.Current && (Match(x.Id, acquisition) || Match(x.Name, acquisition)))) &&
            (string.IsNullOrWhiteSpace(attribute) || hero.Traits.Any(x => Match(x.Code, attribute))) &&
            (string.IsNullOrWhiteSpace(search) || hero.Name.Contains(search, StringComparison.OrdinalIgnoreCase) || hero.Id.Contains(search, StringComparison.OrdinalIgnoreCase)))
            .OrderBy(x => x.Name).ToList();
        return Results.Ok(new HeroPage(filtered.Skip((page - 1) * pageSize).Take(pageSize), filtered.Count, page, pageSize));
    }

    private static async Task<IResult> Filters(HeroRepository repository)
    {
        var importId = await repository.LatestImportAsync();
        var heroes = importId is null ? [] : (await repository.LoadHeroesAsync(importId)).Where(x => x.Classification == "collectible").ToList();
        return Results.Ok(new HeroFilters(Values(heroes.Select(x => x.Class)), Values(heroes.Select(x => x.Tribe)),
            Values(heroes.Select(x => x.Element)), Values(heroes.Select(x => x.DamageType)), Values(heroes.Select(x => JsonText(x.Progression, "rarity_name"))),
            Values(heroes.Select(x => x.Mobility)), Values(heroes.SelectMany(x => x.Acquisition.Where(a => a.Current).Select(a => a.Name))),
            heroes.SelectMany(x => x.Traits).GroupBy(x => x.Code).Select(x => new FilterOption(x.Key, x.First().Name)).OrderBy(x => x.Label)));
    }

    private static async Task<IResult> Detail(HeroRepository repository, string id)
    {
        var importId = await repository.LatestImportAsync();
        if (importId is null) return Results.NotFound();
        var hero = (await repository.LoadHeroesAsync(importId)).FirstOrDefault(x => x.Classification == "collectible" && x.Id.Equals(id, StringComparison.OrdinalIgnoreCase));
        return hero is null ? Results.NotFound() : Results.Ok(new HeroDetail(hero, await repository.LoadSkillsAsync(importId, hero.Id)));
    }

    private static async Task<IResult> Skills(HeroRepository repository, string id)
    {
        var importId = await repository.LatestImportAsync();
        if (importId is null) return Results.NotFound();
        var exists = (await repository.LoadHeroesAsync(importId)).Any(x => x.Classification == "collectible" && x.Id.Equals(id, StringComparison.OrdinalIgnoreCase));
        return exists ? Results.Ok(await repository.LoadSkillsAsync(importId, id)) : Results.NotFound();
    }

    private static bool Match(string? value, string? filter) => string.IsNullOrWhiteSpace(filter) || string.Equals(value, filter, StringComparison.OrdinalIgnoreCase);
    private static string? JsonText(JsonElement element, string name) => HeroMapper.GetString(element, name);
    private static IEnumerable<string> Values(IEnumerable<string?> values) => values.Where(x => !string.IsNullOrWhiteSpace(x)).Select(x => x!).Distinct(StringComparer.OrdinalIgnoreCase).Order();
}
