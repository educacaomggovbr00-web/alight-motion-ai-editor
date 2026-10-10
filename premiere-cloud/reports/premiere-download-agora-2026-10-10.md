# Nova tentativa direta do Premiere — 10/10/2026

A pedido do usuário, priorizamos obter o Premiere pelo link oficial, antes de criar uma simulação.

- URL: `https://creativecloud.adobe.com/apps/download/premiere`.
- Execução real via curl neste ambiente Linux, com TLS verificado, redirecionamentos somente HTTPS,
  timeout de 60 segundos e limite de 650 MB. Nenhum login, cookie de conta ou token foi fornecido.
- HTTP: **200**.
- Content-Type: **text/html**.
- Bytes efetivamente baixados: **66.896**.
- Cabeçalho: `<!doctype html>`; título da página: Adobe.
- Nenhum link direto `.exe`/`.zip` identificado no HTML recebido.
- SHA256 da resposta: `778cbd7c9bf6895edf821e3a80d4081faf46db8033228c9a652d90928b31beb8`.

**Resultado: página oficial baixada, instalador do Premiere não obtido.** Não renomeamos HTML para EXE,
não executamos scripts da página para simular autenticação e não contornamos licença/requisitos.
A resposta permanece na área privada fora do repositório; este relatório só contém dados sanitizados.

O pacote oficial Creative Cloud de 331.128.777 bytes **já foi baixado e verificado** nesta sessão,
conforme [relatório anterior](download-real-2026-10-10.md). Ele é o gerenciador Adobe, não o Premiere.
Sua cópia local não está no celular nem em uma máquina Windows externa.

Para obter o Premiere instalável: abrir Creative Cloud em Windows 11 compatível, fazer login manual
na conta Adobe autorizada e instalar Premiere pelo painel Apps. A máquina Windows/GPU e a autenticação
não estão disponíveis nesta sessão. Simular respostas de API não fornece o aplicativo nem resolve essa ausência.
Nenhuma instalação, exportação Adobe ou contratação paga realizada.
