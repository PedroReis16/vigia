using System.Net;
using System.Net.Http;
using System.Text.Json;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Logging;
using Vigia.Models.DTOs;
using Vigia.Models.Exceptions;

namespace Vigia.Models.Middlewares;

public class GlobalExceptionHandler(ILogger<GlobalExceptionHandler> logger) : IMiddleware
{
    private readonly ILogger<GlobalExceptionHandler> _logger = logger;

    public async Task InvokeAsync(HttpContext context, RequestDelegate next)
    {
        JsonSerializerOptions options = new JsonSerializerOptions
        {
            DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull
        };

        try
        {
            await next(context);
        }
        catch (HttpResponseException ex)
        {
            context.Response.ContentType = "application/json";
            context.Response.StatusCode = ex.StatusCode;
            _logger.LogError($"{context.Request.Method} {context.Request.Path} - Error {ex.StatusCode}: {ex.Message}", context);
            await context.Response.WriteAsJsonAsync(new HttpResponseErrorDTO(ex), options: options);
        }
        catch (Exception ex)
        {
            context.Response.ContentType = "application/json";
            context.Response.StatusCode = (int)HttpStatusCode.InternalServerError;
            _logger.LogCritical($"{context.Request.Method} {context.Request.Path} - Error 500: {ex.Message}", context);
            HttpResponseException responseBody = new(
                context.Response.StatusCode,
                ex.Message
            );
            await context.Response.WriteAsJsonAsync(new HttpResponseErrorDTO(responseBody), options: options);
        }
    }
}