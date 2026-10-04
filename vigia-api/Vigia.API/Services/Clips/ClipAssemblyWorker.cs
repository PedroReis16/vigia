using Microsoft.Extensions.Options;
using Vigia.API.Config;
using Vigia.API.Contracts.Clips;
using Vigia.Cloud.Config;
using Vigia.Cloud.Contracts;
using Vigia.Database.Contracts;
using Vigia.Models.Entities;

namespace Vigia.API.Services.Clips;

internal sealed class ClipAssemblyWorker(
    ClipAssemblyQueue queue,
    IClipAssembler assembler,
    IServiceScopeFactory scopeFactory,
    IOptions<ClipOptions> options,
    IOptions<CloudOptions> cloudOptions,
    ILogger<ClipAssemblyWorker> logger) : BackgroundService
{
    private readonly ClipAssemblyQueue _queue = queue;
    private readonly IClipAssembler _assembler = assembler;
    private readonly IServiceScopeFactory _scopeFactory = scopeFactory;
    private readonly ClipOptions _options = options.Value;
    private readonly CloudOptions _cloudOptions = cloudOptions.Value;
    private readonly ILogger<ClipAssemblyWorker> _logger = logger;

    public override async Task StartAsync(CancellationToken cancellationToken)
    {
        try
        {
            await FailInterruptedAsync(cancellationToken);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Não foi possível reconciliar montagens interrompidas no arranque");
        }

        await base.StartAsync(cancellationToken);
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        Task expire = ExpireSessionsAsync(stoppingToken);
        try
        {
            await foreach (ClipAssemblyJob job in _queue.Reader.ReadAllAsync(stoppingToken))
            {
                try
                {
                    await AssembleAsync(job, stoppingToken);
                }
                catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
                {
                    throw;
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Falha ao montar o clipe {ClipId}", job.ClipId);
                    await MarkFailedAsync(job.ClipId, stoppingToken);
                    ClipStaging.DeleteQuietly(job.StagingDirectory, _logger);
                }
            }
        }
        finally
        {
            try
            {
                await expire;
            }
            catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
            {
            }
        }
    }

    private async Task AssembleAsync(ClipAssemblyJob job, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(_cloudOptions.PicturesBucketName))
            throw new InvalidOperationException("Cloud:PicturesBucketName não está configurado");

        string outputPath = Path.Combine(job.StagingDirectory, "clip.mp4");
        await _assembler.AssembleAsync(job.StagingDirectory, job.Fps, outputPath, cancellationToken);

        string objectKey = ClipObjectKeys.For(job.DeviceId, job.ClipId);
        await using FileStream video = File.OpenRead(outputPath);

        using IServiceScope scope = _scopeFactory.CreateScope();
        ICloudService cloud = scope.ServiceProvider.GetRequiredService<ICloudService>();
        IDeviceClipDao clips = scope.ServiceProvider.GetRequiredService<IDeviceClipDao>();

        await cloud.UploadFileAsync(
            _cloudOptions.PicturesBucketName,
            objectKey,
            video,
            "video/mp4",
            cancellationToken);

        await clips.MarkReadyAsync(job.ClipId, objectKey, cancellationToken);
        ClipStaging.DeleteQuietly(job.StagingDirectory, _logger);
        _logger.LogInformation("Clipe {ClipId} disponível em {ObjectKey}", job.ClipId, objectKey);
    }

    private async Task ExpireSessionsAsync(CancellationToken stoppingToken)
    {
        using PeriodicTimer timer = new(TimeSpan.FromMinutes(1));
        try
        {
            while (await timer.WaitForNextTickAsync(stoppingToken))
            {
                try
                {
                    await ExpireOnceAsync(stoppingToken);
                }
                catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
                {
                    throw;
                }
                catch (Exception ex)
                {
                    _logger.LogWarning(ex, "Falha ao expirar sessões de clipe incompletas");
                }
            }
        }
        catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
        {
        }
    }

    private async Task ExpireOnceAsync(CancellationToken cancellationToken)
    {
        int ttlMinutes = _options.SessionTtlMinutes > 0 ? _options.SessionTtlMinutes : 15;
        DateTime cutoff = DateTime.UtcNow.AddMinutes(-ttlMinutes);

        using IServiceScope scope = _scopeFactory.CreateScope();
        IDeviceClipDao clips = scope.ServiceProvider.GetRequiredService<IDeviceClipDao>();
        List<DeviceClip> stale = await clips.ListReceivingOlderThanAsync(cutoff, cancellationToken);

        foreach (DeviceClip clip in stale)
        {
            await clips.MarkFailedAsync(clip.Id, cancellationToken);
            ClipStaging.DeleteQuietly(ClipStaging.SessionDirectory(_options, clip.DeviceId, clip.Id), _logger);
            _logger.LogInformation("Sessão de clipe {ClipId} expirada", clip.Id);
        }
    }

    private async Task FailInterruptedAsync(CancellationToken cancellationToken)
    {
        using IServiceScope scope = _scopeFactory.CreateScope();
        IDeviceClipDao clips = scope.ServiceProvider.GetRequiredService<IDeviceClipDao>();
        List<DeviceClip> interrupted = await clips.ListAssemblingAsync(cancellationToken);

        foreach (DeviceClip clip in interrupted)
        {
            await clips.MarkFailedAsync(clip.Id, cancellationToken);
            ClipStaging.DeleteQuietly(ClipStaging.SessionDirectory(_options, clip.DeviceId, clip.Id), _logger);
            _logger.LogWarning("Montagem interrompida do clipe {ClipId} marcada como falha", clip.Id);
        }
    }

    private async Task MarkFailedAsync(Guid clipId, CancellationToken cancellationToken)
    {
        try
        {
            using IServiceScope scope = _scopeFactory.CreateScope();
            IDeviceClipDao clips = scope.ServiceProvider.GetRequiredService<IDeviceClipDao>();
            await clips.MarkFailedAsync(clipId, cancellationToken);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Não foi possível marcar o clipe {ClipId} como falha", clipId);
        }
    }
}
