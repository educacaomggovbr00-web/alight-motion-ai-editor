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
