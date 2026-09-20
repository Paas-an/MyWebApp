param(
    [Parameter(Mandatory)][string]$PublishedRoot
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$publishedDirectory = (Resolve-Path -LiteralPath $PublishedRoot).Path
$template = Get-Content -Raw -Encoding utf8 -LiteralPath (Join-Path $repositoryRoot "wwwroot/index.html")
$utf8 = [Text.UTF8Encoding]::new($false)
$pages = @(
    @{ Source = "Pages/Index.razor"; Output = "index.html" },
    @{ Source = "Pages/Contact.razor"; Output = "contact.html" },
    @{ Source = "Pages/Vessels.razor"; Output = "vessels.html" }
)

if (-not $template.Contains("<!-- PAGE_METADATA -->")) {
    throw "The HTML template must include the PAGE_METADATA marker."
}
if (-not (Test-Path -LiteralPath (Join-Path $publishedDirectory "_framework") -PathType Container)) {
    throw "PublishedRoot must point to a published Blazor wwwroot directory."
}

foreach ($page in $pages) {
    $source = Get-Content -Raw -Encoding utf8 -LiteralPath (Join-Path $repositoryRoot $page.Source)
    $title = [regex]::Match($source, '(?s)<PageTitle>(.*?)</PageTitle>')
    $head = [regex]::Match($source, '(?s)<HeadContent>(.*?)</HeadContent>')
    if (-not $title.Success -or -not $head.Success -or $head.Groups[1].Value.Contains('@')) {
        throw "$($page.Source) must contain a literal PageTitle and HeadContent for static SEO publication."
    }

    # Use the page's existing metadata as the single source for both crawlers
    # and client-side navigation. No separate, hand-maintained contact document.
    $metadata = [regex]::Replace($head.Groups[1].Value.Trim(), '<(meta|link)\b', '<$1 data-initial-seo')
    $html = $template.Replace("<!-- PAGE_METADATA -->", $metadata)
    $html = $html.Replace('<title>Jonas Skogtrø Olsen</title>', "<title>$($title.Groups[1].Value)</title>")
    $destination = Join-Path $publishedDirectory $page.Output
    [IO.File]::WriteAllText($destination, $html, $utf8)

    # dotnet publish may have compressed the original shell already. Remove
    # only the stale variants of these generated files; Azure compresses
    # the updated HTML responses itself.
    foreach ($extension in @('.br', '.gz')) {
        $compressedFile = "$destination$extension"
        if (Test-Path -LiteralPath $compressedFile -PathType Leaf) {
            Remove-Item -LiteralPath $compressedFile
        }
    }
}

Write-Host "Published static SEO metadata for /, /contact and /vessels."
