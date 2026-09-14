using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Vigia.Database.Migrations
{
    /// <inheritdoc />
    public partial class InitialMigration : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "groups",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    owner_id = table.Column<Guid>(type: "uuid", nullable: false),
                    created_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: false, defaultValueSql: "now()"),
                    updated_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: true),
                    deleted_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_groups", x => x.id);
                });

            migrationBuilder.CreateTable(
                name: "user_roles",
                columns: table => new
                {
                    id = table.Column<string>(type: "varchar", maxLength: 16, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_user_roles", x => x.id);
                });

            migrationBuilder.CreateTable(
                name: "users",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    name = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: false),
                    email = table.Column<string>(type: "character varying(256)", maxLength: 256, nullable: false),
                    password = table.Column<byte[]>(type: "bytea", nullable: false),
                    salt = table.Column<byte[]>(type: "bytea", nullable: false),
                    created_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: false, defaultValueSql: "now()"),
                    updated_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: true),
                    deleted_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_users", x => x.id);
                });

            migrationBuilder.CreateTable(
                name: "devices",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    name = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: false),
                    nickname = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: true),
                    MacAddress = table.Column<string>(type: "text", nullable: false),
                    public_key = table.Column<string>(type: "character varying(256)", maxLength: 256, nullable: false),
                    GroupId = table.Column<Guid>(type: "uuid", nullable: true),
                    created_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: false, defaultValueSql: "now()"),
                    updated_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: true),
                    deleted_at = table.Column<DateTime>(type: "timestamp without time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_devices", x => x.id);
                    table.ForeignKey(
                        name: "FK_devices_groups_GroupId",
                        column: x => x.GroupId,
                        principalTable: "groups",
                        principalColumn: "id");
                });

            migrationBuilder.CreateTable(
                name: "GroupUser",
                columns: table => new
                {
                    LinkedGroupsId = table.Column<Guid>(type: "uuid", nullable: false),
                    LinkedUsersId = table.Column<Guid>(type: "uuid", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_GroupUser", x => new { x.LinkedGroupsId, x.LinkedUsersId });
                    table.ForeignKey(
                        name: "FK_GroupUser_groups_LinkedGroupsId",
                        column: x => x.LinkedGroupsId,
                        principalTable: "groups",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_GroupUser_users_LinkedUsersId",
                        column: x => x.LinkedUsersId,
                        principalTable: "users",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "UserUserRole",
                columns: table => new
                {
                    RolesId = table.Column<string>(type: "varchar", nullable: false),
                    UsersId = table.Column<Guid>(type: "uuid", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_UserUserRole", x => new { x.RolesId, x.UsersId });
                    table.ForeignKey(
                        name: "FK_UserUserRole_user_roles_RolesId",
                        column: x => x.RolesId,
                        principalTable: "user_roles",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_UserUserRole_users_UsersId",
                        column: x => x.UsersId,
                        principalTable: "users",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.InsertData(
                table: "groups",
                columns: new[] { "id", "created_at", "deleted_at", "owner_id", "updated_at" },
                values: new object[] { new Guid("80eed123-8e77-47a3-8fae-cedb1ab3eef7"), new DateTime(2026, 7, 27, 17, 42, 22, 525, DateTimeKind.Utc).AddTicks(2940), null, new Guid("05ae0d5a-5ef8-44c4-a6de-df0725cdd39b"), null });

            migrationBuilder.InsertData(
                table: "user_roles",
                column: "id",
                values: new object[]
                {
                    "ADMIN",
                    "USER"
                });

            migrationBuilder.InsertData(
                table: "users",
                columns: new[] { "id", "created_at", "deleted_at", "email", "name", "password", "salt", "updated_at" },
                values: new object[] { new Guid("05ae0d5a-5ef8-44c4-a6de-df0725cdd39b"), new DateTime(2026, 7, 27, 17, 42, 22, 525, DateTimeKind.Utc).AddTicks(2940), null, "admin", "Super usuário", new byte[] { 247, 20, 118, 226, 219, 244, 66, 63, 99, 191, 56, 69, 182, 188, 218, 205, 232, 246, 129, 67, 89, 225, 107, 134, 235, 44, 161, 82, 105, 104, 181, 107 }, new byte[] { 2, 20, 73, 2, 70, 73, 43, 120, 27, 233, 195, 53, 98, 210, 219, 129 }, null });

            // Inserção dos dados de relacionamento dos dados gerados com a criação das tabelas
            InsertRelationshipsData(migrationBuilder);

            migrationBuilder.CreateIndex(
                name: "IX_devices_created_at",
                table: "devices",
                column: "created_at");

            migrationBuilder.CreateIndex(
                name: "IX_devices_deleted_at",
                table: "devices",
                column: "deleted_at");

            migrationBuilder.CreateIndex(
                name: "IX_devices_GroupId",
                table: "devices",
                column: "GroupId");

            migrationBuilder.CreateIndex(
                name: "IX_devices_name",
                table: "devices",
                column: "name");

            migrationBuilder.CreateIndex(
                name: "IX_devices_nickname",
                table: "devices",
                column: "nickname");

            migrationBuilder.CreateIndex(
                name: "IX_devices_public_key",
                table: "devices",
                column: "public_key");

            migrationBuilder.CreateIndex(
                name: "IX_devices_updated_at",
                table: "devices",
                column: "updated_at");

            migrationBuilder.CreateIndex(
                name: "IX_groups_created_at",
                table: "groups",
                column: "created_at");

            migrationBuilder.CreateIndex(
                name: "IX_groups_deleted_at",
                table: "groups",
                column: "deleted_at");

            migrationBuilder.CreateIndex(
                name: "IX_groups_owner_id",
                table: "groups",
                column: "owner_id",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_groups_updated_at",
                table: "groups",
                column: "updated_at");

            migrationBuilder.CreateIndex(
                name: "IX_GroupUser_LinkedUsersId",
                table: "GroupUser",
                column: "LinkedUsersId");

            migrationBuilder.CreateIndex(
                name: "IX_user_roles_id",
                table: "user_roles",
                column: "id",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_users_created_at",
                table: "users",
                column: "created_at");

            migrationBuilder.CreateIndex(
                name: "IX_users_deleted_at",
                table: "users",
                column: "deleted_at");

            migrationBuilder.CreateIndex(
                name: "IX_users_email",
                table: "users",
                column: "email");

            migrationBuilder.CreateIndex(
                name: "IX_users_name",
                table: "users",
                column: "name");

            migrationBuilder.CreateIndex(
                name: "IX_users_updated_at",
                table: "users",
                column: "updated_at");

            migrationBuilder.CreateIndex(
                name: "IX_UserUserRole_UsersId",
                table: "UserUserRole",
                column: "UsersId");
        }

        private void InsertRelationshipsData(MigrationBuilder migrationBuilder)
        {

            // Usuário e grupo
            migrationBuilder.InsertData(
                table: "GroupUser",
                columns: new[] { "LinkedGroupsId", "LinkedUsersId" },
                values: new object[] { new Guid("80eed123-8e77-47a3-8fae-cedb1ab3eef7"), new Guid("05ae0d5a-5ef8-44c4-a6de-df0725cdd39b") });

            // Usuário e role
            migrationBuilder.InsertData(
                table: "UserUserRole",
                columns: new[] { "RolesId", "UsersId" },
                values: new object[] { "ADMIN", new Guid("05ae0d5a-5ef8-44c4-a6de-df0725cdd39b") });

            migrationBuilder.InsertData(
                table: "UserUserRole",
                columns: new[] { "RolesId", "UsersId" },
                values: new object[] { "USER", new Guid("05ae0d5a-5ef8-44c4-a6de-df0725cdd39b") });
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "devices");

            migrationBuilder.DropTable(
                name: "GroupUser");

            migrationBuilder.DropTable(
                name: "UserUserRole");

            migrationBuilder.DropTable(
                name: "groups");

            migrationBuilder.DropTable(
                name: "user_roles");

            migrationBuilder.DropTable(
                name: "users");
        }
    }
}
