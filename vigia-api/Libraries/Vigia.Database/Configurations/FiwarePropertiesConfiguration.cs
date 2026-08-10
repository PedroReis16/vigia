using System.Text.Json;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.ChangeTracking;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Vigia.Models.Entities;

namespace Vigia.Database.Configurations;

internal class FiwarePropertiesConfiguration : BaseConfiguration<FiwareProperties>
{
    private static readonly JsonSerializerOptions JsonOptions = new();

    public override void Configure(EntityTypeBuilder<FiwareProperties> builder)
    {
        base.Configure(builder);

        _ = builder.Property(e => e.Protocol)
            .IsRequired()
            .HasColumnName("protocol");

        _ = builder.Property(e => e.Transport)
            .IsRequired()
            .HasColumnName("transport");

        _ = builder.Property(e => e.Commands)
            .IsRequired()
            .HasConversion(
                v => JsonSerializer.Serialize(v, JsonOptions),
                v => JsonSerializer.Deserialize<List<SensorCommand>>(v, JsonOptions) ?? new List<SensorCommand>(),
                CreateListComparer<SensorCommand>())
            .HasColumnType("jsonb")
            .HasColumnName("commands");

        _ = builder.Property(e => e.Attributes)
            .IsRequired()
            .HasConversion(
                v => JsonSerializer.Serialize(v, JsonOptions),
                v => JsonSerializer.Deserialize<List<SensorAttribute>>(v, JsonOptions) ?? new List<SensorAttribute>(),
                CreateListComparer<SensorAttribute>())
            .HasColumnType("jsonb")
            .HasColumnName("attributes");

        _ = builder.HasData(SeedProperties());

    }

    private FiwareProperties[] SeedProperties()
    {
        return [
            new FiwareProperties
            {
                Id = new Guid("61675835-4749-4001-8236-013206775835"),
                Protocol = "PDI-IoTA-UltraLight",
                Transport = "MQTT",
                Commands = [
                    new (){
                        Name = "stream_on",
                        Type = "command"
                    },
                    new (){
                        Name = "stream_off",
                        Type = "command"
                    },
                    new (){
                        Name = "device_on",
                        Type = "command"
                    },
                    new (){
                        Name = "device_off",
                        Type = "command"
                    }
                ],
                Attributes = [
                    new (){
                        ObjectId = "s",
                        Name = "system_status",
                        Type = "Text"
                    },
                    new (){
                        ObjectId = "ss",
                        Name = "stream_status",
                        Type = "Text"
                    },
                    new (){
                        ObjectId = "dp",
                        Name = "detected_person",
                        Type = "Boolean"
                    },
                    new (){
                        ObjectId = "df",
                        Name = "detected_fall",
                        Type = "Boolean"
                    }
                ],
                CreatedAt = new DateTime(2026, 7, 30, 10, 0, 0),
            }
        ];
    }

    private static ValueComparer<List<T>> CreateListComparer<T>() =>
        new(
            (left, right) => JsonSerializer.Serialize(left, JsonOptions) == JsonSerializer.Serialize(right, JsonOptions),
            value => JsonSerializer.Serialize(value, JsonOptions).GetHashCode(),
            value => JsonSerializer.Deserialize<List<T>>(JsonSerializer.Serialize(value, JsonOptions), JsonOptions)!);
}
