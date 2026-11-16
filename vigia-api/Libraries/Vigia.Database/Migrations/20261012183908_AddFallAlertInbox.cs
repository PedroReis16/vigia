using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Vigia.Database.Migrations
{
    /// <inheritdoc />
    public partial class AddFallAlertInbox : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "fall_alert_episodes",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    device_id = table.Column<Guid>(type: "uuid", nullable: false),
                    group_id = table.Column<Guid>(type: "uuid", nullable: false),
                    status = table.Column<string>(type: "character varying(16)", maxLength: 16, nullable: false),
                    first_detected_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: false),
                    last_notified_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: false),
                    next_retry_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: true),
                    notify_count = table.Column<int>(type: "integer", nullable: false),
                    acknowledged_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: true),
                    acknowledged_by_user_id = table.Column<Guid>(type: "uuid", nullable: true),
                    created_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: false, defaultValueSql: "now()"),
                    updated_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: true),
                    deleted_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_fall_alert_episodes", x => x.id);
                    table.ForeignKey(
                        name: "FK_fall_alert_episodes_devices_device_id",
                        column: x => x.device_id,
                        principalTable: "devices",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_fall_alert_episodes_groups_group_id",
                        column: x => x.group_id,
                        principalTable: "groups",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "user_notifications",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    user_id = table.Column<Guid>(type: "uuid", nullable: false),
                    episode_id = table.Column<Guid>(type: "uuid", nullable: false),
                    device_id = table.Column<Guid>(type: "uuid", nullable: false),
                    type = table.Column<string>(type: "character varying(32)", maxLength: 32, nullable: false),
                    title = table.Column<string>(type: "character varying(256)", maxLength: 256, nullable: false),
                    body = table.Column<string>(type: "character varying(1024)", maxLength: 1024, nullable: false),
                    read_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: true),
                    created_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: false, defaultValueSql: "now()"),
                    updated_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: true),
                    deleted_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_user_notifications", x => x.id);
                    table.ForeignKey(
                        name: "FK_user_notifications_devices_device_id",
                        column: x => x.device_id,
                        principalTable: "devices",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_user_notifications_fall_alert_episodes_episode_id",
                        column: x => x.episode_id,
                        principalTable: "fall_alert_episodes",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_user_notifications_users_user_id",
                        column: x => x.user_id,
                        principalTable: "users",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "IX_fall_alert_episodes_created_at",
                table: "fall_alert_episodes",
                column: "created_at");

            migrationBuilder.CreateIndex(
                name: "IX_fall_alert_episodes_deleted_at",
                table: "fall_alert_episodes",
                column: "deleted_at");

            migrationBuilder.CreateIndex(
                name: "IX_fall_alert_episodes_device_id_status",
                table: "fall_alert_episodes",
                columns: new[] { "device_id", "status" });

            migrationBuilder.CreateIndex(
                name: "IX_fall_alert_episodes_group_id",
                table: "fall_alert_episodes",
                column: "group_id");

            migrationBuilder.CreateIndex(
                name: "IX_fall_alert_episodes_next_retry_at",
                table: "fall_alert_episodes",
                column: "next_retry_at");

            migrationBuilder.CreateIndex(
                name: "IX_fall_alert_episodes_status",
                table: "fall_alert_episodes",
                column: "status");

            migrationBuilder.CreateIndex(
                name: "IX_fall_alert_episodes_updated_at",
                table: "fall_alert_episodes",
                column: "updated_at");

            migrationBuilder.CreateIndex(
                name: "IX_user_notifications_created_at",
                table: "user_notifications",
                column: "created_at");

            migrationBuilder.CreateIndex(
                name: "IX_user_notifications_deleted_at",
                table: "user_notifications",
                column: "deleted_at");

            migrationBuilder.CreateIndex(
                name: "IX_user_notifications_device_id",
                table: "user_notifications",
                column: "device_id");

            migrationBuilder.CreateIndex(
                name: "IX_user_notifications_episode_id",
                table: "user_notifications",
                column: "episode_id");

            migrationBuilder.CreateIndex(
                name: "IX_user_notifications_updated_at",
                table: "user_notifications",
                column: "updated_at");

            migrationBuilder.CreateIndex(
                name: "IX_user_notifications_user_id_created_at",
                table: "user_notifications",
                columns: new[] { "user_id", "created_at" });

            migrationBuilder.CreateIndex(
                name: "IX_user_notifications_user_id_episode_id",
                table: "user_notifications",
                columns: new[] { "user_id", "episode_id" });

            migrationBuilder.CreateIndex(
                name: "IX_user_notifications_user_id_read_at",
                table: "user_notifications",
                columns: new[] { "user_id", "read_at" });
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "user_notifications");

            migrationBuilder.DropTable(
                name: "fall_alert_episodes");
        }
    }
}
