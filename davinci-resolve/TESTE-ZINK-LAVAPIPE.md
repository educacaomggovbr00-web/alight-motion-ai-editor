# Tentativa real: Mesa 26.1.6 + Rusticl/Zink + Lavapipe

Data: 11/10/2026. Teste executado no ambiente Codex; não é uma execução do Resolve em GitHub Actions.

## Resultado

**A combinação funciona como driver gráfico/OpenCL por software, mas o DaVinci Resolve 21.1.1 não chegou a uma interface de edição utilizável.**

- Vulkan 1.4.354 enumerado por vulkaninfo; driver Mesa 26.1.6, LLVM 19.1.7; dispositivo físico informado pela API Vulkan: CPU.
- Rusticl enumerou `zink Vulkan 1.4(llvmpipe (LLVM 19.1.7, 256 bits) (MESA_LLVMPIPE))`.
- Kernel OpenCL real passou: [1,2,3,4] * 2 + 1 = [3,5,7,9].
- OpenGL realmente usou Zink sobre Lavapipe, confirmado por glGetString(GL_RENDERER).
- Contexto OpenCL comum: erro 0, criado corretamente.
- Contexto OpenCL compartilhando o contexto GLX real: erro **-1000 / CL_INVALID_GL_SHAREGROUP_REFERENCE_KHR**; não criado.
- clinfo não anuncia `cl_khr_gl_sharing` nessa combinação.
- O executável original do Resolve detectou Zink e selecionou OpenCL, mas DVIP falhou ao inicializar seu contexto. Observação de até 90 segundos, com capturas aos 15, 45 e 90 segundos.
- Não foi criado projeto, importado vídeo ou exportado MP4.

O teste independente demonstra uma limitação real de interoperabilidade. Não identifica a chamada interna exata do DVIP; não prova que seja a única causa do bloqueio.

## Preparação legítima e preservação

Pacotes oficiais Debian trixie-backports **26.1.6-1~bpo13+1**:
mesa-opencl-icd, mesa-vulkan-drivers, mesa-libgallium, libgl1-mesa-dri, libegl-mesa0, libglx-mesa0, libgbm1.

Download de 41,3 MB; os sete SHA-256 foram conferidos contra os metadados APT do índice baixado e validado por APT.
Foram extraídos num prefixo privado, sem instalar ou substituir bibliotecas do sistema.
vulkan-tools foi obtido do repositório Debian configurado. Dependências LLVM/libclc 19 do teste anterior foram reutilizadas.
PRoot mapeou os diretórios privados libclc/LLVM; não modifica o executável proprietário nem a licença.
Nenhum instalador proprietário, URL temporária, credencial ou mídia pessoal foi publicado.

## Configuração encontrada durante os testes

Somente `RUSTICL_ENABLE=zink` retornava zero dispositivos nesta configuração.
Funcionou habilitar a rota de software e Zink conjuntamente:

```bash
export LIBGL_ALWAYS_SOFTWARE=1
export RUSTICL_ENABLE=llvmpipe,zink
export GALLIUM_DRIVER=zink
export MESA_LOADER_DRIVER_OVERRIDE=zink
export LP_NUM_THREADS=2
```

No prefixo privado também foram necessários `LD_LIBRARY_PATH`, `LIBGL_DRIVERS_PATH`, `OCL_ICD_VENDORS` e `VK_DRIVER_FILES` apontando para o ICD Lavapipe.

O teste de kernel usou o tipo CPU verdadeiro. Para tentar o Resolve, foi usada a opção documentada `RUSTICL_DEVICE_TYPE=gpu`. Esse override muda a classificação OpenCL, não cria hardware nem VRAM dedicada. A memória que o aplicativo apresenta como VRAM é RAM compartilhada do host.

## Prova independente de compartilhamento

`probe-gl-opencl.py` usa ctypes e as bibliotecas reais X11, GL e OpenCL. Cria um pbuffer GLX, torna o contexto atual, seleciona o dispositivo OpenCL do tipo GPU (override experimental), cria primeiro um contexto comum e depois outro com `CL_GL_CONTEXT_KHR` e `CL_GLX_DISPLAY_KHR`.

Resultado real:
```json
{"glRenderer":"zink Vulkan 1.4(llvmpipe (LLVM 19.1.7, 256 bits) (MESA_LLVMPIPE))","basicContextError":0,"glSharedContextError":-1000,"glSharingPassed":false,"physicalGpu":false}
```
O código de saída do script não representa compatibilidade com edição: examine os campos de resultado. O script é específico para este experimento sem GPU física; a identificação physicalGpu=false é contexto declarado do teste, não detecção genérica de hardware.

Reprodução: depois de preparar uma sessão X11 e os pacotes, execute `python davinci-resolve/probe-gl-opencl.py` com o ambiente acima e `RUSTICL_DEVICE_TYPE=gpu`. O script não baixa nem inicia o Resolve.
Nos pacotes extraídos fora do sistema, mantenha os mesmos diretórios de compilação e bindings PRoot descritos nos testes anteriores.

## Evidência do Resolve

Log real:
```text
Unknown zink Vulkan 1.4(llvmpipe (LLVM 19.1.7, 256 bits) (MESA_LLVMPIPE))
Selected compute API: OpenCL
Failed to create OpenCL context:
DVIP Exception: OpenCL Context Manager failed to create context.
Failed to initialize OpenCL board manager
Failed to initialize OpenGL texture pool, no valid contexts available.
```

Capturas e logs completos ficaram privados em `/workspace/zink-private/resolve-test/`.
Os grupos de processos do aplicativo/PRoot e da tela virtual foram supervisionados e encerrados ao final. Não ficou servidor de acesso remoto.

## Referências e próximo requisito

- Pacote oficial: https://packages.debian.org/stable-backports/mesa-opencl-icd
- Zink: https://docs.mesa3d.org/drivers/zink.html
- Mudança relevante: https://docs.mesa3d.org/relnotes/25.1.0.html — “support cl_gl_sharing if dmabuf is supported”.
- Contexto do desenvolvimento para Resolve: https://www.phoronix.com/news/Zink-cl_khr_gl_sharing

A implementação de GL/CL sharing depende das capacidades do backend; a mudança no Zink não garante suporte quando o backend é Lavapipe na CPU.
Para avançar sem GPU física, falta uma implementação funcional desse compartilhamento nesta pilha e das demais capacidades exigidas pelo DVIP; não há um pacote comprovado neste teste que ofereça tudo isso. Alternativa comprovada em relatos externos utiliza GPU real com driver apropriado.
**Estado final: computação e OpenGL por software testados; interoperabilidade GL/CL e edição no Resolve bloqueadas.** Não houve custo, instalação de outro sistema operacional ou remoção de projetos anteriores.
