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
