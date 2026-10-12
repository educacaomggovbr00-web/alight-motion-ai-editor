# Análise dos registros existentes — Fusion

Fonte: execução 38187575423. Análise estática; nenhum workflow, download de instalador ou teste novo foi iniciado.

## Evidências do log mais recente

- DVIP criou contexto: linha 131: `0x7f53bbfc5000 | DVIP                 | INFO  | 2026-10-12 00:23:31,823 | Created OpenCL context for devices gpu:c682f421.7b092bf5`
- GLInterop inicializado: linha 137: `0x7f53c1fce000 | UI.GLInterop         | INFO  | 2026-10-12 00:23:31,849 | OpenGL interop was initialized.`; linha 138: `0x7f53c1fce000 | UI.GLInterop         | INFO  | 2026-10-12 00:23:31,849 | OpenGL interop was initialized.`
- Fusion leu templates: linha 177: `0x7f53b9fc3000 | Fusion               | INFO  | 2026-10-12 00:23:34,910 | 429 templates scanned in 0.33 secs`
- Falha ao obter definição do menu: linha 164: `0x7f54ae07c000 | FusionUtils          | WARN  | 2026-10-12 00:23:33,873 | No menu items will be added to resolve for Fusion. Reason: interface call to get menu definition failed.`; linha 235: `0x7f54ae07c000 | FusionUtils          | WARN  | 2026-10-12 00:23:40,513 | No menu items will be added to resolve for Fusion. Reason: interface call to get menu definition failed.`
- Interface pronta: linha 252: `0x7f54ae07c000 | Main                 | INFO  | 2026-10-12 00:23:43,478 | Launching main loop`

## O que isso permite concluir

O contexto gráfico inicializou e a interface chegou ao loop principal. Fusion carregou libfusionsystem e varreu templates, mas houve falha ao consultar a definição dos menus. A captura internal-menu-2.png mostra No Scripts. Isso bloqueia a automação escolhida, porém não identifica por si só a causa da inicialização incompleta.

A mensagem init not completed é um WARN. Não prova deadlock, ausência de biblioteca, restrição de licença ou impossibilidade de editar pela interface. O programa não produziu projeto/importação/render no teste.

O post_install.sh oficial foi lido: não contém uma etapa específica de registro de Scripts/Fusion cuja ausência explique diretamente este sintoma. Não foi executado nem modificado.

O backtrace histórico em dvip-backtrace/glx/application.log mostra Fusion em PreInitialize/AddStartupJobs e criação de threads. É de uma execução anterior e não comprova o estado das threads na execução atual. Não deve ser usado como prova de deadlock atual.

## Limite da evidência

O artefato mais recente não tem o backtrace específico da falha do menu nem a lista de dependências transitivas do Fusion preparada depois. Sem esses dados, não há correção causal comprovável apenas pelos registros atuais. Não alterar GPU, credenciais, bibliotecas ou licença por suposição.

Estado: análise concluída; causa raiz não determinada; nenhuma nova execução iniciada.
