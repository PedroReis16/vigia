using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Vigia.Database.Migrations
{
    /// <inheritdoc />
    public partial class FiwarePropertiesEntity : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "fiware_properties",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    protocol = table.Column<string>(type: "text", nullable: false),
                    transport = table.Column<string>(type: "text", nullable: false),
                    commands = table.Column<string>(type: "jsonb", nullable: false),
                    attributes = table.Column<string>(type: "jsonb", nullable: false),
                    created_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: false, defaultValueSql: "now()"),
                    updated_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: true),
                    deleted_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_fiware_properties", x => x.id);
                });

            migrationBuilder.InsertData(
                table: "fiware_properties",
                columns: new[] { "id", "attributes", "commands", "created_at", "deleted_at", "protocol", "transport", "updated_at" },
                values: new object[] { new Guid("61675835-4749-4001-8236-013206775835"), "[{\"ObjectId\":\"s\",\"Name\":\"system_status\",\"Type\":\"Text\"},{\"ObjectId\":\"ss\",\"Name\":\"stream_status\",\"Type\":\"Text\"},{\"ObjectId\":\"dp\",\"Name\":\"detected_person\",\"Type\":\"Boolean\"},{\"ObjectId\":\"df\",\"Name\":\"detected_fall\",\"Type\":\"Boolean\"}]", "[{\"Name\":\"stream_on\",\"Type\":\"command\"},{\"Name\":\"stream_off\",\"Type\":\"command\"},{\"Name\":\"device_on\",\"Type\":\"command\"},{\"Name\":\"device_off\",\"Type\":\"command\"}]", new DateTime(2026, 7, 30, 10, 0, 0, 0, DateTimeKind.Unspecified), null, "PDI-IoTA-UltraLight", "MQTT", null });

            migrationBuilder.CreateIndex(
                name: "IX_fiware_properties_created_at",
                table: "fiware_properties",
                column: "created_at");

            migrationBuilder.CreateIndex(
                name: "IX_fiware_properties_deleted_at",
                table: "fiware_properties",
                column: "deleted_at");

            migrationBuilder.CreateIndex(
                name: "IX_fiware_properties_updated_at",
                table: "fiware_properties",
                column: "updated_at");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "fiware_properties");
        }
    }
}
