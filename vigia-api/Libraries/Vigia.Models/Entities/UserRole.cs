namespace Vigia.Models.Entities;

public class UserRole : BaseEntity
{
    public new string Id { get; set; } = null!;


    public ICollection<User> Users { get; set; } = null!;

    public UserRole(string id)
    {
        Id = id;
    }

}