param(
    [Parameter(Mandatory)][string]$Executable,
    [ValidateSet('CreativeCloudInstaller','Premiere')][string]$Kind = 'Premiere',
    [string]$Output = 'premiere-cloud/runtime/start.json'
)
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'preflight.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Ambiente bloqueado pelo preflight; nada sera iniciado' }
# Somente depois do preflight e revisão humana; não existe comando de login.
if ((Get-Process -Id $PID).SessionId -eq 0 -or -not [Environment]::UserInteractive) {
    throw 'Abra PowerShell 7 na sessão gráfica remota do usuário'
}
if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) { throw 'Executável ausente' }
$sig = Get-AuthenticodeSignature -LiteralPath $Executable
if ($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Subject -notmatch '(^|,\s*)O="?Adobe (Inc\.|Systems Incorporated)"?(,|$)') {
    throw 'Assinatura Adobe válida obrigatória; nada será iniciado'
}
if ($Kind -eq 'Premiere' -and (Split-Path -Leaf $Executable) -ne 'Adobe Premiere Pro.exe') {
    throw 'Selecione o executável real do Premiere'
}
$version = (Get-Item -LiteralPath $Executable).VersionInfo.ProductVersion
$hash = (Get-FileHash -LiteralPath $Executable -Algorithm SHA256).Hash
$process = Start-Process -FilePath $Executable -PassThru
$window = $false
for ($i=0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    $process.Refresh()
    if ($process.HasExited) { break }
    if ($process.MainWindowHandle -ne 0) { $window = $true; break }
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Output) | Out-Null
@{state='experimental'; kind=$Kind; signature='Valid'; sha256=$hash; fileVersion=$version;
  processExited=$process.HasExited; windowObserved=$window; interfaceConfirmed=$false;
  installedConfirmed=$false; exportConfirmed=$false} | ConvertTo-Json | Set-Content -LiteralPath $Output -Encoding utf8
Write-Host 'Inicialização observada; confirme manualmente a interface. Aplicativo preservado aberto.'
