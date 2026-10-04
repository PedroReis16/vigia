using Vigia.Models.Enums;

namespace Vigia.Models.Entities;

public class User : BaseEntity
{
    public string FirstName { get; set; } = null!;
    public string LastName { get; set; } = null!;
    public string Email { get; set; } = null!;
    public string Phone { get; set; } = null!;

    // 1 usuário pode ter vários grupos -> 1 grupo pode ter vários usuários
    public ICollection<Group> LinkedGroups { get; set; } = null!;
}