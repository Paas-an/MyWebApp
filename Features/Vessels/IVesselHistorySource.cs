namespace webapp.Features.Vessels;

public interface IVesselHistorySource
{
    Task<VesselHistory> LoadAsync(string category, CancellationToken cancellationToken = default);
}
