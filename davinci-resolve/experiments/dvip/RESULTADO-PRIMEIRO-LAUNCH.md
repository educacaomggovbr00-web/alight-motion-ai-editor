# Inicialização real — primeira tentativa com entrada privada

[Execução 38169296941](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38169296941), 11/10/2026.

O segredo configurado passou na validação. A compilação e os quatro compartilhamentos GLX/EGL × tipo anunciado passaram. O instalador oficial foi baixado, verificado e extraído; SHA-256 do executável original permaneceu inalterado nos dois perfis.

O processo original iniciou, mas saiu com código 0 antes da interface, exibindo **Failed to create application support directories**. Isso é falha de inicialização, apesar do código de saída 0. Nenhuma inicialização DVIP, interface funcional, projeto ou exportação foi comprovada.

Artefato auditado: `davinci-original-dvip-evidence`, ID 11714165890, SHA-256 `164eaeb70d20d8c96ee13ee22ca597e71a8de3ab6effcf6ee1a8bcfc1323bb19`. Os arquivos glx/application.log e egl/application.log contêm o erro. Não contém instalador, mídias pessoais ou links assinados.

O script post_install.sh incluído oficialmente no pacote cria diretórios usuais de suporte. O novo experimento permite essas pastas, preserva bin/libs em mounts de leitura, verifica novamente o executável e cria diretórios vazios de suporte. Não instala licença, não altera preferências de scripting e não aceita EULA automaticamente.

Nova tentativa: [38169952312](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38169952312). Resultado ainda pendente ao registrar este relatório; ausência de erros não será tratada como sucesso.
