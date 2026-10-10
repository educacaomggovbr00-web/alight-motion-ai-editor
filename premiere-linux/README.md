# Experimento: Premiere Pro no Linux com Wine

## Resultado REAL do download Adobe (10/10/2026)

**[Ler o relatório da tentativa de download](RESULTADO-DOWNLOAD-ADOBE.md).** O link direto do Premiere retornou **HTTP 403** e não entregou o aplicativo. Conseguimos baixar **331.128.777 bytes** do instalador oficial do Creative Cloud pelo CDN da Adobe; o executável tinha **assinatura Adobe válida**. O Creative Cloud **não é o Premiere**: o Premiere ainda não foi baixado, instalado ou executado. Nenhum instalador foi adicionado ao repositório.

## Resultado real da etapa 3 (Windows)

**[Ver relatório do teste Windows](RESULTADO-TESTE-WINDOWS.md).** No GitHub Actions, o runner padrão foi **Windows Server 2025**, com vídeo virtual **Microsoft Hyper-V Video**. O **Adobe Premiere Pro não estava instalado**. Não há GPU dedicada compatível comprovada. Portanto, **Premiere não foi executado**; o teste mostra as limitações reais do servidor.

## Resultado real do teste gráfico

O teste no GitHub Actions de **10/10/2026** terminou com sucesso para Wine e Direct3D 11, mas os renderizadores OpenGL/Vulkan eram **llvmpipe (CPU)**, sem GPU física comprovada. Portanto, **o Adobe Premiere Pro não foi instalado nem validado**.

**[Leia os resultados completos](RESULTADO-TESTE-GPU.md).**

Esta pasta testa se o **Wine** (camada de compatibilidade de programas Windows)
consegue iniciar em um Linux com tela virtual. **Não contém nem instala o Premiere Pro.**

O Premiere Pro atual tem suporte oficial da Adobe para **Windows e macOS**,
não para Linux/Wine. Mesmo que o diagnóstico passe, isso **não significa** que
Premiere, Creative Cloud, GPU, login ou exportação de vídeos vão funcionar.

