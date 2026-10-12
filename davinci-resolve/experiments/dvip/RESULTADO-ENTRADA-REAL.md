# Resultado da entrada real — 12/10/2026

Execução: https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38186502091

## Comprovado nesta execução

- Segredos de entrada disponíveis; valores não publicados.
- Restauração da imagem completa de dependências livres pelo cache.
- Download privado da mídia, preparo do trecho 45–60 s, 540×960, 30 FPS, DNxHR/PCM, áudio original preservado no preparo.
- Entrada preparada cifrada com AES-GCM e salva no cache antes da tentativa do editor. Cache não é armazenamento permanente.
- Instalador original da Blackmagic validado com SHA-256 conhecido; executável não modificado.
- Teste independente de compartilhamento GL/OpenCL aprovado.

## Bloqueio observado

O processo do Resolve iniciou, mas `uiMainWindowObserved=false`; nenhuma ação de introdução foi reconhecida. A conexão SDK retornou `apiConnected=false`. Não houve projeto, importação, timeline, efeito ou render nativo comprovado. O artefato desta execução contém somente relatório/HTML; NÃO contém vídeo final.

O fluxo privado removeu capturas e logs internos para preservar a mídia. Por isso não há evidência suficiente para atribuir o bloqueio especificamente ao DVIP, licença ou tela de introdução.

## Correção preparada

Limitar também o OCR das telas de abertura a uma thread e registrar seu timeout/exit code. Antes, somente a leitura do menu Scripts recebia esse limite; uma falha de OCR da introdução podia deixar a abertura parada. Esta é uma hipótese verificável, não correção comprovada do Resolve. Os 22 testes locais passaram após a alteração.

Próximo experimento: verificar a abertura com mídia sintética e coletar os relatórios sem exposição de material pessoal, depois repetir a entrada real aproveitando seu cache cifrado. Nenhum novo segredo é necessário no estado verificado nesta execução.
