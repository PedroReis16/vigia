using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Vigia.Models.Entities;

namespace Vigia.Database.Configurations;

internal class GroupInvitesConfiguration : BaseConfiguration<GroupInvite>
{
    public override void Configure(EntityTypeBuilder<GroupInvite> builder)
    {
        base.Configure(builder);

        _ = builder
            .Property(e => e.Token)
            .HasColumnName("token")
            .IsRequired();

        _ = builder
            .Property(e => e.GroupId)
            .HasColumnName("group_id")
            .IsRequired();

        _ = builder
            .Property(e => e.CreatedByUserId)
            .HasColumnName("created_by_user_id")
            .IsRequired();

        _ = builder
            .Property(e => e.ExpiresAt)
            .HasColumnName("expires_at")
            .IsRequired();

        _ = builder
            .Property(e => e.RevokedAt)
            .HasColumnName("revoked_at");

        _ = builder
            .HasOne(e => e.Group)
            .WithMany()
            .HasForeignKey(e => e.GroupId)
            .OnDelete(DeleteBehavior.Cascade);

        _ = builder.HasIndex(e => e.Token).IsUnique();
        _ = builder.HasIndex(e => e.GroupId);
        _ = builder.HasIndex(e => e.CreatedByUserId);
        _ = builder.HasIndex(e => e.ExpiresAt);
    }
}
