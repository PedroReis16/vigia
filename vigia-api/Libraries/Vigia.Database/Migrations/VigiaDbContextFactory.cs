using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Design;
using Vigia.Models.Enums;

namespace Vigia.Database.Migrations;

public class VigiaDbContextFactory : IDesignTimeDbContextFactory<VigiaDbContext>
{
    public VigiaDbContext CreateDbContext(string[] args)
    {
        AppContext.SetSwitch("Npgsql.EnableLegacyTimestampBehavior", true);

        DbContextOptions<VigiaDbContext> options = new DbContextOptionsBuilder<VigiaDbContext>()
            .UseNpgsql(
                "Host=localhost;Database=vigia",
                builder => builder.MapEnum<DeviceRooms>())
            .Options;

        return new VigiaDbContext(options);
    }
}
