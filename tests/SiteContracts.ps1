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

function Assert-Matches {
    param(
        [Parameter(Mandatory)][string]$Content,
        [Parameter(Mandatory)][string]$Pattern,
        [Parameter(Mandatory)][string]$Description
    )

    if (-not [regex]::IsMatch(
        $Content,
        $Pattern,
        [Text.RegularExpressions.RegexOptions]::IgnoreCase -bor
        [Text.RegularExpressions.RegexOptions]::Singleline
    )) {
        throw "Contract failed: $Description"
    }
}

function Get-CanonicalUrl {
    param(
        [Parameter(Mandatory)][string]$Content,
        [Parameter(Mandatory)][string]$PageName
    )

    $match = [regex]::Match(
        $Content,
        '<link\b(?=[^>]*\brel="canonical")(?=[^>]*\bhref="([^"]+)")[^>]*>',
        [Text.RegularExpressions.RegexOptions]::IgnoreCase
    )
    if (-not $match.Success) {
        throw "Contract failed: $PageName must have a canonical URL"
    }

    $canonicalUrl = $match.Groups[1].Value
    $uri = $null
    if (
        -not [Uri]::TryCreate($canonicalUrl, [UriKind]::Absolute, [ref]$uri) -or
        $uri.Scheme -ne [Uri]::UriSchemeHttps
    ) {
        throw "Contract failed: $PageName canonical URL must be an absolute HTTPS URL"
    }

    return $canonicalUrl
}

$homePage = Read-RepositoryFile "Pages/Index.razor"
$contactPage = Read-RepositoryFile "Pages/Contact.razor"
$privatePage = Read-RepositoryFile "Pages/Thea.razor"
$notFoundPage = Read-RepositoryFile "Shared/MyNotFound.razor"
$robots = Read-RepositoryFile "wwwroot/robots.txt"
$sitemapText = Read-RepositoryFile "wwwroot/sitemap.xml"
$staticWebAppConfigText = Read-RepositoryFile "wwwroot/staticwebapp.config.json"

$publicPages = @(
    @{ Name = "home page"; Content = $homePage },
    @{ Name = "contact page"; Content = $contactPage }
)
$canonicalUrls = @()

foreach ($page in $publicPages) {
    Assert-Matches $page.Content '<PageTitle>\s*[^<]+\s*</PageTitle>' "$($page.Name) must have a non-empty title"
    Assert-Matches $page.Content '<meta\b(?=[^>]*\bname="description")(?=[^>]*\bcontent="[^"]+")[^>]*>' "$($page.Name) must have a non-empty description"
    Assert-Matches $page.Content '<meta\b(?=[^>]*\bproperty="og:title")(?=[^>]*\bcontent="[^"]+")[^>]*>' "$($page.Name) must have an Open Graph title"
    $canonicalUrls += Get-CanonicalUrl $page.Content $page.Name
}

Assert-Matches $privatePage '<meta\b(?=[^>]*\bname="robots")(?=[^>]*\bcontent="[^"]*noindex[^"]*")[^>]*>' "/thea must not be indexed"
Assert-Matches $privatePage '<h1\b[^>]*\bid="thea-title"[^>]*>\s*[^<]+\s*</h1>' "/thea must have a non-empty main heading"

$imageTags = [regex]::Matches(
    $privatePage,
    '<img\b[^>]*>',
    [Text.RegularExpressions.RegexOptions]::IgnoreCase
)
if ($imageTags.Count -eq 0) {
    throw "Contract failed: /thea must contain at least one image"
}
foreach ($imageTag in $imageTags) {
    $sourceMatch = [regex]::Match($imageTag.Value, '\bsrc="([^"]+)"', [Text.RegularExpressions.RegexOptions]::IgnoreCase)
    $altMatch = [regex]::Match($imageTag.Value, '\balt="([^"]+)"', [Text.RegularExpressions.RegexOptions]::IgnoreCase)
    if (-not $sourceMatch.Success) {
        throw "Contract failed: every /thea image must have a source"
    }
    if (-not $altMatch.Success -or [string]::IsNullOrWhiteSpace($altMatch.Groups[1].Value)) {
        throw "Contract failed: every /thea image must have descriptive alternative text"
    }

    $imageSource = $sourceMatch.Groups[1].Value
    if ($imageSource -notmatch '^https?://') {
        $imagePath = Join-Path $repositoryRoot ("wwwroot/" + $imageSource.TrimStart("/"))
        if (-not (Test-Path -LiteralPath $imagePath -PathType Leaf)) {
            throw "Contract failed: referenced image does not exist: $imageSource"
        }
    }
}
if ($privatePage.IndexOf("<style>", [StringComparison]::OrdinalIgnoreCase) -ge 0) {
    throw "Contract failed: /thea styles must use the shared design system"
}
Assert-Matches $notFoundPage '<meta\b(?=[^>]*\bname="robots")(?=[^>]*\bcontent="[^"]*noindex[^"]*")[^>]*>' "not-found content must not be indexed"
Assert-Matches $robots '(?m)^Disallow:\s*/thea/?\s*$' "robots.txt must protect /thea from indexing"

$sitemapReference = [regex]::Match(
    $robots,
    '(?m)^Sitemap:\s*(\S+)\s*$',
    [Text.RegularExpressions.RegexOptions]::IgnoreCase
)
if (-not $sitemapReference.Success) {
    throw "Contract failed: robots.txt must reference a sitemap"
}
$sitemapUri = $null
if (
    -not [Uri]::TryCreate($sitemapReference.Groups[1].Value, [UriKind]::Absolute, [ref]$sitemapUri) -or
    $sitemapUri.Scheme -ne [Uri]::UriSchemeHttps -or
    -not $sitemapUri.AbsolutePath.EndsWith("/sitemap.xml", [StringComparison]::OrdinalIgnoreCase)
) {
    throw "Contract failed: robots.txt sitemap reference must be an absolute HTTPS sitemap URL"
}

[xml]$sitemap = $sitemapText
$sitemapUrls = @($sitemap.urlset.url.loc)
if ($sitemapUrls.Count -eq 0) {
    throw "Contract failed: sitemap must contain at least one public route"
}
if (@($sitemapUrls | Select-Object -Unique).Count -ne $sitemapUrls.Count) {
    throw "Contract failed: sitemap URLs must be unique"
}
foreach ($sitemapUrl in $sitemapUrls) {
    $uri = $null
    if (
        -not [Uri]::TryCreate($sitemapUrl, [UriKind]::Absolute, [ref]$uri) -or
        $uri.Scheme -ne [Uri]::UriSchemeHttps
    ) {
        throw "Contract failed: sitemap entries must be absolute HTTPS URLs"
    }
    if ($uri.AbsolutePath.TrimEnd("/") -eq "/thea") {
        throw "Contract failed: sitemap must not expose /thea"
    }
}
foreach ($canonicalUrl in $canonicalUrls) {
    if ($sitemapUrls -notcontains $canonicalUrl) {
        throw "Contract failed: every public page canonical URL must appear in the sitemap"
    }
}

$staticWebAppConfig = $staticWebAppConfigText | ConvertFrom-Json
if ($staticWebAppConfig.navigationFallback.rewrite -ne "/index.html") {
    throw "Contract failed: direct SPA navigation must rewrite to /index.html"
}

Write-Host "All site contracts passed."
