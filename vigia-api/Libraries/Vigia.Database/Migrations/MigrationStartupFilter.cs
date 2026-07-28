using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

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
}