# GPU simulada e soluções pesquisadas — 10/10/2026

Estado: pesquisa documental; nenhuma GPU provisionada, nenhum Premiere executado.
Verificação local: /dev/dri e /dev/kvm continuam ausentes.

## Simulação
LLVMpipe implementa renderização por CPU. WARP também é rasterização por software.
Não fornecem GPU física, VRAM dedicada ou CUDA. Podem testar APIs gráficas; não
constituem prova de funcionamento do Premiere. O teste anterior já usou llvmpipe.
Não repetimos teste equivalente nem falsificamos nome de placa ou VRAM.
vGPU e passthrough compartilham uma GPU física do host, que continua necessária.

Fontes:
- https://docs.mesa3d.org/drivers/llvmpipe.html
- https://learn.microsoft.com/en-us/windows/win32/direct3darticles/directx-warp

## Caminhos reais
1. Shadow PC: ofertas Neo RTX 2000 Ada 16GB, RAM16GB; Power RTX A4500 20GB,
RAM28GB; fornecedor informa Windows11 e SSD. Aplicativo Android disponível.
Para trabalho profissional, consultar ofertas Pro e termos correspondentes.
Disponibilidade no Brasil, latência, preço local, versão do Windows e direitos
de instalação precisam ser confirmados antes de contratar. Licença Adobe à parte.
Não foi comprovado Premiere nesse serviço nesta sessão.
https://support.shadow.tech/hc/en-us/articles/31001157820049-Shadow-PC-Gaming-Offers-Hardware-Specifications
https://shadow.tech/us/download/
https://support.shadow.tech/hc/en-us/articles/33563634214161-Frequently-Asked-Questions-FAQ

2. Azure: documentação atual lista NCasT4_v3 T4 16GB e NVadsA10_v5 A10;
a VRAM efetivamente alocada depende do tamanho da VM, não apenas da placa inteira.
Escolher tamanho com pelo menos4GB disponibilizados. Drivers GRID redistribuídos
incluem licença vGPU; isso não inclui direitos Windows desktop nem Adobe.
Tabela consultada lista Windows11 até25H2, não26H2. A ISO26H2 baixada não foi
validada para esse driver. Precisamos de imagem Windows/driver compatíveis,
direitos Windows adequados e acesso remoto, além de orçamento regional para
VM, disco persistente e tráfego. Nenhum recurso criado.
https://learn.microsoft.com/en-us/azure/virtual-machines/windows/n-series-driver-setup

3. GitHub larger runner GPU: T4 16GB, RAM28GB, 4vCPU, SSD176GB, Windows ou
Ubuntu. Windows GPU custa USD0,102/min (USD6,12/h de execução), mais plano
Team/Enterprise Cloud de organização e licença Adobe; minutos incluídos não
pagam larger runners. A tabela não comprova combinação Windows11+GPU adequada
nem sessão gráfica persistente. Não recomendamos como primeira estação de edição.
https://docs.github.com/en/actions/reference/runners/larger-runners
https://docs.github.com/en/billing/reference/actions-runner-pricing

## Próxima etapa concreta
Priorizar PC Windows persistente com GPU real e acesso Android, depois conectar
runner privado usando o YAML existente. Para Azure, validar imagem até25H2 e
direitos Windows; para Shadow, confirmar região/latência e oferta profissional.
Conta Adobe e autenticação manual na sessão gráfica. Executar preflight,
Creative Cloud, abertura do Premiere, projeto e exportação. Somente depois
de validar MP4 pelo FFprobe marcar o fluxo como funcional.
Não há solução gratuita comprovada para todo esse fluxo encontrada nesta pesquisa.
