using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.ResponseCaching;
using Microsoft.Extensions.Configuration;

namespace Vigia.Models.Middlewares;

public class HttpResponseCacheHandler : IMiddleware
{
    private readonly TimeSpan _maxAge;

    public HttpResponseCacheHandler(IConfiguration configuration)
    {
        IConfigurationSection? cachingConfig = configuration.GetSection("ResponseCaching");
        _maxAge = cachingConfig is null ? TimeSpan.FromSeconds(60) : TimeSpan.FromSeconds(cachingConfig.GetValue<double>("MaxAge"));
    }
    public async Task InvokeAsync(HttpContext context, RequestDelegate next)
    {
        if (_maxAge.TotalSeconds > 0)
        {
            IResponseCachingFeature? cachingFeature = context.Features.Get<IResponseCachingFeature>();

            if (cachingFeature != null)
                cachingFeature.VaryByQueryKeys = new[] { "*" };

            context.Response.GetTypedHeaders().CacheControl =
                new Microsoft.Net.Http.Headers.CacheControlHeaderValue()
                {
                    Public = true,
                    MaxAge = _maxAge
                };
            context.Response.Headers[Microsoft.Net.Http.Headers.HeaderNames.Vary] =
                new string[] { "Accept-Encoding" };
        }

        await next(context);
    }
}