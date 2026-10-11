# Erro do GL sharing corrigido — 11/10/2026

**O teste da imagem foi corrigido e passou no GitHub Actions. O DaVinci ainda não foi testado com essa combinação nova.**

[Execução aprovada](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38165021201) · [Artefato, sete dias](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38165021201/artifacts/11711629156) · [JSON permanente](experiments/resultado-sharing-corrigido.json).

## Correções reais

1. Removemos a alteração que forçava `software_vulkan` no carregador Rusticl. Ela fazia todos os dispositivos desaparecerem. O arquivo do carregador agora permanece idêntico ao original, verificado por SHA-256.
2. Corrigimos o probe Python: libGL/libEGL são carregadas com `RTLD_GLOBAL`. O Rusticl procura `glXGetProcAddress`/`eglGetProcAddress` via `dlsym(NULL, ...)`; `RTLD_LOCAL` impedia a descoberta e produzia `-1000`. Essa diferença foi reproduzida em processos Python independentes e a visibilidade agora é registrada no relatório.
3. Mantivemos a exceção experimental explícita à recusa de dispositivos de software no Mesa 26.2.4. As exigências reais de DMA-BUF, handles, UUID e fences continuam intactas. Não inventamos capacidades ausentes ou alteramos o DaVinci.

## Prova do resultado

| Configuração da mesma compilação | GLX CPU | EGL CPU | GLX tipo GPU anunciado | EGL tipo GPU anunciado |
|---|---|---|---|---|
| Alteração desligada | Bloqueado, `-59` | Bloqueado, `-59` | Bloqueado, `-59` | Bloqueado, `-59` |
| Alteração ligada | Buffer passou | Buffer passou | Buffer passou | Buffer passou |

Nos quatro casos aprovados, contexto compartilhado, criação do buffer CL a partir de GL, fila, aquisição, escrita, liberação e finalização retornaram zero. O buffer começou com `[7, 8, 9, 10]`; OpenCL escreveu `[42, 8, 9, 10]` e OpenGL leu os mesmos valores. É troca real de memória, não apenas listagem de extensão.

O diagnóstico interno registrou `gl_sharing=true dmabuf=3 software=true handles=true uuid=true fence_fd=true allowed=true`. Vulkan também aprovou exportação/importação e leitura/escrita compartilhada de DMA-BUF de 4 KiB. O buffer GL/CL testado tem 16 bytes; não confundir os dois testes.

Renderer: Zink sobre Lavapipe/llvmpipe, LLVM 22.1.8, Mesa 26.2.4. Nenhum render node físico foi exposto. `RUSTICL_DEVICE_TYPE=gpu` muda somente o tipo anunciado, não cria hardware ou VRAM; o teste também passou com tipo CPU nativo.

A [comparação com Mesa oficial sem patch](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38165021204) refez as 16 combinações nas versões 26.1.6/26.2.4 com o probe corrigido: compartilhar continuou bloqueado e o erro observado passou para `-59`. Isso distingue o suporte experimental da configuração oficial.

## Limites e próximo teste

O workflow aprovado não contém o executável original do Resolve. Não houve novo lançamento, DVIP, importação, timeline, efeitos nem exportação MP4. Compartilhar um buffer não certifica imagens/texturas, workloads do editor, desempenho ou suporte oficial da Blackmagic.

O próximo teste autorizado tecnicamente é o DVIP do executável original, no mesmo ambiente com Mesa alterado e `/dev/udmabuf`. O [lançador condicional existente](experiments/test-dvip-after-sharing.py) exige contexto e buffer aprovados, executável existente e DISPLAY; continua experimental, sem afirmar edição após um simples lançamento. O ambiente local que contém a extração anterior não expõe `/dev/udmabuf`; o runner que passou o teste não contém essa extração. Não copiamos o instalador para o repositório público. A URL oficial fornecida anteriormente expirou em 11/10/2026 às 17:54:25 UTC. Portanto, a etapa DVIP ainda precisa de acesso privado legítimo ao aplicativo nesse runner ou de outro host com ambos os recursos.

Depois de DVIP/interface passarem, será preciso criar projeto, importar mídia sintética e exportar pelo próprio Resolve, validando com FFprobe. Nenhum MP4 por FFmpeg será apresentado como render do DaVinci.

## Reproduzir pelo Android

Abra Actions → **DaVinci — patch experimental de GL sharing por CPU** → Run workflow. A execução compila um driver livre isolado e testa a memória; não instala o editor. O resultado aprovado está na execução vinculada acima. O limite continua 45 minutos e os artefatos duram sete dias. A variável `CODEX_EXPERIMENTAL_SOFTWARE_GL_SHARING=1` é criada por este patch, não uma configuração oficial do Mesa.

Todos os arquivos antigos e os relatórios que falharam foram preservados. Os resultados antigos com `-1000` não isolavam o driver da falha de visibilidade GL do probe e não provam impossibilidade do caminho por software. Nenhum recurso pago foi contratado e nenhuma credencial ou mídia pessoal foi publicada.
