# Alteração experimental do Rusticl para CPU

Não é uma correção comprovada do DaVinci. Não cria GPU física e não altera o executável do editor.

O patch cria uma exceção opt-in à condição que recusa dispositivos classificados como software em `is_gl_sharing_supported()` e direciona a criação da tela de software do Rusticl para o backend Vulkan/Zink, no Mesa 26.2.4. O nome `swrast` do carregador e a classificação de software são preservados; `RUSTICL_ENABLE=llvmpipe,zink` permite enumerar esse caminho. Mantém exigências de DMA-BUF, handles, UUID e fences. A exceção só é ativada por `CODEX_EXPERIMENTAL_SOFTWARE_GL_SHARING=1`, uma variável criada por este experimento, não uma opção oficial do Mesa. Sem a variável, a restrição original permanece.

O script verifica o SHA-256 dos dois arquivos fonte antes de modificar exatamente uma ocorrência em cada arquivo. Fonte diferente ou já modificada é recusada. Foram testados localmente a aplicação no arquivo original, a preservação das condições de capacidade e a recusa de reaplicação.

O workflow `testar-mesa-software-sharing.yml` compila um driver mínimo Zink/llvmpipe/Lavapipe/Rusticl em container Debian isolado. Compara a mesma compilação com o patch desligado/ligado em GLX/EGL, com OpenCL anunciando CPU/GPU. Esse anúncio não muda o hardware. O teste só aprova depois de adquirir, escrever, liberar e ler um buffer realmente compartilhado entre GL e CL.

A instalação em `/opt/mesa-experimental` é exclusiva do container; não substitui drivers do host. As ferramentas Vulkan/GL/OpenCL usam os caminhos explícitos dessa instalação. A máquina GitHub pode ter udmabuf compilado no kernel: ausência de um módulo carregável não significa ausência do dispositivo. Se necessário, somente pacotes oficiais de módulos da mesma versão do kernel são tentados, sem reboot.

Limites: job 45 minutos, compilação 35 minutos, cada matriz 240 segundos, dois threads de compilação. Os artefatos duram sete dias. Nenhum instalador proprietário, vídeo pessoal, login ou GPU paga é usado.

Mesmo se o teste de buffer passar, ainda será necessário verificar DVIP e a interface do executável original existente em um ambiente com os mesmos drivers, depois criar projeto e exportar. Este workflow não baixa nem inicia Resolve.

## Resultado comprovado em 11/10/2026

[Execução final](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38163457331) — compilação concluída; verificação de compartilhamento falhou. [Artefato](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38163457331/artifacts/11711252475), sete dias; [JSON permanente](resultado-patch-software-sharing.json).

- Vulkan DMA-BUF: exportação/importação e bytes compartilhados passaram com a alteração ligada e desligada.
- OpenGL: Zink/Lavapipe 4.6, Mesa 26.2.4, inicializou em GLX e EGL.
- Alteração desligada: dispositivo OpenCL Zink enumerado, contexto básico criado, mas compartilhamento GL/CL falhou com `-1000` nas quatro combinações de GLX/EGL e tipo CPU/GPU anunciado.
- Alteração ligada: a plataforma Rusticl carregou, porém enumerou zero dispositivos nas quatro combinações. A alteração do carregador **não corrigiu o suporte e piorou a enumeração nessa configuração**.

Não foi demonstrada uma correção do driver, nem removido o bloqueio do DaVinci. Como o compartilhamento não passou, não iniciamos novamente o editor. O patch permanece opt-in e identificado como experimento malsucedido, não como procedimento de instalação funcional. O teste da exceção isolada de software com enumeração OpenCL válida não foi concluído: a primeira versão habilitava somente `zink`, e a revisão combina a exceção com a alteração do carregador. Portanto, não é possível atribuir os zero dispositivos à exceção isolada.

Também corrigimos falhas do executor: reconhecimento de udmabuf embutido no kernel, rótulos suportados pela matriz, nome real `lvp_icd.x86_64.json` e seleção explícita do manifesto EGL compilado. Execuções anteriores que pararam na preparação ou no carregamento não comprovam incompatibilidade do patch.

Para investigar além disso, seria preciso instrumentar a criação da tela e os predicados de capacidade dentro do Rusticl, mantendo comparações isoladas. Não há evidência suficiente para simplesmente anunciar extensões ausentes ou remover todas as verificações. A edição imediata continua dependendo de um ambiente realmente compatível disponível gratuitamente; nenhum foi contratado ou configurado.
