# Persistência e edição pelo Android — estado real

## Brasil e orçamento R$ 0

Não há infraestrutura privada/GPU nem licença Adobe configuradas nesta sessão. Nenhum recurso pago, conta, avaliação com cobrança ou assinatura foi criado. Não há solução gratuita permanente comprovada para Premiere desktop + Windows licenciado + GPU + armazenamento. O código abaixo permanece preparado para um host cedido legitimamente (por escola, organização ou alguém que autorize o uso), com licença Adobe atribuída ao usuário e acesso remoto seguro. Isso é uma possibilidade a verificar, não um recurso já disponível.

A Adobe anuncia teste de sete dias; ele não oferece uso permanente gratuito. Não iniciar avaliação com renovação automática para um orçamento zero. Fonte: https://www.adobe.com/br/products/premiere/plans.html . Não substituímos o editor solicitado.

## Evidência confirmada

Run https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38093928721 : ISO verificada, Windows 11 iniciou fase specialize e criou dispositivo D3D11 WARP CPU, em 618 segundos com KVM. Disco alocado: 18280476672 bytes. O próprio relatório informa windowsSetupCompletedProven=false, desktopConfirmed=false, premiereInstalledProven=false. Não houve desktop, login, GPU dedicada, instalação Adobe ou exportação comprovados. O disco dessa execução foi descartado; não pode ser recuperado dos relatórios.

## ISO cache não é persistência de Windows

O workflow atual já contém restore/save de ISO somente após tamanho/hash válidos. Esse código ainda precisa de uma execução com cache salvo e de outra com cache-hit confirmado. O run acima usou o YAML anterior sem cache. Cache pode ser removido por quota/inatividade, não é backup e não fornece desktop. Não armazenar disco Windows, TPM, contas ou mídia pessoal no cache público. Fonte: https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching .

## Backup e restauração implementados

`windows/vm_state.py` copia **windows.qcow2 + vars.fd + todos os arquivos TPM**, calcula SHA256 por arquivo e rejeita corrupção, caminhos indevidos, symlinks, checkouts Git e sobrescrita. Executa qemu-img check, com lock padrão, antes/depois da cópia. Só permite backup com confirmação --offline e recusa sockets VM/TPM ativos. Sempre desligar Windows pela interface e aguardar QEMU/swtpm terminarem; copiar só o qcow2 perde UEFI/TPM e pode inutilizar BitLocker. Não copiar uma VM viva. Um encerramento forçado fornece, no máximo, estado de disco sujeito à recuperação do Windows, nunca checkpoint da RAM nem garantia de retomada do instalador.

Exige Python 3, qemu-img, host Linux privado dedicado e armazenamento persistente **já montado**, fora do repositório. Use volume privado criptografado e backup separado. O script restringe permissões Linux, mas **não criptografa**, não configura ACL do provedor e não transfere para um serviço externo. Hash detecta corrupção, não autentica uma origem maliciosa. Use somente seus backups confiáveis. Reserve espaço real para cópia inteira mais 1 GiB; qcow2 tem tamanho virtual maior que seus bytes físicos, porém o backup copia seu tamanho lógico de arquivo. Inclua crescimento e espaço para projetos.

```bash
python3 premiere-cloud/windows/vm_state.py backup --offline --source /private/vm --destination /private-backups/vm-001
python3 premiere-cloud/windows/vm_state.py verify --source /private-backups/vm-001
python3 premiere-cloud/windows/vm_state.py restore --source /private-backups/vm-001 --destination /private/vm-restored
bash premiere-cloud/windows/resume-vm.sh /private/vm-restored
```

O destino precisa ser novo. Restaurar não altera a origem nem formata disco. resume-vm.sh abre o disco existente sem ISO/Autounattend, mantém TPM/UEFI e fornece NAT para completar OOBE normalmente. Pede 10 GiB RAM livre, 8 GiB disco livre e firmware OVMF Microsoft. VNC fica em 127.0.0.1:5901, sem exposição pública: só acessar por túnel SSH/VPN autenticado em host dedicado. O acesso remoto pelo Android requer cliente/túnel ou gateway privado do provedor; não foi criado nem testado. Não habilitamos login automático nem contornamos conta, TPM, licença ou OOBE. Este boot de restauração ainda precisa ser testado com Windows real preservado. VNC std não entrega GPU compatível ao Premiere.

