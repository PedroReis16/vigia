namespace Vigia.Models.Entities;

public class Group : BaseEntity
{
    public Guid OwnerId { get; set; }

    public ICollection<User> LinkedUsers { get; set; } = null!;
    public ICollection<Device> Devices { get; set; } = null!;
}