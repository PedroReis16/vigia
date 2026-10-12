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
    private const string WebAppBaseUrl = "https://vigiadeteccoes.com.br";
    private readonly ILogger<FirebasePushNotificationService> _logger = logger;
    private readonly FirebaseOptions _options = firebaseOptions.Value;

    public bool IsConfigured =>
        FirebaseApp.DefaultInstance is not null
        && (!string.IsNullOrWhiteSpace(_options.CredentialJson) || !string.IsNullOrWhiteSpace(_options.CredentialPath));

    public async Task<PushNotificationResult> SendFallAlertAsync(FallAlertPushRequest request)
    {
        if (request.Tokens.Count == 0)
            return new PushNotificationResult(0, []);

        if (FirebaseApp.DefaultInstance is null)
        {
            _logger.LogWarning(
                "Firebase não configurado. Alerta de queda não enviado para o device {DeviceId}.",
                request.DeviceId);
            return new PushNotificationResult(0, []);
        }

        string displayName = string.IsNullOrWhiteSpace(request.Nickname)
            ? request.DeviceName
            : request.Nickname;

        string title = "Alerta de queda";
        string body = $"Queda detectada em {displayName}";
        string collapseKey = $"fall-{request.DeviceId:D}";

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
                ["type"] = FallAlertType,
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
                    ChannelId = "vigia_fall_alerts",
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
            "Push FCM de queda enviado. Device={DeviceId} AlertId={AlertId} Success={SuccessCount} Failure={FailureCount}",
            request.DeviceId,
            request.AlertId,
            response.SuccessCount,
            response.FailureCount);

        return new PushNotificationResult(response.SuccessCount, invalidTokens);
    }
}
