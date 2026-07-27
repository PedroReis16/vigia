using Microsoft.EntityFrameworkCore;
using Vigia.Database.Configurations;
using Vigia.Models.Entities;

public class VigiaDbContext : DbContext
{
    public DbSet<Device> Devices { get; set; } = null!;

    public VigiaDbContext(DbContextOptions<VigiaDbContext> options) : base(options)
    {
    }

    internal VigiaDbContext(){

    }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        _ = modelBuilder.ApplyConfiguration(new DevicesConfiguration());

        _ = modelBuilder.Ignore<BaseEntity>();
    }
}