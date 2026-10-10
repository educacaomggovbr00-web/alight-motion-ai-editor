# Teste REAL de download a partir dos servidores oficiais Adobe.
# Nao quebra licenca, nao pede login, nao executa instaladores e nao publica binarios.
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$OutDir = "relatorios/adobe-download"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$Report = Join-Path $OutDir "resultado.md"
$Tmp = Join-Path $env:RUNNER_TEMP "download-adobe-oficial"
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
$lines = [System.Collections.Generic.List[string]]::new()
function Write-Result([string]$s) {
  $script:lines.Add($s)
  Write-Host $s
}
function File-Type([string]$path) {
  if (-not (Test-Path -LiteralPath $path)) { return "ausente" }
  $stream = [IO.File]::OpenRead($path)
  try {
    $bytes = [byte[]]::new(8)
    $count = $stream.Read($bytes, 0, 8)
    if ($count -ge 2 -and $bytes[0] -eq 0x4d -and $bytes[1] -eq 0x5a) { return "EXE/PE" }
    if ($count -ge 2 -and $bytes[0] -eq 0x50 -and $bytes[1] -eq 0x4b) { return "ZIP" }
    if ($count -gt 0 -and ($bytes[0] -eq 0x3c -or $bytes[0] -eq 0x7b)) { return "HTML ou texto" }
    return "outro"
  } finally { $stream.Dispose() }
}
function Check-Signature([string]$path) {
  try {
    $sig = Get-AuthenticodeSignature -LiteralPath $path
    $publisher = [string]$sig.SignerCertificate.Subject
    Write-Result "- Assinatura Authenticode: $($sig.Status)"
    Write-Result "- Editor: $publisher"
    if ($sig.Status -ne 'Valid' -or $publisher -notmatch '(?i)Adobe') {
      Write-Result "- **Atencao:** assinatura Adobe valida nao confirmada; arquivo nao sera executado."
    }
  } catch {
    Write-Result "- Nao foi possivel verificar a assinatura: $($_.Exception.Message)"
  }
}
function Download-Official([string]$url, [string]$destination, [int]$timeoutSeconds) {
  # Todos os links sao URLs literais da propria Adobe (dominio Adobe/Adobe CDN).
  $argsList = @(
    '--silent', '--show-error', '--location', '--fail',
    '--max-time', [string]$timeoutSeconds,
    '--max-filesize', '650000000',
    '--connect-timeout', '25',
    '--retry', '1',
    '--user-agent', 'Mozilla/5.0',
    '--output', $destination,
    '--write-out', '%{http_code}|%{content_type}|%{url_effective}|%{size_download}',
    $url
  )
  $info = (& curl.exe @argsList 2>&1 | Out-String).Trim()
  $exitCode = $LASTEXITCODE
  $last = @($info -split "\r?\n")[-1]
  $parts = $last.Split('|')
  if ($parts.Length -ge 4) {
    $urlWithoutQuery = $parts[2]
    try {
      $urlWithoutQuery = ([Uri]$parts[2]).GetLeftPart([System.UriPartial]::Path)
    } catch {}
    Write-Result "- Resposta HTTP: $($parts[0])"
    Write-Result "- Tipo enviado pelo servidor: $($parts[1])"
    Write-Result "- Destino final: $urlWithoutQuery"
    Write-Result "- Bytes recebidos: $($parts[3])"
  } else {
    Write-Result "- Saida de rede: $($info.Substring(0, [math]::Min(220, $info.Length)))"
  }
  Write-Result "- Codigo curl: $exitCode"
  if (Test-Path -LiteralPath $destination) {
    Write-Result "- Arquivo identificado como: $(File-Type $destination)"
    Write-Result "- Tamanho em disco: $((Get-Item -LiteralPath $destination).Length) bytes"
  } else {
    Write-Result "- Nenhum arquivo baixado."
  }
  return $exitCode
}

