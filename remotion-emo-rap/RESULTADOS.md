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

Execução real **concluída com sucesso**: [Testar Remotion Emo Rap](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38097819260), commit 39dccba980415d749e79d415b410868acd2a7119.

[Baixar artefato de teste](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38097819260/artifacts/11686472563): 4627189 bytes, quatro MP4s (três presets de 4s e clipe silencioso/sem letras de 1s), 12 PNGs e smoke.json. Artifact SHA256: sha256:513693631b43868d082ab48ff8759a55c771db4500d2ad335a50fa06d830caa6. Expiração: 2026-10-18T00:17:00Z.

Todos os passos passaram: npm ci, TypeScript, quatro testes de contrato, dois testes Python, render real, FFprobe, diferenças entre quadros/presets e determinismo das amostras. Browser do Actions: Chrome Headless Shell 157.0.8080.0, obtido pelo renderer oficial. Resultado do primeiro commit também passou (run 38097715841); a segunda execução valida a correção dos pulsos demo e os componentes organizados.

| Preset | SHA256 MP4 no Actions (versão final) | Diferença efeito/controle |
|---|---|---:|
| dark-lyrics | cf3966f78b8c07f8c0f81cdef44dabb486d1da3ae6f4a5dd3eb976ffacbe35a7 | 113.53 |
| emo-rap-glitch | d45d6114eb8eb538f81a7069dd3069e15d0511a3c074237068857045d4334656 | 88.69 |
| big-text-impact | 3c892d468b3e44e8de592738c10b749abe4e4bf83bd66e62cba2081e51a5529b | 81.03 |

MP4s no Actions: H.264/AAC, 540×960, 30 FPS, 120 frames, contêiner 4.011s; diferenças entre presets: 79.81, 35.84, 57.69. Sem áudio/letras: teste de 1s com 30 frames validado, detalhes no smoke.json do artefato.

Os timestamps .3/1.1/1.9/2.7/3.5s também foram conferidos no áudio sintético final localmente: RMS antes 0.1061 e após impacto 0.1424 em cada batida. É prova da demo sintetizada, não detecção/transcrição de uma música real.

## Estados

- Três presets e componentes: renderizados/testados localmente e no GitHub Actions com demo.
- Palavras/cores/fontes/timestamps e beats manuais: validados; quatro testes TypeScript passaram.
- Downloader privado e rejeição de ZIP/host indevidos: dois testes Python passaram com fixtures, sem serviço externo provisionado.
- 720p/1080p e mídia real de artista: implementados, render real ainda não executado.
- Workflow manual em Android e download privado: instruções/estrutura prontas, não testados no aparelho do usuário.
- Transcrição, detector automático, tracking, máscara de artista, speed ramp e motion blur físico: não implementados.
- Primeiro edit de artista: depende de entrada autorizada fornecida pelo usuário.

Todo o código legado foi preservado; mudanças fora da pasta nova se limitam aos dois workflows novos e um link no README principal. Nenhuma execução Windows foi cancelada ou alterada.
