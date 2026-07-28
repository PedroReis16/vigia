using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Vigia.Models.Entities;

namespace Vigia.Database.Configurations;

internal class UserRolesConfiguration : BaseConfiguration<UserRole>
{
    public override void Configure(EntityTypeBuilder<UserRole> builder)
    {
        base.Configure(builder);

        _ = builder.HasKey(ur => ur.Id);

        _ = builder.Property(ur => ur.Id)
            .IsRequired()
            .HasColumnName("id")
            .HasColumnType("varchar")
            .HasMaxLength(16);

        _ = builder
            .HasMany(ur => ur.Users)
            .WithMany(u => u.Roles);

        _ = builder.HasIndex(ur => ur.Id).IsUnique();

        _ = builder.Ignore(ur => ur.CreatedAt);
        _ = builder.Ignore(ur => ur.UpdatedAt);
        _ = builder.Ignore(ur => ur.DeletedAt);

        builder.HasData(SeedUserRoles());
    }

    private UserRole[] SeedUserRoles() => new UserRole[]
    {
        new UserRole("ADMIN"),
        new UserRole("USER")
    };
}