using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Vigia.Database.Migrations
{
    /// <inheritdoc />
    public partial class AddDeviceClientCertificate : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<DateTime>(
                name: "client_certificate_not_after",
                table: "devices",
                type: "timestamp without time zone",
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "client_certificate_serial",
                table: "devices",
                type: "character varying(64)",
                maxLength: 64,
                nullable: true);

            migrationBuilder.CreateIndex(
                name: "IX_devices_client_certificate_serial",
                table: "devices",
                column: "client_certificate_serial",
                unique: true,
                filter: "client_certificate_serial IS NOT NULL");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropIndex(
                name: "IX_devices_client_certificate_serial",
                table: "devices");

            migrationBuilder.DropColumn(
                name: "client_certificate_not_after",
                table: "devices");

            migrationBuilder.DropColumn(
                name: "client_certificate_serial",
                table: "devices");
        }
    }
}
