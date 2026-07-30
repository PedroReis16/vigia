using Microsoft.AspNetCore.Hosting;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Vigia.Database.Migrations;
using Vigia.Models.Enums;

namespace Vigia.Database.Extensions;

public static class ConnectionExtension
{
    public static void AddPostgres(this IServiceCollection services, string connectionString)
    {
        services.AddDbContext<VigiaDbContext>(options =>
            options.UseNpgsql(connectionString, options =>
            {
                // Mapear os Enums para o PostgreSQL
                options.MapEnum<DeviceRooms>();
            }));

        AppContext.SetSwitch("Npgsql.EnableLegacyTimestampBehavior", true);
        services.AddTransient<IStartupFilter, MigrationStartupFilter<VigiaDbContext>>();

    }
}