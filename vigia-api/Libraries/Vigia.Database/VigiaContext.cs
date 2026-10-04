using Microsoft.EntityFrameworkCore;
using Vigia.Database.Configurations;
using Vigia.Models.Entities;

public class VigiaDbContext : DbContext
{
    public DbSet<Device> Devices { get; set; } = null!;
    public DbSet<Group> Groups { get; set; } = null!;
    public DbSet<User> Users { get; set; } = null!;
    public DbSet<FiwareProperties> FiwareProperties { get; set; } = null!;
    public DbSet<GroupInvite> GroupInvites { get; set; } = null!;
    public DbSet<UserPushToken> UserPushTokens { get; set; } = null!;
    public DbSet<DeviceClip> DeviceClips { get; set; } = null!;

    public VigiaDbContext(DbContextOptions<VigiaDbContext> options) : base(options)
    {
    }

    internal VigiaDbContext()
    {
    }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        _ = modelBuilder.ApplyConfiguration(new DevicesConfiguration());
        _ = modelBuilder.ApplyConfiguration(new GroupsConfiguration());
        _ = modelBuilder.ApplyConfiguration(new UsersConfiguration());
        _ = modelBuilder.ApplyConfiguration(new FiwarePropertiesConfiguration());
        _ = modelBuilder.ApplyConfiguration(new GroupInvitesConfiguration());
        _ = modelBuilder.ApplyConfiguration(new UserPushTokensConfiguration());
        _ = modelBuilder.ApplyConfiguration(new DeviceClipsConfiguration());

        _ = modelBuilder.Ignore<BaseEntity>();
    }
}