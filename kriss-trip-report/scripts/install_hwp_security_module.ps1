param(
  [string] $ModuleName = "FilePathCheckerModuleExample",

  [string] $DllPath = "",

  [switch] $Force
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($DllPath)) {
  $skillRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
  $candidate = Join-Path $skillRoot "assets\hwp-security-module\FilePathCheckerModuleExample.dll"
  if (Test-Path -LiteralPath $candidate) {
    $DllPath = $candidate
  } else {
    throw "Security module DLL not found. Expected: $candidate"
  }
}

$resolvedDll = (Resolve-Path -LiteralPath $DllPath).Path
$keyPath = "HKCU:\Software\HNC\HwpAutomation\Modules"
New-Item -Path $keyPath -Force | Out-Null

$current = (Get-ItemProperty -Path $keyPath -Name $ModuleName -ErrorAction SilentlyContinue).$ModuleName
if ($current -and $current -ne $resolvedDll -and -not $Force) {
  throw "Registry value already exists for ${ModuleName}: $current. Use -Force to replace it with $resolvedDll"
}

New-ItemProperty -Path $keyPath -Name $ModuleName -Value $resolvedDll -PropertyType String -Force | Out-Null

$hwp = New-Object -ComObject "HWPFrame.HwpObject"
try {
  $registered = $hwp.RegisterModule("FilePathCheckDLL", $ModuleName)
} finally {
  try { $hwp.Quit() } catch {}
}

[pscustomobject]@{
  module_name = $ModuleName
  dll_path = $resolvedDll
  registry_key = "HKEY_CURRENT_USER\Software\HNC\HwpAutomation\Modules"
  registered = [bool] $registered
} | ConvertTo-Json -Depth 3

if (-not $registered) {
  throw "HWP RegisterModule returned False. Check that the DLL path is unquoted and points to a valid FilePathChecker module."
}
