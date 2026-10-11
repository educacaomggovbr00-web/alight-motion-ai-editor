# Próximo YAML: retomar e guardar estado experimental

Workflow manual `premiere-retomar-salvar.yml`. Não altera nem interrompe os workflows Windows anteriores. Não baixa ISO, reinstala, cria conta Adobe ou simula requisitos de licença/GPU. Retoma somente QCOW2 existente com UEFI/TPM. WARP é renderização CPU, não GPU física; o launcher não comprova WARP/Premiere no disco retomado.

## O que persiste

O disco principal permanece no volume privado do host. Ao terminar a VM, o job copia disco QCOW2, UEFI e TPM para um destino exclusivo `run-ID-attempt-N` e verifica SHA256 e qemu-img check. A próxima execução usa o mesmo VM_STATE_SOURCE; para recuperar um backup use o workflow premiere-vm-state existente com destino novo, verifique e aponte VM_STATE_SOURCE para esse estado restaurado. Nunca restaurar por cima do disco original.

Não há salvamento da RAM nem garantia de continuidade exata de um instalador. Se o prazo terminar, a VM é encerrada e Windows pode precisar de recuperação. Integridade do QCOW2 não prova consistência NTFS/aplicativos. Backup não é garantido se o job for cancelado, o host cair, o disco ficar cheio ou a cópia ultrapassar o tempo restante. Prefira desligar Windows normalmente e backup externo do volume. O job reserva nominalmente 60 minutos para backup no modo 300 minutos; isso não garante que uma cópia grande termine.

## Recursos que ainda faltam

Exige cópia privada do repositório, Linux privado/dedicado já existente, armazenamento persistente privado (de preferência criptografado), ferramentas QEMU/swtpm/OVMF, 10 GiB RAM livre e runner self-hosted com label premiere-storage. Configurar no processo do runner `VM_STATE_SOURCE` e `VM_BACKUP_ROOT`, fora do checkout. Marcar variável Actions `PREMIERE_STORAGE_ENABLED=true` somente depois de configurar o host. O GitHub não cria esse host ou volume através dessa variável. O YAML recusa o repositório público atual.

A VM anterior do Actions foi descartada. O RAW de instalação parcial preservado no workspace não é QCOW2 e é recusado: não será apagado, substituído nem convertido automaticamente. Esses pré-requisitos impedem executar a retomada agora. Não foi contratada infraestrutura nem encontrada GPU gratuita.

## Pelo Android

Quando o host estiver disponível, abrir Actions > Premiere - retomar VM experimental e salvar disco privado > Run workflow e escolher tempo (até 300 minutos de VM, job máximo 360). VNC do launcher permanece somente em 127.0.0.1:5901; exige túnel autenticado SSH/VPN ou gateway privado previamente configurado. O YAML não fornece portal remoto nem expõe porta pública. Desktop, login Adobe autorizado, instalação e exportação Premiere continuam testes separados e pendentes.

## Validação

YAML validado por parser local e actionlint quando disponível. CI auxiliar verifica scripts existentes e testes. Isso não equivale a boot do disco restaurado nem instalação Premiere. Nenhum disco/ISO/TPM é colocado em cache GitHub ou artefatos; apenas status sanitizado pode ser enviado.
