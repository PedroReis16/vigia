using Microsoft.EntityFrameworkCore;
using Vigia.Database.Configurations;
using Vigia.Models.Entities;
using Vigia.Models.Enums;

public class VigiaDbContext : DbContext
{
    public DbSet<Device> Devices { get; set; } = null!;
    public DbSet<Group> Groups { get; set; } = null!;
    public DbSet<User> Users { get; set; } = null!;
    public DbSet<UserRole> UserRoles { get; set; } = null!;
    public DbSet<RefreshToken> RefreshTokens { get; set; } = null!;

    public VigiaDbContext(DbContextOptions<VigiaDbContext> options) : base(options)
    {
    }

    internal VigiaDbContext()
    {
    }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        _ = modelBuilder.ApplyConfiguration(new UserRolesConfiguration());
        _ = modelBuilder.ApplyConfiguration(new DevicesConfiguration());
        _ = modelBuilder.ApplyConfiguration(new GroupsConfiguration());
        _ = modelBuilder.ApplyConfiguration(new UsersConfiguration());
        _ = modelBuilder.ApplyConfiguration(new RefreshTokensConfiguration());

        _ = modelBuilder.Ignore<BaseEntity>();
    }
}