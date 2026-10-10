# Alight Motion AI Editor 🎬

## Novo editor de emo rap — Kdenlive + MLT 🖤

O projeto agora também possui [edição dark com Kdenlive/MLT](kdenlive-mlt/README.md). Pelo Android, abra [Actions → Edit emo rap (Kdenlive MLT)](.github/workflows/editar-dark-mlt.yml), forneça seu MP4 e baixe o artefato meu-edit-emo-rap-mlt após a renderização. Este pipeline usa preto e branco e flashes de impacto, sem abrir interface gráfica. O trabalho com Adobe Premiere permanece preservado abaixo para retomada futura.

## Pesquisa preservada para o futuro: Adobe Premiere Pro original

A integração Windows com GPU está em **[premiere-cloud/](premiere-cloud/)**,
com [relatório técnico e custos](premiere-cloud/reports/2026-10-10.md), scripts,
testes e guia para Android. **Premiere ainda não instalado nem executado**:
é necessária uma máquina Windows 11 compatível, sessão gráfica e licença Adobe.
O novo workflow privado prepara tarefas; ainda não edita/exporta. Os recursos antigos abaixo são preservados.

Editor inicial de vídeos **MP4 pelo GitHub Actions**. Aplica zooms, shakes e flashes em impactos estimados da música, gera um novo vídeo e preserva a trilha sonora original.

> **Importante:** esta versão usa **FFmpeg**, não edita dentro do aplicativo Alight Motion. O resultado é um MP4, não um projeto XML editável.

## Como editar pelo GitHub (até pelo celular)

**Opção 1 — enviar vídeo ao repositório**

1. Entre na pasta [input](input) e use **Add file → Upload files** para adicionar o vídeo com nome **video.mp4** (no GitHub pelo navegador, o limite por arquivo é 25 MiB).
2. Enviar um vídeo nessa pasta inicia o workflow automaticamente. Também dá para abrir **Actions → Editar vídeo (MP4) → Run workflow** sem preencher o link.
3. Quando a execução terminar, abra-a e baixe o artefato **meu-video-editado**, um ZIP com o arquivo **editado.mp4**.

**Opção 2 — link HTTPS direto para MP4**

1. Abra **Actions → Editar vídeo (MP4) → Run workflow**.
2. Preencha **video_url** com um **link HTTPS direto para o arquivo MP4** (não um link para uma página de vídeo).
3. Escolha a intensidade: **leve**, **medio** ou **forte**.
4. Abra a execução finalizada e baixe o artefato **meu-video-editado**.

🔒 **Atenção à privacidade:** este repositório é **público**. Vídeos enviados à pasta input e links usados como parâmetros do workflow podem ser públicos; o histórico de commits continua disponível. Para vídeos pessoais, crie/use um repositório **privado**. Não use links privados ou vídeos sensíveis nesse repositório.

## O que a primeira versão faz

- Processa os **primeiros 30 segundos** de um vídeo.
- Converte para **vertical 720×1280 (9:16), 30 FPS**; fontes horizontais podem ter as bordas cortadas.
- Estima picos de energia do áudio para aplicar **shakes, zooms e flashes**. Quando não detecta batidas, utiliza impactos visuais em intervalos fixos.
- Preserva o áudio original de maneira contínua e exporta **MP4 H.264/AAC**.
- Disponibiliza o vídeo em **Actions → Artifacts** por 7 dias.

## Rodar no computador (opcional)

Tenha **Python 3** e **FFmpeg / FFprobe** instalados:

    python3 editor.py input/video.mp4 --output output/editado.mp4 --intensidade forte

Outras opções: --url https://servidor/video.mp4, --max-segundos 45, --largura 720, --altura 1280, --fps 30.

## Limitações e próximos passos

A sincronização musical ainda é **aproximada**. O editor não seleciona cenas automaticamente, não acessa sua galeria, não controla o Alight Motion pelo Android e não altera projetos XML do Alight Motion.

O próximo passo para integração com Alight Motion é validar um **XML exportado pelo próprio app** antes de modificar seus keyframes ou camadas. O GitHub hospeda o código e executa a conversão do vídeo; **não substitui sozinho a conexão com o app**.


## Experimento Premiere Pro no Linux (Wine)

Criamos uma pasta separada para estudar a compatibilidade no Linux:
**[premiere-linux/](premiere-linux/)**.

Na aba [Actions](../../actions), abra **Testar Wine para Premiere (experimental)**
e execute **Run workflow**. O sistema instala Wine e Xvfb num Ubuntu temporário,
tenta abrir um ambiente Windows simulado e gera um relatório de diagnóstico.

**Isso não instala nem executa o Adobe Premiere Pro.** O editor atual da
Adobe não oferece suporte oficial ao Linux; conseguir abrir o Wine não
garante compatibilidade com Premiere, GPU ou Creative Cloud. Não publique
instaladores ou credenciais Adobe neste repositório público.

O editor MP4 com FFmpeg continua disponível independentemente desse teste.

