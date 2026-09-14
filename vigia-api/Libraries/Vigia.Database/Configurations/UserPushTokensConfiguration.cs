using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Vigia.Models.Entities;

namespace Vigia.Database.Configurations;

internal class UserPushTokensConfiguration : BaseConfiguration<UserPushToken>
{
    public override void Configure(EntityTypeBuilder<UserPushToken> builder)
    {
        base.Configure(builder);

        _ = builder
            .Property(e => e.UserId)
            .HasColumnName("user_id")
            .IsRequired();

        _ = builder
            .Property(e => e.Token)
            .HasColumnName("token")
            .HasMaxLength(512)
            .IsRequired();

        _ = builder
            .Property(e => e.Platform)
            .HasColumnName("platform")
            .HasMaxLength(16)
            .IsRequired();

        _ = builder.HasIndex(e => e.Token).IsUnique();
        _ = builder.HasIndex(e => e.UserId);
    }
}
