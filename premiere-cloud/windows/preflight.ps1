param([string]$Output = 'premiere-cloud/runtime/environment.json')
$ErrorActionPreference = 'Stop'
$os = Get-CimInstance Win32_OperatingSystem
$cpu = @(Get-CimInstance Win32_Processor)[0]
$ram = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB
$reasons = [System.Collections.Generic.List[string]]::new()
if ($os.ProductType -ne 1 -or $os.Caption -notmatch 'Windows 11' -or [int]$os.BuildNumber -lt 26100) {
    $reasons.Add('Windows 11 24H2 ou superior obrigatório; Server não aceito')
}
if (-not [Environment]::Is64BitProcess) { $reasons.Add('Processo x64 obrigatório') }
# AVX2 via runtime .NET do PowerShell 7, incluindo suporte efetivo do SO.
$avx2 = $false
try { $avx2 = [System.Runtime.Intrinsics.X86.Avx2]::IsSupported } catch {}
if (-not $avx2) { $reasons.Add('AVX2 não comprovado; use PowerShell 7 x64') }
if ($ram -lt 8) { $reasons.Add('RAM inferior ao mínimo de 8 GiB') }
$free = (Get-PSDrive -Name C).Free / 1GB
if ($free -lt 40) { $reasons.Add('Reserve 40 GiB livres para instalação/cache; margem operacional do projeto') }
$gpu = @()
# AdapterRAM WMI é uint32 e não serve como prova de >=4 GiB VRAM.
if (Get-Command nvidia-smi.exe -ErrorAction SilentlyContinue) {
    $raw = & nvidia-smi.exe --query-gpu=name,memory.total,driver_version --format=csv,noheader,nounits 2>$null
    if ($LASTEXITCODE -eq 0) {
        foreach ($line in $raw) {
            $parts = $line.Split(',')
            if ($parts.Count -eq 3) {
                $gpu += @{name=$parts[0].Trim(); vramMiB=[double]$parts[1].Trim(); driver=$parts[2].Trim()}
            }
        }
    }
}
if (@($gpu | Where-Object { $_.vramMiB -ge 4096 }).Count -eq 0) {
    $reasons.Add('NVIDIA/vGPU com >=4096 MiB não comprovada; AMD/Intel exigem inspeção manual/DXGI adicional')
}
$session = (Get-Process -Id $PID).SessionId
if ($session -eq 0 -or -not [Environment]::UserInteractive) { $reasons.Add('Sessão gráfica interativa necessária') }
$premiere = @(Get-ChildItem "$env:ProgramFiles/Adobe/Adobe Premiere*/Adobe Premiere Pro.exe" -ErrorAction SilentlyContinue)
$versions = @($premiere | ForEach-Object { $_.VersionInfo.ProductVersion })
$report = @{
    schema_version=1; state='bloqueado'; timestampUtc=[DateTime]::UtcNow.ToString('o')
    os=$os.Caption; build=$os.BuildNumber; cpu=$cpu.Name; avx2=$avx2
    ramGiB=[math]::Round($ram,2); freeSystemGiB=[math]::Round($free,2); gpu=$gpu
    sessionInteractive=($session -gt 0 -and [Environment]::UserInteractive)
    premiereFound=($premiere.Count -gt 0); premiereVersions=$versions
    automaticChecksPassed=($reasons.Count -eq 0); blockers=@($reasons)
    manualChecks=@('Geração de CPU', 'GPU Maxwell ou posterior / driver Adobe suportado',
      'DirectX e aceleração no Premiere', 'Tela remota 1920x1080', 'Áudio WDM/ASIO',
      'Licenças Windows e Adobe', 'Interface do Premiere, importação e exportação')
    tests=@{environment='experimental'; creativeCloud='nao_iniciado'; premiere='nao_iniciado'; edit='nao_iniciado'; export='nao_iniciado'}
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Output) | Out-Null
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Output -Encoding utf8
Write-Host "Diagnóstico salvo. Bloqueios automáticos: $($reasons.Count). Verificações manuais continuam obrigatórias."
if ($reasons.Count -gt 0) { exit 2 }