try {
  Write-Result "# Tentativa oficial de download do Adobe Premiere"
  Write-Result ""
  Write-Result "Data UTC: $((Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss'))"
  Write-Result "Runner: $env:RUNNER_OS / $env:ImageOS"
  Write-Result ""
  Write-Result "## 1. Tentar baixar PREMIERE diretamente pela URL oficial"
  Write-Result ""
  $candidate = Join-Path $Tmp "premiere-resposta.bin"
  $direct = 'https://creativecloud.adobe.com/apps/download/premiere'
  Write-Result "- Link oficial tentado: $direct"
  $directRc = Download-Official $direct $candidate 90
  $candidateType = File-Type $candidate
  if ($directRc -eq 0 -and $candidateType -eq "EXE/PE") {
    Write-Result "- O endereco forneceu um executavel. Conferindo editor:"
    Check-Signature $candidate
  } elseif ($directRc -eq 0 -and $candidateType -eq "ZIP") {
    Write-Result "- O endereco forneceu um ZIP. Este teste nao o considera automaticamente um instalador do Premiere."
  } else {
    Write-Result "- **Nao foi obtido um instalador executavel do Premiere nesta tentativa.**"
    Write-Result "- Páginas HTML e redirecionamentos nao equivalem a baixar o aplicativo."
  }

  Write-Result ""
  Write-Result "## 2. Tentar baixar instalador oficial do Creative Cloud"
  Write-Result ""
  Write-Result "O Creative Cloud e o gerenciador oficial utilizado pela Adobe para instalar o Premiere."
  Write-Result "**Nao confunda Creative Cloud com Premiere Pro.**"
  $creativeCloudZip = Join-Path $Tmp "CreativeCloud-Adobe-Oficial.zip"
  # URL extraida da pagina de suporte oficial da Adobe em 10/10/2026.
  $official = 'https://ccmdls.adobe.com/AdobeProducts/StandaloneBuilds/ACCC/ESD/6.10.0/252.41/win64/ACCCx6_10_0_252_41.zip'
  Write-Result "- Link no dominio oficial Adobe: $official"
  $ccRc = Download-Official $official $creativeCloudZip 210
  if ($ccRc -eq 0 -and (File-Type $creativeCloudZip) -eq "ZIP") {
    Write-Result "- **Download do pacote Creative Cloud confirmado (ZIP valido pelo cabecalho).**"
    try {
      Add-Type -AssemblyName System.IO.Compression
      $zip = [IO.Compression.ZipFile]::OpenRead($creativeCloudZip)
      try {
        $exeFiles = @($zip.Entries | Where-Object { $_.FullName -match '(?i)(^|/)(Set-up|Creative.*Cloud.*Installer)\.exe$' -and $_.Length -lt 250000000 })
        Write-Result "- Quantidade de instaladores principais candidatos no ZIP: $($exeFiles.Count)"
        if ($exeFiles.Count -gt 0) {
          $exeFile = $exeFiles[0]
          $extracted = Join-Path $Tmp "Set-up.exe"
          $sourceStream = $exeFile.Open()
          $targetStream = [IO.File]::Create($extracted)
          try { $sourceStream.CopyTo($targetStream) } finally { $targetStream.Dispose(); $sourceStream.Dispose() }
          Write-Result "- Arquivo verificado dentro do ZIP: $($exeFile.FullName)"
          Check-Signature $extracted
        }
      } finally { $zip.Dispose() }
    } catch {
      Write-Result "- Falha ao inspecionar ZIP ou assinatura: $($_.Exception.Message)"
    }
  } else {
    Write-Result "- **Download do Creative Cloud nao foi concluido.**"
  }
  Write-Result ""
  Write-Result "## Conclusao e limites"
  Write-Result ""
  Write-Result "- Nenhum instalador foi executado. Nenhum arquivo proprietario Adobe foi enviado para o repositorio ou artifacts."
  Write-Result "- Para instalar o Premiere efetivamente, a Adobe pode exigir Creative Cloud, conta Adobe e licenca/teste valido."
  Write-Result "- O servidor GitHub Windows padrao e Windows Server, sem GPU compativel comprovada; nao validamos Premiere rodando."
  Write-Result "- O ambiente temporario do GitHub sera descartado apos a execucao."
  Write-Result ""
  Write-Result "Fontes oficiais:"
  Write-Result "- https://helpx.adobe.com/pt/download-install/apps/download-install-apps/creative-cloud-apps/download-creative-cloud-desktop-app-using-direct-links.html"
  Write-Result "- https://helpx.adobe.com/pt/download-install/apps/download-install-apps/creative-cloud-apps/download-creative-cloud-apps.html"
  Write-Result "- https://www.adobe.com/br/products/premiere/free-trial-download.html"
} finally {
  $lines | Out-File -FilePath $Report -Encoding utf8
  Remove-Item -LiteralPath $Tmp -Recurse -Force -ErrorAction SilentlyContinue
}
