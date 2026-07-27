using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Vigia.Models.Entities;

namespace Vigia.Database.Configurations;

internal class DevicesConfiguration : BaseConfiguration<Device>
{
    public override void Configure(EntityTypeBuilder<Device> builder)
    {
        base.Configure(builder);

        _ = builder.Property(e => e.DeviceName)
            .IsRequired()
            .HasColumnName("device_name")
            .HasMaxLength(64);

        _ = builder.Property(e => e.Nickname)
            .HasColumnName("nickname")
            .HasMaxLength(64);

        _ = builder.Property(e => e.PublicKey)
            .IsRequired()
            .HasColumnName("public_key")
            .HasMaxLength(256);


        _ = builder.HasIndex(e => e.DeviceName);
        _ = builder.HasIndex(e => e.PublicKey);
        _ = builder.HasIndex(e => e.Nickname);
    }
}