using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Vigia.Models.Entities;
using Vigia.Models.Enums;

namespace Vigia.Database.Configurations;

internal class UsersConfiguration : BaseConfiguration<User>
{
    public override void Configure(EntityTypeBuilder<User> builder)
    {
        base.Configure(builder);

        _ = builder.Property(u => u.Name)
            .IsRequired()
            .HasColumnName("name")
            .HasMaxLength(64);

        _ = builder.Property(u => u.Email)
            .IsRequired()
            .HasColumnName("email")
            .HasMaxLength(256);

        _ = builder.Property(u => u.Password)
            .IsRequired()
            .HasColumnName("password")
            .HasColumnType("bytea");

        _ = builder.Property(u => u.Salt)
            .IsRequired()
            .HasColumnName("salt")
            .HasColumnType("bytea");

        _ = builder.HasMany(u => u.LinkedGroups)
            .WithMany(g => g.LinkedUsers);

        _ = builder
            .HasMany(u => u.Roles)
            .WithMany(ur => ur.Users);

        _ = builder.HasIndex(u => u.Name);
        _ = builder.HasIndex(u => u.Email);

        builder.HasData(SeedUsers());
    }

    private User[] SeedUsers() => new User[]
    {
        new User
        {
            Id = new Guid("05ae0d5a-5ef8-44c4-a6de-df0725cdd39b"),
            Name = "Super usuário",
            Email = "admin",
            Password = new byte[32]{ 247, 20, 118, 226, 219, 244, 66, 63, 99, 191, 56, 69, 182, 188, 218, 205, 232, 246, 129, 67, 89, 225, 107, 134, 235, 44, 161, 82, 105, 104, 181, 107 }, // Password: admin123
            Salt = new byte[16]{ 2, 20, 73, 2, 70, 73, 43, 120, 27, 233, 195, 53, 98, 210, 219, 129 },
            CreatedAt = new DateTime(2026, 7, 27, 17, 42, 22, 525, DateTimeKind.Utc).AddTicks(2940),
            UpdatedAt = null,
            DeletedAt = null
        }
    };
}