using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Vigia.Models.Entities;

namespace Vigia.Database.Configurations;

internal class UsersConfiguration : BaseConfiguration<User>
{
    public override void Configure(EntityTypeBuilder<User> builder)
    {
        base.Configure(builder);

        _ = builder
            .Property(u => u.FirstName)
            .IsRequired()
            .HasColumnName("first_name")
            .HasMaxLength(64);

        _ = builder
            .Property(u => u.LastName)
            .IsRequired()
            .HasColumnName("last_name")
            .HasMaxLength(64);

        _ = builder
            .Property(u => u.Email)
            .IsRequired()
            .HasColumnName("email")
            .HasMaxLength(256);

        _ = builder
            .Property(u => u.Phone)
            .IsRequired()
            .HasColumnName("phone")
            .HasMaxLength(16);

        _ = builder
            .HasMany(u => u.LinkedGroups)
            .WithMany(g => g.LinkedUsers);

        _ = builder.HasIndex(u => u.FirstName);
        _ = builder.HasIndex(u => u.LastName);
        _ = builder.HasIndex(u => u.Email);
        _ = builder.HasIndex(u => u.Phone);
    }
}