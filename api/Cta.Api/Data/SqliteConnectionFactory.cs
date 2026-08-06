using Cta.Api.Configuration;
using Microsoft.Data.Sqlite;

namespace Cta.Api.Data;

public sealed class SqliteConnectionFactory(RepositoryPaths paths)
{
    private static readonly string[] RequiredTables = ["release_info", "catalog_entities", "catalog_text", "catalog_relations"];

    public async Task<SqliteConnection> OpenAsync()
    {
        var builder = new SqliteConnectionStringBuilder { DataSource = paths.Database, Mode = SqliteOpenMode.ReadOnly, Cache = SqliteCacheMode.Shared };
        var connection = new SqliteConnection(builder.ToString());
        await connection.OpenAsync();
        return connection;
    }

    public async Task VerifyPublicSchemaAsync()
    {
        await using var connection = await OpenAsync();
        await using var command = connection.CreateCommand();
        command.CommandText = $"SELECT count(*) FROM sqlite_master WHERE type='table' AND name IN ({string.Join(',', RequiredTables.Select((_, index) => $"$table{index}"))})";
        for (var index = 0; index < RequiredTables.Length; index++) command.Parameters.AddWithValue($"$table{index}", RequiredTables[index]);
        if (Convert.ToInt32(await command.ExecuteScalarAsync()) != RequiredTables.Length)
            throw new InvalidDataException("Database is not a prepared public catalogue. Run scripts/prepare-public-release.sh first.");
    }
}
