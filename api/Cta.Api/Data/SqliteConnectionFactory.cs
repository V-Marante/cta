using Cta.Api.Configuration;
using Microsoft.Data.Sqlite;

namespace Cta.Api.Data;

public sealed class SqliteConnectionFactory(RepositoryPaths paths)
{
    public async Task<SqliteConnection> OpenAsync()
    {
        var builder = new SqliteConnectionStringBuilder { DataSource = paths.Database, Mode = SqliteOpenMode.ReadOnly, Cache = SqliteCacheMode.Shared };
        var connection = new SqliteConnection(builder.ToString());
        await connection.OpenAsync();
        return connection;
    }
}
