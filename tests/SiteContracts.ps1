$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repositoryRoot = Split-Path -Parent $PSScriptRoot

function Read-RepositoryFile {
    param([Parameter(Mandatory)][string]$RelativePath)

    return Get-Content `
        -LiteralPath (Join-Path $repositoryRoot $RelativePath) `
        -Raw `
        -Encoding utf8
}

function Assert-Contains {
    param(
        [Parameter(Mandatory)][string]$Content,
        [Parameter(Mandatory)][string]$Expected,
        [Parameter(Mandatory)][string]$Description
    )

    if ($Content.IndexOf($Expected, [StringComparison]::Ordinal) -lt 0) {
        throw "Contract failed: $Description"
    }
}

$homePage = Read-RepositoryFile "Pages/Index.razor"
$contactPage = Read-RepositoryFile "Pages/Contact.razor"
$privatePage = Read-RepositoryFile "Pages/Thea.razor"
$notFoundPage = Read-RepositoryFile "Shared/MyNotFound.razor"
$robots = Read-RepositoryFile "wwwroot/robots.txt"
$sitemapText = Read-RepositoryFile "wwwroot/sitemap.xml"
$staticWebAppConfigText = Read-RepositoryFile "wwwroot/staticwebapp.config.json"

Assert-Contains $homePage '<PageTitle>' "home page must have a title"
Assert-Contains $homePage 'name="description"' "home page must have a description"
Assert-Contains $homePage 'rel="canonical"' "home page must have a canonical URL"
Assert-Contains $homePage 'property="og:title"' "home page must have Open Graph metadata"

Assert-Contains $contactPage '<PageTitle>' "contact page must have a title"
Assert-Contains $contactPage 'name="description"' "contact page must have a description"
Assert-Contains $contactPage 'rel="canonical"' "contact page must have a canonical URL"
Assert-Contains $contactPage 'property="og:title"' "contact page must have Open Graph metadata"

Assert-Contains $privatePage 'noindex, nofollow' "/thea is intentionally public but must not be indexed"
Assert-Contains $privatePage 'Den fineste jenta i verden' "/thea must contain the intentional personal message"
if ($privatePage.IndexOf("<style>", [StringComparison]::OrdinalIgnoreCase) -ge 0) {
    throw "Contract failed: /thea styles must use the shared design system"
}
Assert-Contains $notFoundPage 'noindex, nofollow' "not-found content must not be indexed"
Assert-Contains $robots 'Disallow: /thea' "robots.txt must protect /thea from indexing"
Assert-Contains $robots 'https://www.olsenjonas.no/sitemap.xml' "robots.txt must reference the sitemap"

[xml]$sitemap = $sitemapText
$sitemapUrls = @($sitemap.urlset.url.loc)
if ($sitemapUrls.Count -ne 2) {
    throw "Contract failed: sitemap must contain exactly the two public routes"
}
if ($sitemapUrls -notcontains "https://www.olsenjonas.no/") {
    throw "Contract failed: sitemap must contain the home page"
}
if ($sitemapUrls -notcontains "https://www.olsenjonas.no/contact") {
    throw "Contract failed: sitemap must contain the contact page"
}
if ($sitemapUrls -contains "https://www.olsenjonas.no/thea") {
    throw "Contract failed: sitemap must not expose /thea"
}

$staticWebAppConfig = $staticWebAppConfigText | ConvertFrom-Json
if ($staticWebAppConfig.navigationFallback.rewrite -ne "/index.html") {
    throw "Contract failed: direct SPA navigation must rewrite to /index.html"
}

Write-Host "All site contracts passed."
