using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Vigia.Models.Entities;

namespace Vigia.Database.Configurations;

internal class UsersConfiguration : BaseConfiguration<User>
{
    public override void Configure(EntityTypeBuilder<User> builder)
    {
        base.Configure(builder);
    
        _ = builder.Property(u=>u.Name)
            .IsRequired()
            .HasColumnName("name")
            .HasMaxLength(64);

        _ = builder.Property(u=>u.Email)
            .IsRequired()
            .HasColumnName("email")
            .HasMaxLength(256);

        _ = builder.HasMany(u=>u.UserGroups)
            .WithMany(ug=>ug.Users);

        _ = builder.HasIndex(u=>u.Name);
        _ = builder.HasIndex(u=>u.Email);
    }
}