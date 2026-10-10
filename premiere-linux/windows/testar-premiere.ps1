# Windows GitHub runner: diagnostico de requisitos do Premiere Pro.
# Nao baixa, instala, ativa nem executa nenhum software Adobe.
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$OutputDir = "relatorios/premiere-windows"
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
$Report = Join-Path $OutputDir "resultado.md"

$os = Get-CimInstance Win32_OperatingSystem
$computer = Get-CimInstance Win32_ComputerSystem
$cpu = @(Get-CimInstance Win32_Processor)
$gpus = @(Get-CimInstance Win32_VideoController)
$memGiB = [math]::Round(([double]$computer.TotalPhysicalMemory / 1GB), 2)
$windows11orServer = [int]$os.BuildNumber -ge 26100
$isServer = $os.Caption -match "Server"
$hasMinRam = $memGiB -ge 8
$possibleSoftwareOnly = $true
$lines = [System.Collections.Generic.List[string]]::new()
function Add-Line([string]$s) { $script:lines.Add($s) }
Add-Line "# Diagnostico: Premiere Pro no Windows do GitHub Actions"
Add-Line ""
Add-Line "Data UTC: $((Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss'))"
Add-Line ""
Add-Line "## Sistema operacional"
Add-Line ""
Add-Line "- SO: $($os.Caption)"
Add-Line "- Versao: $($os.Version) / build $($os.BuildNumber)"
Add-Line "- Tipo: $(if ($isServer) { 'Windows Server' } else { 'Windows de desktop' })"
Add-Line "- Memoria RAM: $memGiB GiB (minimo Adobe: 8 GiB)"
Add-Line "- CPU: $($cpu[0].Name)"
Add-Line "- Nucleos logicos: $($cpu[0].NumberOfLogicalProcessors)"
Add-Line ""
if ($isServer) {
  Add-Line "**INCOMPATIBILIDADE DE SISTEMA:** o Premiere 26.x requer Windows 11 v24H2, e Windows Server nao e uma plataforma listada como suportada pela Adobe."
} elseif (-not $windows11orServer) {
  Add-Line "**INCOMPATIBILIDADE DE VERSAO:** build inferior a Windows 11 24H2."
} else {
  Add-Line "Versao Windows aparentemente compativel, mas isto nao valida licenca nem requisitos de GPU."
}
Add-Line ""
Add-Line "## Adaptadores de video (relato WMI)"
Add-Line ""
if ($gpus.Count -eq 0) {
  Add-Line "- Nenhum controlador de video reportado pelo Windows."
} else {
  $i = 0
  foreach ($gpu in $gpus) {
    $i += 1
    $name = [string]$gpu.Name
    $driver = [string]$gpu.DriverVersion
    $vram = if ($null -ne $gpu.AdapterRAM) { [math]::Round(([double]$gpu.AdapterRAM / 1GB), 2) } else { "desconhecido" }
    Add-Line "- Adaptador $($i): $name"
    Add-Line "  - Driver: $driver"
    Add-Line "  - AdapterRAM/WMI: $vram GiB (campo pode ser impreciso ou truncado)"
    if ($name -notmatch "(?i)basic|virtual|remote|hyper-v|vmware|parallels|citrix|display adapter|render driver") {
      $possibleSoftwareOnly = $false
    }
  }
}
Add-Line ""
Add-Line "Observacao: nome do controlador e memoria WMI, isoladamente, NAO provam GPU fisica disponivel nem aceleracao que o Premiere exige."
Add-Line ""
Add-Line "## Adobe Premiere Pro"
Add-Line ""
$foundExe = @()
$programDirs = @($env:ProgramFiles, [Environment]::GetFolderPath("ProgramFilesX86")) | Where-Object { $_ -and (Test-Path $_) }
foreach ($base in $programDirs) {
  $adobeFolder = Join-Path $base "Adobe"
  if (-not (Test-Path $adobeFolder)) { continue }
  $premiereFolders = @(Get-ChildItem -Path $adobeFolder -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "(?i)^Adobe Premiere Pro" })
  foreach ($folder in $premiereFolders) {
    $exe = Join-Path $folder.FullName "Adobe Premiere Pro.exe"
    if (Test-Path $exe) {
      $foundExe += $exe
    }
  }
}
$foundExe = @($foundExe | Select-Object -Unique)
if ($foundExe.Count -gt 0) {
  Add-Line "- Executavel do Premiere localizado: SIM ($($foundExe.Count) arquivo(s))."
  Add-Line "- O aplicativo NAO foi aberto, ativado, nem testado para renderizacao."
} else {
  Add-Line "- Executavel do Premiere localizado: NAO."
  Add-Line "- O runner padrao nao inclui uma instalacao valida do Adobe Premiere Pro."
}
Add-Line ""
Add-Line "## Conclusao"
Add-Line ""
if ($foundExe.Count -eq 0) {
  Add-Line "**PREMIERE NAO EXECUTADO:** nao havia Premiere instalado neste runner. O teste apenas diagnosticou o ambiente Windows."
} elseif ($isServer -or -not $hasMinRam -or $possibleSoftwareOnly) {
  Add-Line "**PREMIERE ENCONTRADO, MAS NAO EXECUTADO:** o ambiente apresenta limitacoes; requer teste manual e licenca valida."
} else {
  Add-Line "**PREMIERE ENCONTRADO, MAS NAO EXECUTADO:** requisitos adicionais, aceleracao e ativacao permanecem sem validacao."
}
Add-Line ""
Add-Line "Referencias: requisitos oficiais Adobe: https://helpx.adobe.com/br/premiere/desktop/get-started/technical-requirements/adobe-premiere-pro-technical-requirements.html"
Add-Line "GitHub-hosted runners: https://docs.github.com/en/actions/concepts/runners/github-hosted-runners"
$lines | Out-File -LiteralPath $Report -Encoding utf8
Write-Host ($lines -join [Environment]::NewLine)
