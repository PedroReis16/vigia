using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Vigia.Models.Entities;
using Vigia.Models.Seed;

namespace Vigia.Database.Migrations;

internal static class TestDeviceLocalSeed
{
    public static void Apply(VigiaDbContext db, ILogger? logger)
    {
        User admin = EnsureAdmin(db);
        bool createdDevice = EnsureDevice(db);
        bool linked = EnsureMembership(db, admin);
        db.SaveChanges();

        if (!createdDevice && !linked)
            return;

        logger?.LogInformation(
            "Device de teste {DeviceId} ({DeviceName}) vinculado ao usuário {UserId} (DEBUG)",
            TestDeviceSeed.Id,
            TestDeviceSeed.Name,
            TestDeviceSeed.OwnerId);
    }

    private static User EnsureAdmin(VigiaDbContext db)
    {
        User? admin = db.Users.FirstOrDefault(u => u.Id == TestDeviceSeed.OwnerId);
        if (admin == null)
        {
            admin = new User
            {
                Id = TestDeviceSeed.OwnerId,
                Email = TestDeviceSeed.OwnerEmail,
                Phone = TestDeviceSeed.OwnerPhone,
                CreatedAt = TestDeviceSeed.CreatedAt,
                LinkedGroups = [],
            };
            db.Users.Add(admin);
            return admin;
        }

        if (admin.DeletedAt != null)
        {
            admin.DeletedAt = null;
            admin.UpdatedAt = DateTime.UtcNow;
        }

        return admin;
    }

    private static bool EnsureDevice(VigiaDbContext db)
    {
        if (db.Devices.Any(d => d.Id == TestDeviceSeed.Id))
            return false;

        db.Devices.Add(TestDeviceSeed.Create());
        return true;
    }

    private static bool EnsureMembership(VigiaDbContext db, User admin)
    {
        Group? group = db.Groups
            .Include(g => g.LinkedUsers)
            .FirstOrDefault(g => g.Id == TestDeviceSeed.GroupId && g.DeletedAt == null);

        if (group == null)
            return false;

        group.LinkedUsers ??= [];
        if (group.LinkedUsers.Any(u => u.Id == admin.Id))
            return false;

        group.LinkedUsers.Add(admin);
        group.UpdatedAt = DateTime.UtcNow;
        return true;
    }
}
