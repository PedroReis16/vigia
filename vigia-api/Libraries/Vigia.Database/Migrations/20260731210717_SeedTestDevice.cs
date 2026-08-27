using System;
using Microsoft.EntityFrameworkCore.Migrations;
using Vigia.Models.Enums;

#nullable disable

namespace Vigia.Database.Migrations
{
    /// <inheritdoc />
    public partial class SeedTestDevice : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.InsertData(
                table: "devices",
                columns: new[] { "id", "created_at", "deleted_at", "GroupId", "mac_address", "name", "nickname", "room", "sign_public_key", "updated_at" },
                values: new object[] { new Guid("b7e3c9a1-4f2d-4e8b-9c1a-6d5e4f3a2b1c"), new DateTime(2026, 7, 27, 17, 42, 22, 525, DateTimeKind.Utc).AddTicks(2940), null, new Guid("80eed123-8e77-47a3-8fae-cedb1ab3eef7"), "AA:BB:CC:DD:EE:FF", "Vigia-a1b2c3d4", "Câmera Teste", DeviceRooms.LivingRoom, "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef", null });
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DeleteData(
                table: "devices",
                keyColumn: "id",
                keyValue: new Guid("b7e3c9a1-4f2d-4e8b-9c1a-6d5e4f3a2b1c"));
        }
    }
}
