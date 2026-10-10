# Painel experimental UXP para o Premiere original

**Código preparado e contrato testado. Nunca carregado em um Premiere real nesta sessão.**
Este painel roda dentro do aplicativo Adobe, não no Chrome do Android nem em Node.
Não instala Premiere, não fornece licença e não automatiza login. Não aplica os presets de anime.

## Instalar o código na futura máquina Windows

1. Conclua a instalação/login manual e os diagnósticos do [guia Windows](../../README.md).
2. Instale o UXP Developer Tool pelo Creative Cloud conforme o
   [tutorial oficial Adobe](https://developer.adobe.com/premiere-pro/uxp/plugins/).
   Confirme que a versão do Premiere realmente instalada suporta UXP (25.6+ neste manifest).
3. Obtenha esta pasta pelo GitHub ou pelo artefato `premiere-uxp-panel-source` do novo CI.
   Extraia todos os arquivos na máquina Windows. O ZIP contém apenas código próprio;
   não é instalador Adobe nem pacote `.ccx` assinado/publicado.
4. No UXP Developer Tool, use Add Plugin, selecione `manifest.json` desta pasta e carregue
   com Load & Watch. Abra o painel Premiere Cloud pelo menu Plugins do Premiere.
   A interface/manifest/permissões ainda precisam ser validados nesse host; se o carregamento falhar,
   registre erro local do UDT e a versão sem publicar tokens/caminhos privados.
5. Crie **um projeto vazio de teste**, salve em `projects` da tarefa e abra-o no Premiere.
   Use vídeo sintético inicialmente, com dimensões/FPS já correspondentes a `job.json`.

## Executar os sete botões pela sessão remota

1. Carregue o `job.json` preparado por Actions ou `pipeline.py prepare`.
2. Confira o projeto; o painel vincula a tarefa ao projeto ativo salvo. Se trocar de projeto,
   a operação seguinte será bloqueada até recarregar a tarefa.
3. Importe vídeo/música usando o seletor de arquivos Windows. A API retornar `true` não comprova
   imagem/áudio válidos: confira as mídias no painel Projeto e no Source Monitor.
4. Selecione **exatamente um clipe de vídeo no painel Projeto**, então crie a sequência.
   A sequência recebe o nome `PC-<job_id>` e as configurações derivadas da mídia.
   Não coloca música separada em sincronismo, não aplica cortes, shakes ou efeitos.
   Ajuste manualmente a sequência à resolução e ao FPS da tarefa, se necessário.
5. Salve o projeto pelo botão e confira o `.prproj` local.
6. Crie/exporte um preset `.epr` **no próprio Premiere**, H.264/AAC e dimensões/FPS corretos.
   Clique em solicitar exportação, escolha o `.epr` e a pasta output privada.
   O painel verifica formato da sequência e extensão MP4 do preset; solicita exportação
   imediata pelo Premiere, com a sequência inteira. O nome inclui ID e timestamp.
   Não necessita Adobe Media Encoder para esta rota; não gera preset fictício.
7. Aguarde a conclusão **na interface do Premiere** e salve relatório JSON privado pelo painel.
   Execute a validação FFprobe do guia apontando ao MP4 gerado e assista ao vídeo no Android.
   Preset `.epr` que produz MP4 pode ter codecs/configurações diferentes: FFprobe é obrigatório.

O relatório deliberadamente mantém `state=experimental` e `exportProven=false`. Registra chamadas
e retornos positivos, versão do host e ID da tarefa; não inclui nomes/caminhos privados de mídia,
projeto, preset, URLs ou segredos do job. **Não é prova de exportação concluída.**
Não há webhook, listener de rede, polling, login automático ou execução headless.
Botões ficam bloqueados durante a operação nativa para evitar cliques simultâneos.
Cancelar Actions não cancela uma solicitação já aberta na interface; em travamento, use o próprio
Premiere/UDT para diagnosticar e cancelar, evitando repetir a exportação cegamente.

## APIs oficiais usadas

- [Project](https://developer.adobe.com/premiere-pro/uxp/ppro-reference/classes/project):
  `getActiveProject`, `getSequences`, `importFiles`, `createSequenceFromMedia`,
  `setActiveSequence`, `save`, `getActiveSequence`.
- [ProjectUtils](https://developer.adobe.com/premiere-pro/uxp/ppro-reference/classes/projectutils): seleção de itens.
- [ClipProjectItem](https://developer.adobe.com/premiere-pro/uxp/ppro-reference/classes/clipprojectitem): cast,
  `isSequence`, componente de vídeo.
- [SequenceSettings](https://developer.adobe.com/premiere-pro/uxp/ppro-reference/classes/sequencesettings): tamanho e FPS.
- [EncoderManager](https://developer.adobe.com/premiere-pro/uxp/ppro-reference/classes/encodermanager):
  extensão do preset e `exportSequence` com `Constants.ExportType.IMMEDIATELY`.

Assinaturas consultadas em 10/10/2026. O comportamento na versão instalada continua pendente.
Não copiamos código proprietário ou arquivos do repositório de exemplos Adobe.

## Testes disponíveis agora

`node --test premiere-cloud/tests/uxp-adapter.test.js` verifica nove casos de contrato,
rejeições e privacidade com objetos simulados. Eles não executam o host UXP/Adobe, validam os argumentos
e os bloqueios do adapter. `node --check` verifica sintaxe. O CI disponibiliza os fontes após passar.
Teste real seguinte: carregar painel no Premiere, importação sintética, timeline, salvamento,
exportação e comparação visual/FFprobe. Sem a máquina/licença isso permanece bloqueado.
