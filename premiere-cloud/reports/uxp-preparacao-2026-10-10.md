# Continuação: painel UXP preparado — 10/10/2026

Base: `a6ad00568f8219b98261cbb1bb74c2b99875a49a`, continuação após download Creative Cloud real.
Clone completo em novo checkout; o checkout anterior foi preservado com seus arquivos.
Ambiente continua Linux, sem Windows11/GPU Adobe e sem conta autenticada; nenhum novo download
de instalador nem provisionamento pago foi realizado.

## Implementação nova

Painel próprio em `automation/uxp-panel`: manifest v5, interface em português, adapter CommonJS,
permissão de arquivos por seletor e nenhuma permissão de rede. Carrega contrato `job.json`,
vincula a um projeto salvo, importa mídia selecionada, cria sequência a partir de um clipe de vídeo,
salva projeto e solicita exportação pelo Premiere (`IMMEDIATELY`) com preset `.epr` escolhido.
Bloqueia IDs/formatos inválidos, troca de projeto, seleção múltipla ou sem vídeo, duplicação da sequência,
divergência de resolução/FPS e preset cuja extensão não seja MP4. Não aplica efeitos.

Não automatiza login, não usa API privada/QE DOM ou comandos Premiere de terminal inventados.
Relatório local registra observações/retornos da API sem expor caminhos ou segredos. Retorno da API não
promove exportação a funcional; os relatórios mantêm `exportProven=false`, exigindo conclusão visual e FFprobe.
Recebimento da tarefa pelo painel é manual via seletor; não há integração automática em segundo plano.

## Pesquisa verificável

Consultadas [Project](https://developer.adobe.com/premiere-pro/uxp/ppro-reference/classes/project),
[EncoderManager](https://developer.adobe.com/premiere-pro/uxp/ppro-reference/classes/encodermanager),
[ClipProjectItem](https://developer.adobe.com/premiere-pro/uxp/ppro-reference/classes/clipprojectitem),
[SequenceSettings](https://developer.adobe.com/premiere-pro/uxp/ppro-reference/classes/sequencesettings),
[Constants](https://developer.adobe.com/premiere-pro/uxp/ppro-reference/constants/) e
[tutorial UXP](https://developer.adobe.com/premiere-pro/uxp/plugins/) oficiais.
Referência de exemplos Adobe inspecionada separadamente no commit
`b481f1462400ddec5a7399e4930fafd7f71c58d0`; não redistribuída neste projeto.
Métodos escolhidos documentados a partir de 25.6; manifest mínimo 25.6.0.
Precisa confirmar a versão e testar disponibilidade/comportamento efetivos na máquina futura.

## Testes executados nesta etapa

`node --test premiere-cloud/tests/uxp-adapter.test.js`: **9/9 passaram**, cerca de 0,08 s.
`node --check` passou para adapter e interface. Objetos Adobe são doubles explícitos;
esses testes **não confirmam UXP funcionando no Premiere**. Novo CI executa esses testes além dos auxiliares
existentes e publica ZIP de fontes `premiere-uxp-panel-source`, sem software Adobe ou mídia pessoal.

| Recurso | Estado |
|---|---|
| Contrato/guardas do adapter | testado em Node com doubles |
| Painel/manifest no UXP real | experimental; carregamento não iniciado |
| Importação/timeline/salvamento Adobe | não iniciado no host real |
| Exportação MP4 pelo Premiere | não iniciado no host real |
| Efeitos/presets/keyframes | não iniciado |
| Creative Cloud já baixado | testado na etapa anterior; instalador não executado |
| Windows11/GPU/licença/sessão | bloqueado; não disponíveis |

Uso na sessão remota Android, download do código, instalação UDT e sete etapas:
[guia do painel](../automation/uxp-panel/README.md). Para sair do bloqueio, é preciso disponibilizar
máquina Windows11/GPU compatível licenciada e fazer login Adobe na interface. Sem isso não é possível
provar os testes Adobe solicitados, mesmo com código/API preparados. Nenhum custo contratado.
