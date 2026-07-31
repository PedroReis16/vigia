using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Vigia.Models.Entities;
using Vigia.Models.Enums;

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

        _ = builder.Property(e => e.SignPublicKey)
            .IsRequired()
            .HasColumnName("sign_public_key")
            .HasMaxLength(64);

        _ = builder.HasOne(e => e.Group)
            .WithMany(g => g.Devices)
            .HasForeignKey(e => e.GroupId);

        _ = builder.HasIndex(e => e.Name);
        _ = builder.HasIndex(e => e.Nickname);
        _ = builder.HasIndex(e => e.MacAddress);
        _ = builder.HasIndex(e => e.Room);

        builder.HasData(SeedDevices());
    }

    private Device[] SeedDevices() =>
    [
        new Device
        {
            Id = new Guid("b7e3c9a1-4f2d-4e8b-9c1a-6d5e4f3a2b1c"),
            Name = "Vigia-a1b2c3d4",
            Nickname = "Câmera Teste",
            MacAddress = "AA:BB:CC:DD:EE:FF",
            Room = DeviceRooms.LivingRoom,
            SignPublicKey = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            GroupId = new Guid("80eed123-8e77-47a3-8fae-cedb1ab3eef7"), // Grupo do Admin
            CreatedAt = new DateTime(2026, 7, 27, 17, 42, 22, 525, DateTimeKind.Utc).AddTicks(2940),
            UpdatedAt = null,
            DeletedAt = null
        }
    ];
}
