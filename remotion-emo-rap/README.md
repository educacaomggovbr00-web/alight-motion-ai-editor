# Editar Emo Rap — Remotion

Editor de lyric edits verticais em React/TypeScript, renderizado **pelo Remotion**, não pelo FFmpeg sozinho. FFmpeg gera somente mídia sintética de teste, decodifica amostras e FFprobe valida a saída. Premiere, Wine, Windows e Kdenlive existentes foram preservados. Não requer computador pessoal: use Actions pelo Chrome no Moto G22.

**Render real comprovado no GitHub Actions:** [execução aprovada](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38097819260) e [MP4s de demonstração](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38097819260/artifacts/11686472563). Três presets testados em 540×960/30 FPS; mídia real e 720p/1080p ainda não foram renderizados neste teste.

## Usar no GitHub o video de 45 a 60 segundos (Moto G22)

Para um clipe **ja recortado** em 15 segundos, com trilha sonora dentro do MP4:

1. Baixe o pacote `entrada_github_remotion.zip` preparado com `artist.mp4`, `beats.json` e `lyrics.json`. As palavras no pacote sao **texto artistico de exemplo**, nao transcricao da musica; os impactos sao estimativas de energia do audio.
2. **Atencao: este repositorio e PUBLICO.** Enviar `entrada.zip` a ele divulga video, audio e textos e o conteudo pode permanecer no historico Git. So continue com arquivo que voce tenha direito de publicar; para material privado use copia privada do repositorio e `secret-zip`.
3. No navegador Android, abra [`remotion-emo-rap/importar/`](importar/), toque em **Add file → Upload files**, envie o ZIP renomeado exatamente `entrada.zip` e confirme o commit.
4. Abra [Actions → Editar Emo Rap — Remotion](../../actions/workflows/editar-remotion.yml). Selecione branch main, `entrada=repo-zip`, `preset=big-text-impact`, `intensidade=medio`, `resolucao=540`, `duracao=15`, `reduzir_flashes=true` e **`permitir_resultado_publico=true` somente se tiver autorizacao para divulgar a midia e seu resultado**.
5. Toque em Run workflow e baixe o artefato `meu-edit-remotion` para obter `final.mp4`. O projeto nao abre CapCut e nao altera os projetos Premiere/Kdenlive.

O modo `repo-zip` usa o mesmo extrator seguro `download-input.py` dos uploads secretos, rejeitando ZIPs invalidos. Os testes de CI verificam o importador com dados sinteticos. A renderizacao real de `repo-zip` com este video ainda depende de voce fazer upload e rodar o workflow. Ao enviar video com audio embutido, nao adicione `music.mp3`: o Remotion preserva o audio original.

## Primeiro teste pelo celular

1. Entre no repositório → **Actions → Editar Emo Rap — Remotion → Run workflow**. Se o botão estiver escondido, use “Site para computador” no Chrome.
2. Branch `main`, entrada `demo`, duração `4`, resolução `540`, preset à sua escolha. A demo contém apenas padrões e áudio sintéticos e texto marcado **DEMO**, sem artista/letra comercial.
3. Comece com intensidade `leve` ou `medio` e `reduzir_flashes=true`. O padrão reduz a opacidade de flashes; não desliga shake/glitch.
4. Aguarde o job. Em caso de erro, abra a etapa vermelha. Não inicie vários jobs para a mesma tarefa; eles têm fila, sem cancelar execuções existentes.
5. Abra **Artifacts → meu-edit-remotion**, baixe o ZIP no celular e extraia `final.mp4`. Relatórios de codec e render acompanham o vídeo. Artefato expira em três dias: salve o MP4 no celular.

Resoluções: `540`=540×960, `720`=720×1280, `1080`=1080×1920. Todas 30 FPS. Duração de 1 a 30 segundos; mídia precisa cobrir esse tempo. A demo só fornece quatro segundos. O render é por CPU no runner Linux; não precisa simular GPU, Windows nem instalar Adobe. Não foi provisionado recurso pago. Minutos/armazenamento Actions têm limites do plano; não aumente quotas pagas automaticamente.

## Tradução automática por IA Gemini (opcional)

