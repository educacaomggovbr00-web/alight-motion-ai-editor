# DaVinci Resolve 21.1.1: experimento DVIP por CPU

Branch: `experiment/davinci-21-1-1-software-dvip`. A main e os experimentos anteriores permanecem preservados.

## Evidência anterior e limite

A execução [38165021201](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38165021201) comprovou os quatro compartilhamentos GLX/EGL × CPU/GPU anunciado, inclusive a leitura OpenGL `[42, 8, 9, 10]` após escrita OpenCL. Isso não comprova inicialização do Resolve.

O artefato aprovado contém relatórios, não bibliotecas compiladas. Este experimento reproduz Mesa 26.2.4, patch, opções, imagem Debian fixada pelo digest e LLVM 22.1.8. Uma única imagem nova atende ao gate e ao aplicativo; versões e hashes são registrados. Anunciar tipo GPU não cria GPU física ou VRAM.

## Executar pelo Android

1. Obtenha o download Linux 21.1.1 pelo formulário oficial da Blackmagic Design: https://www.blackmagicdesign.com/support/family/davinci-resolve-and-fusion .
2. Em Settings → Secrets and variables → Actions → New repository secret, configure `DAVINCI_RESOLVE_LINUX_URL` com o endereço temporário oficial do ZIP. Nunca coloque esse endereço em mensagens, arquivos, issues ou logs.
3. Em Actions, abra o workflow existente `testar-mesa-software-sharing.yml`, toque Run workflow e selecione a branch experimental acima. O nome exibido na branch é “DaVinci — DVIP original 21.1.1 por CPU (experimental)”.
4. Consulte `davinci-dvip-preflight` e, quando disponível, `davinci-original-dvip-evidence` em Artifacts. Relatórios e capturas mostram os resultados reais. Apenas um MP4 produzido pelo Resolve e aprovado pelo FFprobe comprova exportação.

Sem entrada válida, o workflow bloqueia antes de compilar ou baixar. Não há instalação Windows, GPU paga, criação de conta ou automação de login.

## Execução e integridade

Primeiro passam os testes de privacidade, limites e gates. O kernel deve disponibilizar `/dev/udmabuf`; memória anunciada não substitui esse recurso. Recompila-se o ambiente auditado e repetem-se os quatro buffers reais. Só depois baixa-se uma vez o ZIP oficial, em pasta temporária privada.

O endereço exige HTTPS e host/caminho/versionamento oficiais. O instalador e o executável são comparados aos SHA-256 da amostra oficial previamente obtida. Esses hashes são referências observadas, não uma assinatura digital publicada pelo fabricante. Divergência bloqueia a execução. A extração AppImage não modifica o executável e não é apresentada como instalação nativa completa. Os diretórios bin e libs são montados somente para leitura; pastas normais de suporte podem ser criadas na extração temporária. Nenhuma credencial ou dado de licença é fornecido. Não há redistribuição ou cache público do instalador.

Dois perfis, GLX e EGL, recebem o mesmo ambiente Mesa/Rusticl. Cada um repete o probe antes de iniciar o original, registra bibliotecas carregadas, captura da interface, OCR e erros DVIP. Cada contêiner limita memória a 6 GiB e CPU a dois núcleos; execução do perfil a 300 segundos, workflow pesado a 45 minutos. Processos próprios são encerrados e arquivos proprietários temporários removidos. Artefatos têm retenção de sete dias e lista explícita de arquivos permitidos.

## Projeto e exportação: limites reais

O teste usa mídia DNxHR sintética de três segundos, gerada com FFmpeg apenas como entrada. O script usa as APIs incluídas oficialmente no SDK 21.1.1 para criar projeto, importar mídia, criar timeline e consultar formatos/codecs realmente disponíveis. Não inventa H.264 disponível no Linux gratuito.

O README de scripting incluído no aplicativo documenta a configuração de scripting externo no Resolve Studio. Se a edição instalada não disponibilizar a conexão, o teste registra o bloqueio: não altera preferências para contornar restrições. O script também é disponibilizado em Workspace → Scripts → Utility dentro da sessão temporária, como alternativa legítima interna; isso não significa que esse menu foi operado automaticamente ou que existe acesso remoto pelo celular.

EULA, licença e autenticação não são automatizadas. Uma janela aberta não comprova interface utilizável. Ausência de mensagem de erro não comprova DVIP. Somente exportação real aprovada pelo FFprobe confirma codec H.264, 640×360, 30 FPS e três segundos. O teste inicial não contém áudio; edição de mídia pessoal e áudio continua pendente.

Os relatórios distinguem compartilhamento, processo iniciado, diálogo Unsupported GPU, erros DVIP, conexão SDK, projeto, timeline e exportação. Nenhum resultado positivo é fabricado. Se falhar, o próximo experimento deve partir do erro registrado, sem repetir downloads desnecessários.

## Cache do Mesa (branch experimental)

A action local `.github/actions/mesa-dvip-cache` guarda somente `docker save codex-mesa-dvip`, comprimido com Zstandard, SHA-256 e ID da imagem. A imagem contém Mesa, LLVM, ferramentas de compilação e probes livres; não contém DaVinci, instaladores, mídia, licença, credenciais ou sessões. O runtime com os scripts atuais é reconstruído a partir desse Mesa a cada execução.

A chave exata inclui sistema, arquitetura e hashes do Dockerfile, patch e três probes copiados. Mudança de código do supervisor não recompila Mesa; mudança nesses arquivos invalida o cache. Não há fallback para chaves antigas. A carga exige SHA-256 e ID de imagem correspondentes. Os quatro testes GL/CL continuam obrigatórios antes de qualquer download proprietário.

