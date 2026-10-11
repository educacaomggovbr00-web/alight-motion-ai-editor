# Finalizacao Gemini + lyric edit

## Evidencias e limites

A documentação oficial consultada lista `gemini-3.8-flash` e o SDK `google-genai` aceita Interactions com entrada de áudio por Files API e saída JSON estruturada. SDK fixado em 2.29.0. A disponibilidade para uma conta específica só será confirmada na chamada real autorizada com a nova chave. Não houve chamada real ao Gemini neste ambiente.

Fontes oficiais: [modelos](https://ai.google.dev/gemini-api/docs/models), [áudio](https://ai.google.dev/gemini-api/docs/audio), [saída estruturada](https://ai.google.dev/gemini-api/docs/structured-output).

O workflow verifica presença do Secret antes de instalar dependências, valida mídia antes de enviar áudio e limita a execução a 45 minutos. Cada requisição ao SDK tem limite de 120 segundos e uma tentativa. A interação usa `store=False`; o arquivo enviado tem exclusão solicitada ao final. Isso não substitui as políticas de dados e retenção do Google; confira-as antes de enviar material pessoal. Falha na limpeza gera aviso sem conteúdo sensível. A API pode ter quotas ou cobranças conforme a conta; não foi ativada cobrança neste trabalho.

A transcrição preserva o original e traduz para pt-BR. Trechos incertos são omitidos. Timestamps inválidos, sobrepostos ou que colapsam ao arredondar são rejeitados. Divisão por palavra é distribuição aproximada do tempo da frase, sem alinhamento fonético comprovado. O arquivo `traducao-para-revisar.json` contém original, tradução e marcação de revisão humana; não publique sem revisar.

## Estética

`big-text-impact` mantém tipografia pesada/gótica legalmente distribuída, escala por spring e rotação por palavra. Agora inclui RGB split e glitch reduzido nas batidas fornecidas, aproximação cinematográfica gradual e pequenos zooms nos inícios das palavras. Frases podem quebrar linha; letras ficam acima do tratamento de cor do vídeo. O glitch reduzido evita inversão branca e respeita intensidade. Redução de flashes continua ligada por padrão. Isso reduz estímulos, mas não constitui certificação de segurança visual.

## Fluxo pelo Moto G22

Para mídia pessoal, use uma **cópia privada** do projeto. Não envie o ZIP para o repositório público: ele conterá vídeo e áudio. No navegador, ative “Site para computador” se necessário.

1. Na cópia privada, abra `Settings > Secrets and variables > Actions > New repository secret`. Nome: `GEMINI_API_KEY`. Valor: uma chave **nova** criada na sua conta Google AI Studio. Nunca envie a chave no chat. Revogue a chave antiga exposta na conta do provedor.
2. Em `remotion-emo-rap/importar/`, use `Add file > Upload files` e envie o pacote renomeado para `entrada.zip`. A mídia deve conter `artist.mp4`, `beats.json` opcional e `lyrics.json` opcional na raiz do ZIP. O upload pelo navegador GitHub tem limite de 25 MB por arquivo; para pacotes maiores use o fluxo `secret-zip` com armazenamento privado HTTPS e link temporário, conforme README.
3. Abra `Actions > Editar Emo Rap — Remotion > Run workflow`. Entrada `repo-zip`, tradução `gemini-ptbr`, preset `big-text-impact`, intensidade `medio`, resolução `540`, duração `15`, reduzir flashes ligado. Na cópia privada não é preciso autorizar resultado público.
4. Após sucesso, abra `Artifacts > meu-edit-remotion`, baixe e extraia. Revise o JSON de tradução junto do MP4. Para exportar maior, repita com resolução `1080` após conferir sincronização na prévia.

Para material comprovadamente publicável, o workflow público exige a autorização explícita `permitir_resultado_publico`; artefatos não são armazenamento privado garantido. Não há autorização para publicar o vídeo pessoal fornecido.

## Estados

- SDK e validação offline: testados, sem credenciais.
- Presets e render sintético: ver execução CI do commit correspondente.
- Trecho original 45–60: pode ser preparado localmente, sem publicação no GitHub.
- Transcrição/tradução do artista por Gemini: bloqueada pela nova chave e execução autorizada com mídia privada.
- MP4 real com tradução validada: pendente; código e diagnóstico não equivalem a esse resultado.
