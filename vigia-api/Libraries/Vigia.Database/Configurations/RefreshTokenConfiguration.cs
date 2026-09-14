using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Vigia.Models.Entities;

namespace Vigia.Database.Configurations;

internal class RefreshTokensConfiguration : BaseConfiguration<RefreshToken>
{
    public override void Configure(EntityTypeBuilder<RefreshToken> builder)
    {
        base.Configure(builder);

        _ = builder
            .Property(e => e.Token)
            .HasColumnName("token")
            .IsRequired();

        _ = builder
            .Property(e => e.UserId)
            .HasColumnName("user_id")
            .IsRequired();

        _ = builder
            .Property(e => e.ExpiresAt)
            .HasColumnName("expires_at")
            .IsRequired();

        _ = builder
            .Property(e => e.RevokedAt)
            .HasColumnName("revoked_at");

        _ = builder
            .Property(e => e.ReplacedToken)
            .HasColumnName("replaced_token");

        _ = builder
            .Property(e => e.RequestIp)
            .HasColumnName("created_by_ip")
            .IsRequired();

        _ = builder.HasIndex(e => e.Token).IsUnique();
        _ = builder.HasIndex(e => e.UserId);
        _ = builder.HasIndex(e => e.RequestIp);
        _ = builder.HasIndex(e => e.ReplacedToken).IsUnique();
    }
}