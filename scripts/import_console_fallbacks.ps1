param(
    [string]$SourceDir = "backend/static/console-fallbacks",
    [string]$TargetDir = "backend/static/console-fallbacks",
    [switch]$Apply,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Normalize-Name {
    param([string]$Text)
    $raw = ""
    if ($null -ne $Text) { $raw = [string]$Text }
    $value = $raw.ToLowerInvariant()
    $value = $value -replace "[_]+", " "
    $value = $value -replace "[-]+", " "
    $value = $value -replace "[^a-z0-9 ]+", " "
    $value = $value -replace "\s+", " "
    return $value.Trim()
}

function Get-SlugFromName {
    param([string]$BaseName)
    $n = Normalize-Name $BaseName
    if ([string]::IsNullOrWhiteSpace($n)) { return $null }

    $base = $null
    if ($n -match "\b(ps1|playstation 1|play station 1|psx)\b") { $base = "playstation" }
    elseif ($n -match "\b(ps2|playstation 2|play station 2)\b") { $base = "playstation-2" }
    elseif ($n -match "\b(ps3|playstation 3|play station 3)\b") { $base = "playstation-3" }
    elseif ($n -match "\b(ps4|playstation 4|play station 4)\b") { $base = "playstation-4" }
    elseif ($n -match "\b(ps5|playstation 5|play station 5)\b") { $base = "playstation-5" }
    elseif ($n -match "\bps vita\b|\bvita\b") { $base = "ps-vita" }
    elseif ($n -match "\bpsp\b") { $base = "psp" }
    elseif ($n -match "\bxbox one\b") { $base = "xbox-one" }
    elseif ($n -match "\bxbox 360\b") { $base = "xbox-360" }
    elseif ($n -match "\bxbox series\b|\bseries x\b|\bseries s\b") { $base = "xbox-series-xs" }
    elseif ($n -match "\bxbox classic\b|\bxbox original\b|\bxbox\b") { $base = "xbox" }
    elseif ($n -match "\bnintendo switch 2\b|\bswitch 2\b") { $base = "nintendo-switch-2" }
    elseif ($n -match "\bnintendo switch\b|\bswitch\b") { $base = "nintendo-switch" }
    elseif ($n -match "\bwii u\b") { $base = "wii-u" }
    elseif ($n -match "\bwii\b") { $base = "wii" }
    elseif ($n -match "\bgamecube\b") { $base = "gamecube" }
    elseif ($n -match "\bnintendo 64\b|\bn64\b") { $base = "nintendo-64" }
    elseif ($n -match "\bsnes\b|\bsuper nintendo\b") { $base = "snes" }
    elseif ($n -match "\bnes\b|\bnintendo entertainment system\b") { $base = "nes" }
    elseif ($n -match "\bgame boy advance\b|\bgba\b") { $base = "game-boy-advance" }
    elseif ($n -match "\bgame boy color\b|\bgbc\b") { $base = "game-boy-color" }
    elseif ($n -match "\bgame boy\b|\bgameboy\b") { $base = "game-boy" }
    elseif ($n -match "\bnintendo ds\b|\bnds\b") { $base = "nintendo-ds" }
    elseif ($n -match "\bnintendo 3ds\b|\b3ds\b") { $base = "nintendo-3ds" }
    elseif ($n -match "\bsega dreamcast\b|\bdreamcast\b") { $base = "sega-dreamcast" }
    elseif ($n -match "\bsega saturn\b|\bsaturn\b") { $base = "sega-saturn" }
    elseif ($n -match "\bmega drive\b|\bgenesis\b") { $base = "sega-genesis" }
    elseif ($n -match "\bmaster system\b") { $base = "sega-master-system" }
    elseif ($n -match "\bgame gear\b") { $base = "sega-game-gear" }

    if (-not $base) {
        $knownSlugs = @(
            "nes","snes","nintendo-64","gamecube","wii","wii-u","nintendo-switch","nintendo-switch-2",
            "game-boy","game-boy-color","game-boy-advance","nintendo-ds","nintendo-3ds",
            "playstation","playstation-2","playstation-3","playstation-4","playstation-5","psp","ps-vita",
            "xbox","xbox-360","xbox-one","xbox-series-xs",
            "sega-master-system","sega-genesis","sega-saturn","sega-dreamcast","sega-game-gear"
        )
        $slugLike = ($n -replace " ", "-")
        if ($knownSlugs -contains $slugLike) { $base = $slugLike }
    }

    if (-not $base) { return $null }

    if ($n -match "\b(controller|gamepad|joy con|joycon|dualshock|dualsense)\b") { return "$base-controller" }
    if ($n -match "\bslim\b") { return "$base-slim" }
    if ($n -match "\bfat\b") { return "$base-fat" }
    if ($n -match "\bpro\b") { return "$base-pro" }
    if ($n -match "\bsuper\b") { return "$base-super" }
    if ($n -match "\bdigital\b") { return "$base-digital" }

    return $base
}

function Normalize-Ext {
    param([string]$Ext)
    $raw = ""
    if ($null -ne $Ext) { $raw = [string]$Ext }
    $e = $raw.ToLowerInvariant()
    if ($e -eq ".jpeg") { return ".jpg" }
    return $e
}

function Get-FileScore {
    param([System.IO.FileInfo]$File)
    $score = 0
    switch (Normalize-Ext $File.Extension) {
        ".png" { $score += 50 }
        ".webp" { $score += 45 }
        ".jpg" { $score += 40 }
        default { $score += 10 }
    }
    $score += [Math]::Min([int]($File.Length / 8192), 50)
    return $score
}

$sourcePath = Resolve-Path -Path $SourceDir
if (-not (Test-Path $TargetDir)) {
    New-Item -Path $TargetDir -ItemType Directory | Out-Null
}
$targetPath = Resolve-Path -Path $TargetDir

$imageExts = @(".png", ".jpg", ".jpeg", ".webp")
$files = Get-ChildItem -Path $sourcePath -File | Where-Object {
    $ext = $_.Extension.ToLowerInvariant()
    $imageExts -contains $ext
}

$rows = @()
foreach ($file in $files) {
    $slug = Get-SlugFromName $file.BaseName
    $rows += [PSCustomObject]@{
        File  = $file
        Name  = $file.Name
        Slug  = $slug
        Score = Get-FileScore $file
    }
}

$mapped = @($rows | Where-Object { $_.Slug })
$unmapped = @($rows | Where-Object { -not $_.Slug })
$duplicatesIgnored = @()

# Keep only best source per slug.
$bestBySlug = @{}
foreach ($entry in ($mapped | Sort-Object Score -Descending)) {
    if (-not $bestBySlug.ContainsKey($entry.Slug)) {
        $bestBySlug[$entry.Slug] = $entry
    } else {
        $duplicatesIgnored += $entry
    }
}

$plan = @()
foreach ($slug in ($bestBySlug.Keys | Sort-Object)) {
    $entry = $bestBySlug[$slug]
    $ext = Normalize-Ext $entry.File.Extension
    $targetFile = Join-Path $targetPath "$slug$ext"
    $sourceFile = $entry.File.FullName

    if ($sourceFile -ieq $targetFile) {
        $action = "keep"
    } elseif ((Test-Path $targetFile) -and -not $Force) {
        $action = "skip_exists"
    } else {
        $action = "move"
    }

    $plan += [PSCustomObject]@{
        Slug = $slug
        Source = [System.IO.Path]::GetFileName($sourceFile)
        Target = [System.IO.Path]::GetFileName($targetFile)
        Action = $action
    }
}

Write-Host ""
Write-Host "Console fallback import plan"
$plan | Format-Table -AutoSize

if ($unmapped.Count -gt 0) {
    Write-Host ""
    Write-Host "Unmapped files (left untouched):"
    $unmapped | Select-Object Name | Format-Table -AutoSize
}

if ($duplicatesIgnored.Count -gt 0) {
    Write-Host ""
    Write-Host "Duplicate candidates ignored (left untouched):"
    $duplicatesIgnored | Select-Object Name,Slug | Format-Table -AutoSize
}

if (-not $Apply) {
    Write-Host ""
    Write-Host "Dry run only. Re-run with -Apply to execute."
    exit 0
}

foreach ($row in $plan) {
    if ($row.Action -eq "move") {
        $src = Join-Path $sourcePath $row.Source
        $dst = Join-Path $targetPath $row.Target
        if ((Test-Path $dst) -and $Force) {
            Remove-Item -Path $dst -Force
        }
        Move-Item -Path $src -Destination $dst -Force
    }
}

Write-Host ""
Write-Host "Done."
