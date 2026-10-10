# Experimento: Premiere Pro no Linux com Wine

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
