namespace Cta.Api.Configuration;

public sealed class CtaOptions
{
    public string Database { get; set; } = "extracted/cta.sqlite";
    public string GameId { get; set; } = "com.godzilab.idlerpg";
    public string HeroIconRoot { get; set; } = "local/proprietary/hero-icons";
    public string UiIconRoot { get; set; } = "local/proprietary/ui-icons";
    public string WebOrigin { get; set; } = "http://localhost:5173";
    public string[] AllowedOrigins { get; set; } = [];
    public string ApplicationVersion { get; set; } = "0.1.0";
    public string Commit { get; set; } = "unknown";
    public string DataImportId { get; set; } = "unknown";
    public string GameVersion { get; set; } = "unknown";
    public string DatabaseHash { get; set; } = "unknown";
    public string AssetsVersion { get; set; } = "unknown";
    public string PortraitMode { get; set; } = "local";
    public string PortraitPathTemplate { get; set; } = "heroes/{version}/{id}.webp";
}
