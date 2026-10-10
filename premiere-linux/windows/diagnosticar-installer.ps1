# Diagnosticando Creative Cloud para uso do Adobe Premiere.
# Somente fontes oficiais. Nao faz login, ativacao ou bypass.
# O relatorio publico NAO inclui texto bruto de logs Adobe.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$outdir = 'relatorios/premiere-instalador'
New-Item -ItemType Directory -Force -Path $outdir | Out-Null
$report = Join-Path $outdir 'resultado.md'
$tmp = Join-Path $env:RUNNER_TEMP 'premiere-official-diagnostic'
$notes = [Collections.Generic.List[string]]::new()
function Note([string]$s) { $script:notes.Add($s); Write-Host $s }
function InspectLogs {
  Note ''
  Note '## Logs de instalacao Adobe (resumo sem dados pessoais)'
  $logDirs = @(
    [IO.Path]::GetTempPath(),
    (Join-Path ([IO.Path]::GetTempPath()) 'AdobeDownload'),
    (Join-Path ([Environment]::GetFolderPath('ProgramFilesX86')) 'Common Files\Adobe\Installers')
  )
  $allowed = @('PDApp.log','dlm.log','ACC.log','install.log','installer.log','Adobe Setup Error.log','oobelib.log')
  $files = @(foreach ($folder in $logDirs) {
    if (Test-Path -LiteralPath $folder) {
      Get-ChildItem -LiteralPath $folder -File -ErrorAction SilentlyContinue |
        Where-Object { $allowed -contains $_.Name -and $_.Length -le 100MB }
    }
  })
  if ($files.Count -eq 0) { Note '- Nenhum log Adobe conhecido encontrado nos diretorios inspecionados.' }
  foreach ($file in $files) {
    $name = $file.Name
    Note "- Arquivo de log: $name (tamanho: $($file.Length) bytes)"
    try {
      $hits = @(Select-String -LiteralPath $file.FullName -Pattern '(?i)\b(error|fatal|failed|failure)\b' -ErrorAction Stop)
      Note "- Quantidade de linhas com erros ($name): $($hits.Count)"
      $codes = @($hits | ForEach-Object {
        foreach ($m in [regex]::Matches($_.Line, '(?i)(?:error|exit|code)\s*(?:code)?\s*[:=# -]+\s*(-?[0-9]{1,8})\b')) {
          $m.Groups[1].Value
        }
      } | Select-Object -Unique -First 8)
      if ($codes.Count -gt 0) { Note "- Codigos numericos de erro ($name): $($codes -join ', ')" }
    } catch {
      Note "- Falha ao examinar contagem de erros ($name)."
    }
  }
}
try {
  Note '# Instalador oficial Creative Cloud — diagnostico para Premiere'
  Note ''
  Note "Data UTC: $((Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss'))"
  $os = Get-CimInstance Win32_OperatingSystem
  Note "Sistema: $($os.Caption)"
  New-Item -ItemType Directory -Force -Path $tmp | Out-Null
  $archive = Join-Path $tmp 'creative-cloud.zip'
  $officialUrl = 'https://ccmdls.adobe.com/AdobeProducts/StandaloneBuilds/ACCC/ESD/6.10.0/252.41/win64/ACCCx6_10_0_252_41.zip'
  Note ''
  Note '## Download oficial'
  & curl.exe --silent --show-error --fail --location --connect-timeout 25 --max-time 180 --max-filesize 650000000 --output $archive $officialUrl
  if ($LASTEXITCODE -ne 0) { throw 'Download oficial Adobe falhou.' }
  Note "- Pacote ZIP baixado: $((Get-Item -LiteralPath $archive).Length) bytes"
  Add-Type -AssemblyName System.IO.Compression
  $zip = [IO.Compression.ZipFile]::OpenRead($archive)
  try {
    $size = ($zip.Entries | Measure-Object -Property Length -Sum).Sum
    if ($zip.Entries.Count -gt 10000 -or $size -gt 2000000000) { throw 'ZIP excede limites de teste.' }
  } finally { $zip.Dispose() }
  $expanded = Join-Path $tmp 'extraido'
  [IO.Compression.ZipFile]::ExtractToDirectory($archive, $expanded)
  $setups = @(Get-ChildItem -LiteralPath $expanded -Recurse -File -Filter 'Set-up.exe')
  if ($setups.Count -ne 1) { throw 'Set-up.exe nao foi encontrado unicamente no ZIP oficial.' }
  $setup = $setups[0].FullName
  $sig = Get-AuthenticodeSignature -LiteralPath $setup
  $subject = [string]$sig.SignerCertificate.Subject
  Note "- Assinatura digital: $($sig.Status)"
  Note "- Assinado pela Adobe: $($subject -match '(?i)Adobe Inc\.')"
  if ($sig.Status -ne 'Valid' -or $subject -notmatch '(?i)Adobe Inc\.') { throw 'Assinatura digital Adobe invalida.' }
  Note ''
  Note '## Execucao monitorada (ate 70 segundos)'
  $p = Start-Process -FilePath $setup -WorkingDirectory $setups[0].DirectoryName -PassThru
  Note '- Processo Adobe Set-up.exe iniciado.'
  $observed = [Collections.Generic.HashSet[string]]::new()
  $finished = $false
  for ($i=0; $i -lt 14; $i++) {
    Start-Sleep -Seconds 5
    $p.Refresh()
    foreach ($proc in @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
      $_.ProcessName -match '(?i)adobe|creative|ccx|coresync|installer|set-up|aam|pdapp'
    })) {
      if ($proc.ProcessName -match '^[A-Za-z0-9 ._-]{1,70}$') { [void]$observed.Add($proc.ProcessName) }
    }
    if ($p.HasExited) {
      $finished = $true
      Note "- Processo principal encerrou. Exit code: $($p.ExitCode)"
      break
    }
  }
  if (-not $finished) {
    Note '- Instalador ainda aberto apos 70 segundos; encerrando a arvore de processos.'
    & taskkill.exe /PID $p.Id /T /F *> $null
  }
  if ($observed.Count -gt 0) { Note "- Processos observados: $(($observed | Sort-Object) -join ', ')" }
  Note ''
  Note '## Verificacao de instalacao'
  $ccPaths = @(
    'C:\Program Files\Adobe\Adobe Creative Cloud\ACC\Creative Cloud.exe',
    'C:\Program Files (x86)\Adobe\Adobe Creative Cloud\ACC\Creative Cloud.exe'
  )
  $premierePaths = @(
    'C:\Program Files\Adobe\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe',
    'C:\Program Files\Adobe\Adobe Premiere Pro 2025\Adobe Premiere Pro.exe'
  )
  $ccInstalled = @($ccPaths | Where-Object { Test-Path -LiteralPath $_ }).Count -gt 0
  $premiereInstalled = @($premierePaths | Where-Object { Test-Path -LiteralPath $_ }).Count -gt 0
  Note "- Creative Cloud presente nos caminhos conhecidos: $ccInstalled"
  Note "- Premiere Pro presente nos caminhos conhecidos: $premiereInstalled"
  InspectLogs
  Note ''
  Note '## Conclusao'
  if ($premiereInstalled) {
    Note '**Premiere encontrado em diretorio padrao, mas nao executado nem ativado.**'
  } elseif ($ccInstalled) {
    Note '**Creative Cloud detectado, mas nao encontramos o Premiere nos caminhos verificados.**'
  } else {
    Note '**Instalacao do Creative Cloud ou Premiere nao confirmada nos caminhos verificados.**'
  }
  Note 'O instalador pode exigir sessao grafica ou conta Adobe, e o Windows Server nao tem suporte oficial para Premiere 26.x.'
  Note 'Nenhuma credencial ou binario proprietario e enviado ao GitHub.'
} catch {
  Note ''
  Note '**O experimento nao concluiu a instalacao.**'
  Note "Tipo de erro: $($_.Exception.GetType().Name)"
  InspectLogs
} finally {
  $notes | Out-File -LiteralPath $report -Encoding utf8
  try { Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue } catch {}
}
