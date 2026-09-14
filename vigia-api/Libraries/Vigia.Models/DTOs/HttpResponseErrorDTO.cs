using Vigia.Models.Enums;
using Vigia.Models.Exceptions;

namespace Vigia.Models.DTOs;

public class HttpResponseErrorDTO
{
    public int StatusCode { get; set; }
    public string? ErrorMessage { get; set; }
    public ErrorCodes ErrorCode { get; set; }
    public Dictionary<string, object>? AdditionalDetails { get; set; }

    public HttpResponseErrorDTO()
    {

    }

    public HttpResponseErrorDTO(HttpResponseException exception)
    {
        StatusCode = exception.StatusCode;
        ErrorMessage = exception.ErrorMessage;
        ErrorCode = exception.ErrorCode;
        AdditionalDetails = exception.AdditionalDetails;
    }
}