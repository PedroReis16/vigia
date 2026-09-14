using System.Text.RegularExpressions;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Vigia.Models.Entities;

namespace Vigia.Database.Configurations;

internal abstract class BaseConfiguration<TEntity> : IEntityTypeConfiguration<TEntity> where TEntity : BaseEntity
{
    public virtual void Configure(EntityTypeBuilder<TEntity> builder)
    {
        _ = builder.HasKey(x => x.Id);
        _ = builder.HasIndex(x => x.CreatedAt);
        _ = builder.HasIndex(x => x.UpdatedAt);
        _ = builder.HasIndex(x => x.DeletedAt);

        _ = builder.ToTable(Regex.Replace(GetType().Name.ToString().Replace("Configuration", ""), "([a-z])([A-Z])", "$1_$2").ToLower());

        _ = builder.Property(p => p.Id)
            .HasColumnType("uuid")
            .HasColumnName("id")
            .IsRequired();

        _ = builder.Property(p => p.CreatedAt)
               .HasColumnName("created_at")
               .HasDefaultValueSql("now()")
               .HasConversion(v => v, v => DateTime.SpecifyKind(v, DateTimeKind.Utc))
               .IsRequired();

        _ = builder.Property(p => p.UpdatedAt)
               .IsRequired(false)
               .HasColumnName("updated_at")
               .HasConversion(v => v, v => v.HasValue ? DateTime.SpecifyKind(v.Value, DateTimeKind.Utc) : v);

        _ = builder.Property(p => p.DeletedAt)
               .IsRequired(false)
               .HasColumnName("deleted_at");
    }
}