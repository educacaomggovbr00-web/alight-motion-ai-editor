# Importar um video de 15 segundos

Coloque aqui um ZIP com nome **entrada.zip** (via Add file → Upload files no navegador do GitHub).

Depois abra **Actions → Editar Emo Rap — Remotion → Run workflow** e escolha `entrada=repo-zip`, `duracao=15`, `preset=big-text-impact` e resolucao 540. O workflow utiliza `scripts/import-repo-zip.py` para verificar/extrair o ZIP e renderizar MP4 com Remotion.

**ATENCAO: repositório PUBLICO.** Fazer upload desse ZIP publica video/audio e os deixa no historico Git. Nao envie materiais privados ou de terceiros sem permissao. Para midia pessoal use uma copia PRIVADA do repo com `secret-zip`.

Nao precisa enviar o arquivo music.mp3 separadamente se quiser manter o audio dentro de `artist.mp4`.
