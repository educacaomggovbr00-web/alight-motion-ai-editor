# Mesa/Rusticl + llvmpipe: teste real, 11/10/2026

Foi baixada e preparada uma segunda implementação OpenCL por software, além do PoCL: **Mesa 25.0.7 + Rusticl + llvmpipe, LLVM 19.1.7**. Fonte: pacotes oficiais Debian, snapshot configurado neste ambiente. Não foi instalado outro sistema operacional nem contratado recurso.

## Resultados separados

- Rusticl enumerou `llvmpipe (LLVM 19.1.7, 256 bits)`.
- `clinfo`: OpenCL 3.0; dispositivo disponível; suporte a imagens; **Device Type CPU**.
- Memória informada 9,735 GiB é RAM compartilhada do host, não VRAM dedicada.
- O kernel real de `opencl_cpu_probe.c` passou: [1,2,3,4] * 2 + 1 = **[3,5,7,9]**.
- O executável original **DaVinci Resolve 21.1.1.0010** foi iniciado novamente com Rusticl, Xvfb e OpenGL llvmpipe. Tela de carregamento apareceu; em seguida veio **Unsupported GPU Processing Mode**.
- Log de 15:09:34 UTC: `No matched GPUs found`, `No GPUs selected!`, `Unsupported GPU Processing Mode`.
- Nenhuma edição ou exportação foi realizada. Ter OpenCL funcional na CPU não resolveu o bloqueio do editor.
- O teste ocorreu no ambiente Codex, **não no GitHub Actions**.

## Preparação realizada
Pacotes extraídos em prefixo privado: mesa-opencl-icd, libclc-19, libclang-cpp19, libllvm19, libllvmspirvlib19.1, libclang-common-19-dev, mesa-utils e mesa-utils-bin. PRoot e libtalloc permitiram mapear os arquivos de desenvolvimento para os caminhos que o compilador exige, sem root e sem modificar bibliotecas proprietárias.

O primeiro kernel falhou porque faltava `opencl-c-base.h`; foi corrigido com libclang-common-19-dev e seu diretório LLVM. O erro foi corrigido antes de tentar o aplicativo novamente.

SHA-256 mesa-opencl-icd:
`a4262d559868897ad228bc8f159e897f5f20aaa83436da76c60b93ba3c653dbb`, igual ao metadado do pacote Debian consultado.

## Reprodução em Linux com pacotes instalados
Requer Mesa/Rusticl, libclc e cabeçalhos OpenCL Clang compatíveis; `clinfo`, compilador C e loader OpenCL; Xvfb e as dependências reais do Resolve.
```bash
export RUSTICL_ENABLE=llvmpipe
export LP_NUM_THREADS=2
clinfo -l
gcc davinci-resolve/opencl_cpu_probe.c -o /tmp/resolve-opencl-probe -l:libOpenCL.so.1
/tmp/resolve-opencl-probe
bash davinci-resolve/tentar-abrir-extraido.sh /pasta/privada/squashfs-root /pasta/privada/relatorios
```
Para prefixo privado, configure `LD_LIBRARY_PATH`, `OCL_ICD_VENDORS` e mapeie os diretórios libclc/LLVM como feito no teste. Não falsifique o tipo CPU, a VRAM ou a identidade do hardware.

Captura local privada do erro: `/workspace/rusticl-private/resolve-after.png`; SHA-256 `94557b23aaded3cae32a0655686a0ad927de7f376a60c519dba4912ebe15f217`.
O aplicativo foi encerrado pelo botão Quit. O comando interno tinha timeout de 40 segundos, mas o supervisor PRoot permaneceu ativo após a saída do aplicativo e precisou ser encerrado explicitamente. A tela virtual também foi encerrada. Não reutilize esse arranjo como job sem supervisionar o processo externo inteiro.

Documentação oficial: https://docs.mesa3d.org/rusticl.html
Ela define Rusticl como implementação OpenCL sobre Gallium, com drivers habilitados por `RUSTICL_ENABLE`; não promete compatibilidade com Resolve.

**Conclusão deste teste:** o processamento gráfico por software existe e foi preparado, mas esta combinação não habilitou o DaVinci. Nenhuma GPU física foi criada. Falta uma GPU e um driver aceitos pelo aplicativo para avançar à edição.

