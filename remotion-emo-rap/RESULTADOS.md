# Evidência de execução — 2026-10-11

## Render local real

Remotion 4.0.534 + Chromium local. Três renders de quatro segundos completos, um por preset, com vídeo/áudio/texto sintéticos. FFprobe: H.264/AAC, 540×960, 30/1 FPS, 120 quadros, duração de contêiner 4.011s (áudio AAC com pequena diferença de encapsulamento). Nenhuma mídia pessoal foi utilizada.

| Preset | SHA256 MP4 local | Diferença média efeito/controle (RGB 0–255) |
|---|---|---:|
| dark-lyrics | a45aa3edf885d0e51c9f47be7efd8b9604430ee67de2ccc60c49507151f99f1b | 113.52 |
| emo-rap-glitch | 20530bbdb798f631e44f921034171dd6c4ffa47f6794b55202eac4e36620ec9f | 88.68 |
| big-text-impact | 50635e5e2da2ee82464622d10e89af91227b7054c1e5a468b0378f0f27487e9b | 81.03 |

O mesmo quadro 34 foi renderizado duas vezes por preset e seus pixels reduzidos tiveram hash igual. Frames 34/46 diferiram e os três presets apresentaram diferenças entre si. Comparação não prova isoladamente cada efeito nem qualidade artística. Fontes, cores, posição e composição das amostras foram inspecionadas visualmente. Os MP4s reais são produzidos pelo renderMedia; FFmpeg somente gera insumos e decodifica quadros.

## GitHub Actions

Execução real no GitHub ainda pendente no momento deste commit. O workflow Testar Remotion Emo Rap inicia por push nesta pasta, gera três renders reais e também um clipe silencioso/sem letras, valida MP4s e publica artefatos. Resultado deve ser registrado após consultar jobs/logs. Não declarar sucesso GitHub apenas com teste local.

## Estados

- Três presets e componentes: renderizados/testados localmente com demo.
- Palavras/cores/fontes/timestamps e beats manuais: validados; quatro testes TypeScript passaram.
- Downloader privado e rejeição de ZIP/host indevidos: dois testes Python passaram com fixtures, sem serviço externo provisionado.
- 720p/1080p e mídia real de artista: implementados, render real ainda não executado.
- Workflow manual em Android e download privado: instruções/estrutura prontas, não testados no aparelho do usuário.
- Transcrição, detector automático, tracking, máscara de artista, speed ramp e motion blur físico: não implementados.
- Primeiro edit de artista: depende de entrada autorizada fornecida pelo usuário.

Todo o código legado foi preservado; mudanças fora da pasta nova se limitam aos dois workflows novos e um link no README principal. Nenhuma execução Windows foi cancelada ou alterada.
