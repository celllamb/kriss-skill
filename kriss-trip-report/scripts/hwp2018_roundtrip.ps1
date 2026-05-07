param(
  [Parameter(Mandatory = $true)]
  [string] $InputPath,

  [Parameter(Mandatory = $true)]
  [string] $OutputPath,

  [string] $SecurityModuleName = "FilePathCheckerModuleExample",

  [switch] $Force
)

$ErrorActionPreference = "Stop"

$resolvedInput = (Resolve-Path -LiteralPath $InputPath).Path
$resolvedOutput = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputPath)

if ((Test-Path -LiteralPath $resolvedOutput) -and -not $Force) {
  throw "Output already exists. Use -Force or choose a new output path: $resolvedOutput"
}

if (Test-Path -LiteralPath $resolvedOutput) {
  Remove-Item -LiteralPath $resolvedOutput -Force
}

$hwp = New-Object -ComObject "HWPFrame.HwpObject"
$previousMode = $null

try {
  try {
    $securityRegistered = $hwp.RegisterModule("FilePathCheckDLL", $SecurityModuleName)
  } catch {
    throw "RegisterModule(FilePathCheckDLL, $SecurityModuleName) failed: $($_.Exception.Message)"
  }

  if (-not $securityRegistered) {
    throw "RegisterModule(FilePathCheckDLL, $SecurityModuleName) returned False. Install/register the Hancom security module first, for example: scripts\install_hwp_security_module.ps1 -Force"
  }

  try {
    $previousMode = $hwp.GetMessageBoxMode()
  } catch {
    $previousMode = 0
  }

  # 0x00020000은 HWP 자동화의 일반 메시지 상자를 비대화식으로 처리한다.
  # 덮어쓰기 확인에 의존하지 않도록 새 출력 경로를 사용한다.
  $null = $hwp.SetMessageBoxMode(0x00020000)

  $opened = $hwp.Open($resolvedInput, "HWPX", "")
  if (-not $opened) {
    throw "HWP2018 failed to open input: $resolvedInput"
  }

  $saved = $hwp.SaveAs($resolvedOutput, "HWPX", "")
  if (-not $saved) {
    throw "HWP2018 failed to save output: $resolvedOutput"
  }

  $hwp.Clear(1) | Out-Null

  $openHwpX = $hwp.Open($resolvedOutput, "HWPX", "")
  if ($openHwpX) {
    $hwp.Clear(1) | Out-Null
  }

  $openAuto = $hwp.Open($resolvedOutput, "", "")
  if ($openAuto) {
    $hwp.Clear(1) | Out-Null
  }

  [pscustomobject]@{
    input = $resolvedInput
    output = $resolvedOutput
    security_module = $SecurityModuleName
    security_registered = [bool] $securityRegistered
    saved = [bool] $saved
    open_hwp_x = [bool] $openHwpX
    open_auto = [bool] $openAuto
  } | ConvertTo-Json -Depth 3
}
finally {
  try {
    if ($null -ne $previousMode) {
      $null = $hwp.SetMessageBoxMode([int] $previousMode)
    } else {
      $null = $hwp.SetMessageBoxMode(0)
    }
  } catch {}

  try {
    $hwp.Quit()
  } catch {}
}
