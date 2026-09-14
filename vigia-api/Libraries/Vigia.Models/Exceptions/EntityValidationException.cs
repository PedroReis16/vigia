using Vigia.Models.Enums;

namespace Vigia.Models.Exceptions;

public class EntityValidationException : HttpResponseException
{
    public string PropertyName { get; set; } = string.Empty;

    public EntityValidationException(string propertyName, string validationError, Dictionary<string, object>? additionalDetails = null)
        : base(400, $"Erro na validação da propriedade '{propertyName}': {validationError}", ErrorCodes.VALIDATION_ERROR, additionalDetails)
    {
        PropertyName = propertyName ?? throw new ArgumentNullException(nameof(propertyName));
    }

    public EntityValidationException(string propertyName, string validationError, ErrorCodes errorCode, Dictionary<string, object>? additionalDetails = null)
        : base(400, $"Erro na validação da propriedade '{propertyName}': {validationError}", errorCode, additionalDetails)
    {
        PropertyName = propertyName ?? throw new ArgumentNullException(nameof(propertyName));
    }
}