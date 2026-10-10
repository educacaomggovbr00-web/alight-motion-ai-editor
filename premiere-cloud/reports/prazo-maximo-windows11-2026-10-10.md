# Prazo máximo do job Windows 11

Atualização a pedido do usuário: limite total de 360 minutos (6 horas), máximo atual por job GitHub-hosted: https://docs.github.com/en/actions/reference/limits . Download limitado a 1800 segundos (30 minutos); instalação/teste limitado a 18000 segundos (5 horas). Os 30 minutos restantes acomodam preparação, checksum, encerramento e publicação dos relatórios. Os limites não obrigam a execução a durar esse tempo: sucesso, erros ou falta de espaço encerram antes. Não foram criados loops ou recursos pagos.

Substitui os limites anteriores de 75 minutos por job, 20 minutos por download e 45 minutos por teste da VM. Mantidos origem oficial, hash, reservas de armazenamento e regras de comprovação. A VM continua temporária. O prazo máximo não garante instalação nem altera os termos de uso do Actions.

Validação local: actionlint v1.7.7 e compilação de sintaxe Python passaram. Nenhuma instalação do Windows ou execução do Premiere é comprovada por essa validação. Iniciar nova execução manual em main para usar os limites atualizados; reexecutar uma execução antiga usa o commit antigo.
