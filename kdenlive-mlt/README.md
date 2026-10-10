# Kdenlive + MLT — Edits dark de emo rap (sem PC)

Este módulo produz edits de **artistas reais** usando o motor de edição do Kdenlive, **MLT/melt**, instalado e executado no **Linux do GitHub Actions**. Você controla a renderização pelo navegador do celular Android. A interface gráfica do Kdenlive não abre dentro do GitHub Actions: o workflow trabalha com projetos MLT/XML e produz MP4.

**Você não perdeu o Premiere:** os experimentos Adobe continuam no repositório.

## Como fazer um edit pelo Moto G22

1. Abra o repositório no GitHub e entre na aba **Actions**.
2. Selecione **Edit emo rap (Kdenlive MLT)**.
3. Toque em **Run workflow**.
4. Em **video_url**, cole um **link HTTPS direto que entrega o arquivo MP4**; se deixar vazio, o editor usa o arquivo público **input/video.mp4**, caso ele exista no repositório.
5. Escolha a intensidade dos flashes: **leve, medio ou forte**.
6. Escolha a qualidade: **540×960/30 fps** (recomendado para começar), **720×1280/30**, **1080×1920/30**, ou **540×960/60**.
7. Escolha o trecho do vídeo: 10, 15, 25, 30, 45 ou 60 segundos.
8. Execute, abra a execução concluída, desça até **Artifacts** e baixe **meu-edit-emo-rap-mlt**. Ele contém o **editado.mp4** pronto.

O artefato opcional **projeto-dark-mlt** contém o projeto **projeto.mlt**, o clipe preparado **assets/preparado.mp4** e um **manifesto.json** com as marcas de impacto estimadas. Para rodar esse projeto manualmente, extraia os arquivos mantendo a mesma estrutura de pastas.

**Privacidade:** este repositório é **público**. Nunca compartilhe vídeos pessoais ou links privados nos inputs/commits de um repositório público. Um vídeo em input/video.mp4 pode ficar para sempre no histórico Git. Para arquivos maiores ou privados, prefira repositório privado e URLs HTTPS temporárias (lembre-se de que parâmetros de workflow também podem ficar visíveis a pessoas com acesso). O download HTTPS aceita até **250 MiB** por arquivo.

## Efeitos desta primeira versão

- **Preto e branco** feito por filtro **greyscale do MLT**.
- **Flash nas batidas** feito pelo filtro **brightness do MLT** em curtos trechos.
- **Cortes na timeline MLT**, delimitando trechos normais e impactos.
- **Sincronização aproximada:** detecção de picos de energia do áudio; fallback com batidas a cada 0,75 segundo se não detectar o suficiente.
- **Formato vertical 9:16, H.264, áudio AAC** quando o arquivo de entrada tem áudio.
- MLT renderiza o vídeo; FFmpeg faz conversão/preparo e recoloca o áudio original no resultado.

**Ainda NÃO faz:** velocity verdadeiro, motion blur, RGB split, vários clipes simultâneos, legendas automáticas ou shakes de câmera. Esses recursos são para versões futuras. O algoritmo não compreende o estilo musical; ele apenas estima picos de volume.

Os primeiros 25 segundos são processados por padrão. A duração limite é 60 segundos, embora exportações longas em 1080p possam demorar ou exceder o tempo do workflow.

## Scripts e renderizador

- **editar_dark.py:** Python 3, cria vídeo preparado e gera projeto MLT.
- **../.github/workflows/editar-dark-mlt.yml:** workflow manual do celular.
- **../.github/workflows/testar-kdenlive-mlt.yml:** teste de instalação Kdenlive + MLT, clipe sintético, renderização real, validação H.264/AAC e artefato.
- **MLT:** https://www.mltframework.org/
- **Kdenlive:** https://kdenlive.org/

Uso local opcional num computador Linux (não é necessário possuir PC; GitHub Actions faz isso):

    sudo apt-get install kdenlive melt ffmpeg frei0r-plugins
    python3 kdenlive-mlt/editar_dark.py input/video.mp4 --intensidade forte --output-dir output/mlt-dark

Para re-renderizar um projeto extraído, entre na pasta contendo projeto.mlt e assets, e execute:

    melt -progress2 projeto.mlt -consumer avformat:reexportado.mp4 vcodec=libx264 acodec=none

A reexportação direta acima renderiza a **imagem sem trilha sonora**; o editado.mp4 produzido pelo script completo inclui áudio se ele estiver presente na fonte.

## Teste

Na aba **Actions**, confira **Testar Kdenlive + MLT**. O teste baixa as dependências e produz um clipe sintético de ~2 s com som. A confirmação de funcionamento é a execução bem-sucedida da etapa **Verificar vídeo, áudio, timeline e metadados**. O teste não contém vídeos reais de artistas; para isso é preciso fornecer seu próprio MP4 ou URL.
