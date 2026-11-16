using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Vigia.Database.Migrations
{
    /// <inheritdoc />
    public partial class AddDeviceClip : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "device_clips",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    device_id = table.Column<Guid>(type: "uuid", nullable: false),
                    status = table.Column<string>(type: "character varying(16)", maxLength: 16, nullable: false),
                    frame_count = table.Column<int>(type: "integer", nullable: false),
                    fps = table.Column<int>(type: "integer", nullable: false),
                    object_key = table.Column<string>(type: "character varying(512)", maxLength: 512, nullable: true),
                    created_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: false, defaultValueSql: "now()"),
                    updated_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: true),
                    deleted_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_device_clips", x => x.id);
                    table.ForeignKey(
                        name: "FK_device_clips_devices_device_id",
                        column: x => x.device_id,
                        principalTable: "devices",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "IX_device_clips_created_at",
                table: "device_clips",
                column: "created_at");

            migrationBuilder.CreateIndex(
                name: "IX_device_clips_deleted_at",
                table: "device_clips",
                column: "deleted_at");

            migrationBuilder.CreateIndex(
                name: "IX_device_clips_device_id",
                table: "device_clips",
                column: "device_id");

            migrationBuilder.CreateIndex(
                name: "IX_device_clips_status",
                table: "device_clips",
                column: "status");

            migrationBuilder.CreateIndex(
                name: "IX_device_clips_updated_at",
                table: "device_clips",
                column: "updated_at");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "device_clips");
        }
    }
}
