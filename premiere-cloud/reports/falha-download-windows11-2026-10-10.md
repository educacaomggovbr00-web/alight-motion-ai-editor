# Falha real no download da ISO — 2026-10-10

Execução: https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38092904875

O preflight de espaço passou. O download oficial falhou com curl código 28: limite de 600 segundos, recebidos 5012062201 de 8170147840 bytes. A verificação SHA256 e a instalação da VM não começaram; o passo de instalação foi ignorado. Os logs consultados não indicam suspensão da conta.

Correção: prazo do download aumentado de 600 para 1200 segundos (20 minutos), job de 60 para 75 minutos para acomodar download, preparação e teste de VM limitado a 45 minutos. Mantidas origem Microsoft, verificação SHA256, limites de espaço e proteção contra publicação da ISO/disco. Nenhum loop de novas tentativas foi adicionado.

Validação: actionlint v1.7.7 sem erros no YAML alterado. Ainda não houve nova execução desse workflow com a correção. Aumentar o prazo permite completar na velocidade observada, mas não garante download ou instalação; a próxima execução precisa confirmar ambos. Windows instalado, WARP na VM e Premiere continuam sem comprovação por essa execução.

No celular: abrir Actions → Windows 11 - instalar VM e testar WARP → Run workflow → main. Usar uma nova execução em main; reexecutar o job antigo reutiliza o YAML do commit antigo.