O novo workflow `premiere-vm-state.yml` executa verify/backup/restore **apenas em repositório privado**, com variável PREMIERE_STORAGE_ENABLED=true e runner self-hosted Linux X64 com label premiere-storage. Configure VM_STATE_SOURCE e VM_STATE_DESTINATION no processo do runner, fora do checkout; para restore use origem backup e destino novo. É manual, sem agendamento, retries ou uploads de discos. Recusa este repositório público. Ele não salva automaticamente a VM efêmera do workflow público e não cria host/storage. Não habilitar enquanto esses recursos não existirem.

## Caminho de produção

Para edição preferimos Windows 11 nativo/VM GPU gerenciada persistente, evitando QEMU com GPU apenas por software. Instalar GPU/driver e confirmar preflight, sessão gráfica e licença de virtualização Windows. Registrar runner Windows na sessão interativa do repositório privado com label premiere-gpu. Os workflows já existentes baixam Creative Cloud assinado e preparam tarefas; o login Adobe é manual na sessão remota. Precisamos completar todos os testes Adobe antes de declarar funcional.

No Android: entrar no portal privado do host, abrir desktop remoto em modo paisagem/touchpad, transferir vídeo/música privadamente, abrir projeto no Premiere, editar/exportar H.264/AAC, validar com FFprobe e baixar por portal autenticado. Não há portal de upload/download, desktop remoto ou primeiro edit prontos agora. Mouse Bluetooth é opcional; toque/teclado virtual limita precisão. Salvar projetos fora do checkout e fazer backup pelo recurso privado do provedor, com Premiere fechado. Para Windows gerenciado do provedor não usar estes scripts qcow2: usar snapshots/backups nativos autorizados do serviço.

## Opções pesquisadas, não contratadas

Shadow fornece Windows 11, GPU RTX, Android/navegador e disco persistente enquanto a assinatura existir. Referência de oferta britânica em 2026-10-10: Neo Pro £39.99/mês; Power Pro £52.99/mês com 28 GB RAM/20 GB VRAM, não orçamento para Brasil. Brasil não consta da lista principal de países suportados. Não recomendamos assinar de outra região sem confirmar elegibilidade/latência. https://shadow.tech/gb/shadowpc/offers/ e https://support.shadow.tech/hc/en-us/articles/32731843752977-Accepted-Payment-Methods-for-Shadow .

Azure Virtual Desktop tem requisitos de identidade corporativa/licença elegível e cobra computação, discos/backups e tráfego; não é PC Windows grátis para conta Microsoft pessoal. Windows Server barato não substitui licença Windows 11. Preços dependem da região/SKU e não foram cotados para contratação. https://learn.microsoft.com/en-us/azure/virtual-desktop/licensing e https://learn.microsoft.com/en-us/azure/virtual-desktop/prerequisites .

Com R$0, próximo requisito concreto é encontrar acesso **cedido e autorizado** a uma máquina compatível e licença, sem criar cobrança ao usuário. Até lá, Premiere, primeiro edit e exportação permanecem bloqueados. Repetir o experimento de ISO não resolve esse requisito.

## Validação

Testes de cópia/restauração com fixtures, corrupção, sobrescrita, caminhos e symlinks passaram localmente; teste de qcow2 real pequeno vazio roda no CI com qemu-utils. Fixtures não são Windows e nenhum teste comprova desktop ou Premiere. Sintaxe shell e workflow validadas; actionlint configurado com o label personalizado do runner.

CI real concluído com sucesso: https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38095649252 . Quinze testes Python, incluindo backup/restauração e qemu-img check de qcow2 vazio real, e nove contratos UXP passaram. Backup do Windows de 18 GB e boot do disco restaurado ainda não foram executados.
