using Microsoft.Extensions.Options;
using Vigia.API.Config;
using Vigia.API.Contracts;
using Vigia.Database.Contracts;
using Vigia.Models.Entities;
using Vigia.Models.Enums;

namespace Vigia.API.Services;

internal sealed class FallAlertRetryWorker(
    IServiceScopeFactory scopeFactory,
    IOptions<AlertOptions> alertOptions,
    ILogger<FallAlertRetryWorker> logger) : BackgroundService
{
    private readonly IServiceScopeFactory _scopeFactory = scopeFactory;
    private readonly AlertOptions _options = alertOptions.Value;
    private readonly ILogger<FallAlertRetryWorker> _logger = logger;

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        using PeriodicTimer timer = new(TimeSpan.FromSeconds(30));

        while (await timer.WaitForNextTickAsync(stoppingToken))
        {
            try
            {
                await ProcessDueEpisodesAsync(stoppingToken);
            }
            catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
            {
                throw;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Falha ao processar reenvios de alerta de queda");
            }
        }
    }

    private async Task ProcessDueEpisodesAsync(CancellationToken cancellationToken)
    {
        using IServiceScope scope = _scopeFactory.CreateScope();
        IFallAlertEpisodeDao episodeDao = scope.ServiceProvider.GetRequiredService<IFallAlertEpisodeDao>();
        IUserDao userDao = scope.ServiceProvider.GetRequiredService<IUserDao>();
        IUserPushTokenDao pushTokenDao = scope.ServiceProvider.GetRequiredService<IUserPushTokenDao>();
        IPushNotificationService push = scope.ServiceProvider.GetRequiredService<IPushNotificationService>();

        DateTime now = DateTime.UtcNow;
        List<FallAlertEpisode> due = await episodeDao.ListDueForRetryAsync(now, cancellationToken);
        if (due.Count == 0)
            return;

        int maxRetries = Math.Max(1, _options.MaxRetries);
        int intervalSeconds = Math.Max(1, _options.RetryIntervalSeconds);

        foreach (FallAlertEpisode episode in due)
        {
            if (episode.NotifyCount >= maxRetries)
            {
                episode.Status = FallAlertEpisodeStatus.Expired;
                episode.NextRetryAt = null;
                await episodeDao.UpdateAsync(episode, cancellationToken);
                _logger.LogInformation(
                    "Episódio de queda expirou após {NotifyCount} envios. Episode={EpisodeId} Device={DeviceId}",
                    episode.NotifyCount,
                    episode.Id,
                    episode.DeviceId);
                continue;
            }

            Device? device = episode.Device;
            if (device is null)
            {
                episode.Status = FallAlertEpisodeStatus.Expired;
                episode.NextRetryAt = null;
                await episodeDao.UpdateAsync(episode, cancellationToken);
                continue;
            }

            List<User> groupUsers = await userDao.GetUsersByGroupAsync(episode.GroupId);
            List<string> tokens = await pushTokenDao.GetTokensByUserIdsAsync(groupUsers.Select(u => u.Id));
            if (tokens.Count == 0)
            {
                episode.NextRetryAt = now.AddSeconds(intervalSeconds);
                await episodeDao.UpdateAsync(episode, cancellationToken);
                _logger.LogWarning(
                    "Reenvio de queda sem tokens FCM. Episode={EpisodeId} Device={DeviceId}",
                    episode.Id,
                    episode.DeviceId);
                continue;
            }

            PushNotificationResult result = await push.SendFallAlertAsync(
                new FallAlertPushRequest(episode.Id, device.Id, device.Name, device.Nickname, tokens));

            if (result.InvalidTokens.Count > 0)
                await pushTokenDao.DeleteTokensAsync(result.InvalidTokens);

            episode.NotifyCount += 1;
            episode.LastNotifiedAt = now;

            if (episode.NotifyCount >= maxRetries)
            {
                episode.Status = FallAlertEpisodeStatus.Expired;
                episode.NextRetryAt = null;
            }
            else
            {
                episode.NextRetryAt = now.AddSeconds(intervalSeconds);
            }

            await episodeDao.UpdateAsync(episode, cancellationToken);

            _logger.LogInformation(
                "Reenvio de alerta de queda. Episode={EpisodeId} Device={DeviceId} NotifyCount={NotifyCount} Status={Status}",
                episode.Id,
                episode.DeviceId,
                episode.NotifyCount,
                episode.Status);
        }
    }
}
