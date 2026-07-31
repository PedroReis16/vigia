using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Vigia.Models.Entities;

namespace Vigia.Database.Configurations;

internal class DevicesConfiguration : BaseConfiguration<Device>
{
    public override void Configure(EntityTypeBuilder<Device> builder)
    {
        base.Configure(builder);

        _ = builder.Property(e => e.Name)
            .IsRequired()
            .HasColumnName("name")
            .HasMaxLength(64);

        _ = builder.Property(e => e.Nickname)
            .HasColumnName("nickname")
            .HasMaxLength(64);

        _ = builder.Property(e => e.MacAddress)
            .IsRequired()
            .HasColumnName("mac_address");

        _ = builder.Property(e => e.Room)
            .HasColumnName("room");

        _ = builder.Property(e => e.SignPublicKey)
            .IsRequired()
            .HasColumnName("sign_public_key")
            .HasMaxLength(64);

        _ = builder.HasOne(e => e.Group)
            .WithMany(g => g.Devices)
            .HasForeignKey(e => e.GroupId);

        _ = builder.HasIndex(e => e.Name);
        _ = builder.HasIndex(e => e.Nickname);
        _ = builder.HasIndex(e => e.MacAddress);
        _ = builder.HasIndex(e => e.Room);
    }
}
