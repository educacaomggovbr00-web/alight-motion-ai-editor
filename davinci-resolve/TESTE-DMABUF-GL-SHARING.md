# DaVinci sem GPU física: resultado real em 11/10/2026

**Nota posterior: o probe tinha um problema de visibilidade GL corrigido com RTLD_GLOBAL. O Mesa alterado passou quatro testes de buffer. [Resultado atual](ERRO-GL-SHARING-CORRIGIDO.md). Este relatório preserva a execução anterior e não prova impossibilidade do caminho por CPU.**

**Estado: bloqueado para edição e exportação. Nenhum MP4 foi exportado pelo DaVinci.**

[Execução real no GitHub Actions](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38153583030). O resultado final é `failure` porque a verificação exige compartilhamento OpenGL/OpenCL funcional. As instalações dos ambientes e os diagnósticos terminaram; a falha é o requisito gráfico não atendido, não uma prova de editor funcionando.

## Resultados

| Etapa | Resultado | Limite da evidência |
|---|---|---|
| Mesa 26.1.6 e 26.2.4, Lavapipe com `/dev/udmabuf` | Testado: exportação/importação de DMA-BUF e leitura/escrita compartilhada de 4 KiB passaram em ambas as versões | Usa CPU e RAM; não cria GPU física nem VRAM dedicada |
| Zink + Rusticl, GLX/EGL, com/sem udmabuf, CPU/tipo GPU sobrescrito | Bloqueado: 16 combinações, zero compartilhamentos completos aprovados | Contexto OpenCL básico passou; contexto compartilhado falhou com `-1000`; `cl_khr_gl_sharing` ausente |
| DVIP após esse diagnóstico | Não iniciado | A condição de compartilhamento não passou; não repetimos o lançamento pesado |
| Projeto, timeline e exportação MP4 | Não iniciado | Não existe editor utilizável comprovado nesse ambiente |
| Rusticl com AMD física | Bloqueado, não testado | Nenhum hardware AMD disponível; nenhum recurso pago contratado |

O script antigo `probe-gl-opencl.py` também foi executado sem alterações: `glSharingPassed: false`. Um diagnóstico sair com código zero significa que produziu um relatório, não que Resolve funciona. O processo opcional `vulkaninfo --summary` retornou erro; a prova de DMA-BUF acima vem do teste direto das chamadas Vulkan e dos bytes compartilhados, não dessa ferramenta de metadados.

## Por que DMA-BUF não resolveu sozinho

O código da versão estável mais recente consultada, Mesa 26.2.4, exige explicitamente que o dispositivo não seja de software para permitir GL sharing no Rusticl. Em `src/gallium/frontends/rusticl/core/device.rs`, `is_gl_sharing_supported()` combina capacidade GL sharing, DMA-BUF, handles e fences com:

```rust
&& !self.is_device_software()
```

`is_device_software()` verifica a classificação do carregador Gallium. `RUSTICL_DEVICE_TYPE=gpu` muda o tipo anunciado pelo OpenCL, mas não transforma o dispositivo de software em hardware nem elimina essa condição. Encontrar memória compartilhável no Lavapipe foi um avanço real; não removeu o bloqueio do Rusticl.

SHA-256 do arquivo fonte 26.2.4 auditado: `a19c449b95586524b6b73e252fd42713c0250b7e4e43bc297fbbb8ef2b324530`.

