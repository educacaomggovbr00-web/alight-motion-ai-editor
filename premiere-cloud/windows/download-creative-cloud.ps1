param([Parameter(Mandatory)][string]$Destination)
$ErrorActionPreference = 'Stop'
# Confirme este link na documentação Adobe antes de usar; não aceita URLs arbitrárias.
$url = 'https://ccmdls.adobe.com/AdobeProducts/StandaloneBuilds/ACCC/ESD/6.10.0/252.41/win64/ACCCx6_10_0_252_41.zip'
if (Test-Path -LiteralPath $Destination) { throw 'Destino deve ser novo, privado e fora do repositorio' }
New-Item -ItemType Directory -Path $Destination | Out-Null
$archive = Join-Path $Destination 'creative-cloud.zip'
& curl.exe --silent --fail --proto '=https' --connect-timeout 20 --max-time 300 --max-filesize 650000000 --output $archive $url
if ($LASTEXITCODE -ne 0) { throw 'Download Adobe falhou; nada foi iniciado' }
Add-Type -AssemblyName System.IO.Compression
$zip = [IO.Compression.ZipFile]::OpenRead($archive)
try {
    if ($zip.Entries.Count -gt 10000 -or ($zip.Entries | Measure-Object Length -Sum).Sum -gt 2GB) {
        throw 'Pacote excede limites'
    }
    $root = [IO.Path]::GetFullPath((Join-Path $Destination 'extracted')) + [IO.Path]::DirectorySeparatorChar
    foreach ($entry in $zip.Entries) {
        $target = [IO.Path]::GetFullPath((Join-Path $root $entry.FullName))
        if (-not $target.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) { throw 'Caminho inseguro no ZIP' }
    }
} finally { $zip.Dispose() }
$expanded = Join-Path $Destination 'extracted'
[IO.Compression.ZipFile]::ExtractToDirectory($archive, $expanded)
$setup = @(Get-ChildItem -LiteralPath $expanded -Filter 'Set-up.exe' -File -Recurse)
if ($setup.Count -ne 1) { throw 'Instalador unico nao localizado' }
$sig = Get-AuthenticodeSignature -LiteralPath $setup[0].FullName
if ($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Subject -notmatch '(^|,\s*)O="?Adobe (Inc\.|Systems Incorporated)"?(,|$)') {
    throw 'Assinatura Adobe valida nao confirmada; nao execute o arquivo'
}
@{state='testado'; scope='download_e_assinatura_apenas'; signature='Valid';
  archiveBytes=(Get-Item -LiteralPath $archive).Length;
  installerSha256=(Get-FileHash -LiteralPath $setup[0].FullName).Hash;
  installationStarted=$false} | ConvertTo-Json | Set-Content (Join-Path $Destination 'download-report.json') -Encoding utf8
Write-Host 'Pacote baixado e assinatura verificada. Abra Set-up.exe na sessao grafica; nenhum login automatizado.'
