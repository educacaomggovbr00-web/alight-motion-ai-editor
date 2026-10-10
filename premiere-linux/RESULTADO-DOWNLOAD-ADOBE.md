# Resultado real — tentativa de download Adobe (2026-10-10)

Execução: [GitHub Actions #38084682961](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38084682961)

[Baixar relatório produzido pelo runner](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38084682961/artifacts/11681539418) (artefato disponível por 7 dias).

## Tentativa 1 — Adobe Premiere Pro

- URL oficial: https://creativecloud.adobe.com/apps/download/premiere
- Destino do redirecionamento: https://www.adobe.com/download/premiere
- Resposta HTTP **403** (text/html).
- Recebidos **0 bytes** de instalador executável.
- **Resultado: não foi possível baixar o Premiere Pro diretamente** nesse GitHub Actions.

## Tentativa 2 — aplicativo Creative Cloud

- Fonte: [links diretos na documentação oficial Adobe](https://helpx.adobe.com/pt/download-install/apps/download-install-apps/creative-cloud-apps/download-creative-cloud-desktop-app-using-direct-links.html)
- URL utilizada: https://ccmdls.adobe.com/AdobeProducts/StandaloneBuilds/ACCC/ESD/6.10.0/252.41/win64/ACCCx6_10_0_252_41.zip
- Resposta HTTP **200** (application/zip).
- Bytes baixados: **331.128.777** (cerca de 316 MiB).
- ZIP continha um instalador **Set-up.exe**.
- Assinatura Authenticode do instalador: **Valid**.
- Emissor do certificado de assinatura: **Adobe Inc.**
- **Resultado: o instalador oficial do Creative Cloud foi baixado e validado com sucesso.**

## O que isso NÃO significa

- **Creative Cloud não é Premiere Pro**. O pacote contém o instalador do gerenciador, não uma instalação pronta do Premiere.
- **O Premiere não foi instalado, iniciado nem testado para exportar vídeos**.
- Instalar Premiere normalmente exige Creative Cloud, autenticação e licença ou período de teste legítimo.
- O runner Windows padrão do GitHub foi identificado antes como Windows Server 2025 com vídeo virtual Hyper-V, sem GPU compatível comprovada e sem suporte oficial para Premiere 26.x.

## O que foi salvo?

Somente o **código de automação e o relatório** estão no GitHub. **Nenhum instalador Adobe foi incluído no repositório ou disponibilizado como artefato**. Os downloads ficam exclusivamente no disco do runner temporário e são excluídos após a verificação.

**Próxima possibilidade:** testar instalação do Creative Cloud somente em um computador/ambiente Windows 11 adequado e com conta Adobe própria. A conta e a licença do usuário não estão presentes no GitHub Actions. O projeto de edição MP4 via FFmpeg segue funcional.

Referências oficiais:
- [Adobe: download Creative Cloud por links diretos](https://helpx.adobe.com/pt/download-install/apps/download-install-apps/creative-cloud-apps/download-creative-cloud-desktop-app-using-direct-links.html)
- [Adobe: instalar aplicativos pelo Creative Cloud](https://helpx.adobe.com/pt/download-install/apps/download-install-apps/creative-cloud-apps/download-creative-cloud-apps.html)
- [Adobe: teste oficial do Premiere](https://www.adobe.com/br/products/premiere/free-trial-download.html)
