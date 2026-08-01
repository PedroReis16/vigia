using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Vigia.Database.Migrations
{
    /// <inheritdoc />
    public partial class UpdateDevicesProperties : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropIndex(
                name: "IX_devices_public_key",
                table: "devices");

            migrationBuilder.DropColumn(
                name: "public_key",
                table: "devices");

            migrationBuilder.RenameColumn(
                name: "MacAddress",
                table: "devices",
                newName: "mac_address");

            migrationBuilder.CreateIndex(
                name: "IX_devices_mac_address",
                table: "devices",
                column: "mac_address");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropIndex(
                name: "IX_devices_mac_address",
                table: "devices");

            migrationBuilder.RenameColumn(
                name: "mac_address",
                table: "devices",
                newName: "MacAddress");

            migrationBuilder.AddColumn<string>(
                name: "public_key",
                table: "devices",
                type: "character varying(256)",
                maxLength: 256,
                nullable: false,
                defaultValue: "");

            migrationBuilder.CreateIndex(
                name: "IX_devices_public_key",
                table: "devices",
                column: "public_key");
        }
    }
}
