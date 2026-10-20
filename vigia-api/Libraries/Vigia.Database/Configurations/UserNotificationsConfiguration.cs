using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Vigia.Models.Entities;

namespace Vigia.Database.Configurations;

internal class UserNotificationsConfiguration : BaseConfiguration<UserNotification>
{
    public override void Configure(EntityTypeBuilder<UserNotification> builder)
    {
        base.Configure(builder);

        _ = builder.Property(e => e.UserId)
            .HasColumnName("user_id")
            .IsRequired();

        _ = builder.Property(e => e.EpisodeId)
            .HasColumnName("episode_id")
            .IsRequired();

        _ = builder.Property(e => e.DeviceId)
            .HasColumnName("device_id")
            .IsRequired();

        _ = builder.Property(e => e.Type)
            .HasColumnName("type")
            .HasMaxLength(32)
            .IsRequired();

        _ = builder.Property(e => e.Title)
            .HasColumnName("title")
            .HasMaxLength(256)
            .IsRequired();

        _ = builder.Property(e => e.Body)
            .HasColumnName("body")
            .HasMaxLength(1024)
            .IsRequired();

        _ = builder.Property(e => e.ReadAt)
            .HasColumnName("read_at")
            .HasConversion(v => v, v => v.HasValue ? DateTime.SpecifyKind(v.Value, DateTimeKind.Utc) : v);

        _ = builder.HasOne(e => e.User)
            .WithMany()
            .HasForeignKey(e => e.UserId)
            .OnDelete(DeleteBehavior.Cascade);

        _ = builder.HasOne(e => e.Episode)
            .WithMany(e => e.Notifications)
            .HasForeignKey(e => e.EpisodeId)
            .OnDelete(DeleteBehavior.Cascade);

        _ = builder.HasOne(e => e.Device)
            .WithMany()
            .HasForeignKey(e => e.DeviceId)
            .OnDelete(DeleteBehavior.Cascade);

        _ = builder.HasIndex(e => new { e.UserId, e.CreatedAt });
        _ = builder.HasIndex(e => new { e.UserId, e.ReadAt });
        _ = builder.HasIndex(e => e.EpisodeId);
        _ = builder.HasIndex(e => new { e.UserId, e.EpisodeId });
    }
}
