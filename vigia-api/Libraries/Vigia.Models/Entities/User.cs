namespace Vigia.Models.Entities;

public class User : BaseEntity
{
    public string Name { get; set; } = null!;
    public string Email { get; set; } = null!;


    // 1 usuário pode ter vários grupos -> 1 grupos pode ter vários usuários
    public List<UserGroup> UserGroups { get; set; } = null!;
}