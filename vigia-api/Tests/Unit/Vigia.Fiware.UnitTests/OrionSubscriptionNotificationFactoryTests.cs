using System.Text.Json;
using Vigia.Fiware.Services;

namespace Vigia.Fiware.UnitTests;

public class OrionSubscriptionNotificationFactoryTests
{
    [Fact]
    public void Create_ComAuthorization_UsaHttpCustom()
    {
        var notification = OrionSubscriptionNotificationFactory.Create(
            "http://vigia-api:8080/vigia/devices/alert",
            ["fall_state"],
            "normalized",
            "Basic dGVzdA==");

        string json = JsonSerializer.Serialize(notification);

        Assert.Null(notification.Http);
        Assert.Equal("Basic dGVzdA==", notification.HttpCustom?.Headers["Authorization"]);
        Assert.Contains("httpCustom", json, StringComparison.Ordinal);
        Assert.DoesNotContain("\"http\":", json, StringComparison.Ordinal);
    }

    [Fact]
    public void Create_SemAuthorization_UsaHttp()
    {
        var notification = OrionSubscriptionNotificationFactory.Create(
            "http://vigia-api:8080/vigia/devices/alert",
            ["fall_state"],
            "normalized",
            null);

        Assert.Equal("http://vigia-api:8080/vigia/devices/alert", notification.Http?.Url);
        Assert.Null(notification.HttpCustom);
    }
}
