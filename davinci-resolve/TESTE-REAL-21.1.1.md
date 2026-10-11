# Teste real do DaVinci Resolve 21.1.1 no Linux — 11/10/2026

## Resultado
O executável original da edição gratuita foi realmente iniciado neste ambiente. Ele confirmou a versão **21.1.1.0010** e abriu uma janela de erro e a interface de preferências. **Edição e exportação estão bloqueadas:** a tela informou `Unsupported GPU Processing Mode`. Não foi criado projeto nem exportado vídeo.

Este é um teste local no ambiente de execução do Codex, não uma execução de instalação no GitHub Actions. Os testes anteriores de OpenCL em Actions continuam sendo apenas testes de computação na CPU.

## Download e preparação
- Fonte: HTTPS oficial `sw.blackmagicdesign.com`, usando o link temporário fornecido pelo usuário. A URL assinada não foi publicada.
- ZIP: HTTP 200; 4.093.133.440 bytes; extração com verificação CRC concluída.
- Instalador extraído: `DaVinci_Resolve_21.1.1_Linux.run`; 4.103.939.296 bytes.
- SHA-256 do instalador: `6ed698d0b1bd7fe2fa97076fae0c24f9e0cdd0fdeaf0cfea9a8a3df730a48a15`.
- O hash identifica o arquivo testado; não há hash esperado publicado nem assinatura digital validada neste teste.
- Payload AppImage extraído com SquashFS; executado diretamente por `bin/resolve`. **Não foi concluída instalação de sistema em /opt/resolve.**
- Os instaladores e arquivos extraídos permanecem privados no ambiente temporário. O ZIP duplicado foi removido após extração validada para liberar espaço. Não são armazenamento permanente nem foram enviados ao repositório.
- As instruções HTML incluídas pela Blackmagic afirmam que a edição gratuita não exige dongle nem ativação. Nenhuma licença foi contornada.

## Ambiente efetivamente usado
Debian 13 x86_64; RAM indicada pelo aplicativo: 9,7 GB; sem dispositivo GPU /dev/dri ou /dev/nvidia0.
Tela virtual X.Org/Xvfb 1280×720, sem acesso externo; Mesa em modo software e PoCL 6.0 OpenCL na CPU, com dois threads.
O teste anterior de kernel OpenCL produziu [3,5,7,9], mas isso não transforma a CPU em uma GPU aceita pelo editor.

## Evidência do aplicativo
A primeira tentativa perdeu a tela virtual e sofreu erro de inicialização Qt. Corrigida a tela, a segunda tentativa realmente apresentou a interface:
1. Janela `Unsupported GPU Processing Mode`.
2. Botão `Update Configuration` abriu `Memory and GPU`.
3. Lista de GPUs vazia; ao desmarcar o modo automático, nenhum modo de processamento apareceu.
4. Ao desmarcar a seleção automática de GPU, a lista continuou vazia.
5. Tentativa limitada a 65 segundos; nenhuma mídia pessoal foi importada.

Trechos reais do log de 15:04:31 UTC:
```text
GPUDetect: No matched GPUs found.
Main.GPUConfig: Failed to select a valid compute API.
Main.GPUConfig: No GPUs selected!
GPU.MultiBoardMgr: Fatal error: "Unsupported GPU Processing Mode",
"Please review the GPU drivers and GPU configuration under preferences."
UI.GLIO: MainPlayer: Failed to create DVIP context.
Main: Failed to initialize OpenGL texture pool, no valid contexts available.
```

Capturas locais privadas: `now92.png` (erro) e `preferences92.png` (configuração).
SHA-256:
- erro: `94557b23aaded3cae32a0655686a0ad927de7f376a60c519dba4912ebe15f217`
- configuração: `41f10ab903a5efe9255dff76548f261170bd1b549fd343cf53dadc78e19d9424`

## Estados separados
| Etapa | Estado |
| --- | --- |
| Download oficial e extração | Testado |
| Executável original iniciado, versão confirmada | Testado |
| Janela de erro e preferências | Testado |
| Instalação de sistema | Não concluída |
| GPU compatível e motor de processamento | Bloqueado |
| Projeto, timeline e exportação MP4 | Não iniciados |
| Acesso remoto utilizável no Android | Não preparado |

## Reprodução
`bash davinci-resolve/tentar-abrir-extraido.sh /caminho/privado/squashfs-root /caminho/privado/relatorio`
Requer Xvfb, timeout e as dependências reais do aplicativo. Para PoCL instalado fora do sistema, forneça os diretórios através de `DAVINCI_EXTRA_LIBS` e `OCL_ICD_VENDORS`.
O script abre o executável durante até 65 segundos e registra o resultado. Código de saída 0 ou uma janela de preferências **não comprovam edição**. Os logs ficam privados fora do checkout; revise-os antes de compartilhar.

## Próxima etapa necessária
Repetir o teste em máquina com GPU real e drivers OpenCL/CUDA suportados pela versão instalada, RAM suficiente e sessão gráfica persistente. Com orçamento zero, falta acesso autorizado a essa máquina; este teste não encontrou solução funcional com CPU simulando GPU. Não foram contratados recursos.
Os projetos Premiere, Kdenlive e Remotion e todos os workflows existentes foram preservados.
