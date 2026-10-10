$ErrorActionPreference = 'Stop'
$port = New-Object System.IO.Ports.SerialPort 'COM1',115200,'None',8,'One'
$port.Open()
try {
    $os = Get-CimInstance Win32_OperatingSystem
    $isWindows11 = $os.ProductType -eq 1 -and [int]$os.BuildNumber -ge 22000
    if (-not $isWindows11) { throw 'Primeiro boot nao e Windows 11 desktop' }
    $first = @{windows11=$true; osCaption=$os.Caption; build=$os.BuildNumber; phase='specialize'} | ConvertTo-Json -Compress
    $port.WriteLine('CODEX_WINDOWS11_FIRST_BOOT ' + $first)
    New-Item -ItemType Directory -Path 'C:\CodexEvidence' -Force | Out-Null
    & (Join-Path $PSScriptRoot 'test-warp.ps1') -RequireWindows11 -Output 'C:\CodexEvidence\warp.json'
    $result = Get-Content 'C:\CodexEvidence\warp.json' -Raw | ConvertFrom-Json
    $port.WriteLine('CODEX_WINDOWS11_WARP_OK ' + ($result | ConvertTo-Json -Compress))
} catch {
    $port.WriteLine('CODEX_GUEST_ERROR ' + (@{state='bloqueado'; errorType=$_.Exception.GetType().Name} | ConvertTo-Json -Compress))
    exit 2
} finally {
    $port.Close()
    $port.Dispose()
}
