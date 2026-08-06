using Cta.Api.Configuration;
using Cta.Api.Data;
using Cta.Api.Features.Heroes;
using Microsoft.Extensions.FileProviders;
using Microsoft.AspNetCore.HttpOverrides;
using Microsoft.Extensions.Options;

var builder = WebApplication.CreateBuilder(args);
builder.Services.Configure<CtaOptions>(builder.Configuration);
builder.Services.AddSingleton<RepositoryPaths>();
builder.Services.AddSingleton<SqliteConnectionFactory>();
builder.Services.AddSingleton<ImportSelector>();
builder.Services.AddSingleton<HeroRepository>();
builder.Services.AddCors(options => options.AddDefaultPolicy(policy =>
{
    var configuredOrigins = builder.Configuration.GetSection("AllowedOrigins").Get<string[]>() ?? [];
    var developmentOrigin = builder.Configuration["WebOrigin"] ?? "http://localhost:5173";
    var allowedOrigins = builder.Environment.IsDevelopment()
        ? configuredOrigins.Append(developmentOrigin).Distinct(StringComparer.OrdinalIgnoreCase).ToArray()
        : configuredOrigins;
    if (!builder.Environment.IsDevelopment() && allowedOrigins.Length == 0)
        throw new InvalidOperationException("Production requires at least one AllowedOrigins entry (for example AllowedOrigins__0=https://example.com).");
    policy.WithOrigins(allowedOrigins).AllowAnyHeader().AllowAnyMethod();
}));
builder.Services.Configure<ForwardedHeadersOptions>(options =>
{
    options.ForwardedHeaders = ForwardedHeaders.XForwardedFor | ForwardedHeaders.XForwardedProto;
    options.KnownIPNetworks.Clear();
    options.KnownProxies.Clear();
});

var app = builder.Build();
if (!app.Environment.IsDevelopment()) app.UseExceptionHandler("/error");
app.UseForwardedHeaders();
app.UseCors();

var paths = app.Services.GetRequiredService<RepositoryPaths>();
if (!File.Exists(paths.Database))
    throw new FileNotFoundException("Required SQLite database is missing. Set Database to a readable approved public artifact.", paths.Database);
try
{
    await using var connection = await app.Services.GetRequiredService<SqliteConnectionFactory>().OpenAsync();
    await using var command = connection.CreateCommand();
    command.CommandText = "SELECT 1";
    await command.ExecuteScalarAsync();
}
catch (Exception exception)
{
    throw new InvalidOperationException("Required SQLite database cannot be opened read-only.", exception);
}
if (Directory.Exists(paths.HeroIconRoot))
    app.UseStaticFiles(new StaticFileOptions { FileProvider = new PhysicalFileProvider(paths.HeroIconRoot), RequestPath = "/portraits" });
if (Directory.Exists(paths.UiIconRoot))
    app.UseStaticFiles(new StaticFileOptions { FileProvider = new PhysicalFileProvider(paths.UiIconRoot), RequestPath = "/ui-icons" });

app.MapHeroEndpoints();
app.MapGet("/health", () => Results.Ok(new HealthResponse("ok"))).WithName("Health").Produces<HealthResponse>();
app.MapGet("/ready", async (SqliteConnectionFactory connections) =>
{
    try
    {
        await using var connection = await connections.OpenAsync();
        await using var command = connection.CreateCommand();
        command.CommandText = "SELECT 1";
        await command.ExecuteScalarAsync();
        return Results.Ok(new HealthResponse("ready"));
    }
    catch { return Results.Json(new HealthResponse("unavailable"), statusCode: 503); }
}).WithName("Readiness").Produces<HealthResponse>().Produces<HealthResponse>(503);
app.MapGet("/api/meta", (IOptions<CtaOptions> options) =>
{
    var value = options.Value;
    return Results.Ok(new MetaResponse(value.ApplicationVersion, value.Commit, value.DataImportId,
        value.GameVersion, value.DatabaseHash, value.AssetsVersion));
}).WithName("Metadata").Produces<MetaResponse>();
app.Map("/error", () => Results.Problem(statusCode: 500, title: "An unexpected error occurred."));
app.Run();

public partial class Program { }
public sealed record MetaResponse(string ApplicationVersion, string Commit, string DataImportId, string GameVersion, string DatabaseHash, string AssetsVersion);
