# Executa no GitHub Actions somente instalador OFICIAL do Adobe Creative Cloud.
# NAO ativa, burla licenca, fornece credenciais, nem executa o Premiere Pro.
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$reportDir = "relatorios/execucao-creative-cloud"
New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
$report = Join-Path $reportDir "resultado.md"
$tempRoot = Join-Path $env:RUNNER_TEMP "adobe-teste-execucao"
New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
$notes = [System.Collections.Generic.List[string]]::new()

function Say([string]$message) {
  $script:notes.Add($message)
  Write-Host $message
}

function Get-Download([string]$url, [string]$destination, [int]$seconds) {
  $response = (& curl.exe --silent --show-error --location --fail --max-time $seconds --connect-timeout 20 --max-filesize 650000000 --retry 1 --output $destination --write-out '%{http_code}|%{content_type}|%{size_download}' $url 2>&1 | Out-String).Trim()
  $code = $LASTEXITCODE
  $last = @($response -split '\r?\n')[-1]
  Say "- Resultado HTTP/tipo/bytes: $last"
  Say "- Codigo do curl: $code"
  return $code
}

function File-Header([string]$path) {
  if (-not (Test-Path -LiteralPath $path)) { return "ausente" }
  $f = [IO.File]::OpenRead($path)
  try {
    $buf = [byte[]]::new(4)
    $len = $f.Read($buf, 0, 4)
    if ($len -ge 2 -and $buf[0] -eq 0x4d -and $buf[1] -eq 0x5a) { return "PE" }
    if ($len -ge 4 -and $buf[0] -eq 0x50 -and $buf[1] -eq 0x4b) { return "ZIP" }
    return "outro"
  } finally { $f.Dispose() }
}

