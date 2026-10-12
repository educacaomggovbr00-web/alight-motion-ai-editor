# Cache cifrado do instalador oficial do DaVinci Resolve 21.1.1

**Estado:** este código prepara o cache, mas NÃO significa que o instalador já esteja armazenado. Um runner precisa fazer o download oficial com uma URL válida pelo menos uma vez.

## Endereços oficiais
- Histórico de versões e download 21.1.1: https://www.blackmagicdesign.com/support/family/davinci-resolve-and-fusion
- Página do DaVinci Resolve: https://www.blackmagicdesign.com/br/products/davinciresolve

Selecione **DaVinci Resolve 21.1.1 (gratuito), Linux**, não Studio. A Blackmagic gera uma URL assinada e temporária. Não coloque essa URL no código, em issues ou no chat.

## Secrets necessários

No GitHub, acesse Settings → Secrets and variables → Actions e adicione:

- `DAVINCI_RESOLVE_LINUX_URL`: a URL HTTPS oficial temporária da versão Linux 21.1.1.
- `DAVINCI_INSTALLER_CACHE_PASSWORD`: segredo **novo, exclusivo e aleatório com 32+ caracteres**. Não use sua senha pessoal nem copie a senha do vídeo. Guarde essa senha fora do repositório.

Após configurar, abra Actions → **DaVinci — guardar instalador oficial cifrado (manual)** na branch `experiment/davinci-21-1-1-software-dvip` e execute uma vez. Esse workflow valida o SHA-256 esperado e grava **somente AES-256-GCM cifrado** no cache do GitHub. O ZIP e .run NÃO são salvos como artefatos, nunca entram no Git e são apagados do runner ao finalizar.

## Execuções seguintes

O preflight consulta a existência do cache **sem baixá-lo**. Se houver hit, permite iniciar mesmo se a URL oficial já expirou. No runner, o cache é restaurado, autenticado, seu conteúdo é conferido contra o SHA-256 do instalador original e só depois o .run é usado temporariamente. Se o cache não existir, o workflow exige a URL oficial válida.

O cache é independente do cache da imagem Mesa e não inclui código proprietário no Docker image. Existe um limite padrão de armazenamento do GitHub (10 GB por repositório); o cache pode ser removido por falta de espaço ou por política de retenção. Se a senha mudar, gere um novo cache com uma chave diferente (o identificador da chave depende do segredo aleatório).

## Segurança e limitações

CACHES DE REPOSITÓRIOS PÚBLICOS NÃO SÃO PRIVADOS: usuários podem acessar os bytes do cache a partir de workflows com acesso permitido. Por isso a criptografia autenticada é obrigatória. Nenhum segredo ou link é incluído no cache. Mesmo assim, avalie os termos de uso da Blackmagic; um repositório privado é preferível para material proprietário.

Isso não ativa o DaVinci nem prova exportação. O motor original continua sujeito a suas limitações de hardware, licença e runtime. Nenhuma restrição de licença é contornada.
