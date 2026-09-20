using System.Globalization;
using System.Text.Json.Serialization;

namespace webapp.Features.Vessels;

public sealed class VesselHistory
{
    public int SchemaVersion { get; init; }
    public string Category { get; init; } = "";
    public List<Vessel> Vessels { get; init; } = [];
}

public sealed class Vessel
{
    public string Id { get; init; } = "";
    public string Name { get; init; } = "";
    public string? Note { get; init; }
    public List<VesselEntry> Entries { get; init; } = [];

    [JsonIgnore]
    public decimal? TotalTonnes => Entries.Any(entry => entry.IncludeInTotal && entry.Tonnes.HasValue)
        ? Entries.Where(entry => entry.IncludeInTotal).Sum(entry => entry.Tonnes ?? 0)
        : null;

    [JsonIgnore]
    public bool HasExcludedWeights => Entries.Any(entry => !entry.IncludeInTotal);
}

public sealed class VesselEntry
{
    public string Id { get; init; } = "";
    public List<WorkPeriod> Periods { get; init; } = [];
    public decimal? Tonnes { get; init; }
    public string? TonnageKind { get; init; }
    public bool IncludeInTotal { get; init; }
    public string? Description { get; init; }
    public List<string> SourceUrls { get; init; } = [];
}

public sealed class WorkPeriod
{
    public DateOnly Start { get; init; }
    public DateOnly? End { get; init; }

    public string Display => End.HasValue && End.Value != Start
        ? $"{Start:dd.MM.yyyy}–{End.Value:dd.MM.yyyy}"
        : Start.ToString("dd.MM.yyyy", CultureInfo.InvariantCulture);
}
