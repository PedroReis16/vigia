using FirebaseAdmin;
using FirebaseAdmin.Messaging;
using Microsoft.Extensions.Options;
using Vigia.API.Config;
using Vigia.API.Contracts;

namespace Vigia.API.Services;

internal class FirebasePushNotificationService(
    ILogger<FirebasePushNotificationService> logger,
    IOptions<FirebaseOptions> firebaseOptions) : IPushNotificationService
{
    private const string FallAlertType = "fall";
    private const string FallChannelId = "vigia_fall_alerts";
    private const string WebAppBaseUrl = "https://vigiadeteccoes.com.br";
    private readonly ILogger<FirebasePushNotificationService> _logger = logger;
    private readonly FirebaseOptions _options = firebaseOptions.Value;

    public bool IsConfigured =>
        FirebaseApp.DefaultInstance is not null
        && (!string.IsNullOrWhiteSpace(_options.CredentialJson) || !string.IsNullOrWhiteSpace(_options.CredentialPath));

    public Task<PushNotificationResult> SendFallAlertAsync(FallAlertPushRequest request)
    {
        string displayName = DisplayName(request);
        return SendAsync(
            request,
            FallAlertType,
            "Alerta de queda",
            $"Queda detectada em {displayName}",
            $"fall-{request.DeviceId:D}",
            FallChannelId,
            "Push FCM de queda enviado. Device={DeviceId} AlertId={AlertId} Success={SuccessCount} Failure={FailureCount}");
    }

    private async Task<PushNotificationResult> SendAsync(
        FallAlertPushRequest request,
        string type,
        string title,
        string body,
        string collapseKey,
        string channelId,
        string successLogTemplate)
    {
        if (request.Tokens.Count == 0)
            return new PushNotificationResult(0, []);

        if (FirebaseApp.DefaultInstance is null)
        {
            _logger.LogWarning(
                "Firebase não configurado. Push {Type} não enviado para o device {DeviceId}.",
                type,
                request.DeviceId);
            return new PushNotificationResult(0, []);
        }

        MulticastMessage message = new()
        {
            Tokens = request.Tokens.ToList(),
            Notification = new Notification
            {
                Title = title,
                Body = body,
            },
            Data = new Dictionary<string, string>(StringComparer.Ordinal)
            {
                ["type"] = type,
                ["deviceId"] = request.DeviceId.ToString(),
                ["deviceName"] = request.DeviceName,
                ["nickname"] = request.Nickname ?? string.Empty,
                ["alertId"] = request.AlertId.ToString(),
            },
            Android = new AndroidConfig
            {
                Priority = Priority.High,
                CollapseKey = collapseKey,
                Notification = new AndroidNotification
                {
                    ChannelId = channelId,
                    Priority = NotificationPriority.HIGH,
                    Tag = collapseKey,
                },
            },
            Apns = new ApnsConfig
            {
                Aps = new Aps
                {
                    Sound = "default",
                },
            },
            Webpush = new WebpushConfig
            {
                Notification = new WebpushNotification
                {
                    Title = title,
                    Body = body,
                    Tag = collapseKey,
                },
                FcmOptions = new WebpushFcmOptions
                {
                    Link = $"{WebAppBaseUrl}/devices/{request.DeviceId}",
                },
            },
        };

        BatchResponse response = await FirebaseMessaging.DefaultInstance.SendEachForMulticastAsync(message);
        List<string> invalidTokens = [];

        for (int index = 0; index < response.Responses.Count; index++)
        {
            SendResponse sendResponse = response.Responses[index];
            if (sendResponse.IsSuccess)
                continue;

            MessagingErrorCode? errorCode = sendResponse.Exception?.MessagingErrorCode;
            if (errorCode is MessagingErrorCode.Unregistered or MessagingErrorCode.InvalidArgument)
                invalidTokens.Add(request.Tokens[index]);

            _logger.LogWarning(
                sendResponse.Exception,
                "Falha ao enviar push FCM. Device={DeviceId} AlertId={AlertId} TokenIndex={TokenIndex} ErrorCode={ErrorCode}",
                request.DeviceId,
                request.AlertId,
                index,
                errorCode);
        }

        _logger.LogInformation(
            successLogTemplate,
            request.DeviceId,
            request.AlertId,
            response.SuccessCount,
            response.FailureCount);

        return new PushNotificationResult(response.SuccessCount, invalidTokens);
    }

    private static string DisplayName(FallAlertPushRequest request) =>
        string.IsNullOrWhiteSpace(request.Nickname) ? request.DeviceName : request.Nickname;
}
