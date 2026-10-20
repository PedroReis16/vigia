namespace Vigia.API.Models.DTOs.Users;

public class UserProfileDTO
{
    public Guid Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string FirstName { get; set; } = string.Empty;
    public string LastName { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public string Phone { get; set; } = string.Empty;
    public string? PictureUrl { get; set; }
    public bool CanDeleteAccount { get; set; }
}
