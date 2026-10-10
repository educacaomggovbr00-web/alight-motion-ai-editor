# Tentativa real de instalar Windows 11 em disco esparso

Estado: **experimental**, instalação iniciada, não concluída nesta evidência.

Após pedido do usuário para avançar, conferimos novamente os recursos: volume
`/workspace` com32GiB físicos totais e aproximadamente21GiB livres no início.
`/tmp` é outro volume de4,9GiB; não fornece espaço suficiente para transferir
a ISO de7,7GiB inteira. `/dev/kvm` e GPU continuam ausentes.

Criamos disco RAW esparso novo de100GiB virtuais. O sistema convidado vê100GB,
mas a ocupação física aumenta conforme grava; não apresentamos100GiB como
capacidade física disponível. Monitor de reserva mínima4GiB e limite600s.

## Configuração executada

- QEMU10.0.13, q35 com SMM, TCG multithread, CPUmax, 2vCPU, RAM6GiB.
- OVMF_CODE_4M.ms.fd e cópia privada de OVMF_VARS_4M.ms.fd; flash seguro.
- swtpm TPM2.0 por socket local. Não alteramos a ISO nem registros de requisitos.
- ROMs QEMU/SeaBIOS reunidas em diretório privado; corrigido aviso kvmvapic.
- ISO Microsoft Windows11 Enterprise Evaluation pt-BR26H2 previamente verificada.
- Disco novo exclusivo desta VM; sem rede, sem discos pessoais conectados.

Primeira inicialização do TPM falhou porque a biblioteca swtpm estava em um
subdiretório. Corrigimos o caminho de bibliotecas e preservamos o relatório
da tentativa inicial. Na segunda tentativa, TPM e QEMU iniciaram.

## Evidências observadas

1. Instalador abriu, idioma e teclado em português.
2. Instalador reconheceu “Disco0 Espaço Não Alocado —100,0GB”.
3. Tela “Pronto para instalar” informou Windows11 Enterprise Evaluation.
4. Acionamos Instalar somente no disco novo criado para o experimento.
5. Tela “Instalando o Windows11”, primeiro10%, depois11%; gravação física
   observada, chegando a aproximadamente1,2GiB nessa observação.

Isso comprova que a tentativa avançou até copiar arquivos. Não comprova
Windows instalado, sessão de desktop, WARP no Windows11 ou Premiere.

Capturas e disco ficam fora do repositório público em
`/workspace/adobe-private-downloads/win-install-2/`. Nenhum instalador ou imagem
de sistema proprietária foi publicado.

## Reprodução

Launcher: `premiere-cloud/windows/try-windows-install.py`. Requer Python,
QEMU, swtpm, ISO oficial verificada, firmware OVMF e diretório completo de ROMs.
Para instalações normais usar caminhos dos pacotes do sistema. Para os pacotes
Debian extraídos nesta sessão, configurar LD_LIBRARY_PATH com os diretórios
`usr/lib/x86_64-linux-gnu` e `usr/lib/x86_64-linux-gnu/swtpm` da extração privada.

```bash
python premiere-cloud/windows/try-windows-install.py \
  --qemu /caminho/qemu-system-x86_64 --swtpm /caminho/swtpm \
  --iso /privado/windows11.iso --firmware /caminho/OVMF_CODE_4M.ms.fd \
  --vars-template /caminho/OVMF_VARS_4M.ms.fd --roms /caminho/roms \
  --destination /privado/tentativa-nova
```

A interface é observada/controlada por socket QMP local; não existe sessão
remota exposta nesta sessão. O script não automatiza conta, autenticação ou
cliques de instalação. Preserva disco, TPM e variáveis quando encerra.
`--resume` valida estado anterior e abre o mesmo disco sem recriar, com boot
pelo disco. Isso não garante retomar uma cópia incompleta antes do primeiro
reboot; não substitui análise do estado e não deve rodar em paralelo com a VM.

Verificações locais: compilação Python e CLI; destino existente e retomada
inválida foram recusados sem alterar o disco de teste. CI auxiliar passou:
https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38091740245

## Limites

Emulação por CPU está lenta. A reserva física ainda não foi atingida nas
observações acima. RAM6GiB serve a esta tentativa Windows, mas não atende o
mínimo8GiB do Premiere. Para testar Premiere depois, a VM precisa receber RAM
suficiente, Windows funcional, acesso autorizado à Adobe e login manual.
WARP no Windows Server já passou no teste separado; no Windows11 segue pendente.

## Resultado ao encerrar

Última captura antes do encerramento mostrou **18% concluído**. O supervisor
encerrou a VM ao atingir600s; motivo `limite_600s`, não falta de espaço nem
mensagem de incompatibilidade observada. Não houve primeiro reboot confirmado
nem desktop Windows. Encerrar o processo durante a cópia não equivale a pausar
e salvar a memória da VM; o disco contém instalação parcial e pode não iniciar.

Relatório privado `attempt.json`:

```json
{
  "state": "experimental",
  "reason": "limite_600s",
  "durationSeconds": 600,
  "freePhysicalBytes": 18868948992,
  "diskVirtualBytes": 107374182400,
  "diskAllocatedBytes": 3393892352,
  "qemuExit": 0,
  "windowsInstalledProven": false,
  "warpInWindows11Proven": false,
  "premiereInstalledProven": false
}
```

Ocupação física do disco:3,16GiB; espaço físico restante:17,57GiB. A reserva4GiB
não foi atingida. Captura privada final `screen-final.ppm`, SHA256:
`2014adbe1f0b352af984a40fdf8bff13dfbd46c5163c2b84d45cea58d58756f2`.
Disco parcial, TPM e firmware privado preservados; nenhum recurso pago criado.

CI após a opção de retomada passou:
https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38092127133

Próxima tentativa precisa de orçamento de tempo maior, mantendo monitor físico;
nesta execução o espaço não impediu começar. A compatibilidade do Premiere com
WARP continua pendente até existir desktop Windows funcional.
