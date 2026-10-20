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

        _ = builder.Property(e => e.IsClipsEnabled)
            .IsRequired()
            .HasColumnName("is_clips_enabled")
            .HasDefaultValue(false);

        _ = builder.Property(e => e.IsBlurEnabled)
            .IsRequired()
            .HasColumnName("is_blur_enabled")
            .HasDefaultValue(false);

        _ = builder.Property(e => e.LastHeartbeatAt)
            .HasColumnName("last_heartbeat_at")
            .HasConversion(v => v, v => v.HasValue ? DateTime.SpecifyKind(v.Value, DateTimeKind.Utc) : v);

        _ = builder.Property(e => e.ClientCertificateSerial)
            .HasColumnName("client_certificate_serial")
            .HasMaxLength(64);

        _ = builder.Property(e => e.ClientCertificateNotAfter)
            .HasColumnName("client_certificate_not_after")
            .HasConversion(v => v, v => v.HasValue ? DateTime.SpecifyKind(v.Value, DateTimeKind.Utc) : v);

        _ = builder.HasIndex(e => e.ClientCertificateSerial)
            .IsUnique()
            .HasFilter("client_certificate_serial IS NOT NULL");

        _ = builder.HasOne(e => e.Group)
            .WithMany(g => g.Devices)
            .HasForeignKey(e => e.GroupId);

        _ = builder.HasIndex(e => e.Name);
        _ = builder.HasIndex(e => e.Nickname);
        _ = builder.HasIndex(e => e.MacAddress);
        _ = builder.HasIndex(e => e.Room);
        _ = builder.HasIndex(e => e.IsClipsEnabled);
        _ = builder.HasIndex(e => e.IsBlurEnabled);
        _ = builder.HasIndex(e => e.LastHeartbeatAt);
    }
}
