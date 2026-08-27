using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Vigia.Models.Entities;

namespace Vigia.Database.Configurations;

internal class GroupsConfiguration : BaseConfiguration<Group>
{
    public override void Configure(EntityTypeBuilder<Group> builder)
    {
        base.Configure(builder);

        _ = builder.Property(g => g.OwnerId)
            .IsRequired()
            .HasColumnName("owner_id");

        _ = builder.HasMany(g => g.Devices)
            .WithOne(d => d.Group);


        _ = builder.HasMany(g => g.LinkedUsers)
            .WithMany(u => u.LinkedGroups);


        _ = builder.HasIndex(g => g.OwnerId).IsUnique();

        builder.HasData(SeedGroups());
    }

    private Group[] SeedGroups() => new Group[]
    {
        new Group
        {
            Id = new Guid("80eed123-8e77-47a3-8fae-cedb1ab3eef7"),
            OwnerId = new Guid("05ae0d5a-5ef8-44c4-a6de-df0725cdd39b"),
            CreatedAt = new DateTime(2026, 7, 27, 17, 42, 22, 525, DateTimeKind.Utc).AddTicks(2940),
            UpdatedAt = null,
            DeletedAt = null
        }
    };
}
