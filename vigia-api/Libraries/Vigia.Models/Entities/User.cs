using Vigia.Models.Enums;

namespace Vigia.Models.Entities;

public class User : BaseEntity
{
    public string Name { get; set; } = null!;
    public string Email { get; set; } = null!;

    public byte[] Password { get; set; } = null!;
    public byte[] Salt { get; set; } = null!;

    // 1 usuário pode ter vários grupos -> 1 grupo pode ter vários usuários
    public ICollection<Group> LinkedGroups { get; set; } = null!;
    public ICollection<UserRole> Roles { get; set; } = null!;
}