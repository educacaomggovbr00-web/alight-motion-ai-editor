# Menu interno e bloqueio Fusion — 12/10/2026

Execução: https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38187575423
Artefato: https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38187575423/artifacts/11720487202

## Evidências reais

- O executável original 21.1.1 inicia sem alteração de hash.
- A introdução foi completada com Continue/Skip reconhecidos; janela principal confirmada.
- Contexto OpenCL do DVIP criado e GLInterop inicializado, sem Unsupported GPU observado.
- Clique em Workspace > Scripts abre submenu, comprovado por `glx/internal-menu-2.png`.
- O submenu mostra Comp/Edit/Color/Deliver e **No Scripts**. Nosso script estava nas duas pastas Utility oficiais antes do lançamento.
- Logs indicam `Fusion ... init not completed` e falha de obtenção da definição do menu de Fusion.
- A saída ALSA null eliminou nesta execução a enxurrada anterior de erros de placa de som.

## Ainda bloqueado

Não há conexão SDK, execução de script, projeto criado pelo teste, importação, timeline ou render comprovado. Esta execução não produz vídeo editado.

Não atribuímos a causa à licença ou à GPU apenas com estes avisos. Próximo experimento deve registrar dependências transitivas das bibliotecas Fusion e backtrace das threads quando o script não aparece. Essa instrumentação foi preparada, mas ainda não executada. Nenhuma modificação no executável proprietário, autenticação ou licença.

Cache de dependências livres restaurado nesta execução. A entrada pessoal cifrada foi salva na execução 38186502091; não foi repetida enquanto o teste sintético continua bloqueado.
