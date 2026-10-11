# Editar Emo Rap — Remotion

Editor de lyric edits verticais em React/TypeScript, renderizado **pelo Remotion**, não pelo FFmpeg sozinho. FFmpeg gera somente mídia sintética de teste, decodifica amostras e FFprobe valida a saída. Premiere, Wine, Windows e Kdenlive existentes foram preservados. Não requer computador pessoal: use Actions pelo Chrome no Moto G22.

## Primeiro teste pelo celular

1. Entre no repositório → **Actions → Editar Emo Rap — Remotion → Run workflow**. Se o botão estiver escondido, use “Site para computador” no Chrome.
2. Branch `main`, entrada `demo`, duração `4`, resolução `540`, preset à sua escolha. A demo contém apenas padrões e áudio sintéticos e texto marcado **DEMO**, sem artista/letra comercial.
3. Comece com intensidade `leve` ou `medio` e `reduzir_flashes=true`. O padrão reduz a opacidade de flashes; não desliga shake/glitch.
4. Aguarde o job. Em caso de erro, abra a etapa vermelha. Não inicie vários jobs para a mesma tarefa; eles têm fila, sem cancelar execuções existentes.
5. Abra **Artifacts → meu-edit-remotion**, baixe o ZIP no celular e extraia `final.mp4`. Relatórios de codec e render acompanham o vídeo. Artefato expira em três dias: salve o MP4 no celular.

Resoluções: `540`=540×960, `720`=720×1280, `1080`=1080×1920. Todas 30 FPS. Duração de 1 a 30 segundos; mídia precisa cobrir esse tempo. A demo só fornece quatro segundos. O render é por CPU no runner Linux; não precisa simular GPU, Windows nem instalar Adobe. Não foi provisionado recurso pago. Minutos/armazenamento Actions têm limites do plano; não aumente quotas pagas automaticamente.

## Seu vídeo, música e letras

Crie um ZIP **sem subpastas**, com nomes exatos:

```text
artist.mp4       obrigatório: MP4/H.264, até 300 MiB, até 5 min, até 3840 px por dimensão
music.wav       opcional: ou music.mp3 ou music.m4a, somente uma, até 100 MiB/5 min
lyrics.json     opcional: até 1 MiB/300 palavras
beats.json      opcional: até 1 MiB/90 impactos
```

Limite ZIP/download/expansão: 450 MiB. Vídeo e áudio precisam ter duração suficiente; são cortados no tempo escolhido, não esticados. Artista usa corte central `cover`; confira se o rosto está centralizado. Quando há música, ela substitui o áudio original; sem música preserva o áudio do vídeo se existente. Sem qualquer áudio, exporta MP4 silencioso. Sem letras, não inventa legendas. **Não há transcrição nem detector automático de batidas neste módulo.**

No Android, use o gerenciador de arquivos que permita compactar ZIP. Faça upload para armazenamento que permita obter um link HTTPS temporário direto ao ZIP (não página HTML de compartilhamento). O serviço não foi provisionado por este projeto. Não cole esse link em Issues, workflow inputs, commits ou chat público.

No GitHub pelo Chrome:

- Settings → Secrets and variables → Actions → **Secrets** → New repository secret: `REMOTION_INPUT_BUNDLE_URL` com o link temporário do ZIP.
- Em **Variables**, crie `REMOTION_MEDIA_HOST` com o hostname exato, por exemplo `media.exemplo.com`, sem `https://` ou caminho. Use apenas host público confiável controlado pelo armazenamento escolhido; redirecionamentos para outro host são recusados.
- Rode workflow com entrada `secret-zip`, duração/resolução/preset desejados. Links expirados, IPs privados, ZIPs inválidos e entradas ausentes são recusados com mensagem sanitizada. O downloader não imprime URL nem credenciais.

**Repositório público implica resultado publicável:** Secrets protegem o link, mas **não tornam privado o MP4 publicado em Artifact**. Por padrão o workflow bloqueia `secret-zip` neste repo público. Use uma cópia privada do repositório para vídeos pessoais. Somente se você pode publicar a mídia, marque `permitir_resultado_publico=true`. Nunca envie mídia pessoal via Upload files no repo público. Somente saída/relatório são publicados, não mídia de entrada, bundle de React ou JSON com suas letras. Sem servidor de upload próprio ou interface de timeline: esta primeira versão é um formulário Actions.

## Letras e impactos

```json
{"words":[
  {"text":"DEMO","start":0.5,"end":0.8},
  {"text":"DARK","start":0.8,"end":1.2,"x":0.5,"y":0.6,"size":1.2,"color":"#ff334e","font":"gothic"},
  {"text":"TEXT","start":1.2,"end":1.7}
]}
```

