namespace Vigia.API.Services.Clips;

internal readonly record struct ClipByteRange(long Start, long End)
{
    public string ContentRange(long total) => $"bytes {Start}-{End}/{total}";
}

internal static class ClipByteRanges
{
    public static bool TryResolve(string? header, long totalLength, out ClipByteRange range, out bool unsatisfiable)
    {
        range = default;
        unsatisfiable = false;

        if (string.IsNullOrWhiteSpace(header))
            return false;

        const string unit = "bytes=";
        if (!header.Trim().StartsWith(unit, StringComparison.OrdinalIgnoreCase))
        {
            unsatisfiable = true;
            return false;
        }

        string spec = header.Trim()[unit.Length..].Trim();
        if (spec.Length == 0 || spec.Contains(','))
        {
            unsatisfiable = true;
            return false;
        }

        if (totalLength <= 0)
        {
            unsatisfiable = true;
            return false;
        }

        if (spec.StartsWith('-'))
        {
            if (!long.TryParse(spec[1..], out long suffix) || suffix <= 0)
            {
                unsatisfiable = true;
                return false;
            }

            long length = Math.Min(suffix, totalLength);
            range = new ClipByteRange(totalLength - length, totalLength - 1);
            return true;
        }

        string[] parts = spec.Split('-', 2);
        if (parts.Length != 2 || !long.TryParse(parts[0], out long start) || start < 0)
        {
            unsatisfiable = true;
            return false;
        }

        long end;
        if (parts[1].Length == 0)
        {
            end = totalLength - 1;
        }
        else if (!long.TryParse(parts[1], out end) || end < start)
        {
            unsatisfiable = true;
            return false;
        }

        if (start >= totalLength)
        {
            unsatisfiable = true;
            return false;
        }

        if (end >= totalLength)
            end = totalLength - 1;

        range = new ClipByteRange(start, end);
        return true;
    }
}
