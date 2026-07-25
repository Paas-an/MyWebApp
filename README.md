# MyWebApp

A personal contact and portfolio site built with Blazor WebAssembly and deployed
to Azure Static Web Apps.

## Requirements

- .NET 10 SDK

The repository includes `global.json` to select the supported SDK.

## Local development

```powershell
dotnet restore
dotnet run
```

## Validate a release

```powershell
dotnet restore
dotnet build --configuration Release --no-restore
dotnet publish --configuration Release --no-build
```

The published static site is written to
`bin/Release/net10.0/publish/wwwroot`.

## Deployment

Pushes to `main` and pull requests targeting `main` are validated by GitHub
Actions. Successful builds are deployed to Azure Static Web Apps. The
`AZURE_STATIC_WEB_APPS_API_TOKEN_KIND_SAND_0CAAD6B03` repository secret must be
configured for deployment.

## Site contracts and monitoring

Run the lightweight SEO and routing contract checks with:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./tests/SiteContracts.ps1
```

GitHub Actions checks the production routes after each deployment and every six
hours. The scheduled workflow only performs HTTP availability checks and does
not add client-side tracking or collect visitor data.
