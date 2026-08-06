using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using Cta.Api.Data;
using Microsoft.Extensions.DependencyInjection;
using Xunit;

namespace Cta.Api.Tests;

public sealed class HeroApiTests
{
    [Fact]
    public async Task No_successful_import_returns_empty_page()
    {
        using var factory = new ApiFactory();
        var page = await factory.CreateClient().GetFromJsonAsync<JsonElement>("/api/heroes");
        Assert.Equal(0, page.GetProperty("total").GetInt32());
    }

    [Fact]
    public async Task Latest_configured_game_import_is_selected_and_other_games_are_ignored()
    {
        using var factory = new ApiFactory("cta");
        factory.Seed("cta-old", "cta", "2026-01-01", new HeroSeed("Old", "Old Hero"));
        factory.Seed("other-new", "other", "2026-03-01", new HeroSeed("Wrong", "Wrong Game"));
        factory.Seed("cta-new", "cta", "2026-02-01", new HeroSeed("New", "New Hero"));
        var page = await factory.CreateClient().GetFromJsonAsync<JsonElement>("/api/heroes");
        Assert.Equal("New", page.GetProperty("items")[0].GetProperty("id").GetString());
    }

    [Fact]
    public async Task Collectible_default_non_collectible_opt_in_search_and_filters_work()
    {
        using var factory = Seeded(); var client = factory.CreateClient();
        Assert.Equal(2, (await Get(client, "/api/heroes")).GetProperty("total").GetInt32());
        Assert.Equal(3, (await Get(client, "/api/heroes?includeNonCollectible=true")).GetProperty("total").GetInt32());
        foreach (var query in new[] { "search=aLPHa", "class=Ranger", "element=Fire", "rarity=Epic", "mobility=ground", "acquisition=Test%20Chest", "attribute=Evade" })
            Assert.Equal(1, (await Get(client, $"/api/heroes?{query}")).GetProperty("total").GetInt32());
    }

    [Fact]
    public async Task Pagination_is_clamped_and_has_stable_boundaries()
    {
        using var factory = Seeded(); var client = factory.CreateClient();
        var first = await Get(client, "/api/heroes?page=0&pageSize=1");
        Assert.Equal(1, first.GetProperty("page").GetInt32()); Assert.Single(first.GetProperty("items").EnumerateArray());
        Assert.Empty((await Get(client, "/api/heroes?page=3&pageSize=1")).GetProperty("items").EnumerateArray());
        Assert.Equal(250, (await Get(client, "/api/heroes?pageSize=999")).GetProperty("pageSize").GetInt32());
    }

    [Fact]
    public async Task Detail_not_found_and_detail_skills_with_localization_fallback()
    {
        using var factory = Seeded(); factory.SeedSkill("current", "Alpha"); var client = factory.CreateClient();
        Assert.Equal(HttpStatusCode.NotFound, (await client.GetAsync("/api/heroes/Missing")).StatusCode);
        var detail = await Get(client, "/api/heroes/Alpha");
        Assert.Equal("Fallback Skill", detail.GetProperty("skills")[0].GetProperty("name").GetString());
        Assert.Equal("Fallback description", detail.GetProperty("skills")[0].GetProperty("description").GetString());
    }

    [Fact]
    public async Task Filters_health_and_read_only_connection_are_exposed()
    {
        using var factory = Seeded(); var client = factory.CreateClient();
        var filters = await Get(client, "/api/heroes/filters");
        Assert.Contains("Ranger", filters.GetProperty("classes").EnumerateArray().Select(x => x.GetString()));
        Assert.Contains(filters.GetProperty("attributes").EnumerateArray(), x => x.GetProperty("value").GetString() == "Evade");
        Assert.Equal("ok", (await Get(client, "/health")).GetProperty("status").GetString());
        await using var db = await factory.Services.GetRequiredService<SqliteConnectionFactory>().OpenAsync();
        Assert.Contains("Mode=ReadOnly", db.ConnectionString, StringComparison.OrdinalIgnoreCase);
    }

    private static ApiFactory Seeded()
    {
        var factory = new ApiFactory("cta");
        factory.Seed("current", "cta", "2026-02-01",
            new("Alpha", "Alpha Hero"),
            new("Beta", "Beta Hero", "Knight", "Orc", "Water", "Magic", "flying", "Rare", "Block", Acquisition: null),
            new("Variant", "Alpha Variant", Classification: "transformed_variant"));
        return factory;
    }
    private static async Task<JsonElement> Get(HttpClient client, string url) => await client.GetFromJsonAsync<JsonElement>(url);
}
