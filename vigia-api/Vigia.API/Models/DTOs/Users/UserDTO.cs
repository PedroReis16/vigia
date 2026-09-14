namespace Vigia.API.Models.DTOs.Users;

public class UserDTO
{
    public Guid Id { get; set; }
    public string Name { get; set; } = null!;
    public string? Email { get; set; } = null!;
    public string? UserPictureUrl { get; set; }
}