try {
  Say "# Tentativa REAL de executar instalador Adobe (GitHub Actions)"
  Say ""
  Say "Data UTC: $((Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss'))"
  $os = Get-CimInstance Win32_OperatingSystem
  Say "Sistema: $($os.Caption)"
  Say ""
  Say "## 1. Nova tentativa de baixar Premiere diretamente"
  $premiere = Join-Path $tempRoot "premiere.bin"
  $premiereUrl = "https://creativecloud.adobe.com/apps/download/premiere"
  Say "- URL: $premiereUrl"
  $premiereRc = Get-Download $premiereUrl $premiere 65
  $premiereKind = File-Header $premiere
  Say "- Cabecalho detectado: $premiereKind"
  if ($premiereRc -ne 0 -or $premiereKind -ne "PE") {
    Say "**O link direto nao forneceu um executavel Premiere para este runner.**"
  } else {
    $premiereSig = Get-AuthenticodeSignature -LiteralPath $premiere
    Say "- Assinatura executavel direto: $($premiereSig.Status)"
    Say "- Assinante: $($premiereSig.SignerCertificate.Subject)"
    Say "**Nao executando download inesperado: o teste de execucao abaixo e limitado ao instalador Creative Cloud oficial e assinado.**"
  }

  Say ""
  Say "## 2. Rebaixar Creative Cloud do servidor oficial"
  $ccUrl = "https://ccmdls.adobe.com/AdobeProducts/StandaloneBuilds/ACCC/ESD/6.10.0/252.41/win64/ACCCx6_10_0_252_41.zip"
  $ccZip = Join-Path $tempRoot "creative-cloud.zip"
  $ccCode = Get-Download $ccUrl $ccZip 230
  if ($ccCode -ne 0 -or (File-Header $ccZip) -ne "ZIP") {
    throw "Download do ZIP oficial Creative Cloud falhou."
  }
  Say "- ZIP oficial baixado: $((Get-Item -LiteralPath $ccZip).Length) bytes"
  $unpacked = Join-Path $tempRoot "extraido"
  New-Item -ItemType Directory -Force -Path $unpacked | Out-Null
  Add-Type -AssemblyName System.IO.Compression
  $zip = [IO.Compression.ZipFile]::OpenRead($ccZip)
  try {
    $entryCount = $zip.Entries.Count
    $sumBytes = 0L
    foreach ($e in $zip.Entries) { $sumBytes += [long]$e.Length }
    Say "- Entradas ZIP: $entryCount; tamanho descompactado declarado: $sumBytes bytes"
    if ($entryCount -gt 10000 -or $sumBytes -gt 2500000000) {
      throw "ZIP excedeu os limites definidos para o teste."
    }
  } finally { $zip.Dispose() }
  [IO.Compression.ZipFile]::ExtractToDirectory($ccZip, $unpacked)
  $setup = @(Get-ChildItem -LiteralPath $unpacked -Filter "Set-up.exe" -File -Recurse | Sort-Object FullName | Select-Object -First 1)
  if ($setup.Count -lt 1) { throw "Set-up.exe nao foi encontrado no ZIP oficial." }
  $exe = $setup[0].FullName
  $sig = Get-AuthenticodeSignature -LiteralPath $exe
  $publisher = [string]$sig.SignerCertificate.Subject
  Say "- Instalador extraido: $($setup[0].Name)"
  Say "- Assinatura Authenticode: $($sig.Status)"
  Say "- Editor: $publisher"
  if ($sig.Status -ne "Valid" -or $publisher -notmatch "(?i)(CN=Adobe Inc\.|O=Adobe Inc\.)") {
    throw "O executavel nao tem uma assinatura Adobe valida. Execucao bloqueada."
  }

  Say ""
  Say "## 3. EXECUTAR Set-up.exe oficial, sem login"
  Say "- O runner de GitHub Actions e nao interativo. Se o instalador exigir interface, conta ou licenca, ele pode travar."
  Say "- Limite de observacao: 90 segundos; sem argumentos ocultos de instalacao ou bypass."
  $started = $null
  try {
    $started = Start-Process -FilePath $exe -WorkingDirectory (Split-Path -Parent $exe) -PassThru -ErrorAction Stop
    Say "- Processo Set-up.exe iniciado, PID: $($started.Id)"
  } catch {
    Say "- Falha ao iniciar Set-up.exe: $($_.Exception.Message)"
  }
  if ($null -ne $started) {
    $deadline = (Get-Date).AddSeconds(90)
    $ended = $false
    while ((Get-Date) -lt $deadline) {
      Start-Sleep -Seconds 5
      $started.Refresh()
      if ($started.HasExited) { $ended = $true; break }
    }
    if ($ended) {
      Say "- Set-up.exe encerrou durante o teste. Codigo de saida: $($started.ExitCode)"
    } else {
      Say "- Set-up.exe ainda estava rodando apos 90 segundos (sem interface acessivel ao GitHub)."
      Say "- Parando o processo para nao manter a execucao pendente."
      & taskkill.exe /PID $started.Id /T /F *> $null
    }
  }
  Say ""
  Say "## 4. Verificar resultado sem abrir conta Adobe"
  $targets = @(
    "C:\Program Files\Adobe\Adobe Creative Cloud\ACC\Creative Cloud.exe",
    "C:\Program Files (x86)\Adobe\Adobe Creative Cloud\ACC\Creative Cloud.exe",
    "C:\Program Files\Adobe\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe",
    "C:\Program Files\Adobe\Adobe Premiere Pro 2025\Adobe Premiere Pro.exe"
  )
  foreach ($target in $targets) {
    if (Test-Path -LiteralPath $target) {
      Say "- Encontrado: $target"
    } else {
      Say "- Ausente: $target"
    }
  }
  $adobeProcesses = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match "(?i)^adobe|^creative cloud|^ccxprocess|^coresync|^aam|^set-up$" })
  $procNames = @($adobeProcesses | Select-Object -ExpandProperty ProcessName -Unique)
  if ($procNames.Count -gt 0) {
    Say "- Processos Adobe ainda visiveis: $($procNames -join ', ')"
  } else {
    Say "- Nenhum processo Adobe encontrado ao terminar a observacao."
  }
  Say ""
  Say "**Isto NAO demonstra que Premiere foi instalado ou executado.**"
  Say "Creative Cloud pode precisar de UI e login Adobe para instalar aplicativos."
  Say "Windows Server nao e a plataforma Windows 11 oficialmente suportada pelo Premiere."
  Say ""
  Say "Nenhum binario da Adobe nem informacao de conta sera publicado no GitHub ou nos artefatos."
} catch {
  Say ""
  Say "ERRO NO TESTE: $($_.Exception.Message)"
  Say "Nao foi demonstrado que o Premiere funciona."
} finally {
  $notes | Out-File -LiteralPath $report -Encoding utf8
  try { Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue } catch {}
}
