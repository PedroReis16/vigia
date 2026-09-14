using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Vigia.Database.Migrations
{
    /// <inheritdoc />
    public partial class UserPushTokenEntity : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "user_push_tokens",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    user_id = table.Column<Guid>(type: "uuid", nullable: false),
                    token = table.Column<string>(type: "character varying(512)", maxLength: 512, nullable: false),
                    platform = table.Column<string>(type: "character varying(16)", maxLength: 16, nullable: false),
                    created_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: false, defaultValueSql: "now()"),
                    updated_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: true),
                    deleted_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_user_push_tokens", x => x.id);
                });

            migrationBuilder.UpdateData(
                table: "fiware_properties",
                keyColumn: "id",
                keyValue: new Guid("61675835-4749-4001-8236-013206775835"),
                column: "attributes",
                value: "[{\"ObjectId\":\"s\",\"Name\":\"system_status\",\"Type\":\"Text\"},{\"ObjectId\":\"ns\",\"Name\":\"network_status\",\"Type\":\"Text\"},{\"ObjectId\":\"ss\",\"Name\":\"stream_status\",\"Type\":\"Text\"},{\"ObjectId\":\"dp\",\"Name\":\"detected_person\",\"Type\":\"Boolean\"},{\"ObjectId\":\"fall\",\"Name\":\"fall_state\",\"Type\":\"Text\"}]");

            migrationBuilder.CreateIndex(
                name: "IX_user_push_tokens_created_at",
                table: "user_push_tokens",
                column: "created_at");

            migrationBuilder.CreateIndex(
                name: "IX_user_push_tokens_deleted_at",
                table: "user_push_tokens",
                column: "deleted_at");

            migrationBuilder.CreateIndex(
                name: "IX_user_push_tokens_token",
                table: "user_push_tokens",
                column: "token",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_user_push_tokens_updated_at",
                table: "user_push_tokens",
                column: "updated_at");

            migrationBuilder.CreateIndex(
                name: "IX_user_push_tokens_user_id",
                table: "user_push_tokens",
                column: "user_id");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "user_push_tokens");

            migrationBuilder.UpdateData(
                table: "fiware_properties",
                keyColumn: "id",
                keyValue: new Guid("61675835-4749-4001-8236-013206775835"),
                column: "attributes",
                value: "[{\"ObjectId\":\"s\",\"Name\":\"system_status\",\"Type\":\"Text\"},{\"ObjectId\":\"ss\",\"Name\":\"stream_status\",\"Type\":\"Text\"},{\"ObjectId\":\"dp\",\"Name\":\"detected_person\",\"Type\":\"Boolean\"},{\"ObjectId\":\"df\",\"Name\":\"detected_fall\",\"Type\":\"Boolean\"}]");
        }
    }
}
