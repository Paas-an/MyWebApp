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
pwsh -NoProfile -File ./scripts/PublishSeo.ps1 -PublishedRoot ./bin/Release/net10.0/publish/wwwroot
pwsh -NoProfile -File ./tests/SeoMetadata.ps1 -PublishedRoot ./bin/Release/net10.0/publish/wwwroot
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

## SEO and link previews

Run the two PowerShell 7 commands above after `dotnet publish`. CI does this
automatically. `PublishSeo.ps1` copies the literal `PageTitle` and `HeadContent`
from the home/contact Razor pages into the published HTML shells. Azure serves
`contact.html` internally for `/contact` and `/contact/`. This makes each route's
title, description and canonical URL available to crawlers that do not execute
JavaScript. This is metadata generation, not prerendering of the visible page.

`seo-bootstrap.js` removes only the generated route tags before Blazor starts;
`HeadOutlet` then owns them during client navigation. The shared Open Graph
image, Twitter large-image card and Schema.org `Person` JSON-LD remain in the
HTML head. The person record uses only the name, role and profile links already
published on the site; it does not claim eligibility for Google rich results.

The shared 1200 x 630 PNG is `wwwroot/images/social-card.png`; its editable vector
source is `assets/social-card.svg`. If the design changes, export the SVG to a
PNG at the same dimensions and update both files. The card deliberately uses
typography and the existing site colours rather than personal photographs.

### Search Console after merging

1. Open [Google Search Console](https://search.google.com/search-console/) and
   add the Domain property `olsenjonas.no` (or use the existing property).
2. Verify ownership using the DNS TXT record supplied by Google at the domain's
   DNS provider. Keep that record after verification. No account credentials or
   verification values belong in this repository.
3. Submit `https://www.olsenjonas.no/sitemap.xml` in Sitemaps.
4. Inspect `https://www.olsenjonas.no/` and `https://www.olsenjonas.no/contact`,
   run the live URL test and request indexing if needed. These steps require
   the site owner's Google account and are not performed by the deployment.
5. After deployment, check both URLs in a link-preview inspector (for example
   LinkedIn Post Inspector) to refresh old cached previews.

Google documents [site ownership and sitemap submission](https://developers.google.com/search/docs/monitor-debug/search-console-start).
Submitting a sitemap helps discovery but does not guarantee indexing.