O cache é salvo imediatamente depois da compilação, mesmo se o DVIP ou a exportação falharem depois. A primeira execução ainda compila; as próximas podem restaurar. Cache não é backup permanente: pode ser removido pelo GitHub por limites de armazenamento ou inatividade. Não preserva projetos ou o desktop, nem corrige o erro DVIP.

O workflow separado `testar-cache-mesa-dvip.yml` verifica gravação num runner e restauração em outro, identidade da imagem e quatro buffers reais. Não utiliza o segredo do Resolve nem baixa o instalador. Commits marcados `[mesa-cache-only]` acionam esse teste sem iniciar uma nova tentativa pesada do aplicativo; o workflow manual original continua disponível.

Validação real do cache: [RESULTADO-CACHE.md](RESULTADO-CACHE.md). Gravação e restauração entre runners e execuções passaram; carga medida em 45–61 segundos. Avanço nativo GLX: [RESULTADO-GLX-INTERFACE.md](RESULTADO-GLX-INTERFACE.md). Exportação pelo Resolve ainda não comprovada.

## Entrada privada e cache ampliado (experimental)

O cache agora guarda a imagem completa de dependências livres, incluindo Mesa e ferramentas. Em cache hit, não baixa também a imagem Mesa separada; copia apenas os scripts atuais. Em cache miss, recupera o cache Mesa anterior antes de instalar dependências adicionais. Não inclui DaVinci, instaladores, licença, credenciais ou caches de kernels proprietários.

A tentativa GLX invoca apenas `CodexSyntheticSmoke` pelo menu oficial Workspace → Scripts, quando seus rótulos são reconhecidos. Nunca aceita licença ou faz login. O teste sintético tem áudio, projeto, timeline, zoom estático 1.06 e consulta os codecs reais. Se H.264 MP4 não estiver disponível, tenta DNxHR MOV anunciado pelo editor e registra separadamente a conversão auxiliar do render nativo para H.264/AAC. FFmpeg não gera a timeline ou substitui a renderização do Resolve. Sem render nativo e FFprobe, o workflow falha. O estilo completo de emo rap continua pendente.

Para disponibilizar seu vídeo ao runner sem publicar seu link ou um MP4 em claro, configure no navegador Android, em **Settings → Secrets and variables → Actions → New repository secret**:

- `DAVINCI_INPUT_VIDEO_URL`: o link do arquivo no Google Drive, com acesso suficiente para download pelo runner. Não automatizamos login do Google.
- `DAVINCI_MEDIA_PASSWORD`: uma senha/frase particular de pelo menos 16 caracteres. Nunca cole essa senha em chat, código, comentários ou issues. Ela também será usada para abrir o resultado no celular.

O segredo já existente `DAVINCI_RESOLVE_LINUX_URL` continua necessário e deve conter uma URL oficial válida. Não afirmamos que os dois novos segredos estejam configurados: só o preflight da execução solicitada pode confirmar.

Em Actions → `testar-mesa-software-sharing.yml` → Run workflow, selecione a branch experimental e marque **private_media**. O fluxo privado prepara **45–60 segundos**, 15 segundos finais, 540×960, 30 FPS, com áudio original convertido para PCM na entrada. A imagem original é ajustada com barras pretas, sem cortar seu enquadramento. O Resolve deverá importar, criar timeline, aplicar zoom e renderizar; ainda é um teste de edição básica, não um lyric edit final.

O cache de mídia só recebe `prepared.dvi`, cifrado com AES-256-GCM e chave derivada por PBKDF2-SHA256 (600 mil iterações, sal e nonce aleatórios). A chave de cache é um HMAC que muda com conteúdo, senha e receita de preparação; não é o link, senha ou SHA público do vídeo. O cache é salvo antes da tentativa de render, podendo acelerar retries mesmo quando o aplicativo falhar. Nunca inclui mídia em claro. Sem a senha correta ou com arquivo alterado, a abertura falha antes de importar no editor.

No modo privado, artefatos não recebem screenshots, logs internos, projetos ou MP4 em claro. Após validar o render, o resultado é cifrado em `final.dvr`; mídia temporária e capturas são removidas. O artefato `meu-edit-davinci-protegido` contém o arquivo protegido, resumo sem mídia e `decrypt.html`. Se o render falhar, pode existir só resumo/HTML; isso não é um vídeo pronto.

No Moto G22: baixe o artefato, extraia o ZIP e abra `decrypt.html` num navegador compatível. Escolha `final.dvr`, digite a mesma senha e toque **Baixar MP4**. O processamento de abertura ocorre no aparelho, sem enviar senha/vídeo a um servidor. O utilitário aceita resultados até 100 MiB e foi validado com WebCrypto em Node; ainda não foi testado no seu Motorola. Alguns visualizadores HTML do Android não disponibilizam WebCrypto. Nesse caso, abra no Chrome em contexto seguro, ou publique apenas este HTML público via GitHub Pages (Settings → Pages; branch experimental, raiz) e use o endereço HTTPS do arquivo. Não publique a senha ou o vídeo na pasta de Pages. Essa configuração não foi realizada automaticamente.

O cache não conserva desktop, instalação ou sessão autenticada. Projetos e caches proprietários do DVIP não são guardados. As execuções ainda precisam iniciar o aplicativo e carregar kernels pela CPU. O pipeline privado foi preparado; sua renderização real continua condicionada à execução do editor e aos novos segredos.
