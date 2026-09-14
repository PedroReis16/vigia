using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Vigia.Database.Migrations
{
    /// <inheritdoc />
    public partial class GroupInviteEntity : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "group_invites",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    token = table.Column<string>(type: "text", nullable: false),
                    group_id = table.Column<Guid>(type: "uuid", nullable: false),
                    created_by_user_id = table.Column<Guid>(type: "uuid", nullable: false),
                    expires_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: false),
                    revoked_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: true),
                    created_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: false, defaultValueSql: "now()"),
                    updated_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: true),
                    deleted_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_group_invites", x => x.id);
                    table.ForeignKey(
                        name: "FK_group_invites_groups_group_id",
                        column: x => x.group_id,
                        principalTable: "groups",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "IX_group_invites_created_at",
                table: "group_invites",
                column: "created_at");

            migrationBuilder.CreateIndex(
                name: "IX_group_invites_created_by_user_id",
                table: "group_invites",
                column: "created_by_user_id");

            migrationBuilder.CreateIndex(
                name: "IX_group_invites_deleted_at",
                table: "group_invites",
                column: "deleted_at");

            migrationBuilder.CreateIndex(
                name: "IX_group_invites_expires_at",
                table: "group_invites",
                column: "expires_at");

            migrationBuilder.CreateIndex(
                name: "IX_group_invites_group_id",
                table: "group_invites",
                column: "group_id");

            migrationBuilder.CreateIndex(
                name: "IX_group_invites_token",
                table: "group_invites",
                column: "token",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_group_invites_updated_at",
                table: "group_invites",
                column: "updated_at");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "group_invites");
        }
    }
}
