using Cta.Api.Configuration;
using Cta.Api.Data;
using Cta.Api.Features.Heroes;
using Microsoft.Extensions.FileProviders;

var builder = WebApplication.CreateBuilder(args);
builder.Services.Configure<CtaOptions>(builder.Configuration);
builder.Services.AddSingleton<RepositoryPaths>();
builder.Services.AddSingleton<SqliteConnectionFactory>();
builder.Services.AddSingleton<ImportSelector>();
builder.Services.AddSingleton<HeroRepository>();
builder.Services.AddCors(options => options.AddDefaultPolicy(policy =>
    policy.WithOrigins(builder.Configuration["WebOrigin"] ?? "http://localhost:5173").AllowAnyHeader().AllowAnyMethod()));

var app = builder.Build();
app.UseCors();

var paths = app.Services.GetRequiredService<RepositoryPaths>();
if (!File.Exists(paths.Database))
    throw new FileNotFoundException($"Importer database not found at '{paths.Database}'. Run the importer first or set Database to an existing SQLite file.", paths.Database);
if (Directory.Exists(paths.HeroIconRoot))
    app.UseStaticFiles(new StaticFileOptions { FileProvider = new PhysicalFileProvider(paths.HeroIconRoot), RequestPath = "/portraits" });

app.MapHeroEndpoints();
app.MapGet("/health", () => Results.Ok(new { status = "ok" }));
app.Run();

public partial class Program { }
