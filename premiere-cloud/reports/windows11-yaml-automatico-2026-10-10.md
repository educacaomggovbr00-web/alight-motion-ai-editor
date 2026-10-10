# Windows 11 por YAML: instalação automática experimental

Workflow: `.github/workflows/windows11-instalar.yml`.

No celular, abrir Actions → **Windows 11 - instalar VM e testar WARP** →
**Run workflow** → escolher main → executar. Não precisa de PC local.
O workflow é manual: não roda a cada commit nem entra em loop.

## O que implementamos

Download direto da ISO Microsoft de avaliação pt-BR26H2, SHA256 oficial obrigatório.
Instalador original com `Autounattend.xml` pela interface documentada Microsoft.
Disco QCOW2 novo80GiB, RAM8GiB, TPM2.0 emulado, UEFI com firmware Microsoft.
KVM se disponível e acessível; TCG como alternativa experimental, mais lenta.
OCR reconhece o prompt DVD e envia Enter somente uma vez, sem clicar às cegas
no instalador. O arquivo de respostas particiona exclusivamente o disco novo0.
Não conectar discos pessoais ao reutilizar este código.

Após copiar Windows e iniciar a fase `specialize`, o convidado consulta o próprio
Windows e cria dispositivo WARP Direct3D11. Envia evidência por porta serial
local. Sucesso do workflow exige ambas as evidências. Timeout, erro do convidado,
ISO incorreta ou falta de recurso causam falha explícita.

## Estados e limites

**Experimental** até a execução completa. Testes de contrato e XML não comprovam
instalação. Primeiro boot na fase specialize não é conclusão de OOBE, desktop
interativo nem licença ativada. A fase de conta Microsoft permanece manual;
não há bypass, senha, chave de produto, login automático ou conta fabricada.
Premiere/Creative Cloud não são instalados por este workflow.

Tempo VM45min; job60min; download10min. Reserva física8GiB, pelo menos48GiB
livres antes do download e38GiB depois. Disco virtual80GiB não cria espaço
físico. Runner padrão não garante essa capacidade: a referência GitHub informa
14GB SSD para runners padrão. O workflow mede o ambiente real e pode bloquear
antes de baixar; não contrata larger runner automaticamente. A disponibilidade
de KVM também é verificada, não presumida.

A VM e seu Windows desaparecem ao fim do job GitHub. Artefatos contêm somente
JSON, log QEMU e captura de tela por7dias; nunca ISO, disco Windows ou credenciais.
Isso testa instalar Windows e WARP; não cria PC remoto persistente para edição.
Recursos do runner continuam sujeitos às regras e cotas da conta GitHub.

## Fontes oficiais

- https://www.microsoft.com/en-us/evalcenter/download-windows-11-enterprise
- https://support.microsoft.com/en-us/servicing/os/windows/docs/2026/09/verify-the-authenticity-of-a-windows-11-enterprise-evaluation-iso-file
- https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/automate-windows-setup?view=windows-11
- https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/windows-setup-automation-overview?view=windows-11
- https://docs.github.com/en/actions/reference/runners/github-hosted-runners

O XML usa imagem índice1 da ISO fixada. Se a Microsoft mudar o arquivo, a
verificação SHA256 bloqueia o download; revisar versão, hash e índice antes de
atualizar. Não usamos registros LabConfig, modificação de requisitos ou imagens mini.

## Verificação desta entrega

Onze testes Python passaram localmente, incluindo os quatro testes novos de
evidência, erro do convidado, proteção de disco existente e XML. YAML foi lido
e o workflow passou no actionlint1.7.7 oficial (binário verificado com o SHA256
publicado na mesma release). CI validou também a sintaxe PowerShell dos scripts:
https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38092720917

Essa execução é de testes auxiliares. O workflow Windows11 de45min foi publicado
para execução manual e **ainda não foi executado**. Não há nova instalação
Windows completa comprovada nesta entrega; o experimento local anterior chegou18%.
