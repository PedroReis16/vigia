using Microsoft.AspNetCore.Hosting;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Vigia.Database.Cache;
using Vigia.Database.CacheContracts;
using Vigia.Database.Contracts;
using Vigia.Database.EFDao;
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

    public static void AddRepositoryServices(this IServiceCollection services)
    {
        // Dao Services
        services.AddTransient<IDevicesDao, DevicesDao>();
        services.AddTransient<IGroupDao, GroupDao>();
        services.AddTransient<IGroupInviteDao, GroupInviteDao>();
        services.AddTransient<IRefreshTokenDao, RefreshTokenDao>();
        services.AddTransient<IUserDao, UserDao>();
        services.AddTransient<IFiwarePropertiesDao, FiwarePropertiesDao>();
        services.AddTransient<IUserPushTokenDao, UserPushTokenDao>();

        // Cache Services
        services.AddTransient<IDevicesDaoCache, DevicesDaoCache>();
        services.AddTransient<IGroupDaoCache, GroupDaoCache>();
        services.AddTransient<IUserDaoCache, UserDaoCache>();
    }
}