namespace Cta.Api.Configuration;

public sealed class CtaOptions
{
    public string Database { get; set; } = "extracted/cta.sqlite";
    public string GameId { get; set; } = "com.godzilab.idlerpg";
    public string HeroIconRoot { get; set; } = "local/proprietary/hero-icons";
    public string UiIconRoot { get; set; } = "local/proprietary/ui-icons";
    public string WebOrigin { get; set; } = "http://localhost:5173";
}
