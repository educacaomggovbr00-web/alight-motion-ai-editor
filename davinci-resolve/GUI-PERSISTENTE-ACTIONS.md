# DaVinci Resolve original — GitHub Actions e desktop persistente

## O que foi implementado

O workflow principal [DaVinci original — editar vídeo com Console Full HD (uma tentativa)](../.github/workflows/tentar-edicao-privada-console-fullhd-once.yml) na branch `main` oferece, via `Actions → Run workflow`:

| Modo | O que realmente faz |
| --- | --- |
| `diagnostico` | Gera um resumo **sem instalar/abrir** DaVinci e sem ler Secrets |
| `tentar-console-fullhd` | Com confirmação explícita, chama o experimento original Linux 21.1.1 da branch `experiment/davinci-21-1-1-software-dvip`, com vídeo privado e Console Full HD |
| `abrir-linux-persistente` | Usa um runner próprio na **sessão gráfica existente** de um Linux para tentar abrir um DaVinci já instalado |
| `abrir-windows-persistente` | Usa um runner próprio na **sessão gráfica existente** do Windows para tentar abrir um DaVinci já instalado |

**Não provisiona uma VM, não fornece GPU, não instala DaVinci, não ativa uma máquina desligada e não cria acesso remoto.** O sucesso do launcher significa somente que um processo foi detectado. Confirme na tela se a interface abre, se a GPU é aceita e se o programa edita/exporta.

A branch experimental contém o workflow reutilizável `experimentar-davinci-dvip.yml` com `source_ref` explícito. Isto permite que o Actions em `main` baixe o código e as actions locais da branch correta, sem misturá-los com os arquivos diferentes da `main`.

## Limite dos runners GitHub

Um job GitHub-hosted é temporário. Mesmo se abrir DaVinci usando Xvfb, ele não se torna um desktop remoto permanente; o processo termina ao encerrar o job, e o limite de execução GitHub-hosted é de 6 horas. O experimento atual limita a execução pesada a **45 minutos**. Nenhum botão do Actions muda isso.

Para deixar o desktop acessível no Android, é necessário **um computador/VM persistente com GPU compatível**, online e com sessão gráfica; o acesso remoto é configurado pelo proprietário da máquina, fora do GitHub Actions. **Não exponha diretamente VNC, RDP ou porta de administração à internet**; utilize conexão privada autenticada, MFA quando suportado e configuração de firewall.

## Preparar Windows (máquina própria ou VM autorizada)

1. Instale Windows compatível, driver gráfico oficial e **DaVinci Resolve original** pela fonte oficial Blackmagic. Confirme manualmente que o editor abre e que qualquer licença exigida é válida.
2. Configure um meio **privado e autenticado** de desktop remoto para acessar pelo celular, sem publicar endereço, credenciais ou tokens no repositório.
3. Na máquina Windows, faça login na sessão **interativa** em que o Resolve será usado. A instalação de um runner como **serviço em sessão não interativa** não fornece uma GUI controlável.
4. No GitHub, abra **Settings → Actions → Runners → New self-hosted runner**, selecione Windows x64 e execute os comandos oficiais exibidos **naquela máquina**. Acrescente o label `davinci-gpu` e mantenha o runner em modo aplicativo, com a sessão gráfica ativa.
5. Confira no GitHub que o runner está **online**. Em **Actions → DaVinci original... → Run workflow**, escolha `abrir-windows-persistente`.
6. Leia o resumo da execução e confira **na própria sessão remota** se o DaVinci ficou visível. A sessão e a máquina dependem do host, não do Actions.

O workflow procura `C:\Program Files\Blackmagic Design\DaVinci Resolve\Resolve.exe`. Ajuste o caminho no YAML caso tenha instalado legitimamente em outro lugar.

## Preparar Linux (máquina própria ou VM autorizada)

1. Configure uma distribuição/driver/hardware compatíveis com a sua versão do DaVinci. Instale e teste manualmente o executável original em `/opt/resolve/bin/resolve`.
2. Abra uma sessão gráfica **X11** e confirme que `DISPLAY`, `xset q` e a GPU real funcionam com o **usuário que vai executar o runner**. A detecção de um dispositivo não comprova suporte do editor.
3. Em **Settings → Actions → Runners → New self-hosted runner**, selecione Linux x64. Instale o runner naquele Linux e use-o **como aplicativo na sessão gráfica**, com label `davinci-gpu`; não como serviço headless.
4. Com o host online, escolha `abrir-linux-persistente` no Actions. Confira na tela e use o acesso remoto privado já configurado para abrir pelo Android.

O job tenta iniciar o processo, sem publicar logs de interface. Caso não apareça, examine os logs **localmente na máquina**, não em issues/artefatos públicos. Não há correção automática de drivers, OpenCL, CUDA, GPU, licença ou prompts de primeiro uso.

## Executar a tentativa Console Full HD original

1. Mantenha o repositório **privado**. O pipeline antigo é experimental e só pode afirmar render se verificar arquivo produzido pelo **motor DaVinci**.
2. Nas opções de execução, escolha `tentar-console-fullhd` e ative **autorizar_tentativa**; caso contrário, o workflow bloqueia a tentativa.
3. Configure os Secrets exigidos pelo experimento, conforme [documentação DVIP da branch experimental](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/blob/experiment/davinci-21-1-1-software-dvip/davinci-resolve/experiments/dvip/README.md): `DAVINCI_INPUT_VIDEO_URL`, `DAVINCI_MEDIA_PASSWORD`; para o instalador, cache privado válido ou `DAVINCI_RESOLVE_LINUX_URL` oficial temporária.
4. Consulte os jobs `preflight`, `original` e o resumo final. **Um diagnóstico aprovado ou processo aberto não prova exportação.** Esta tentativa pode falhar exatamente no bloqueio de Console/GPU conhecido.
5. Não cole links de mídia, senhas, chaves Adobe/Blackmagic ou segredos no chat, no commit ou na entrada manual do workflow.

## Quando um job nem começa

Se a execução for marcada como failed e o job apresentar **runner_id=0, nenhum runner_name e zero steps**, não houve execução de comandos e a causa ainda precisa ser vista no aviso do GitHub Actions. Verifique no site a mensagem de falha, permissões de Actions, runner disponibilizado, e estado de cota/faturamento para repositórios privados. Não interprete como falha técnica do DaVinci.

Se um modo `abrir-*-persistente` permanecer em **Queued**, o GitHub provavelmente está aguardando um runner com os labels exatos, online e disponível. Ele não cria a máquina para você.

## Fontes

- [GitHub — executar workflows manualmente](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)
- [GitHub — limites do Actions](https://docs.github.com/en/actions/reference/limits)
- [Blackmagic Design — downloads e suporte](https://www.blackmagicdesign.com/support/family/davinci-resolve-and-fusion)
