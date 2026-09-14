using Microsoft.EntityFrameworkCore.Migrations;
using Vigia.Models.Enums;

#nullable disable

namespace Vigia.Database.Migrations
{
    /// <inheritdoc />
    public partial class DevicesRoomProperty : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AlterDatabase()
                .Annotation("Npgsql:Enum:device_rooms", "backyard,bathroom,bedroom,frontyard,garage,kitchen,living_room,office");

            migrationBuilder.AddColumn<DeviceRooms>(
                name: "room",
                table: "devices",
                type: "device_rooms",
                nullable: true);

            migrationBuilder.CreateIndex(
                name: "IX_devices_room",
                table: "devices",
                column: "room");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropIndex(
                name: "IX_devices_room",
                table: "devices");

            migrationBuilder.DropColumn(
                name: "room",
                table: "devices");

            migrationBuilder.AlterDatabase()
                .OldAnnotation("Npgsql:Enum:device_rooms", "backyard,bathroom,bedroom,frontyard,garage,kitchen,living_room,office");
        }
    }
}
