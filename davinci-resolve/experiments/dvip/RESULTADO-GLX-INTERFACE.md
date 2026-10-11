# DaVinci original: GLX chegou à interface principal

Evidência: [execução 38175687312](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38175687312), commit `ef55f3b267bccdccef16ae25eff873edffb60f0f`, concluída em 11/10/2026. O workflow terminou com FAILURE porque exige MP4 realmente exportado, e não houve exportação. Isso não significa que todos os estágios falharam.

Artefato `davinci-original-dvip-evidence`, ID `11716256239`, digest `sha256:0bf7f00379e4157f56981cc021bb1dcd294d8d792f0c4a94b085b636b36cbbd1`, retenção até 18/10/2026. Não contém instalador ou mídia pessoal.

## Resultados distintos

| Estágio | GLX | EGL |
|---|---|---|
| Quatro buffers externos GL/CL | Passaram na matriz comum | Passaram na matriz comum |
| Executável original iniciado | Sim | Sim |
| Versão 21.1.1 confirmada nos logs | Sim | Sim |
| Contexto OpenCL criado pelo DVIP | Confirmado nos logs | Falhou antes da criação |
| Interop e players OpenGL | Inicializados nos logs | Bloqueados |
| Interface principal | Captura real `glx/screen-after-sdk.png`, título `DaVinci Resolve - New Project` | Inicialização bloqueada |
| Conexão SDK externo | Não conectou | Não conectou |
| Importação / timeline / exportação | Não comprovadas | Não comprovadas |

A captura GLX mostra o editor original na página de corte, com Media Pool e timeline vazios. Não é uma montagem ou outro editor. A observação da interface não prova todas as operações do aplicativo ou acesso remoto pelo celular. O projeto vazio padrão não conta como projeto criado pelo nosso teste.

## Evidência GLX

No arquivo `glx/resolve-debug-fresh.log`:

```text
UI.GLContext Initialized OpenGL 4.6 (requested 4.5) on device 'Mesa zink Vulkan 1.4(llvmpipe (LLVM 22.1.8, 256 bits) (MESA_LLVMPIPE))'
DVIP Created OpenCL context for devices gpu:c682f421.7b092bf5
UI.GLInterop OpenGL interop was initialized.
UI.GLIO Initialized MainPlayer OpenGL I/O on OpenCL device 'zink Vulkan 1.4(llvmpipe (LLVM 22.1.8, 256 bits) (MESA_LLVMPIPE))'
UI.GLIO Initialized AuxPlayer OpenGL I/O on OpenCL device 'zink Vulkan 1.4(llvmpipe (LLVM 22.1.8, 256 bits) (MESA_LLVMPIPE))'
UI.Scopes Initialized GPU Scopes Manager on OpenCL device 'zink Vulkan 1.4(llvmpipe (LLVM 22.1.8, 256 bits) (MESA_LLVMPIPE))'
```

Isso comprova o contexto DVIP e subsistemas citados, não renderização ou todos os kernels. O supervisor atual só marca `dvipInitializationConfirmed` depois da exportação; o `false` conservador do JSON bruto não invalida esses logs. Este relatório separa os níveis de evidência sem alterar o artefato original.

## Bloqueios restantes

EGL: `Failed to make current new shared context`, seguido de `Attempted to create OpenCL context with OpenGL interop enabled but no OpenGL context is current`. Não generalizar essa falha ao GLX, que criou o contexto.

GLX: a interface abriu, mas `ResolvePython` retornou sem conexão ao SDK. A documentação incluída no aplicativo relaciona scripting externo ao Resolve Studio; apenas esse retorno não identifica definitivamente a causa. Não foram alteradas preferências, executável, licença ou autenticação. O próximo teste útil é o script interno autorizado em Workspace → Scripts → Utility, já disponibilizado na sessão, ou uma importação sintética pela interface. Consultar os codecs reais antes de exigir H.264; ausência de suporte não autoriza fingir uma exportação pelo Resolve usando FFmpeg.

Há mensagens sobre ausência de dispositivo de áudio e plugin ProRes RAW; não impediram a interface GLX e não são apresentadas como causa do bloqueio SDK.

O SHA-256 do executável permaneceu `d083cf9f1eb875bdb928db54b20425b4111b53a16cae72a1aef1c3eeb603a121` antes e depois. Sem GPU física, instalador público, licença contornada ou alteração do binário.

## Persistência e cache

Código salvo apenas na branch experimental; main preservada. Sessão, projetos e instalador desaparecem ao fim do runner. Artefatos de evidência duram sete dias. O novo cache do Mesa livre é uma otimização independente, em validação por workflow separado: não conserva a instalação nem transforma esse resultado em exportação comprovada.
