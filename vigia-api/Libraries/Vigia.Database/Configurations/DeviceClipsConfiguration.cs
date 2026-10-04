using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Vigia.Models.Entities;

namespace Vigia.Database.Configurations;

internal class DeviceClipsConfiguration : BaseConfiguration<DeviceClip>
{
    public override void Configure(EntityTypeBuilder<DeviceClip> builder)
    {
        base.Configure(builder);

        _ = builder.Property(e => e.Id)
            .ValueGeneratedNever();

        _ = builder.Property(e => e.DeviceId)
            .HasColumnName("device_id")
            .IsRequired();

        _ = builder.Property(e => e.Status)
            .HasConversion<string>()
            .HasColumnName("status")
            .HasMaxLength(16)
            .IsRequired();

        _ = builder.Property(e => e.FrameCount)
            .HasColumnName("frame_count")
            .IsRequired();

        _ = builder.Property(e => e.Fps)
            .HasColumnName("fps")
            .IsRequired();

        _ = builder.Property(e => e.ObjectKey)
            .HasColumnName("object_key")
            .HasMaxLength(512);

        _ = builder.HasOne(e => e.Device)
            .WithMany()
            .HasForeignKey(e => e.DeviceId)
            .OnDelete(DeleteBehavior.Cascade);

        _ = builder.HasIndex(e => e.DeviceId);
        _ = builder.HasIndex(e => e.Status);
    }
}