**Novo:** em **Actions → Editar Emo Rap — Remotion → Run workflow**, escolha
\`traducao_ia=gemini-ptbr\` para pedir ao Gemini que **escute um único trecho**
e entregue frases que ele conseguiu reconhecer com **tradução em português do Brasil
e tempos aproximados**. O Remotion usa essas frases como textos animados no edit.
Quando esta opção está **desligada** (padrão), o editor continua usando o arquivo
\`lyrics.json\` existente ou fica sem legendas, exatamente como antes.

### Configurar pelo Moto G22 (uma única vez)

1. Obtenha uma chave de API para o projeto no [Google AI Studio](https://aistudio.google.com/apikey).
   A conta Gemini de chat não é automaticamente uma chave de API e o acesso ao modelo
   depende da sua região, limites e nível de faturamento.
2. No GitHub, entre neste repositório e abra **Settings → Secrets and variables →
   Actions → New repository secret**. Nome **\`GEMINI_API_KEY\`**, valor a chave obtida
   no AI Studio. **NÃO cole a chave no ZIP, no chat, no código, em Issues ou em inputs do Actions.**
3. Faça upload do arquivo \`entrada.zip\` permitido na pasta \`remotion-emo-rap/importar\`,
   ou use \`secret-zip\` numa cópia privada do repositório. Os arquivos precisam incluir
   \`artist.mp4\` com áudio embutido, ou um dos arquivos opcionais \`music.wav/mp3/m4a\`.
4. No [workflow manual](../../actions/workflows/editar-remotion.yml), escolha
   \`entrada=repo-zip\` ou \`secret-zip\`, \`traducao_ia=gemini-ptbr\`, \`duracao=15\`,
   \`preset=big-text-impact\`, \`resolucao=540\` e \`reduzir_flashes=true\`.
   No repositório **público**, só autorize \`permitir_resultado_publico=true\` para
   uma mídia que você possa publicar. Não use a opção \`demo\` com Gemini.
5. Quando terminar, abra **Artifacts → meu-edit-remotion**: baixe \`final.mp4\` e
   \`traducao-para-revisar.json\`, que registra o texto reconhecido, a tradução e
   a clareza declarada por trecho. Esse JSON também é exposto a quem puder baixar
   o artefato, então **use repositório privado para mídia pessoal**.

Ao ligar a IA, as legendas que vierem no \`lyrics.json\` do ZIP são substituídas
**somente na cópia temporária do runner**, inclusive se forem textos DEMO.
O ZIP no GitHub não é alterado. Se quiser preservar legendas revisadas manualmente,
deixe \`traducao_ia=desligada\`.

### Limitações, custos e privacidade

- A API recebe **o áudio extraído do vídeo**, enviado ao Google para transcrição/
  tradução. A rotina tenta apagar o arquivo da Files API após a análise, mas
  as políticas de retenção e tratamento de dados do Google continuam valendo.
  Consulte condições da sua conta, especialmente em planos gratuitos.
- **IA não traduz letras perfeitamente.** Voz abafada, música alta, gírias,
  edição e sobreposição de vozes podem gerar erros. Tempos são por frase,
  **não alinhamento exato palavra por palavra**. Trechos marcados como
  incertos são omitidos das legendas automaticamente; revise antes de postar.
- A rotina usa **Gemini 3.8 Flash** pela API oficial (SDK \`google-genai==2.29.0\`),
  com **uma interação de áudio** por edição. Usa apenas os primeiros segundos
  escolhidos em \`duracao\`; até 30 segundos. Não faz pesquisa online de letras
  nem preenche lacunas inventando versos.
- Pode existir cota gratuita, mas **não garantimos gratuidade**; chave sem
  acesso ao modelo, cota esgotada ou erros da API causam falha explícita.
  Não adicionamos faturamento, pagamento automático ou qualquer chave ao código.
- Se o áudio não permitir transcrição clara, \`lyrics.json\` pode ficar vazio:
  o edit ainda terá o vídeo/áudio e efeitos, sem legendas inventadas.
- Não executamos chamada real à API com a tua chave: os testes automatizados
  usam respostas simuladas. A renderização Remotion anterior com os três presets
  foi testada; o caminho Gemini real só será validado após você configurar o
  secret e executar uma edição autorizada.
- Documentação oficial:
  [compreensão de áudio](https://ai.google.dev/gemini-api/docs/audio),
  [structured outputs](https://ai.google.dev/gemini-api/docs/structured-output),
  [limites](https://ai.google.dev/gemini-api/docs/rate-limits),
  [preços e tratamento por nível](https://ai.google.dev/gemini-api/docs/pricing).

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
