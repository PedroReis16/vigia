namespace Vigia.Models.Entities;

public class SensorCommand
{
    public string Name { get; set; } = null!;
    public string Type { get; set; } = null!;
}

public class SensorAttribute
{
    public string ObjectId { get; set; } = null!;
    public string Name { get; set; } = null!;
    public string Type { get; set; } = null!;
}

public class FiwareProperties : BaseEntity
{
    public string Protocol { get; set; } = null!;
    public string Transport { get; set; } = null!;
    public List<SensorCommand> Commands { get; set; } = null!;
    public List<SensorAttribute> Attributes { get; set; } = null!;
}