using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Configuration;

namespace Vigia.API.Controllers;

/// <summary>
/// Landing pública de convite. O link compartilhado aponta para cá (HTTPS),
/// e esta página redireciona para o deep link interno do app — sem expor
/// o scheme <c>vigia://</c> no texto compartilhado.
/// </summary>
[ApiController]
[Route("i")]
[AllowAnonymous]
public class InviteRedirectController(IConfiguration configuration) : ControllerBase
{
    private readonly IConfiguration _configuration = configuration;

    [HttpGet("{code}")]
    [Produces("text/html")]
    public IActionResult OpenInvite(string code)
    {
        if (string.IsNullOrWhiteSpace(code) || code.Length > 64)
            return BadRequest();

        string deepLinkBase = _configuration.GetValue<string>("Invite:DeepLinkBase") ?? "vigia://invite/";
        if (!deepLinkBase.EndsWith('/'))
            deepLinkBase += "/";

        string deepLink = $"{deepLinkBase}{Uri.EscapeDataString(code)}";
        string safeHref = System.Net.WebUtility.HtmlEncode(deepLink);

        string? webInviteBase = _configuration.GetValue<string>("Invite:WebInviteBase");
        string webLinkHtml = string.Empty;
        if (!string.IsNullOrWhiteSpace(webInviteBase))
        {
            if (!webInviteBase.EndsWith('/'))
                webInviteBase += "/";

            string webInviteUrl = $"{webInviteBase}{Uri.EscapeDataString(code)}";
            string safeWebHref = System.Net.WebUtility.HtmlEncode(webInviteUrl);
            webLinkHtml = $"""<p><a href="{safeWebHref}">Continuar na web</a></p>""";
        }

        string html = $$"""
            <!DOCTYPE html>
            <html lang="pt-BR">
            <head>
              <meta charset="utf-8" />
              <meta name="viewport" content="width=device-width, initial-scale=1" />
              <meta http-equiv="refresh" content="0;url={{safeHref}}" />
              <title>Vigia</title>
              <style>
                body { font-family: -apple-system, system-ui, sans-serif; display: flex;
                       min-height: 100vh; align-items: center; justify-content: center;
                       margin: 0; background: #0b0b0b; color: #f5f5f5; text-align: center; }
                a { color: #7dd3fc; font-size: 1.1rem; }
                p { opacity: 0.85; }
              </style>
              <script>window.location.replace({{System.Text.Json.JsonSerializer.Serialize(deepLink)}});</script>
            </head>
            <body>
              <div>
                <p>Abrindo o Vigia…</p>
                <p><a href="{{safeHref}}">Abrir no aplicativo</a></p>
                {{webLinkHtml}}
              </div>
            </body>
            </html>
            """;

        return Content(html, "text/html; charset=utf-8");
    }
}
