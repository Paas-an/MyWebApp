using System.Net.Http.Json;

namespace webapp.Features.Vessels;

public sealed class JsonVesselHistorySource(HttpClient http) : IVesselHistorySource
{
    public async Task<VesselHistory> LoadAsync(string category, CancellationToken cancellationToken = default)
    {
        if (category is not ("engineering" or "unloading"))
            throw new ArgumentOutOfRangeException(nameof(category));

        var history = await http.GetFromJsonAsync<VesselHistory>($"data/vessels/{category}.json", cancellationToken)
            ?? throw new InvalidDataException("Vessel history is empty.");
        if (history.SchemaVersion != 1 || history.Category != category || history.Vessels is null)
            throw new InvalidDataException("Unsupported vessel history.");

        var vesselIds = new HashSet<string>();
        foreach (var vessel in history.Vessels)
        {
            if (vessel is null || string.IsNullOrWhiteSpace(vessel.Id) || !vesselIds.Add(vessel.Id)
                || string.IsNullOrWhiteSpace(vessel.Name) || vessel.Entries is null)
                throw new InvalidDataException("Invalid vessel record.");

            var entryIds = new HashSet<string>();
            foreach (var entry in vessel.Entries)
            {
                if (entry is null || string.IsNullOrWhiteSpace(entry.Id) || !entryIds.Add(entry.Id)
                    || entry.Periods is null || entry.Periods.Count == 0 || entry.SourceUrls is null
                    || entry.Periods.Any(period => period is null || period.Start == default || period.End < period.Start)
                    || entry.Tonnes < 0 || (entry.IncludeInTotal && entry.Tonnes is null))
                    throw new InvalidDataException("Invalid work history entry.");
            }
        }
        return history;
    }
}
