using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Vigia.Fiware.Contracts;

namespace Vigia.Fiware.BackgroundJobs;

public class FiwareServiceJob(ILogger<FiwareServiceJob> logger, IServiceScopeFactory scopeFactory) : BackgroundService
{
    private readonly ILogger<FiwareServiceJob> _logger = logger;
    private readonly IServiceScopeFactory _scopeFactory = scopeFactory;

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        try
        {
            using IServiceScope scope = _scopeFactory.CreateScope();
            IFiwareService fiwareService = scope.ServiceProvider.GetRequiredService<IFiwareService>();

            //1. Verifica a existência e as condições do serviço do FIWARE
            await fiwareService.AddOrUpdateServiceAsync();

            _logger.LogInformation("Atualizações sobre o serviço do FIWARE realizadas com sucesso");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Erro ao realizar as atualizações sobre o serviço do FIWARE");
        }
    }
}
