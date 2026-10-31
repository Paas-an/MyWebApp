# MyWebApp

Personal portfolio built with Blazor WebAssembly and hosted on Azure Static Web Apps.

## Requirements

- .NET 10 SDK, selected by `global.json`.
- Python 3 for vessel imports and import tests.
- `openpyxl` for the engineering Excel importer:
  `python -m pip install -r scripts/requirements-engineering.txt`.

## Local development

```powershell
dotnet restore
dotnet run
```

## Release checks

```powershell
python -m unittest discover -s tests -p "test_*.py"
pwsh -NoProfile -File ./tests/SiteContracts.ps1
dotnet restore
dotnet build --configuration Release --no-restore
dotnet publish --configuration Release --no-build
pwsh -NoProfile -File ./scripts/PublishSeo.ps1 -PublishedRoot ./bin/Release/net10.0/publish/wwwroot
pwsh -NoProfile -File ./tests/SeoMetadata.ps1 -PublishedRoot ./bin/Release/net10.0/publish/wwwroot
```

The published site is in `bin/Release/net10.0/publish/wwwroot`.
Check `/`, `/contact`, `/vessels` and `/thea` on desktop and mobile before release.

## Deployment and monitoring

GitHub Actions validates pull requests and publishes changes merged into `main`.
Deployment uses the repository secret
`AZURE_STATIC_WEB_APPS_API_TOKEN_KIND_SAND_0CAAD6B03`.
The production monitor checks public routes after deployment and every six hours.

`PublishSeo.ps1` generates initial HTML metadata for the home, contact and vessel
routes. `wwwroot/js/seo-bootstrap.js` hands metadata ownership to Blazor during
startup; both are part of the deployment.

Cloudflare Web Analytics is configured in `wwwroot/index.html`.
Reports for `www.olsenjonas.no` are available in the Cloudflare Web Analytics dashboard.

## Data and design

See [vessel data](Features/Vessels/README.md) for imports and date updates.
Global styles are in `wwwroot/css/app.css`; component styles sit beside their
Razor files. The editable sharing-card design is `assets/social-card.svg`, with
its published PNG in `wwwroot/images/social-card.png`.
