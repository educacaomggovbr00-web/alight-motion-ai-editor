# Download real do Creative Cloud e verificação Linux — 10/10/2026

Pedido: continuar a preparação e baixar os arquivos oficiais disponíveis, sem custos adicionais.
O proxy do shell voltou a responder nesta etapa. Clone Git completo realizado; nenhum histórico removido.

## Resultado medido nesta sessão

| Item | Resultado |
|---|---|
| Origem | ccmdls.adobe.com, HTTPS, pacote 6.10.0/252.41 win64 |
| Resposta | HTTP 200 |
| Arquivo baixado | 331.128.777 bytes |
| ZIP | 227 entradas, todos os CRCs verificados, sem entrada corrompida |
| Instalador | Set-up.exe, único no pacote |
| Assinante | Adobe Inc. |
| Assinatura PE, cadeia e timestamp | osslsigncode retornou 0, Signature verification: ok |
| Revogação | Saída do verificador indicou Signature CRL verification: ok e Timestamp Server Signature CRL verification: ok |
| Adobe instalado/executado | Não |
| Premiere baixado/instalado/executado | Não |

SHA256 do ZIP:
`4e5f5b72db712a30a212aafa2c5cb47c555248c5b30f20b529103519c7d4fa4c`

SHA256 do Set-up.exe:
`a4e40fa74f89415a2514d28fa78930202f0e59220c945ba417baf41d62509595`

Verificador livre [osslsigncode](https://github.com/mtrojnar/osslsigncode) 2.12 compilado nesta sessão,
tag resolvida para commit `fac81646228a4d58aa9df41ac2b84c5a21d9d2d9`; OpenSSL 3.5.7 e bundle
de CAs do sistema `/etc/ssl/certs/ca-certificates.crt`. Não desabilitamos TLS ou verificação da cadeia.
Certificado assinante emitido por DigiCert, validade 06/10/2025–05/10/2027, timestamp 10/02/2026.
Isso é verificação Authenticode via ferramenta Linux; repita `Get-AuthenticodeSignature` no Windows antes de abrir.

Pacote proprietário e extração ficaram em `/workspace/adobe-private-downloads/`, fora dos dois checkouts,
com diretório de acesso restrito. Não foram enviados para GitHub, artefatos públicos ou links de download no chat.
Este workspace não é armazenamento permanente nem disco da futura VM. Não estão no celular do usuário.

## Reprodução sem instalação

Consulte a [página oficial Adobe](https://helpx.adobe.com/download-install/apps/download-install-apps/creative-cloud-apps/download-creative-cloud-desktop-app-using-direct-links.html)
e confirme a URL antes de executar. Em uma área privada fora do repositório:

```bash
curl --silent --show-error --fail --proto '=https' --connect-timeout 20 --max-time 300 --max-filesize 650000000 --output creative-cloud.zip https://ccmdls.adobe.com/AdobeProducts/StandaloneBuilds/ACCC/ESD/6.10.0/252.41/win64/ACCCx6_10_0_252_41.zip
python3 premiere-cloud/inspect_download.py --archive /CAMINHO/creative-cloud.zip --verifier /CAMINHO/osslsigncode --report /CAMINHO/download-report.json
```

`inspect_download.py` limita tamanho/entradas/extração, rejeita caminhos inseguros e instaladores ambíguos,
verifica CRCs e assinatura Adobe. Não executa instaladores. Relatório só contém hashes/estados e informações
do pacote, sem credenciais. Requer Python >=3.11 e verificador osslsigncode já instalado/compilado.
Dois novos testes locais passaram: rejeição de caminhos absolutos/travessia e ausência/duplicação de Set-up.exe.
A validação foi executada sobre o ZIP real e produziu `download-report.json` privado.

## O que continua bloqueado

Não existe Windows 11 GPU anexado a esta sessão. Não temos uma conta Adobe autenticada ou licença validada.
O instalador Windows não foi executado no Linux. Não baixamos uma ISO Windows, uma coleção de dependências
ou instaladores de fontes alternativas: isso não resolveria GPU, direitos de virtualização ou sessão gráfica.
O Premiere será baixado pelo Creative Cloud **na máquina Windows** depois do login manual legítimo.
Os workflows e procedimentos da [integração](../README.md) já estão preparados; efeitos e exportação Adobe
permanecem não iniciados. Nenhuma máquina paga foi contratada ou criada.
