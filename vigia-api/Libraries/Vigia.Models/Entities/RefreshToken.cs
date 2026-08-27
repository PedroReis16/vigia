namespace Vigia.Models.Entities;

public class RefreshToken : BaseEntity
{
    public string Token { get; set; } = null!; // JWT Token Hash
    public Guid UserId { get; set; }
    public DateTime ExpiresAt { get; set; }
    public DateTime? RevokedAt { get; set; }
    public string? ReplacedToken { get; set; } // Replaced Token Hash
    public string RequestIp { get; set; } = null!;
}