Texto acima é demonstração, não letra/transcrição. Segundos relativos ao início da mídia: start≥0, end>start, end≤duração, starts ordenados. Palavras podem sobrepor seus intervalos para camadas; cada palavra é animada independentemente e só aparece em seu intervalo. `x/y` de 0.1 a 0.9 são posições relativas; `size` de 0.4 a 1.6 é escala; `color` hexadecimal; `font`: heavy/gothic/mono. Limite 40 caracteres por palavra. A fonte ajusta tamanho de palavras longas para caber na tela. Sem quebra automática de versos nem separação do artista/rosto.

```json
{"beats":[0.5,1.2,1.9,2.7]}
```

Impactos ordenados, dentro da duração e separados por pelo menos 0.33 segundos (no máximo ~3/s). Ausência de beats.json significa sem impactos musicais, mantendo animações de letras. Ajuste os timestamps ouvindo a música; o sistema não afirma sincronização perfeita nem estima batidas sem informar. A integração automática com o analisador antigo não está incluída.

## Presets e componentes

| Preset | Composição visual |
|---|---|
| `dark-lyrics` | Artista monocromático escurecido, preto, palavra branca central, fade, glow discreto, aumento gradual com curva Bezier e zoom lento |
| `emo-rap-glitch` | Letras agressivas, cópia cromática da palavra, RGB split em camadas de imagem/texto, tiras deslocadas/invertidas e scanlines, shake, zoom/blur curto e flashes vermelho/branco nos impactos |
| `big-text-impact` | Fonte gótica/pesada alternada, palavras grandes e pequenas, rotação/escala por spring, posições variadas, detalhe tipográfico em camada e impacto de câmera |

Componentes reais: AnimatedLyrics, ArtistVideo (OffthreadVideo), AnimatedBackground, DarkColorGrade, BeatShake, ImpactZoom, RGBSplit, GlitchEffect e FlashOverlay. Usam useCurrentFrame/useVideoConfig, interpolate, Easing e spring. Não usam Math.random, relógio ou rede para animações. Fontes Anton e UnifrakturCook são carregadas localmente dos pacotes fixados, com licenças OFL em `licenses/`; não há fonte proprietária. O mesmo frame/projeto deve ser determinístico no mesmo ambiente. Encoding MP4 pode variar entre versões de navegador/FFmpeg; não prometemos arquivo binário idêntico entre máquinas.

Glitch, glow, blur e RGB split são efeitos CSS compostos pelo Chromium; não são plugins de Alight Motion nem reconstrução fiel de uma referência específica. Motion blur físico, máscaras do artista, speed ramp, tracking e animação de cada letra dentro de uma palavra ainda não foram implementados. O nível profissional depende da fonte, tipografia e escolha dos timestamps; o teste não julga qualidade artística automaticamente.

## Teste real e desenvolvimento

Workflow **Testar Remotion Emo Rap** executa em pushes nesta pasta e manualmente. Gera os insumos sintéticos, renderiza os três presets de 4 segundos/120 frames/540×960, verifica H.264/AAC, duração e FPS por FFprobe. Compara quadros com/sem efeitos, impacto/estabilizado e entre presets, e repete o mesmo frame para hash de pixels determinista. Também renderiza um clipe sem letras e sem áudio. Artefato `teste-remotion-emo-rap` inclui MP4s, PNGs e `smoke.json`, expira em sete dias. Nenhum teste usa artista ou música protegida.

```bash
cd remotion-emo-rap
npm ci
npm run typecheck
npm test
python3 -m unittest discover -s tests -p 'test_*.py' -v
npm run test:render
# Entrada real já em public/input:
PRESET=dark-lyrics RESOLUTION=540 DURATION=4 INTENSITY=medio npm run prepare:edit
npm run render
npm run verify
```

Node 22.18.0 no Actions. Remotion/bundler/renderer 4.0.534, dependências diretas fixadas e package-lock com versões/integridades transitivas. Chromium é obtido pelo renderer quando necessário; localmente pode indicar `REMOTION_BROWSER_EXECUTABLE=/usr/bin/chromium`. O motor usa renderMedia com H.264, CRF 18, yuv420p e AAC 192k; nenhuma exportação é feita pelo Premiere.

API oficial: [renderMedia](https://www.remotion.dev/docs/renderer/render-media), [OffthreadVideo](https://www.remotion.dev/docs/offthreadvideo), [spring](https://www.remotion.dev/docs/spring), [interpolate](https://www.remotion.dev/docs/interpolate). Consulte a [licença Remotion](https://www.remotion.dev/docs/license/pricing) antes de ampliar uso empresarial; não foi comprada licença nem contratado serviço.

A prova e limitações da execução estão em [RESULTADOS.md](RESULTADOS.md). Só declarar render validado após job real bem-sucedido; implementação de código isolada não equivale a render funcional.
