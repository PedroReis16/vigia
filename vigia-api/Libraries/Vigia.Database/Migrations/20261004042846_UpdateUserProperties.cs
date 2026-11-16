using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Vigia.Database.Migrations
{
    /// <inheritdoc />
    public partial class UpdateUserProperties : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DeleteData(
                table: "users",
                keyColumn: "id",
                keyValue: new Guid("05ae0d5a-5ef8-44c4-a6de-df0725cdd39b"));

            migrationBuilder.DropColumn(
                name: "password",
                table: "users");

            migrationBuilder.DropColumn(
                name: "salt",
                table: "users");

            migrationBuilder.RenameColumn(
                name: "name",
                table: "users",
                newName: "last_name");

            migrationBuilder.RenameIndex(
                name: "IX_users_name",
                table: "users",
                newName: "IX_users_last_name");

            migrationBuilder.AddColumn<string>(
                name: "first_name",
                table: "users",
                type: "character varying(64)",
                maxLength: 64,
                nullable: false,
                defaultValue: "");

            migrationBuilder.AddColumn<string>(
                name: "phone",
                table: "users",
                type: "character varying(16)",
                maxLength: 16,
                nullable: false,
                defaultValue: "");

            migrationBuilder.CreateIndex(
                name: "IX_users_first_name",
                table: "users",
                column: "first_name");

            migrationBuilder.CreateIndex(
                name: "IX_users_phone",
                table: "users",
                column: "phone");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropIndex(
                name: "IX_users_first_name",
                table: "users");

            migrationBuilder.DropIndex(
                name: "IX_users_phone",
                table: "users");

            migrationBuilder.DropColumn(
                name: "first_name",
                table: "users");

            migrationBuilder.DropColumn(
                name: "phone",
                table: "users");

            migrationBuilder.RenameColumn(
                name: "last_name",
                table: "users",
                newName: "name");

            migrationBuilder.RenameIndex(
                name: "IX_users_last_name",
                table: "users",
                newName: "IX_users_name");

            migrationBuilder.AddColumn<byte[]>(
                name: "password",
                table: "users",
                type: "bytea",
                nullable: false,
                defaultValue: new byte[0]);

            migrationBuilder.AddColumn<byte[]>(
                name: "salt",
                table: "users",
                type: "bytea",
                nullable: false,
                defaultValue: new byte[0]);

            migrationBuilder.InsertData(
                table: "users",
                columns: new[] { "id", "created_at", "deleted_at", "email", "name", "password", "salt", "updated_at" },
                values: new object[] { new Guid("05ae0d5a-5ef8-44c4-a6de-df0725cdd39b"), new DateTime(2026, 7, 27, 17, 42, 22, 525, DateTimeKind.Utc).AddTicks(2940), null, "admin", "Super usuário", new byte[] { 81, 63, 165, 86, 58, 124, 112, 36, 10, 178, 217, 152, 172, 164, 210, 132, 253, 161, 96, 153, 164, 26, 37, 230, 224, 66, 50, 93, 84, 223, 94, 216 }, new byte[] { 2, 20, 73, 2, 70, 73, 43, 120, 27, 233, 195, 53, 98, 210, 219, 129 }, null });
        }
    }
}
