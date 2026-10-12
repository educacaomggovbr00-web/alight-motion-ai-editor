# DaVinci 21.1.1 — teste temporário sem configurar GitHub Secrets

Este modo permite tentar abrir o **DaVinci Resolve original** num runner Linux comum e processar um **vídeo sintético** no Console Lua. A fonte do programa deve ser uma URL oficial temporária inserida manualmente no formulário de execução. O script valida host, caminho, expiração e SHA-256 antes de extrair o instalador, sem alterar o binário.

## Atenção à privacidade

**O campo `installer_url_once` não é secreto.** No repositório público, inputs de workflow_dispatch podem ser acessíveis por outros usuários e aparecer em registros, metadados e logs. Não coloque senhas de conta, links de arquivos pessoais ou chaves duradouras ali. A URL oficial de download pode permitir que outros baixem o instalador antes da expiração. É preciso marcar o aceite explícito. Para privacidade total, use Secrets.

## Como executar

1. Vá ao workflow da branch main **DaVinci — teste real sem Secrets (URL temporária)**.
2. Clique em **Run workflow**, selecione `main`.
3. Cole no campo `installer_url_once` a URL oficial completa e ainda válida do arquivo DaVinci Resolve 21.1.1 Linux; marque a confirmação de visibilidade pública.
4. O workflow chamará o experimento DVIP de `experiment/davinci-21-1-1-software-dvip`, tentando baixar/extrair o DaVinci original, criar mídia sintética e usar Console Lua para criar timeline e renderização nativa.
5. Leia o artifact `davinci-original-dvip-evidence`. Apenas `nativeRenderProven = true` e FFprobe podem provar renderização. Uma execução verde de diagnóstico não significa MP4 real.

**Sem `DAVINCI_INSTALLER_CACHE_PASSWORD`, nada é armazenado permanentemente no cache.** O instalador é baixado ao runner temporário e apagado ao final. Não fazemos cache em claro do programa proprietário num repositório público. O download pode ficar bloqueado quando o endereço expirar. Não é uma alternativa à versão paga, nem contorna limitações Studio.

As alterações não mudam o conteúdo da `main` além do pequeno workflow manual de entrada, e não executam DaVinci automaticamente ao receber pushes.
