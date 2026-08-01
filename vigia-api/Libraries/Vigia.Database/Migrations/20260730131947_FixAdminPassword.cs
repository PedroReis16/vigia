using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Vigia.Database.Migrations
{
    /// <inheritdoc />
    public partial class FixAdminPassword : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.UpdateData(
                table: "users",
                keyColumn: "id",
                keyValue: new Guid("05ae0d5a-5ef8-44c4-a6de-df0725cdd39b"),
                column: "password",
                value: new byte[] { 81, 63, 165, 86, 58, 124, 112, 36, 10, 178, 217, 152, 172, 164, 210, 132, 253, 161, 96, 153, 164, 26, 37, 230, 224, 66, 50, 93, 84, 223, 94, 216 });
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.UpdateData(
                table: "users",
                keyColumn: "id",
                keyValue: new Guid("05ae0d5a-5ef8-44c4-a6de-df0725cdd39b"),
                column: "password",
                value: new byte[] { 247, 20, 118, 226, 219, 244, 66, 63, 99, 191, 56, 69, 182, 188, 218, 205, 232, 246, 129, 67, 89, 225, 107, 134, 235, 44, 161, 82, 105, 104, 181, 107 });
        }
    }
}
