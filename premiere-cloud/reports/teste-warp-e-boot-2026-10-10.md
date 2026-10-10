# Teste real WARP e tentativa de Windows 11

## WARP: testado em Windows Server, não em Windows 11

Criamos um dispositivo Direct3D11 usando `D3D11CreateDevice` com
`D3D_DRIVER_TYPE_WARP=5`, SDK7 e feature level11.0. O código verifica HRESULT,
ponteiros de dispositivo/contexto e libera as interfaces COM. Não testa pixels,
CUDA, efeitos, Premiere nem exportação.

Execução real passou no Windows Server2025 build26100:
https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38091335060

Log: `Dispositivo WARP Direct3D11 criado. Nao testa renderizacao nem Premiere.`
Artefato de diagnóstico:
https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38091335060/artifacts/11683309201

Script: `premiere-cloud/windows/test-warp.ps1`. Em Windows11 efetivamente instalado:

```powershell
pwsh -File premiere-cloud/windows/test-warp.ps1 -RequireWindows11
```

O parâmetro recusa Windows Server. WARP não faz o preflight de GPU física passar;
não alteramos os requisitos do instalador nem falsificamos VRAM.

## VM local: experimental

Preparação sem root: pacotes Debian do snapshot configurado, índice assinado,
QEMU10.0.13, OVMF e SeaBIOS extraídos em diretório privado fora do repositório.
A primeira tentativa falhou por ROM VGA ausente no caminho. Ajustar o diretório
de ROM para SeaBIOS permitiu iniciar o firmware UEFI. Log posterior registrou
aviso de ROM `kvmvapic.bin` ausente; precisa reunir também as ROMs QEMU no
diretório antes de uma próxima tentativa. Não usamos este boot como confirmação
de uma instalação correta.

Após cerca de111s de execução QEMU, a interface gráfica do instalador oficial
Windows11 abriu em português, na tela “Selecionar as configurações de idioma”.
Esse boot do ambiente de instalação foi observado; não é um Windows instalado.
Captura: `/workspace/adobe-private-downloads/windows-boot/boot5.ppm`.
SHA256: `7b0d59a91dea026102eb285e31c84418506d65bb9c01ad4d9eaf03dafd293092`.
VM encerrada por QMP após capturar a tela, antes de instalar; limite180s mantido.

ISO Windows11 Enterprise avaliação x64 pt-BR26H2 previamente verificada por
SHA256. VM: q35, TCG multithread, CPUmax, 2vCPU, RAM4GiB, VGA padrão, sem rede,
sem disco de instalação, sem modificar ISO, sem bypass de TPM ou Secure Boot.
Limite:180s. Sem `/dev/kvm` nem `/dev/dri` no host. Tela capturada via QMP mostrou
UEFI, prompt de boot CD/DVD e depois indicador de carregamento do Windows.
Isso não comprova desktop Windows11 nem dispositivo WARP no Windows11.

Captura local privada de carregamento: `windows-boot/boot4.ppm`, SHA256
`3f46f5e64f57d7aeebb2d4f70c41d8243a3d33eb3a415d8e7cb4246295e8260a`.

Launcher reproduzível: `premiere-cloud/windows/boot-windows-iso.sh` (validado com
`bash -n`). Usa caminhos fornecidos, nenhuma rede ou disco pessoal, destino novo
privado e timeout. Em instalação normal do QEMU, informar diretório de ROMs
completo. Nesta extração Debian, reunir ROMs de `usr/share/qemu` e
`usr/share/seabios`. A confirmação de boot exige enviar tecla pelo monitor QMP;
não há automação de login ou instalação.

## Bloqueios para continuar

Restam cerca de21GiB físicos nesta sessão. Não há capacidade de disco segura para
instalar Windows, Creative Cloud e Premiere. Um disco virtual esparso de64GiB
não cria64GiB físicos disponíveis. A VM de boot não tem TPM nem sistema
instalado; nenhuma instalação Adobe foi iniciada nela.

Próxima etapa: ambiente com armazenamento persistente suficiente (planejar ao
menos100GiB para sistema e aplicativos, além da mídia), RAM8GiB ou mais para
Premiere, CPU compatível e VM Windows11 com TPM2.0/UEFI configurados corretamente.
GPU física não é necessária para **testar WARP**, mas compatibilidade do Premiere
com WARP continua não comprovada. Só depois do desktop funcional executar o
script WARP e tentar Creative Cloud/Premiere com login manual e licença válida.

Estados: WARP/Server **testado**; boot Windows11 **experimental**;
WARP/Windows11, instalação Adobe e exportação **bloqueados**.
