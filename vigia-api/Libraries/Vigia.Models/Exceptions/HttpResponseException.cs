using Vigia.Models.Enums;

namespace Vigia.Models.Exceptions;

public class HttpResponseException : Exception
{
    public int StatusCode { get; private set; }
    public string ErrorMessage { get; private set; }
    public ErrorCodes ErrorCode { get; private set; }
    public Dictionary<string, object>? AdditionalDetails { get; set; }

    public HttpResponseException(int statusCode, string errorMessage, Dictionary<string, object>? additionalDetails = null) : base(errorMessage)
    {
        StatusCode = statusCode;
        ErrorMessage = errorMessage ?? throw new ArgumentNullException(nameof(errorMessage));
        ErrorCode = ErrorCodes.UNKNOWN_ERROR;
        AdditionalDetails = additionalDetails;
    }

    public HttpResponseException(int statusCode, string message, ErrorCodes errorCode, Dictionary<string, object>? additionalDetails = null) : base(message)
    {
        StatusCode = statusCode;
        ErrorMessage = message ?? throw new ArgumentNullException(nameof(message));
        ErrorCode = errorCode;
        AdditionalDetails = additionalDetails;
    }
}