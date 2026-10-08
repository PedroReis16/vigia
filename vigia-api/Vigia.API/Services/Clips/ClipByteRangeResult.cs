using Microsoft.AspNetCore.Mvc;
using Vigia.Cloud.Contracts;

namespace Vigia.API.Services.Clips;

internal sealed class ClipByteRangeResult(CloudObjectRead read, string contentType, bool partial) : IActionResult
{
    private readonly CloudObjectRead _read = read;
    private readonly string _contentType = contentType;
    private readonly bool _partial = partial;

    public async Task ExecuteResultAsync(ActionContext context)
    {
        HttpResponse response = context.HttpContext.Response;
        response.ContentType = _contentType;
        response.Headers.AcceptRanges = "bytes";

        long slice = _read.End >= _read.Start ? _read.End - _read.Start + 1 : 0;
        if (_partial)
        {
            response.StatusCode = StatusCodes.Status206PartialContent;
            response.Headers.ContentRange = $"bytes {_read.Start}-{_read.End}/{_read.TotalLength}";
        }
        else
        {
            response.StatusCode = StatusCodes.Status200OK;
        }

        response.ContentLength = slice;
        try
        {
            if (slice > 0)
                await _read.Body.CopyToAsync(response.Body, context.HttpContext.RequestAborted);
        }
        finally
        {
            await _read.DisposeAsync();
        }
    }
}
