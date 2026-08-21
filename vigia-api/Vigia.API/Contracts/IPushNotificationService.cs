namespace Vigia.API.Contracts;

public record FallAlertPushRequest(
    Guid DeviceId,
    string DeviceName,
    string? Nickname,
    IReadOnlyList<string> Tokens);

public record PushNotificationResult(
    int SuccessCount,
    IReadOnlyList<string> InvalidTokens);

public interface IPushNotificationService
{
    bool IsConfigured { get; }

    Task<PushNotificationResult> SendFallAlertAsync(FallAlertPushRequest request);
}