Fontes oficiais:
- [Requisitos atuais do Premiere](https://helpx.adobe.com/premiere/desktop/get-started/technical-requirements/adobe-premiere-pro-technical-requirements.html)
- [GitHub Actions e runners hospedados](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)

## Testar pelo GitHub no celular

1. Entre na aba [Actions](../../actions).
2. Escolha **Testar Wine para Premiere (experimental)**.
3. Toque em **Run workflow**.
4. Abra a execução e baixe o artefato **diagnostico-wine-linux** para
   ler o arquivo **resultado.md** e o log técnico **wine.log**.

O workflow instala Wine, Xvfb e ferramentas gráficas no runner temporário
Ubuntu 24.04. Ele inicia um ambiente Windows 64-bit simulado e executa
um pequeno comando do Windows. Não baixa nenhum software Adobe.

## Testar localmente num computador Linux

Instale o Wine, Xvfb e o utilitário xauth conforme sua distribuição. Depois:

    bash premiere-linux/diagnostico.sh

Para experimentar o Premiere original localmente, você precisaria de um
**instalador obtido legitimamente da Adobe**, uma licença válida e um ambiente
com recursos gráficos compatíveis. Faça isso no seu próprio computador,
não publique o instalador nem dados de ativação no repositório público.
Esta pasta não fornece bypass de ativação nem download de instaladores Adobe.

## Interpretação do resultado

- **OK:** Wine e a tela virtual conseguiram executar um comando simples.
- **Falhou:** a infraestrutura de compatibilidade não passou nem no teste básico.
- **Em ambos os casos:** o Premiere ainda **não foi testado**; desempenho,
  plugins, codecs, drivers gráficos, login Adobe e exportação continuam
  **desconhecidos**.

O editor MP4 FFmpeg existente no repositório continua independente e funcional.


## Etapa 2 — Diagnóstico de gráficos (Direct3D 11 / Vulkan)

**[Rodar o diagnóstico gráfico no GitHub Actions](../.github/workflows/testar-gpu-premiere.yml)**

1. Abra a aba **Actions**.
2. Escolha **Testar gráficos para Premiere (experimental)**.
3. Toque em **Run workflow**.
4. Abra o resultado e baixe o artefato **diagnostico-premiere-gpu**.
5. Leia o relatório resultado.md e os logs directx11.txt e vulkan.txt.

A automação instala ferramentas de código aberto, compila um executável
Windows simples a partir de **windows/d3d11_probe.c** e o executa no Wine.
Ela mede se o ambiente consegue listar adaptadores gráficos DXGI e criar
um dispositivo Direct3D 11. Também inspeciona OpenGL e Vulkan no runner.

O diagnóstico deve ser interpretado com cuidado:
- Se aparecer **llvmpipe/lavapipe**, a renderização é por **CPU**, não por GPU física.
- Os valores de memória gráfica apresentados por adaptadores virtualizados
  podem ser simulados e não comprovam VRAM real.
- O Premiere atual exige **Windows 11 v24H2** e GPU compatível com **4 GB de memória gráfica**
  para edição no Windows, entre outros requisitos.
- Mesmo que Direct3D 11 funcione, isso **não significa** compatibilidade com Premiere,
  DirectX 12, Creative Cloud ou exportação de vídeo.

Fontes:
- [Adobe: requisitos do Premiere 26.x (2026)](https://helpx.adobe.com/br/premiere/desktop/get-started/technical-requirements/adobe-premiere-pro-technical-requirements.html)
- [DXVK: requisitos de Vulkan e drivers](https://github.com/doitsujin/dxvk/wiki/Driver-support)

Nenhum programa Adobe é instalado ou incluído, e nenhum teste exige licença Adobe.


## Etapa 3 — Teste em Windows do GitHub

Criamos um teste no runner **windows-2025**:
[Executar a verificacao Windows](../.github/workflows/testar-premiere-windows.yml).

Na aba **Actions**, escolha **Testar Premiere no Windows (requisitos)**.
Quando finalizar, baixe o artefato **diagnostico-premiere-windows** com
o relatorio resultado.md.

Ele identifica:
- versao e edicao real do Windows no runner;
- RAM e controladores de video expostos;
- se existe uma instalacao local legitima do Premiere Pro no caminho padrao.

**Nao baixa ou instala Premiere, nao solicita credenciais Adobe,
nao o executa e nao exporta videos.** Mesmo com um Windows de build recente,
um runner Windows **Server** nao equivale ao Windows 11 requerido pelo Premiere.
A GPU pode ser virtual ou basica, nao uma GPU fisica compativel.

Caso o Premiere nao esteja instalado, o relatorio vai dizer isso claramente.
Para testar o aplicativo de verdade, precisamos de **Windows 11 compativel,
GPU adequada e instalacao/licenca propria**. O GitHub padrao so pode diagnosticar
seu ambiente; runners com GPU sao uma modalidade diferente, com requisitos de plano
e custo adicionais.

Fontes oficiais:
- [Adobe Premiere — requisitos 26.x](https://helpx.adobe.com/br/premiere/desktop/get-started/technical-requirements/adobe-premiere-pro-technical-requirements.html)
- [GitHub — runners hospedados, incluindo larger GPU](https://docs.github.com/en/actions/concepts/runners/github-hosted-runners)


## Etapa 4 — Tentativa REAL de baixar Premiere oficialmente

Criamos [um workflow que tenta baixar o Premiere pela URL oficial da Adobe](../.github/workflows/tentar-baixar-premiere.yml).
Ele usa o servidor Windows do GitHub (temporário) e tenta dois caminhos:

1. A **URL oficial do Premiere** (https://creativecloud.adobe.com/apps/download/premiere). Verifica se resulta em instalador executável ou apenas página de login/download.
2. O **ZIP oficial do aplicativo Creative Cloud**, que é o gerenciador usado pela Adobe para baixar e instalar o Premiere. Verifica o arquivo e, se houver executável, a assinatura Authenticode.

**O Creative Cloud não é o Premiere.** Baixar o Creative Cloud não prova que seja possível obter, instalar ou executar o Premiere automaticamente. Para utilizar o aplicativo, a Adobe exige conta e licença/teste válido, e os servidores padrão GitHub não atendem a todos os requisitos gráficos e de sistema.

Para conferir, abra **Actions → Tentar baixar Premiere (Adobe oficial)** e baixe o artefato **resultado-tentativa-premiere** depois do teste. **Nenhum instalador proprietário é armazenado no repositório nem anexado aos resultados**, e o servidor temporário apaga os downloads ao terminar. O fluxo nunca tenta ativar, instalar ou executar o Premiere.

Referência do download direto do Creative Cloud (Adobe):
https://helpx.adobe.com/pt/download-install/apps/download-install-apps/creative-cloud-apps/download-creative-cloud-desktop-app-using-direct-links.html
