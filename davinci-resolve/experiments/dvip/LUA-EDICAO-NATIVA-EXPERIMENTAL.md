# DaVinci Resolve 21.1.1 (Free): caminho Lua nativo experimental

Estado: **código e validação leve em CI**, sem execução do Resolve original para esta mudança. **Nenhum vídeo foi exportado neste teste novo.**

## Por que experimentar Lua?

No Resolve 21.1 Free, scripts Python externos não conectaram na nossa sessão, e Workspace > Scripts indicou No Scripts para nosso .py. Há relatos de que Python externo foi restringido nesta versão. Por outro lado, outros usuários mediram uma sessão Lua dentro de Workspace > Console com objeto resolve acessível e comando dofile. Isso não é garantia de que a GUI sob Mesa/Zink por CPU opere da mesma maneira.

Referências:
- https://github.com/samuelgursky/davinci-resolve-mcp/issues/203
- https://tech.hatada.jp/en/posts/resolve-free-what-ai-can-still-do-en
- https://www.blackmagicdesign.com/support

## O que esta mudança acrescenta

1. O workflow pesado continua **manual** (workflow_dispatch): nenhum push inicia download de DaVinci, instalação proprietária ou renderização.
2. A opção **lua_native_edit**, desativada por padrão, somente habilita o teste com vídeo *sintético*. Com `private_media` ativo, o teste Lua é desabilitado mesmo se ambas opções forem marcadas. O supervisor rejeita `--lua-native-edit` com `--input-video`.
3. Após a janela principal abrir, primeiro tenta o Python externo e o menu interno como antes. Se nenhum funcionar, o fallback só digita comandos após reconhecer Workspace > Console e um prompt `Lua>` na interface.
4. Primeiro executa **CodexLuaProbe.lua**, de leitura, para confirmar acesso ao objeto `resolve`. Só com retorno verdadeiro e novo prompt reconhecido envia `CodexLuaEditSmoke.lua`, usando caminho fixo e autorizado.
5. O script Lua nativo tenta: verificar 21.1.1, criar projeto, configurar resolução/FPS, importar mídia sintética, criar timeline, aplicar zoom opcional, salvar, consultar formatos e codecs de render realmente anunciados e tentar exportar MOV DNxHR/ProRes ou MP4 H.264 se disponibilizado.
6. Um MOV ProRes não é confundido com MP4 gerado pelo Resolve. `supervise.py` só marca `nativeRenderProven=true` após verificar existência e conteúdo de um render nativo com FFprobe; se necessário, FFmpeg cria um MP4 **a partir do MOV realmente renderizado**. A conversão auxiliar continua distinguida da exportação nativa em todos os relatórios.

## Limitações

- Sintaxe Lua e testes de controle simulados não comprovam funcionamento do DaVinci original.
- O menu Console pode não abrir ou o OCR pode não reconhecer o prompt. O fallback não deve digitar nada nesses casos.
- O caminho de render definido para o contêiner pode não ser aceito pelo Media Storage do Resolve; o codec pretendido pode estar indisponível.
- Em Linux Free, um relato obteve ProRes MOV nativo com áudio apenas depois de fornecer dispositivo de áudio virtual real. Nossa configuração ALSA null não foi comprovada equivalente.
- Nenhum desbloqueio de Studio, modificação do binário original ou contorno de licença.
- Para não consumir cotas, nenhum workflow pesado foi executado automaticamente nesta alteração.

## Para validar futuramente pelo Android

GitHub > Actions > **DaVinci — DVIP original 21.1.1 por CPU (experimental)** > **Run workflow** na branch com as mudanças. Deixe `private_media=false` e escolha `lua_native_edit=true`. Confirme primeiro a validade da URL oficial privada do instalador em Secrets.

Se executar, verificar no artefato sintético:
- `glx/result.json`: `luaApiReachable`, `luaEditSubmitted`, `projectCreated`, `timelineCreated`, `nativeRenderProven`, `mp4DeliveryValidated`;
- `glx/render/sdk-result.json`: relatório emitido pelo Lua, nunca tratado como prova de exportação sozinho;
- `glx/ffprobe-native.json` e `glx/ffprobe.json`: provas adicionais **somente se forem geradas**.

Não marcar como sucesso qualquer execução que apenas inicie o programa ou produza JSON; o requisito é vídeo real renderizado pelo Resolve, validado.
