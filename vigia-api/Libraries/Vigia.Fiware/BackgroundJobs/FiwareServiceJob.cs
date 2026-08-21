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
        const int maxAttempts = 5;

        for (int attempt = 1; attempt <= maxAttempts && !stoppingToken.IsCancellationRequested; attempt++)
        {
            try
            {
                using IServiceScope scope = _scopeFactory.CreateScope();
                IFiwareService fiwareService = scope.ServiceProvider.GetRequiredService<IFiwareService>();

                //1. Verifica a existência e as condições do serviço do FIWARE
                bool serviceSynced = await fiwareService.AddOrUpdateServiceAsync();
                if (!serviceSynced)
                {
                    _logger.LogWarning(
                        "Tentativa {Attempt}/{MaxAttempts}: não foi possível garantir o serviço do FIWARE conforme as configurações",
                        attempt,
                        maxAttempts);
                }
                else
                {
                    _logger.LogInformation("Atualizações sobre o serviço do FIWARE realizadas com sucesso");
                }

                //2. Sincroniza schema (attributes/commands) dos devices quando Fiware:Devices divergir de FiwareProperties
                bool devicesSynced = await fiwareService.SyncDevicesSchemaAsync();
                if (!devicesSynced)
                {
                    _logger.LogWarning(
                        "Tentativa {Attempt}/{MaxAttempts}: sincronização de schema dos devices finalizou com falhas",
                        attempt,
                        maxAttempts);
                }
                else
                {
                    _logger.LogInformation(
                        "Sincronização do schema (attributes/commands) dos devices realizada com sucesso");

                    //3. Garante as subscrições Orion definidas em Fiware:Subscriptions
                    bool subscriptionsSynced = await fiwareService.SyncSubscriptionsAsync();
                    if (!subscriptionsSynced)
                    {
                        _logger.LogWarning(
                            "Tentativa {Attempt}/{MaxAttempts}: sincronização das subscrições Orion finalizou com falhas",
                            attempt,
                            maxAttempts);
                    }
                    else
                    {
                        _logger.LogInformation(
                            "Sincronização das subscrições Orion realizada com sucesso");

#if DEBUG
                        //4. Garante o dispositivo de teste (mesmo da seed do banco) no IoT Agent / Orion
                        bool seedDeviceReady = await fiwareService.EnsureSeedDeviceAsync();
                        if (!seedDeviceReady)
                        {
                            _logger.LogWarning(
                                "Tentativa {Attempt}/{MaxAttempts}: não foi possível garantir o device seed no FIWARE",
                                attempt,
                                maxAttempts);
                        }
                        else
                        {
                            _logger.LogInformation("Device seed provisionado/confirmado no FIWARE com sucesso");
                            return;
                        }
#else
                        return;
#endif
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(
                    ex,
                    "Tentativa {Attempt}/{MaxAttempts}: erro ao sincronizar FIWARE",
                    attempt,
                    maxAttempts);
            }

            if (attempt < maxAttempts)
                await Task.Delay(TimeSpan.FromSeconds(Math.Min(30, attempt * 3)), stoppingToken);
        }
    }
}