Fontes: [Rusticl oficial](https://docs.mesa3d.org/rusticl.html), [Zink oficial](https://docs.mesa3d.org/drivers/zink.html), [release Mesa 26.2.4](https://docs.mesa3d.org/relnotes/26.2.4.html), [arquivo fonte distribuído pelo Debian](https://deb.debian.org/debian/pool/main/m/mesa/mesa_26.2.4.orig.tar.xz).

## Testes adicionais do executável original

Antes da decisão de condicionar novas tentativas ao probe, testamos a extração já existente do Resolve 21.1.1, sem novo download do instalador e sem alterar seus arquivos. Foram examinados os ajustes do [resolve-setup](https://github.com/bluhtsturm/resolve-setup); o modo de instalação desse script não foi executado.

- llvmpipe com configuração Qt xcb: apareceu **Unsupported GPU Processing Mode**.
- Zink e bibliotecas GLib do sistema, Qt GLX: inicialização do contexto DVIP falhou; splash permaneceu em **LOADING COLOR PAGE**.
- Zink e bibliotecas GLib do sistema, Qt EGL: DVIP informou ausência de contexto OpenGL corrente para interop; splash permaneceu em **LOADING COLOR PAGE**.

Esses lançamentos limitados comprovam tentativa real e bloqueio; não comprovam instalação nativa, interface utilizável, edição ou render. A carga das bibliotecas do sistema foi verificada no perfil EGL; não foi confirmada no perfil GLX. As conclusões sanitizadas estão em [resultado-resolve-setup.json](experiments/resultado-resolve-setup.json).

## Reprodução e evidências

Pelo Android: abra **Actions → DaVinci — testar Zink GL sharing sem GPU → Run workflow**. É somente diagnóstico: não baixa Resolve, não abre sessão remota e não gera edit. Utiliza runners públicos padrão Ubuntu e containers Debian isolados. O Mesa do host não é substituído. Há limites de execução e encerramento dos processos criados pelo teste.

O workflow [testar-davinci-gl-sharing.yml](../.github/workflows/testar-davinci-gl-sharing.yml) compara Debian 13/backports (26.1.6) e Debian sid (26.2.4 na data). As versões dos pacotes são registradas; execuções futuras podem receber versões diferentes. A ativação legítima do módulo `udmabuf` no runner não representa uma GPU física.

Evidências da execução, retidas por sete dias:

- [Artefato Mesa 26.1.6](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38153583030/artifacts/11707392312).
- [Artefato Mesa 26.2.4](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38153583030/artifacts/11707229094).
- [JSON permanente com resultados, versões e digests dos artefatos](experiments/resultado-gl-sharing.json).

O [probe Vulkan](experiments/vulkan-dmabuf-probe.py) verifica exportação/importação e alteração dos mesmos bytes. O [probe GL/OpenCL](experiments/gl-sharing-probe.py) só aprova depois de criar contexto compartilhado, adquirir um buffer GL no OpenCL, alterar bytes, liberar e conferir pelo OpenGL. O [executor da matriz](experiments/run-gl-sharing-matrix.py) cria uma sessão X11 isolada e limita cada processo. Não basta listar uma extensão.

O [lançador condicional DVIP](experiments/test-dvip-after-sharing.py) rejeita relatórios sem contexto e buffer compartilhados comprovados; sua recusa foi testada. O caminho de aprovação continua experimental e não foi executado, pois nenhum relatório passou. Ele também não cria timeline nem exporta vídeo.

Não foram publicados vídeos pessoais, instaladores proprietários, credenciais nem logs privados completos. Os arquivos antigos foram preservados.

## Próxima ação capaz de chegar à edição

Para usar o DaVinci agora, falta uma máquina com GPU e driver realmente compatíveis, cedida gratuitamente ou já disponível, com acesso remoto seguro pelo Android. Não há essa máquina configurada neste projeto. Como o orçamento é zero, não provisionamos serviços pagos.

Continuar exclusivamente por CPU exigiria desenvolvimento e validação do suporte de software no driver Mesa/Rusticl e de todos os requisitos de interop do Resolve. Não existe uma configuração pronta comprovada pelos testes. Repetir o instalador, reservar RAM ou anunciar o dispositivo como GPU não resolve a condição identificada. Mesmo um futuro probe aprovado ainda precisará passar pelo DVIP, interface, projeto real e exportação validada com FFprobe antes de declarar edição funcional.

