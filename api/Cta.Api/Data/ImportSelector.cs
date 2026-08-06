using Cta.Api.Configuration;
using Microsoft.Extensions.Options;

namespace Cta.Api.Data;

public sealed class ImportSelector(SqliteConnectionFactory connections, IOptions<CtaOptions> options)
{
    public async Task<string?> LatestSuccessfulAsync()
    {
        await using var db = await connections.OpenAsync();
        await using var command = db.CreateCommand();
        command.CommandText = "SELECT id FROM release_info WHERE game_id=$gameId ORDER BY finished_at DESC LIMIT 1";
        command.Parameters.AddWithValue("$gameId", options.Value.GameId);
        return await command.ExecuteScalarAsync() as string;
    }
}
