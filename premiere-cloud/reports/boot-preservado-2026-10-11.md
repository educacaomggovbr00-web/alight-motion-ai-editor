# Teste real de retomada — 11/10/2026

Estado: bloqueado. O QEMU 10.0.13 e swtpm iniciaram uma VM com o RAW privado preservado, 4 GiB de RAM, CPU emulada TCG, UEFI Secure Boot e copia de TPM/UEFI, sem ISO e sem rede. O disco original foi aberto com snapshot=on: escritas experimentais foram descartadas; o original nao foi alterado.

A captura do firmware informou `failed to load Boot0002 ... Not Found` e `No bootable option or device was found`. Portanto, o estado parcial de 18% nao forneceu boot nesta configuracao. Isso nao comprova que nenhuma recuperacao seja possivel, mas impede prometer retomada normal do Windows instalado. Nenhum desktop, GPU fisica ou Premiere foi iniciado.

Observacao limitada a 60 segundos, seguida de encerramento QEMU/TPM. Evidencia privada: `resume-readonly-20261011/screen0.png`. Nenhuma ISO foi baixada, instalacao reiniciada ou infraestrutura paga criada. Para progredir seria necessario completar/reparar a instalacao oficial e, separadamente, resolver os requisitos de GPU, armazenamento persistente e licenca Adobe.
