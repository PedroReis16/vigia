using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Vigia.Cloud.Config;
using Vigia.Cloud.Contracts;

namespace Vigia.Cloud.BackgroundJob;

internal class InitCloudJob(
    ILogger<InitCloudJob> logger,
    IServiceScopeFactory scopeFactory,
    IOptions<CloudOptions> options) : BackgroundService
{
    private readonly ILogger<InitCloudJob> _logger = logger;
    private readonly IServiceScopeFactory _scopeFactory = scopeFactory;
    private readonly CloudOptions _options = options.Value;

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        using IServiceScope scope = _scopeFactory.CreateScope();
        ICloudService cloudService = scope.ServiceProvider.GetRequiredService<ICloudService>();

        var tasks = new List<Task>();

        if (!string.IsNullOrWhiteSpace(_options.VersionsBucketName))
        {
            tasks.Add(cloudService.EnsureBucketAsync(_options.VersionsBucketName, stoppingToken));
        }

        if (!string.IsNullOrWhiteSpace(_options.PicturesBucketName))
        {
            tasks.Add(cloudService.EnsureBucketAsync(_options.PicturesBucketName, stoppingToken));
        }

        if (tasks.Count == 0)
        {
            _logger.LogWarning("Nenhum bucket configurado em Cloud; inicialização ignorada");
            return;
        }

        await Task.WhenAll(tasks);
        _logger.LogInformation("Buckets inicializados com sucesso");
    }
}
