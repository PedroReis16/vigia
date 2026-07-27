using Microsoft.AspNetCore.Hosting;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Vigia.Database;
using Vigia.Database.Migrations;

namespace Vigia.Database.Extensions;

public static class ConnectionExtension
{
    public static void AddPostgres(this IServiceCollection services, string connectionString)
    {
        services.AddDbContext<VigiaDbContext>(options =>
            options.UseNpgsql(connectionString));

        AppContext.SetSwitch("Npgsql.EnableLegacyTimestampBehavior", true);
        services.AddTransient<IStartupFilter, MigrationStartupFilter<VigiaDbContext>>();

    }
}