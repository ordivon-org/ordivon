param(
    [Parameter(Mandatory=$true)][string]$InputPptx,
    [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-fA-F]{64}$')][string]$ExpectedSha256,
    [Parameter(Mandatory=$true)][string]$OutputPdf,
    [Parameter(Mandatory=$true)][string]$RenderDirectory,
    [Parameter(Mandatory=$true)][string]$EvidenceJson,
    [int]$WidthPx = 1920,
    [int]$HeightPx = 1080
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-StreamSha256([System.IO.FileStream]$Stream) {
    $originalPosition = $Stream.Position
    try {
        $Stream.Position = 0
        $sha = [System.Security.Cryptography.SHA256]::Create()
        try {
            $bytes = $sha.ComputeHash($Stream)
            return ([System.BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
        }
        finally {
            $sha.Dispose()
        }
    }
    finally {
        $Stream.Position = $originalPosition
    }
}

$input = [System.IO.Path]::GetFullPath($InputPptx)
$pdf = [System.IO.Path]::GetFullPath($OutputPdf)
$renderDir = [System.IO.Path]::GetFullPath($RenderDirectory)
$evidence = [System.IO.Path]::GetFullPath($EvidenceJson)
$expected = $ExpectedSha256.ToLowerInvariant()

if (-not (Test-Path -LiteralPath $input -PathType Leaf)) {
    throw "Input PPTX is absent: $input"
}
New-Item -ItemType Directory -Force -Path ([System.IO.Path]::GetDirectoryName($pdf)) | Out-Null
New-Item -ItemType Directory -Force -Path $renderDir | Out-Null
New-Item -ItemType Directory -Force -Path ([System.IO.Path]::GetDirectoryName($evidence)) | Out-Null
Get-ChildItem -LiteralPath $renderDir -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -ieq '.png' } | Remove-Item -Force

# PowerPoint's native PDF/PNG exporters are not reliable when asked to write
# directly into the WSL UNC workspace. Keep target rendering on local Windows
# NTFS, then copy the exact resulting bytes back to the requested evidence paths.
$stageRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('ordivon-artifact-target-' + [Guid]::NewGuid().ToString('N'))
$stageRenderDir = Join-Path $stageRoot 'renders'
$stagePdf = Join-Path $stageRoot 'companion.pdf'
New-Item -ItemType Directory -Force -Path $stageRenderDir | Out-Null

# Hold the source open for the complete target run. FileShare.Read permits the
# read-only PowerPoint open but denies ordinary write/delete/rename opens while
# target evidence is being produced. Hashes are computed from this same handle.
$sourceStream = [System.IO.File]::Open($input, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
$app = $null
$presentation = $null
try {
    $artifactShaBefore = Get-StreamSha256 $sourceStream
    $artifactSize = [int64]$sourceStream.Length
    if ($artifactShaBefore -ne $expected) {
        throw "Input PPTX SHA-256 mismatch: expected $expected, observed $artifactShaBefore"
    }

    $app = New-Object -ComObject PowerPoint.Application
    $app.DisplayAlerts = 1
    $presentation = $app.Presentations.Open($input, $true, $false, $false)
    $slideCount = [int]$presentation.Slides.Count
    if ($slideCount -lt 1) { throw 'PowerPoint opened the artifact but exposed zero slides' }

    # ppSaveAsPDF=32. For the ordinary PDF_VIEW companion, use PowerPoint's
    # native SaveAs PDF path. ExportAsFixedFormat remains appropriate for
    # profiles that need its extra policy controls, but PowerShell COM binding
    # on this target rejected its PrintRange argument shapes during R1.
    $presentation.SaveAs($stagePdf, 32)
    $presentation.Export($stageRenderDir, 'PNG', $WidthPx, $HeightPx)

    if (-not (Test-Path -LiteralPath $stagePdf -PathType Leaf)) { throw 'PowerPoint did not produce the requested PDF' }
    $stagePngs = @(Get-ChildItem -LiteralPath $stageRenderDir -File | Where-Object { $_.Extension -ieq '.png' } | Sort-Object Name)
    if ($stagePngs.Count -ne $slideCount) {
        throw "PowerPoint PNG export count mismatch: expected $slideCount, got $($stagePngs.Count)"
    }

    $stagePdfSha = Get-Sha256 $stagePdf
    Copy-Item -LiteralPath $stagePdf -Destination $pdf -Force
    $pdfSha = Get-Sha256 $pdf
    if ($pdfSha -ne $stagePdfSha) { throw "PowerPoint PDF copy digest mismatch: local $stagePdfSha, destination $pdfSha" }

    $pngs = @()
    foreach ($stagePng in $stagePngs) {
        $destination = Join-Path $renderDir $stagePng.Name
        $stageSha = Get-Sha256 $stagePng.FullName
        Copy-Item -LiteralPath $stagePng.FullName -Destination $destination -Force
        $destinationSha = Get-Sha256 $destination
        if ($destinationSha -ne $stageSha) {
            throw "PowerPoint PNG copy digest mismatch for $($stagePng.Name): local $stageSha, destination $destinationSha"
        }
        $pngs += [ordered]@{ name=$stagePng.Name; sha256=$destinationSha }
    }

    $artifactShaAfter = Get-StreamSha256 $sourceStream
    if ($artifactShaAfter -ne $expected -or $artifactShaAfter -ne $artifactShaBefore) {
        throw "Input PPTX changed during target render: expected $expected, before $artifactShaBefore, after $artifactShaAfter"
    }

    $powerPointExe = Join-Path $app.Path 'POWERPNT.EXE'
    $result = [ordered]@{
        capturedAtUtc = [DateTime]::UtcNow.ToString('o')
        artifact = [ordered]@{
            path = $input
            size = $artifactSize
            expectedSha256 = $expected
            sha256 = $artifactShaAfter
        }
        inputFence = [ordered]@{
            method = 'persistent-read-handle'
            fileAccess = 'Read'
            fileShare = 'Read'
            preRenderSha256 = $artifactShaBefore
            postRenderSha256 = $artifactShaAfter
            digestStable = ($artifactShaBefore -eq $artifactShaAfter -and $artifactShaAfter -eq $expected)
            boundary = 'The worker holds one read-only source handle with FileShare.Read for the full PowerPoint run, denying ordinary write/delete/rename opens. This is target-process byte continuity evidence, not protection against stronger machine authority or alternate namespace semantics.'
        }
        renderer = [ordered]@{
            name = 'Microsoft PowerPoint Desktop'
            platform = 'Windows'
            version = [string]$app.Version
            executable = $powerPointExe
            executableSha256 = if (Test-Path -LiteralPath $powerPointExe -PathType Leaf) { Get-Sha256 $powerPointExe } else { $null }
        }
        result = [ordered]@{
            pdfExportMethod = 'Presentation.SaveAs/ppSaveAsPDF'
            targetStaging = [ordered]@{
                kind = 'windows-local-ntfs-temp'
                copyBackDigestVerified = $true
            }
            slideCount = $slideCount
            pdfPath = $pdf
            pdfSha256 = $pdfSha
            renderDirectory = $renderDir
            pngCount = $pngs.Count
            pngs = @($pngs)
        }
        boundary = 'One-shot target-render evidence. Exact source bytes are expected-digest fenced and held against ordinary write/delete/rename for the run. This does not prove visual defect absence or destination delivery/read-back.'
    }
    $json = $result | ConvertTo-Json -Depth 8
    [System.IO.File]::WriteAllText($evidence, $json + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
    Write-Output $json
}
finally {
    if ($presentation -ne $null) {
        try { $presentation.Close() } catch {}
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($presentation)
    }
    if ($app -ne $null) {
        try { $app.Quit() } catch {}
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($app)
    }
    if ($sourceStream -ne $null) {
        $sourceStream.Dispose()
    }
    if ($stageRoot -and (Test-Path -LiteralPath $stageRoot)) {
        try { Remove-Item -LiteralPath $stageRoot -Recurse -Force -ErrorAction Stop } catch {}
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
