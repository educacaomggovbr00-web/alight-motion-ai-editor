# Pesquisa e teste de GPU por software — 11/10/2026

## Avanço real e limite
A pesquisa encontrou **RUSTICL_DEVICE_TYPE=gpu**, opção oficial de teste/configuração do Mesa. Ela mudou o resultado de detecção: o DaVinci Resolve gratuito 21.1.1.0010 passou a enumerar llvmpipe e selecionar OpenCL.

**Isso não tornou o editor funcional.** O motor DVIP falhou ao criar seu contexto de imagem. As capturas aos 33 e 38 segundos mostram o carregamento da página Color; não foi alcançada uma timeline utilizável. Nenhum projeto foi criado, nenhuma mídia importada e nenhum MP4 exportado.

Essa descoberta complementa TESTE-RUSTICL.md: o teste anterior usava a classificação CPU padrão; este altera explicitamente apenas a classificação OpenCL para avaliar compatibilidade. Não foi modificada a licença nem o executável proprietário.

## O que foi pesquisado
- Mesa oficial: https://docs.mesa3d.org/envvars.html#envvar-RUSTICL_DEVICE_TYPE — permite apresentar o tipo accelerator/cpu/custom/gpu.
- Rusticl oficial: https://docs.mesa3d.org/rusticl.html — implementação OpenCL sobre Gallium.
- SwiftShader oficial: https://github.com/google/swiftshader — Vulkan na CPU; não fornece por si só o contexto OpenCL/CUDA usado aqui pelo Resolve. Não foi baixado outro grande pacote sem um mecanismo identificado para resolver o erro.
- Guia comunitário: https://github.com/bluhtsturm/resolve-setup — usa Rusticl, mas seus resultados práticos são com Radeon 680M real; citar llvmpipe entre opções não comprova edição sem hardware.
- Tutorial: https://qubitsandbytes.co.uk/linux/fixing-da-vinci-resolve-not-detecting-gpu-using-rusticl/ — demonstra Radeon W5700 real, não GPU criada pela CPU.
- Contêiner: https://github.com/zelikos/davincibox — organiza dependências; continua dependendo do dispositivo e driver de computação do host.
- Blackmagic Cloud: https://help.cloud.blackmagicdesign.com/intro/what-is-blackmagic-cloud/ — colaboração, projetos, mídia e licenças; não foi identificada nessa documentação uma máquina GPU gratuita que execute o editor.

Não foi encontrada prova verificável de edição/exportação no Resolve 21.1.1 usando somente CPU nas fontes consultadas. A busca não prova impossibilidade absoluta; os testes abaixo comprovam o comportamento desta configuração.

## Dois testes reais
Ambiente: Debian 13, Mesa 25.0.7, LLVM 19.1.7, Rusticl/llvmpipe, Xvfb; sem GPU física, sem VRAM dedicada.

1. RUSTICL_ENABLE=llvmpipe, RUSTICL_DEVICE_TYPE=gpu; versão OpenCL padrão 3.0.
2. Mesma configuração com RUSTICL_CL_VERSION=1.2.

Em ambos:
```text
Detected 1 GPUs
Unknown llvmpipe (LLVM 19.1.7, 256 bits)
Matches: OpenCL
Selected compute API: OpenCL
Created OpenCL context for devices ...
Failed to create OpenCL context:
DVIP Exception: OpenCL Context Manager failed to create context.
Failed to initialize OpenCL board manager
MainPlayer: Failed to create DVIP context.
Failed to initialize OpenGL texture pool, no valid contexts available.
```

**Interpretação da GPU e memória:** com o override, o aplicativo escreve “Discrete, 9.7 GiB VRAM”. Isso é classificação do driver e RAM do host apresentada pela API. Não apareceu uma placa discreta nem memória dedicada; o processamento segue na CPU.

clinfo confirma suporte a imagens e cl_khr_image2d_from_buffer, mas não anuncia cl_khr_gl_sharing nesta combinação. Isso é uma limitação observada relevante para interoperabilidade; o log DVIP não identifica a chamada exata, portanto não está comprovado que seja a única causa.

Os testes executaram o binário original extraído, não uma instalação de sistema. Ocorreram no ambiente Codex, não nos runners GitHub Actions. Foi usado PRoot apenas para mapear diretórios privados libclc/LLVM. Os grupos de processos foram encerrados pelo supervisor após as capturas; não ficou uma sessão remota para Android.

## Reprodução experimental
Depois de preparar os pacotes Mesa/Rusticl, libclc e cabeçalhos Clang conforme TESTE-RUSTICL.md:
```bash
export RUSTICL_ENABLE=llvmpipe
export RUSTICL_DEVICE_TYPE=gpu
export LP_NUM_THREADS=2
clinfo -l
bash davinci-resolve/tentar-abrir-extraido.sh /pasta/privada/squashfs-root /pasta/privada/relatorios

# Segundo teste, com compatibilidade da versão:
export RUSTICL_CL_VERSION=1.2
bash davinci-resolve/tentar-abrir-extraido.sh /pasta/privada/squashfs-root /pasta/privada/relatorios-cl12
```
Use prefixo privado e mapeamentos PRoot somente se os arquivos não estiverem nos caminhos normais. Supervisione o grupo de processos inteiro ao usar PRoot, porque um timeout interno pode não encerrar o supervisor. O override deve sempre constar nos relatórios: nunca considere a enumeração GPU como prova de hardware real.

## Evidências
- Captura padrão: /workspace/rusticl-private/gpu-type/frame33.png.
- SHA-256 da captura: 767564a38f406980307045f8213fe4b5b1ebffd860b8a9eb300843f285a656ea.
- Captura OpenCL 1.2: /workspace/rusticl-private/gpu-type-cl12/frame38.png.
- Logs completos privados preservados por variante; apenas os trechos necessários foram publicados.

**Estado:** detecção do dispositivo por software testada; processamento DVIP bloqueado; edição/exportação não iniciadas. Nenhum custo ou contratação, nenhuma substituição do editor e nenhum arquivo antigo removido.
