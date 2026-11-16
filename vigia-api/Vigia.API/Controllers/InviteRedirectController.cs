using System.Text.RegularExpressions;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Configuration;

namespace Vigia.API.Controllers;

/// <summary>
/// Entrada pública do convite. O link compartilhado aponta para cá (HTTPS).
/// No computador responde com redirect para a web. No celular tenta o app e,
/// se ele não abrir, segue para a web. Não há página de escolha.
/// </summary>
[ApiController]
[Route("i")]
public partial class InviteRedirectController(IConfiguration configuration) : ControllerBase
{
    private readonly IConfiguration _configuration = configuration;

    [AllowAnonymous]
    [HttpGet("{code}")]
    public IActionResult OpenInvite(string code)
    {
        if (string.IsNullOrWhiteSpace(code) || code.Length > 64)
            return BadRequest();

        string deepLink = AppendCode(ConfiguredBase("Invite:DeepLinkBase") ?? "vigia://invite/", code);
        string? webInviteUrl = ConfiguredBase("Invite:WebInviteBase") is string webBase
            ? AppendCode(webBase, code)
            : null;
        if (webInviteUrl is not null && !IsMobileUserAgent(Request.Headers.UserAgent.ToString()))
            return Redirect(webInviteUrl);

        return Content(BuildHandoffHtml(deepLink, webInviteUrl), "text/html; charset=utf-8");
    }

    private string? ConfiguredBase(string configKey)
    {
        string? baseUrl = _configuration.GetValue<string>(configKey);
        return string.IsNullOrWhiteSpace(baseUrl) ? null : baseUrl;
    }

    private static string AppendCode(string baseUrl, string code)
    {
        if (!baseUrl.EndsWith('/'))
            baseUrl += "/";

        return $"{baseUrl}{Uri.EscapeDataString(code)}";
    }

    private static bool IsMobileUserAgent(string userAgent)
    {
        return !string.IsNullOrWhiteSpace(userAgent) && MobileUserAgent().IsMatch(userAgent);
    }

    /// <summary>
    /// Página vazia. O script corre no head, antes de qualquer pintura, tenta o app
    /// e cai na web se a página continuar visível.
    /// </summary>
    private static string BuildHandoffHtml(string deepLink, string? webInviteUrl)
    {
        string deepLinkJson = System.Text.Json.JsonSerializer.Serialize(deepLink);
        string webInviteJson = webInviteUrl is null
            ? "null"
            : System.Text.Json.JsonSerializer.Serialize(webInviteUrl);

        return $$"""
            <!DOCTYPE html>
            <html lang="pt-BR">
            <head>
              <meta charset="utf-8" />
              <meta name="viewport" content="width=device-width, initial-scale=1" />
              <title>Vigia</title>
              <script>
                (function () {
                  var deepLink = {{deepLinkJson}};
                  var webInvite = {{webInviteJson}};
                  var timer = 0;
                  function cancel() { window.clearTimeout(timer); }
                  function fallback() { if (webInvite) window.location.replace(webInvite); }
                  document.addEventListener("visibilitychange", function () {
                    if (document.hidden) cancel();
                  });
                  window.addEventListener("pagehide", cancel);
                  window.location.replace(deepLink);
                  timer = window.setTimeout(fallback, 800);
                })();
              </script>
            </head>
            <body></body>
            </html>
            """;
    }

    [GeneratedRegex("Android|iPhone|iPad|iPod|Mobile", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant)]
    private static partial Regex MobileUserAgent();
}
