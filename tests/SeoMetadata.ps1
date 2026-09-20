param(
    [Parameter(Mandatory)][string]$PublishedRoot
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$repositoryRoot = Split-Path -Parent $PSScriptRoot

function Assert-Equal($Actual, $Expected, [string]$Message) {
    if ($Actual -cne $Expected) {
        throw "$Message (expected '$Expected', got '$Actual')."
    }
}

function Get-Meta([string]$Html, [string]$Key) {
    $pattern = '<meta\b[^>]*(?:name|property)="' + [regex]::Escape($Key) + '"[^>]*>'
    $tags = [regex]::Matches($Html, $pattern)
    Assert-Equal $tags.Count 1 "Exactly one $Key tag is required"
    $value = [regex]::Match($tags[0].Value, '\bcontent="([^"]+)"')
    if (-not $value.Success) { throw "$Key must have non-empty content." }
    return $value.Groups[1].Value
}

$config = Get-Content -Raw -LiteralPath (Join-Path $PublishedRoot 'staticwebapp.config.json') | ConvertFrom-Json
# Azure normalizes a trailing slash before detecting duplicate route rules.
$normalizedRoutes = @($config.routes | ForEach-Object { $_.route.TrimEnd('/') })
Assert-Equal @($normalizedRoutes | Select-Object -Unique).Count $normalizedRoutes.Count 'Azure routes must be unique after trailing-slash normalization'
$contactRule = @($config.routes | Where-Object route -eq '/contact')
Assert-Equal $contactRule.Count 1 'A unique rule must serve the contact route'
Assert-Equal $contactRule[0].rewrite '/contact.html' 'The contact route must serve metadata without JavaScript'
$vesselsRule = @($config.routes | Where-Object route -eq '/vessels')
Assert-Equal $vesselsRule.Count 1 'A unique rule must serve the vessels route'
Assert-Equal $vesselsRule[0].rewrite '/vessels.html' 'The vessels route must serve metadata without JavaScript'
if ($config.navigationFallback.exclude -notcontains '/data/*') { throw 'Missing data must return an HTTP error rather than the app shell.' }

$pages = @(
    @{ File = 'index.html'; Source = 'Pages/Index.razor'; Url = 'https://www.olsenjonas.no/' },
    @{ File = 'contact.html'; Source = 'Pages/Contact.razor'; Url = 'https://www.olsenjonas.no/contact' },
    @{ File = 'vessels.html'; Source = 'Pages/Vessels.razor'; Url = 'https://www.olsenjonas.no/vessels' }
)
foreach ($page in $pages) {
    $htmlPath = Join-Path $PublishedRoot $page.File
    $html = Get-Content -Raw -Encoding utf8 -LiteralPath $htmlPath
    $source = Get-Content -Raw -Encoding utf8 -LiteralPath (Join-Path $repositoryRoot $page.Source)
    $expectedTitle = [regex]::Match($source, '<PageTitle>(.*?)</PageTitle>').Groups[1].Value
    Assert-Equal ([regex]::Match($html, '<title>(.*?)</title>').Groups[1].Value) $expectedTitle 'Initial HTML must contain the route title'
    Assert-Equal (Get-Meta $html 'og:title') $expectedTitle 'Open Graph title must match the route'
    Assert-Equal (Get-Meta $html 'twitter:title') $expectedTitle 'Twitter title must match the route'
    Assert-Equal (Get-Meta $html 'description') (Get-Meta $source 'description') 'Description must match the source page'
    Assert-Equal (Get-Meta $html 'twitter:description') (Get-Meta $html 'og:description') 'Social descriptions must agree'
    Assert-Equal (Get-Meta $html 'og:url') $page.Url 'Open Graph URL must identify the route'
    $canonicals = [regex]::Matches($html, '<link\b[^>]*rel="canonical"[^>]*>')
    Assert-Equal $canonicals.Count 1 'There must be exactly one canonical link'
    Assert-Equal ([regex]::Match($canonicals[0].Value, 'href="([^"]+)"').Groups[1].Value) $page.Url 'Canonical URL must identify the route'

    Assert-Equal (Get-Meta $html 'twitter:card') 'summary_large_image' 'Use a large-image sharing card'
    Assert-Equal (Get-Meta $html 'og:image') 'https://www.olsenjonas.no/images/social-card.png' 'Sharing image must be an absolute public URL'
    Assert-Equal (Get-Meta $html 'twitter:image') (Get-Meta $html 'og:image') 'Both cards must use the same image'
    Assert-Equal (Get-Meta $html 'twitter:image:alt') (Get-Meta $html 'og:image:alt') 'Both cards must have alternative text'
    Assert-Equal (Get-Meta $html 'og:image:type') 'image/png' 'Sharing image type must match the asset'
    Assert-Equal (Get-Meta $html 'og:image:width') '1200' 'Image width must match the asset'
    Assert-Equal (Get-Meta $html 'og:image:height') '630' 'Image height must match the asset'

    $jsonScripts = [regex]::Matches($html, '(?s)<script type="application/ld\+json">(.*?)</script>')
    Assert-Equal $jsonScripts.Count 1 'There must be one structured person record'
    $person = $jsonScripts[0].Groups[1].Value | ConvertFrom-Json
    Assert-Equal $person.'@context' 'https://schema.org' 'Use the Schema.org context'
    Assert-Equal $person.'@type' 'Person' 'Describe the website owner as a person'
    Assert-Equal $person.name 'Jonas Skogtrø Olsen' 'Use the published name'
    Assert-Equal $person.url 'https://www.olsenjonas.no/' 'Person URL must identify the home page'
    Assert-Equal $person.sameAs.Count 2 'Include only the two existing public profiles'
    foreach ($profile in $person.sameAs) {
        $contact = Get-Content -Raw -Encoding utf8 -LiteralPath (Join-Path $repositoryRoot 'Pages/Contact.razor')
        if (-not $contact.Contains('href="' + $profile + '"')) { throw "Unverified profile: $profile" }
    }

    if ($html.Contains('<!-- PAGE_METADATA -->')) { throw 'Page metadata was not generated.' }
    if ($html.IndexOf('js/seo-bootstrap.js') -gt $html.IndexOf('_framework/blazor.webassembly.js') -or
        -not $html.Contains('src="js/seo-bootstrap.js"')) {
        throw 'Metadata ownership must transfer before Blazor starts.'
    }
    foreach ($extension in @('.br', '.gz')) {
        if (Test-Path -LiteralPath "$htmlPath$extension") { throw 'Stale precompressed HTML must not be published.' }
    }
}

$png = [IO.File]::ReadAllBytes((Join-Path $PublishedRoot 'images/social-card.png'))
Assert-Equal ([BitConverter]::ToString($png[0..7])) '89-50-4E-47-0D-0A-1A-0A' 'Image must be a real PNG'
$width = ([int]$png[16] -shl 24) -bor ([int]$png[17] -shl 16) -bor ([int]$png[18] -shl 8) -bor [int]$png[19]
$height = ([int]$png[20] -shl 24) -bor ([int]$png[21] -shl 16) -bor ([int]$png[22] -shl 8) -bor [int]$png[23]
Assert-Equal $width 1200 'PNG width'
Assert-Equal $height 630 'PNG height'
Write-Host 'Published SEO metadata, person JSON-LD, routing and PNG checks passed.'
