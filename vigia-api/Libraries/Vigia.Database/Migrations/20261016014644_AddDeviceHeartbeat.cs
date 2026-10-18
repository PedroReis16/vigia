using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Vigia.Database.Migrations
{
    /// <inheritdoc />
    public partial class AddDeviceHeartbeat : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<string>(
                name: "kind",
                table: "fall_alert_episodes",
                type: "character varying(32)",
                maxLength: 32,
                nullable: false,
                defaultValue: "Fall");

            migrationBuilder.AddColumn<DateTime>(
                name: "last_heartbeat_at",
                table: "devices",
                type: "timestamp without time zone",
                nullable: true);

            migrationBuilder.CreateIndex(
                name: "IX_fall_alert_episodes_device_id_kind_status",
                table: "fall_alert_episodes",
                columns: new[] { "device_id", "kind", "status" });

            migrationBuilder.CreateIndex(
                name: "IX_devices_last_heartbeat_at",
                table: "devices",
                column: "last_heartbeat_at");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropIndex(
                name: "IX_fall_alert_episodes_device_id_kind_status",
                table: "fall_alert_episodes");

            migrationBuilder.DropIndex(
                name: "IX_devices_last_heartbeat_at",
                table: "devices");

            migrationBuilder.DropColumn(
                name: "kind",
                table: "fall_alert_episodes");

            migrationBuilder.DropColumn(
                name: "last_heartbeat_at",
                table: "devices");
        }
    }
}
