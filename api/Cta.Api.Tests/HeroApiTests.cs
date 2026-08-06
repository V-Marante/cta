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
    public async Task Cached_projection_changes_when_a_new_import_becomes_latest()
    {
        using var factory = new ApiFactory("cta");
        factory.Seed("old", "cta", "2026-01-01", new HeroSeed("Old", "Old Hero"));
        var client = factory.CreateClient();
        Assert.Equal("Old", (await Get(client, "/api/heroes")).GetProperty("items")[0].GetProperty("id").GetString());
        factory.Seed("new", "cta", "2026-02-01", new HeroSeed("New", "New Hero"));
        Assert.Equal("New", (await Get(client, "/api/heroes")).GetProperty("items")[0].GetProperty("id").GetString());
    }

    [Fact]
    public async Task Only_collectible_heroes_are_exposed_and_search_and_filters_work()
    {
        using var factory = Seeded(); var client = factory.CreateClient();
        Assert.Equal(2, (await Get(client, "/api/heroes")).GetProperty("total").GetInt32());
        Assert.Equal(2, (await Get(client, "/api/heroes?includeNonCollectible=true")).GetProperty("total").GetInt32());
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
        var skill = detail.GetProperty("skills")[0];
        Assert.Equal("Works for 5 seconds.", skill.GetProperty("description").GetString());
        Assert.Equal("5 seconds", skill.GetProperty("descriptionParameters").GetProperty("duration").GetString());
        Assert.Empty(skill.GetProperty("unresolvedPlaceholders").EnumerateArray());
        Assert.Equal("0", skill.GetProperty("components")[1].GetProperty("attributes").GetProperty("cooldown").GetString());
    }

    [Fact]
    public async Task Progression_semantics_and_legacy_availability_are_distinct_from_explicit_sources()
    {
        using var factory = Seeded(); var detail = await Get(factory.CreateClient(), "/api/heroes/Alpha");
        var hero = detail.GetProperty("hero");
        Assert.Equal("unresolved", hero.GetProperty("progressionSemantics").GetProperty("base_stars").GetProperty("status").GetString());
        Assert.True(hero.GetProperty("legacyAvailability").GetProperty("shop").GetProperty("value").GetBoolean());
        Assert.Contains(hero.GetProperty("acquisition").EnumerateArray(),
            source => source.GetProperty("evidenceType").GetString() == "explicit_configuration");
    }

    [Fact]
    public async Task Stat_semantics_preserve_supported_and_unresolved_source_values()
    {
        using var factory = Seeded(); var hero = (await Get(factory.CreateClient(), "/api/heroes/Alpha")).GetProperty("hero");
        Assert.Equal("base_attack_damage", hero.GetProperty("statSemantics").GetProperty("attack").GetProperty("meaning").GetString());
        Assert.Equal("unresolved", hero.GetProperty("statSemantics").GetProperty("power").GetProperty("status").GetString());
        Assert.Equal("Factor per Star", hero.GetProperty("sourceCalculations").GetProperty("factor_per_star").GetProperty("source_field").GetString());
    }

    [Fact]
    public async Task Filters_health_and_read_only_connection_are_exposed()
    {
        using var factory = Seeded(); var client = factory.CreateClient();
        var filters = await Get(client, "/api/heroes/filters");
        Assert.Contains("Ranger", filters.GetProperty("classes").EnumerateArray().Select(x => x.GetString()));
        Assert.Contains(filters.GetProperty("attributes").EnumerateArray(), x => x.GetProperty("value").GetString() == "Evade");
        Assert.Equal("ok", (await Get(client, "/health")).GetProperty("status").GetString());
        Assert.Equal("ready", (await Get(client, "/ready")).GetProperty("status").GetString());
        await using var db = await factory.Services.GetRequiredService<SqliteConnectionFactory>().OpenAsync();
        Assert.Contains("Mode=ReadOnly", db.ConnectionString, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task Metadata_contains_only_configured_public_build_values()
    {
        using var factory = new ApiFactory();
        var metadata = await Get(factory.CreateClient(), "/api/meta");
        Assert.Equal("test-version", metadata.GetProperty("applicationVersion").GetString());
        Assert.Equal("abcdef1", metadata.GetProperty("commit").GetString());
        Assert.False(metadata.TryGetProperty("databasePath", out _));
    }

    [Fact]
    public void Missing_production_database_fails_with_a_clear_startup_error()
    {
        using var factory = new ApiFactory(createDatabase: false, environment: "Production");
        var exception = Assert.ThrowsAny<Exception>(() => factory.CreateClient());
        Assert.Contains("Required SQLite database is missing", exception.ToString());
    }

    [Fact]
    public void Importer_database_is_rejected_instead_of_failing_on_the_first_api_query()
    {
        using var factory = new ApiFactory(validPublicSchema: false);
        var exception = Assert.ThrowsAny<Exception>(() => factory.CreateClient());
        Assert.Contains("not a prepared public catalogue", exception.ToString());
    }

    [Fact]
    public async Task Unified_host_serves_frontend_routes_assets_and_preserves_404_boundaries()
    {
        using var factory = new ApiFactory(environment: "Production");
        var client = factory.CreateClient();
        Assert.Contains("CTA synthetic frontend", await client.GetStringAsync("/"));
        Assert.Contains("CTA synthetic frontend", await client.GetStringAsync("/team-planner"));
        var asset = await client.GetAsync("/assets/heroes/test-assets/Alpha.png");
        Assert.Equal(HttpStatusCode.OK, asset.StatusCode);
        Assert.Contains("immutable", asset.Headers.CacheControl?.Extensions.Select(x => x.Name) ?? []);
        Assert.Equal(HttpStatusCode.NotFound, (await client.GetAsync("/assets/heroes/test-assets/Missing.png")).StatusCode);
        Assert.Equal(HttpStatusCode.NotFound, (await client.GetAsync("/api/missing")).StatusCode);
    }

    [Fact]
    public async Task Existing_local_ui_icons_are_served_read_only()
    {
        using var factory = new ApiFactory(withUiIcon: true);
        var client = factory.CreateClient();
        using var request = new HttpRequestMessage(HttpMethod.Get, "/ui-icons/elements/fire.png");
        var response = await client.SendAsync(request);
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.Equal("image/png", response.Content.Headers.ContentType?.MediaType);
        Assert.Equal(HttpStatusCode.NotFound, (await client.PostAsync("/ui-icons/elements/fire.png", null)).StatusCode);
    }

    [Fact]
    public async Task Existing_mapped_hero_icons_are_returned_and_served_read_only()
    {
        using var factory = new ApiFactory("cta", withHeroIcon: true);
        factory.Seed("current", "cta", "2026-02-01", new HeroSeed("Alpha", "Alpha Hero"));
        factory.SeedPortraitReference("current", "Alpha");
        var client = factory.CreateClient();
        var hero = (await Get(client, "/api/heroes/Alpha")).GetProperty("hero");
        Assert.Equal("/portraits/Alpha.png", hero.GetProperty("portraitUrl").GetString());
        using var request = new HttpRequestMessage(HttpMethod.Get, "/portraits/Alpha.png");
        var portrait = await client.SendAsync(request);
        Assert.Equal(HttpStatusCode.OK, portrait.StatusCode);
        Assert.Equal(HttpStatusCode.NotFound, (await client.PostAsync("/portraits/Alpha.png", null)).StatusCode);
    }

    [Fact]
    public async Task Bundled_portrait_mode_returns_a_same_origin_versioned_asset_path()
    {
        using var factory = new ApiFactory("cta", portraitMode: "bundled");
        factory.Seed("current", "cta", "2026-02-01", new HeroSeed("Alpha", "Alpha Hero"));
        factory.SeedPortraitReference("current", "Alpha");
        var hero = (await Get(factory.CreateClient(), "/api/heroes/Alpha")).GetProperty("hero");
        Assert.Equal("/assets/heroes/test-assets/Alpha.png", hero.GetProperty("portraitUrl").GetString());
    }

    [Fact]
    public async Task Bundled_portrait_mode_uses_packaged_file_even_without_database_portrait_marker()
    {
        using var factory = new ApiFactory("cta", portraitMode: "bundled");
        factory.Seed("current", "cta", "2026-02-01", new HeroSeed("Alpha", "Alpha Hero"));
        var hero = (await Get(factory.CreateClient(), "/api/heroes/Alpha")).GetProperty("hero");
        Assert.Equal("/assets/heroes/test-assets/Alpha.png", hero.GetProperty("portraitUrl").GetString());
    }

    [Fact]
    public async Task Legacy_external_portrait_mode_still_uses_the_packaged_same_origin_asset()
    {
        using var factory = new ApiFactory("cta", portraitMode: "external");
        factory.Seed("current", "cta", "2026-02-01", new HeroSeed("Alpha", "Alpha Hero"));
        var hero = (await Get(factory.CreateClient(), "/api/heroes/Alpha")).GetProperty("hero");
        Assert.Equal("/assets/heroes/test-assets/Alpha.png", hero.GetProperty("portraitUrl").GetString());
    }

    [Fact]
    public async Task Non_playable_classifications_are_omitted_from_all_hero_endpoints()
    {
        using var factory = new ApiFactory("cta");
        var categories = new[] { "collectible", "uncertain", "enemy", "npc", "summoned_variant", "transformed_variant", "cosmetic_variant", "non_collectible" };
        factory.Seed("categories", "cta", "2026-04-01", categories.Select((kind, index) =>
            new HeroSeed($"Hero{index}", $"Hero {index}", Classification: kind)).ToArray());
        var client = factory.CreateClient();
        Assert.Equal(1, (await Get(client, "/api/heroes")).GetProperty("total").GetInt32());
        Assert.Equal(1, (await Get(client, "/api/heroes?includeNonCollectible=true")).GetProperty("total").GetInt32());
        foreach (var index in Enumerable.Range(1, categories.Length - 1))
        {
            Assert.Equal(HttpStatusCode.NotFound, (await client.GetAsync($"/api/heroes/Hero{index}")).StatusCode);
            Assert.Equal(HttpStatusCode.NotFound, (await client.GetAsync($"/api/heroes/Hero{index}/skills")).StatusCode);
        }
        var metadata = await Get(client, "/api/heroes/filters");
        Assert.False(metadata.TryGetProperty("classifications", out _));
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
