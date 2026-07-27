namespace Vigia.Models.Entities;

public class UserGroup : BaseEntity
{
    public Guid GroupOwner { get; set; }

    // 1 usuário pode ter vários grupos
    public List<User> Users { get; set; } = null!;

    // 1 grupo pode ter vários dispositivos -> 1 dispositivo só pode estar em 1 grupo
    public List<Device> Devices { get; set; } = null!;
}