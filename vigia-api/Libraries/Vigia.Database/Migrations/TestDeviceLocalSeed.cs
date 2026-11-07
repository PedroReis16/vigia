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
        int createdDevices = EnsureDevices(db);
        bool linked = EnsureMembership(db, admin);
        db.SaveChanges();

        if (createdDevices == 0 && !linked)
            return;

        logger?.LogInformation(
            "Seed DEBUG: {CreatedCount} device(s); edge={EdgeId}; mockPool={MockCount}; admin={UserId}",
            createdDevices,
            TestDeviceSeed.Id,
            MockDevicesSeed.All.Count,
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

    private static int EnsureDevices(VigiaDbContext db)
    {
        int created = 0;

        if (!db.Devices.Any(d => d.Id == TestDeviceSeed.Id))
        {
            db.Devices.Add(TestDeviceSeed.Create());
            created++;
        }

        foreach (MockDeviceDefinition definition in MockDevicesSeed.All)
        {
            if (definition.Id == TestDeviceSeed.Id)
                throw new InvalidOperationException(
                    "MockDevicesSeed não pode incluir o ID do TestDeviceSeed (edge real).");

            if (db.Devices.Any(d => d.Id == definition.Id))
                continue;

            db.Devices.Add(MockDevicesSeed.Create(definition));
            created++;
        }

        return created;
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
