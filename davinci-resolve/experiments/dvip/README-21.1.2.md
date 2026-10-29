# DaVinci Resolve 21.1.2 — Console Full HD experimental

Branch: `experiment/davinci-21-1-2-console-fullhd`. Independente da antiga 21.1.1.

Este fluxo executa uma tentativa **manual e autorizada** com vídeo **sintético** num runner Linux efêmero. Reutiliza o pipeline DVIP/Mesa experimental e tenta abrir o Resolve original em display Xvfb 1920×1080. Ele **não fornece desktop remoto persistente**, nem GPU física.

## Fonte oficial e privacidade

O instalador precisa estar em `DAVINCI_RESOLVE_LINUX_URL` (GitHub Actions Secret), não nos inputs públicos nem em commits. O downloader aceita apenas `https://sw.blackmagicdesign.com/DaVinciResolve/v21.1.2/DaVinci_Resolve_21.1.2_Linux.zip` com URL assinada ainda válida. Rejeita hosts/caminhos/redirecionamentos fora desse padrão. Download limitado a 6 GiB, extração a 5 GiB.

**O hash SHA-256 oficial da 21.1.2 não foi confirmado.** O pipeline calcula SHA-256 do instalador obtido via HTTPS do domínio oficial, valida o ZIP e verifica o arquivo antes de extrair; registra também hash do executável antes/depois da sessão. Isso verifica integridade e origem HTTPS, **não equivale a uma assinatura ou hash publicado pela Blackmagic**. Caso obtenha uma referência independente confiável, configure `DAVINCI_RESOLVE_2112_SHA256` como Secret para fixar o hash e rejeitar outro instalador.

A versão 21.1.1, seus hashes e caches antigos **não são reutilizados**. Cada execução 21.1.2 baixa novamente o original quando aprovada; o preflight impede o download se o Secret estiver ausente/expirado. Nenhum ZIP ou executável proprietário é publicado nos artifacts ou no repositório.

## O que confirma funcionamento

Uma janela, processo, menu ou diagnóstico GL/CL bem-sucedido **não é render**. O teste só declara sucesso caso o SDK/Lua dentro do DaVinci crie vídeo nativo e a validação FFprobe confirme um MP4 de saída (MOV nativo convertido para MP4 é identificado separadamente). Sem exportação nativa comprovada, o job falha explicitamente.

Cuidado com custos: o job original pode usar até 45 minutos de Actions e baixar cerca de 4 GiB de dados. Não acione repetidamente sem conferir os bloqueios. A URL assinada expira e deverá ser substituída no GitHub Secret.

## Android

1. Configure o Secret `DAVINCI_RESOLVE_LINUX_URL` em **Settings → Secrets and variables → Actions**. Nunca inclua query strings assinadas no código.
2. Abra **Actions → DaVinci original — editar vídeo com Console Full HD (uma tentativa)**, escolha `tentar-console-fullhd` e marque `autorizar_tentativa`.
3. Confira os jobs preflight, original e logs/artefatos sanitizados.
4. Para **abrir desktop interativo** pelo celular, é preciso uma VM/PC persistente com GPU compatível e conexão remota privada. GitHub-hosted Actions não mantém essa sessão; não conecte um runner de desktop pessoal diretamente a um repositório público.
