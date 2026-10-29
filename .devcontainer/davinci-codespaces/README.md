# DaVinci 21.1.2: desktop Linux no GitHub Codespaces

Este ambiente cria um **desktop Linux para diagnostico e desenvolvimento**, visivel no browser pelo noVNC. **Nao e uma VM com GPU e nao garante executar o DaVinci original.** O GitHub descontinuou Codespaces com GPU em agosto de 2025. O Codespace para por inatividade e nao fica ligado permanentemente.

## Abrir pelo Android

1. Abra o repositorio na branch main -> Code -> Codespaces -> Create codespace. Selecione a configuracao **DaVinci 21.1.2 - Desktop Linux (Codespaces sem GPU)**. Confirme a cobranca indicada pelo GitHub antes de criar.
2. No VS Code online, abra Terminal -> New Terminal.
3. Execute:

    bash .devcontainer/davinci-codespaces/start-desktop.sh

4. Abra a aba Ports, localize 6080 e confirme **Port Visibility: Private**. Abra o link encaminhado pelo GitHub e selecione vnc.html -> Connect. Apenas voce, autenticado pelo GitHub, deve acessar essa porta.
5. Rode o diagnostico de GPU:

    bash .devcontainer/davinci-codespaces/check-gpu.sh

6. Quando terminar, pare o Codespace em https://github.com/codespaces para evitar consumo desnecessario.

## Versao original 21.1.2

O workflow **DaVinci original — editar vídeo com Console Full HD (uma tentativa)** usa uma branch separada, experiment/davinci-21-1-2-console-fullhd, e o runner GitHub Actions. Esse teste e independente do Codespace. O download do DaVinci original **nao** ocorre automaticamente aqui: e proprietario, grande, requer URL oficial temporaria e, para uso real, uma GPU compativel. Nunca coloque a URL assinada ou videos pessoais no repositorio PUBLICO. Para o Actions, configure URL somente em Secret. Codespaces Secrets sao separados dos Actions Secrets.

Para realmente editar em DaVinci pelo celular, use PC/VM persistente com GPU compativel, escritorio remoto privado e DaVinci instalado legitimamente. O Codespaces nao fornece esse hardware.

Nao mude a visibilidade da porta 6080 para Public. O servidor VNC e o proxy escutam so em localhost. Nao coloque senha ou video pessoal em commits publicos.

Documentacao:
- https://docs.github.com/en/codespaces/developing-in-a-codespace/creating-a-codespace-for-a-repository
- https://docs.github.com/en/codespaces/reference/security-in-github-codespaces
- https://github.blog/changelog/2025-08-01-upcoming-deprecation-of-gpu-machine-type-in-codespaces/

## Link e senha no terminal

No Codespace ativo, atualize sua branch e execute `bash .devcontainer/davinci-codespaces/start-desktop.sh`. A saída imprime a URL do noVNC usando `CODESPACE_NAME` e `GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN`, além de uma senha VNC aleatória de **8 caracteres** (limite de autenticação VNC clássica). Mantenha a porta encaminhada `6080` como **Private**, mesmo com senha. Senha guardada só no HOME do Codespace (`chmod 600`), nunca no repositório. Não envie captura de tela com senha.

## Próxima etapa: DaVinci original

Diagnóstico rápido, sem download:
```bash
bash .devcontainer/davinci-codespaces/try-davinci.sh
```

**Tentativa explícita** de baixar o ZIP oficial 21.1.2 e abrir o editor original (pode ocupar mais de 15 GiB de disco, consumir minutos de Codespaces e falhar devido à falta de GPU):
```bash
bash .devcontainer/davinci-codespaces/try-davinci.sh --download-and-launch
```

O script usa o Secret de ambiente `DAVINCI_RESOLVE_LINUX_URL`, quando disponível, ou solicita colar a URL assinada em entrada **oculta** no próprio terminal, sem salvá-la no repositório ou histórico do shell. O downloader confere a origem oficial HTTPS, nome/versão do ZIP, tamanho e hash observado, não uma assinatura publicada pelo fabricante. Um `Expires` vencido bloqueia o download. A extração permanece numa pasta privada em `$HOME/.local/state/davinci-codespaces/resolve-21.1.2`. O launcher não promete interface funcional, GPU ou render. Não exponha VNC ao público.


## Desktop de computador completo — XFCE

O comando `bash .devcontainer/davinci-codespaces/start-desktop.sh` agora instala (na primeira execucao) o XFCE com **barra de tarefas inferior, menu Iniciar, alternancia entre janelas, relogio e icones de desktop**. Inclui: Thunar (arquivos), Terminal XFCE, navegador Falkon, Mousepad (editor de texto), Galculator, Ristretto (imagens), Xarchiver, capturas de tela e configuracoes XFCE. A primeira instalacao pode consumir armazenamento e tempo de Codespaces; o resto dos boots reutiliza os pacotes. `start-full-desktop.sh` tambem pode ser usado diretamente depois que Xvfb estiver ligado.

Para atualizar seu Codespace existente:
```bash
git pull --ff-only origin experiment/davinci-21-1-2-console-fullhd
bash .devcontainer/davinci-codespaces/start-desktop.sh
```

Abra o LINK exibido no terminal, informe a SENHA VNC **somente no navegador** e mantenha a porta 6080 **Private**. Se a imagem nao atualizar, use Reconnect no noVNC. Em tela de celular, use Scaling > Local Scaling ou vire o aparelho para horizontal. A versao de desktop usa XFCE (leve), nao GNOME/KDE; o GitHub Codespaces nao oferece GPU para editar no DaVinci original. O desktop ainda desliga por inatividade.
