namespace Vigia.API.Config;

public class AlertOptions
{
    public const string SectionName = "Alerts";

    /// <summary>Intervalo entre reenvios FCM enquanto o episódio estiver Active.</summary>
    public int RetryIntervalSeconds { get; set; } = 120;

    /// <summary>Máximo de envios (incluindo o primeiro) antes de Expired.</summary>
    public int MaxRetries { get; set; } = 15;

    /// <summary>Máximo de notificações retornadas por página no inbox.</summary>
    public int InboxPageSize { get; set; } = 50;
}
