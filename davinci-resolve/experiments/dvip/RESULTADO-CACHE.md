# Cache Mesa DVIP: gravação e restauração comprovadas

Branch experimental `experiment/davinci-21-1-1-software-dvip`; main preservada.

## Prova real

[Execução 38176656297](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38176656297): SUCCESS. O primeiro runner compilou e gravou o cache; outro runner restaurou a imagem sem compilar, conferiu SHA-256 do arquivo, ID da imagem e repetiu os quatro compartilhamentos reais GLX/EGL × CPU/GPU anunciado. Todos passaram, incluindo leitura OpenGL `[42,8,9,10]` após escrita OpenCL. Nenhum download proprietário foi iniciado.

- Compilar, comprimir e salvar: **471 segundos (7min51s)**.
- Restaurar, verificar e carregar: **45 segundos**.
- Repetir quatro compartilhamentos: **4 segundos**.
- Arquivo comprimido: cerca de **869 MiB** (imagem Docker descomprimida: 3,50 GiB).
- Chave: `mesa-dvip-image-v1-Linux-X64-fa4f883c1cb25e60943abf0b8e7cf3bf4322fe9209f16035f749638137210be9`.
- Imagem restaurada: `sha256:b6824aac699a728eda3502901d38c8f3ddddd87fc077b2b14d6d9997f1b56250`.
- Artefato `mesa-cache-restore-proof`: ID `11716316126`, digest `sha256:0cfbfdd172a016134fda5abfedd7bcf381e0310e85f0ac8e744c0d03f058133b`, disponível até 18/10/2026.

Os tempos medem essas etapas específicas, não o workflow completo. A preparação do runtime e os testes do DaVinci ainda levam tempo. Não é uma medição de exportação ou fluidez do editor.

## O que fica salvo

Somente imagem Mesa, LLVM, ferramentas e probes livres. Não há cache de instalador, DaVinci extraído, sessões, licenças, projetos, vídeos ou credenciais. A action salva antes da tentativa do aplicativo; falha posterior do DVIP ou da exportação não desfaz a gravação.

A chave muda quando mudam o Dockerfile Mesa, patch, probes, sistema ou arquitetura. Não utiliza chaves parciais antigas. O runtime é reconstruído com os scripts atuais, e os quatro buffers continuam obrigatórios antes de baixar o instalador oficial. Um cache indisponível exige compilação no workflow normal; no teste exclusivo de restauração, a ausência falha imediatamente para não desperdiçar minutos.

Cache pode ser removido pelo GitHub por quota/inatividade e não substitui backup permanente. Artefatos têm retenção de sete dias. Não foi ampliado plano ou contratado serviço.

## Uso pelo Moto G22

Abra Actions → workflow `testar-mesa-software-sharing.yml` → Run workflow → selecione **`experiment/davinci-21-1-1-software-dvip`**. Se a chave exata continuar disponível, aparecerá “Conferir integridade e carregar Mesa sem recompilar”, e a etapa de compilação será pulada. `mesa-cache.json` no artefato registra `cacheHit`, chave e ID reais.

A mudança está integrada ao workflow experimental do DaVinci. Não foi iniciada outra tentativa completa do aplicativo só para testar o cache. O teste independente não usa segredos do Resolve e não baixa seus 4 GB.

A interface principal original e o contexto DVIP em GLX já foram observados separadamente: [relatório GLX](RESULTADO-GLX-INTERFACE.md). Importação, timeline e exportação continuam sem prova.

## Confirmação entre execuções e versão final

A [execução 38177153826](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38177153826), commit `30bb2bdad48fa49fcc185a9970dcd52ddb2de6e4`, também terminou com **SUCCESS**. Seu primeiro runner encontrou o cache da execução anterior e restaurou em 45 segundos. O segundo restaurou em 61 segundos e repetiu os quatro buffers em 3 segundos. O modo restore-only impede uma nova compilação se houver cache miss.

O artefato final `mesa-cache-restore-proof`, ID `11716925190`, digest `sha256:bf3b260a0ca4302416a5c1b767fd2dd053d4de6fbe7a3be26dde9805d1911472`, foi baixado e verificado independentemente: `cacheHit=true`, identidade da imagem preservada e quatro provas válidas com round-trip GL/CL. Retenção até 18/10/2026. O runtime não foi construído nesse teste separado; o relatório final usa `runtimeRebuildRequired=true`.

Portanto, o cache foi salvo e reutilizado entre execuções reais, sem recompilar Mesa. A integração completa do workflow com DaVinci ainda não foi reexecutada com esse cache; não confundir essa validação com exportação pelo editor. Dados estruturados em [resultado-cache.json](resultado-cache.json).
