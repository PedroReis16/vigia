using Vigia.Models.Enums;

namespace Vigia.Models.Entities;

public class User : BaseEntity
{
    public string FirstName { get; set; } = string.Empty;
    public string LastName { get; set; } = string.Empty;
    public string Email { get; set; } = null!;
    public string Phone { get; set; } = null!;

    /// <summary>Chave do objeto no bucket de pictures. Nula quando o usuário não tem foto.</summary>
    public string? PictureKey { get; set; }

    // 1 usuário pode ter vários grupos -> 1 grupo pode ter vários usuários
    public ICollection<Group> LinkedGroups { get; set; } = null!;
}