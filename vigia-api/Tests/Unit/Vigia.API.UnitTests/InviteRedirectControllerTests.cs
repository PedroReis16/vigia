using System.Reflection;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Configuration;
using Vigia.API.Controllers;

namespace Vigia.API.UnitTests;

public class InviteRedirectControllerTests
{
    [Fact]
    public void OpenInvite_IsAnonymous()
    {
        MethodInfo? method = typeof(InviteRedirectController).GetMethod(nameof(InviteRedirectController.OpenInvite));
        Assert.NotNull(method);
        Assert.NotNull(method!.GetCustomAttribute<AllowAnonymousAttribute>());
    }

    [Fact]
    public void OpenInvite_RedirectsDesktopStraightToTheWeb()
    {
        InviteRedirectController controller = CreateController(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15");

        RedirectResult result = Assert.IsType<RedirectResult>(controller.OpenInvite("abc_12"));

        Assert.Equal("http://localhost:4200/invite/abc_12", result.Url);
    }

    [Fact]
    public void OpenInvite_MobileHandoffHasNoVisibleChoices()
    {
        InviteRedirectController controller = CreateController(
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148");

        ContentResult result = Assert.IsType<ContentResult>(controller.OpenInvite("abc_12"));

        Assert.Contains("vigia://invite/abc_12", result.Content);
        Assert.Contains("http://localhost:4200/invite/abc_12", result.Content);
        Assert.Contains("window.location.replace(deepLink)", result.Content);
        Assert.Contains("window.location.replace(webInvite)", result.Content);
        Assert.DoesNotContain("Abrir no aplicativo", result.Content);
        Assert.DoesNotContain("Continuar na web", result.Content);
        Assert.DoesNotContain("<a ", result.Content);
    }

    private static InviteRedirectController CreateController(string userAgent)
    {
        IConfiguration configuration = new ConfigurationBuilder()
            .AddInMemoryCollection(new Dictionary<string, string?>
            {
                ["Invite:DeepLinkBase"] = "vigia://invite/",
                ["Invite:WebInviteBase"] = "http://localhost:4200/invite/",
            })
            .Build();

        DefaultHttpContext httpContext = new();
        httpContext.Request.Headers.UserAgent = userAgent;

        return new InviteRedirectController(configuration)
        {
            ControllerContext = new ControllerContext { HttpContext = httpContext },
        };
    }
}
