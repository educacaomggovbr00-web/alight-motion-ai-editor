# Resolve 21.1 Free: Console sem prompt visível

Tentativa privada #38282441070: DaVinci original iniciou e abriu janela GLX,
mas o OCR do painel Console não reconheceu **nenhum** token Lua. O código não
digitou e não produziu vídeo. O diagnóstico anterior também não exibia script
no menu Workspace > Scripts.

A nova mudança testa o bloqueio de **visibilidade do Console em resolução baixa**:
a área virtual Xvfb sobe de 1280×720 para 1920×1080. O campo de entrada pode
estar abaixo da região renderizada em 720p. A lógica de onboarding localiza
o botão Continue em janela centralizada também na nova resolução.

Na tela de Console, o script verifica a entrada com OCR PSM 11, fallback PSM 6
e um recorte OCR separado do terço inferior, sempre exigindo literalmente
`Lua>` antes de digitar. O relatório registra apenas dimensões, categorias
de UI permitidas, posição de prompt e booleano de janela focada. **Não
copia texto de vídeo privado, pixels brutos ou caminhos para logs públicos.**

O modo gratuito 21.1 pode ter um console unificado sem seletor Lua/Py3;
não inventar um seletor nem afirmar que a API está acessível sem prova:
https://github.com/samuelgursky/davinci-resolve-mcp/issues/203

**Status:** correção experimental de visibilidade; só uma execução do DaVinci
21.1.1 original e relatório de origem podem comprovar que o prompt funciona.
Não altera binário ou licença. Falha fechada sem prompt Lua identificável.
