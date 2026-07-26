param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$InputPath,

    [string]$OutDir = "",

    [switch]$Json
)

# Optional Microsoft PowerPoint validation.
# Key principle: Passing ZIP/XML validation does not guarantee Microsoft
# PowerPoint compatibility. This script uses local PowerPoint COM automation to
# open, save as a new PPTX, and reopen the output. It never modifies the input.

$ErrorActionPreference = "Stop"

function Release-ComObjectIfPresent($Object) {
    if ($null -ne $Object) {
        try {
            [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($Object)
        } catch {
        }
    }
}

$resolvedInput = (Resolve-Path -LiteralPath $InputPath).Path
if (-not $OutDir) {
    $OutDir = Join-Path (Split-Path -Path $resolvedInput -Parent) "powerpoint_roundtrip"
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$stem = [System.IO.Path]::GetFileNameWithoutExtension($resolvedInput)
$outputPath = Join-Path $OutDir ($stem + "_powerpoint_roundtrip.pptx")
if (Test-Path -LiteralPath $outputPath) {
    Remove-Item -LiteralPath $outputPath -Force
}

$ppt = $null
$presentation = $null
$reopened = $null
$result = [ordered]@{
    input = $resolvedInput
    output = $outputPath
    powerpointVersion = $null
    openOk = $false
    saveOk = $false
    reopenOk = $false
    slideCount = $null
    reopenedSlideCount = $null
    errors = @()
}

try {
    $ppt = New-Object -ComObject PowerPoint.Application
    $result.powerpointVersion = $ppt.Version
    $ppt.DisplayAlerts = 1 # ppAlertsNone

    # Presentations.Open(FileName, ReadOnly, Untitled, WithWindow)
    $presentation = $ppt.Presentations.Open($resolvedInput, -1, 0, 0)
    $result.openOk = $true
    $result.slideCount = $presentation.Slides.Count

    # ppSaveAsOpenXMLPresentation = 24
    $presentation.SaveAs($outputPath, 24)
    $result.saveOk = Test-Path -LiteralPath $outputPath

    $presentation.Close()
    Release-ComObjectIfPresent $presentation
    $presentation = $null

    $reopened = $ppt.Presentations.Open($outputPath, -1, 0, 0)
    $result.reopenOk = $true
    $result.reopenedSlideCount = $reopened.Slides.Count
    $reopened.Close()
    Release-ComObjectIfPresent $reopened
    $reopened = $null
} catch {
    $result.errors += $_.Exception.Message
} finally {
    if ($null -ne $reopened) {
        try { $reopened.Close() } catch {}
        Release-ComObjectIfPresent $reopened
    }
    if ($null -ne $presentation) {
        try { $presentation.Close() } catch {}
        Release-ComObjectIfPresent $presentation
    }
    if ($null -ne $ppt) {
        try { $ppt.Quit() } catch {}
        Release-ComObjectIfPresent $ppt
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

if ($Json) {
    $result | ConvertTo-Json -Depth 4
} else {
    "PowerPoint version: $($result.powerpointVersion)"
    "Input: $($result.input)"
    "Output: $($result.output)"
    "Open OK: $($result.openOk)"
    "Save OK: $($result.saveOk)"
    "Reopen OK: $($result.reopenOk)"
    "Slide count: $($result.slideCount)"
    "Reopened slide count: $($result.reopenedSlideCount)"
    foreach ($err in $result.errors) {
        "Error: $err"
    }
}

if ($result.openOk -and $result.saveOk -and $result.reopenOk) {
    exit 0
}
exit 1
