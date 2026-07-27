using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Vigia.Models.Entities;

namespace Vigia.Database.Configurations;

internal class UserGroupsConfiguration : BaseConfiguration<UserGroup>
{
    public override void Configure(EntityTypeBuilder<UserGroup> builder)
    {
        base.Configure(builder);

        builder.Property(u => u.GroupOwner)
            .IsRequired()
            .HasColumnName("group_owner");

        _ = builder.HasMany(u => u.Devices)
            .WithOne(d => d.UserGroup);

        _ = builder.HasMany(u => u.Users)
            .WithMany(ug => ug.UserGroups);
    }
}