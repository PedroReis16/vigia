using System.Net.Http.Headers;
using Microsoft.AspNetCore.Http;

namespace Vigia.Models.Middlewares;

public class ForwardingHandler : DelegatingHandler
{
    private readonly IHttpContextAccessor _httpContextAccessor;

    public ForwardingHandler(IHttpContextAccessor httpContextAccessor)
    {
        _httpContextAccessor = httpContextAccessor;
    }

    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        var currentContext = _httpContextAccessor.HttpContext;
        if (currentContext != null && currentContext.Request.Headers.ContainsKey("Authorization"))
        {
            var token = currentContext.Request.Headers["Authorization"].ToString();
            request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token.Replace("Bearer ", ""));
        }

        return await base.SendAsync(request, cancellationToken);
    }
}