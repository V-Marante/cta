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
builder.Services.Configure<ForwardedHeadersOptions>(options =>
{
    options.ForwardedHeaders = ForwardedHeaders.XForwardedFor | ForwardedHeaders.XForwardedProto;
    options.KnownIPNetworks.Clear();
    options.KnownProxies.Clear();
});

var app = builder.Build();
if (!app.Environment.IsDevelopment()) app.UseExceptionHandler("/error");
app.UseForwardedHeaders();
app.Use(async (context, next) =>
{
    context.Response.OnStarting(() =>
    {
        context.Response.Headers.XContentTypeOptions = "nosniff";
        context.Response.Headers.XFrameOptions = "DENY";
        context.Response.Headers["Referrer-Policy"] = "strict-origin-when-cross-origin";
        context.Response.Headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()";
        return Task.CompletedTask;
    });
    await next();
});

var paths = app.Services.GetRequiredService<RepositoryPaths>();
if (!File.Exists(paths.Database))
    throw new FileNotFoundException("Required SQLite database is missing. Set Database to a readable approved public artifact.", paths.Database);
try
{
    await app.Services.GetRequiredService<SqliteConnectionFactory>().VerifyPublicSchemaAsync();
}
catch (Exception exception)
{
    throw new InvalidOperationException("Required SQLite database cannot be opened read-only.", exception);
}
if (Directory.Exists(paths.HeroIconRoot))
{
    app.UseStaticFiles(new StaticFileOptions { FileProvider = new PhysicalFileProvider(paths.HeroIconRoot), RequestPath = "/portraits" });
    app.UseStaticFiles(new StaticFileOptions { FileProvider = new PhysicalFileProvider(paths.HeroIconRoot), RequestPath = $"/assets/heroes/{Uri.EscapeDataString(app.Configuration["AssetsVersion"] ?? "synthetic")}" });
}
if (Directory.Exists(paths.UiIconRoot))
{
    app.UseStaticFiles(new StaticFileOptions { FileProvider = new PhysicalFileProvider(paths.UiIconRoot), RequestPath = "/ui-icons" });
    app.UseStaticFiles(new StaticFileOptions { FileProvider = new PhysicalFileProvider(paths.UiIconRoot), RequestPath = $"/assets/ui-icons/{Uri.EscapeDataString(app.Configuration["AssetsVersion"] ?? "synthetic")}" });
}
app.UseStaticFiles(new StaticFileOptions
{
    OnPrepareResponse = context =>
    {
        var requestPath = context.Context.Request.Path.Value ?? "";
        if (requestPath.StartsWith("/assets/", StringComparison.OrdinalIgnoreCase))
            context.Context.Response.Headers.CacheControl = "public,max-age=31536000,immutable";
        else if (string.Equals(requestPath, "/index.html", StringComparison.OrdinalIgnoreCase))
            context.Context.Response.Headers.CacheControl = "no-cache";
    }
});

app.MapHeroEndpoints();
app.MapGet("/health", () => Results.Ok(new HealthResponse("ok"))).WithName("Health").Produces<HealthResponse>();
app.MapGet("/ready", async (SqliteConnectionFactory connections) =>
{
    try
    {
        await connections.VerifyPublicSchemaAsync();
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
app.MapFallback((HttpContext context) =>
{
    if (context.Request.Path.StartsWithSegments("/api") || context.Request.Path.StartsWithSegments("/assets"))
        return Results.NotFound();
    context.Response.Headers.CacheControl = "no-cache";
    return Results.File(Path.Combine(app.Environment.WebRootPath, "index.html"), "text/html");
});
app.Run();

public partial class Program { }
public sealed record MetaResponse(string ApplicationVersion, string Commit, string DataImportId, string GameVersion, string DatabaseHash, string AssetsVersion);
