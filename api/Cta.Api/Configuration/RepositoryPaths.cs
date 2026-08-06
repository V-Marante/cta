using Microsoft.Extensions.Options;
using Microsoft.AspNetCore.Hosting;

namespace Cta.Api.Configuration;

public sealed class RepositoryPaths
{
    public RepositoryPaths(IWebHostEnvironment environment, IOptions<CtaOptions> options)
    {
        var root = FindRepositoryRoot(environment.ContentRootPath);
        Database = Resolve(options.Value.Database, root);
        HeroIconRoot = Resolve(options.Value.HeroIconRoot, root);
        UiIconRoot = Resolve(options.Value.UiIconRoot, root);
        BundledHeroIconRoot = Path.Combine(environment.WebRootPath ?? Path.Combine(environment.ContentRootPath, "wwwroot"), "assets", "heroes", options.Value.AssetsVersion);
    }

    public string Database { get; }
    public string HeroIconRoot { get; }
    public string UiIconRoot { get; }
    public string BundledHeroIconRoot { get; }

    private static string Resolve(string path, string root) =>
        Path.GetFullPath(Path.IsPathRooted(path) ? path : Path.Combine(root, path));

    private static string FindRepositoryRoot(string start)
    {
        for (var directory = new DirectoryInfo(start); directory is not null; directory = directory.Parent)
            if (File.Exists(Path.Combine(directory.FullName, "pyproject.toml"))) return directory.FullName;
        return Directory.GetCurrentDirectory();
    }
}
