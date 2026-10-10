# Alight Motion AI Editor 🎬

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
