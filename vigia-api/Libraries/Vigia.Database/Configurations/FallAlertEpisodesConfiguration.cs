using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Vigia.Models.Entities;
using Vigia.Models.Enums;

namespace Vigia.Database.Configurations;

internal class FallAlertEpisodesConfiguration : BaseConfiguration<FallAlertEpisode>
{
    public override void Configure(EntityTypeBuilder<FallAlertEpisode> builder)
    {
        base.Configure(builder);

        _ = builder.Property(e => e.DeviceId)
            .HasColumnName("device_id")
            .IsRequired();

        _ = builder.Property(e => e.GroupId)
            .HasColumnName("group_id")
            .IsRequired();

        _ = builder.Property(e => e.Kind)
            .HasConversion<string>()
            .HasColumnName("kind")
            .HasMaxLength(32)
            .HasDefaultValue(AlertEpisodeKind.Fall)
            .IsRequired();

        _ = builder.Property(e => e.Status)
            .HasConversion<string>()
            .HasColumnName("status")
            .HasMaxLength(16)
            .IsRequired();

        _ = builder.Property(e => e.FirstDetectedAt)
            .HasColumnName("first_detected_at")
            .HasConversion(v => v, v => DateTime.SpecifyKind(v, DateTimeKind.Utc))
            .IsRequired();

        _ = builder.Property(e => e.LastNotifiedAt)
            .HasColumnName("last_notified_at")
            .HasConversion(v => v, v => DateTime.SpecifyKind(v, DateTimeKind.Utc))
            .IsRequired();

        _ = builder.Property(e => e.NextRetryAt)
            .HasColumnName("next_retry_at")
            .HasConversion(v => v, v => v.HasValue ? DateTime.SpecifyKind(v.Value, DateTimeKind.Utc) : v);

        _ = builder.Property(e => e.NotifyCount)
            .HasColumnName("notify_count")
            .IsRequired();

        _ = builder.Property(e => e.AcknowledgedAt)
            .HasColumnName("acknowledged_at")
            .HasConversion(v => v, v => v.HasValue ? DateTime.SpecifyKind(v.Value, DateTimeKind.Utc) : v);

        _ = builder.Property(e => e.AcknowledgedByUserId)
            .HasColumnName("acknowledged_by_user_id");

        _ = builder.HasOne(e => e.Device)
            .WithMany()
            .HasForeignKey(e => e.DeviceId)
            .OnDelete(DeleteBehavior.Cascade);

        _ = builder.HasOne(e => e.Group)
            .WithMany()
            .HasForeignKey(e => e.GroupId)
            .OnDelete(DeleteBehavior.Cascade);

        _ = builder.HasIndex(e => new { e.DeviceId, e.Status });
        _ = builder.HasIndex(e => new { e.DeviceId, e.Kind, e.Status });
        _ = builder.HasIndex(e => e.NextRetryAt);
        _ = builder.HasIndex(e => e.Status);
    }
}
