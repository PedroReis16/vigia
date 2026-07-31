using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
#if DEBUG
using Vigia.Models.Seed;
#endif

namespace Vigia.Database.Migrations;

public class MigrationStartupFilter<TContext> : IStartupFilter where TContext : DbContext
{
    public Action<IApplicationBuilder> Configure(Action<IApplicationBuilder> next)
    {
        return app =>
            {
                using (IServiceScope scope = app.ApplicationServices.CreateScope())
                {
                    ILogger<MigrationStartupFilter<TContext>>? logger = scope.ServiceProvider.GetService<ILogger<MigrationStartupFilter<TContext>>>();
                    try
                    {
                        foreach (TContext context in scope.ServiceProvider.GetServices<TContext>())
                        {
                            context.Database.SetCommandTimeout(0);
                            context.Database.Migrate();

#if DEBUG
                            SeedTestDevice(context, logger);
#endif
                        }
                    }
                    catch (Exception ex)
                    {
                        logger?.LogCritical(ex, "Erro durante a execução das Migrations no banco de dados: {0}", ex.Message);
                    }
                }
                next(app);
            };
    }

#if DEBUG
    private static void SeedTestDevice(TContext context, ILogger? logger)
    {
        if (context is not VigiaDbContext db)
            return;

        if (db.Devices.Any(d => d.Id == TestDeviceSeed.Id))
            return;

        db.Devices.Add(TestDeviceSeed.Create());
        db.SaveChanges();
        logger?.LogInformation(
            "Device de teste {DeviceId} ({DeviceName}) seedado no banco (DEBUG)",
            TestDeviceSeed.Id,
            TestDeviceSeed.Name);
    }
#endif
}
