# DaVinci Resolve 21.1: diagnóstico conservador pelo Console Lua

**Estado: código preparado e 22 testes locais de preflight aprovados no GitHub Actions. Não houve nova execução pesada do Resolve e não foi demonstrada edição ou renderização.**

## Diagnóstico da falha anterior

Na execução [38188809728](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38188809728), a janela principal GLX foi observada, mas o SDK Python externo não conectou, e o menu `Workspace > Scripts` não executou `CodexSyntheticSmoke.py`. O relatório mostrou `No Scripts`. Isso não deve ser automaticamente atribuído a falha de Mesa.

Um [relato independente de 21.1 Free no Linux](https://github.com/samuelgursky/davinci-resolve-mcp/issues/203) documenta que scripts `.py` deixam de aparecer no menu. A discussão também apresenta observações de um Console Lua funcional em Windows com Resolve 21.1 Free, mas não prova que esta mesma combinação funciona aqui. Não modificamos licença, binário ou preferências.

## Mudança experimental isolada

- O supervisor instala `CodexLuaProbe.lua` numa pasta de scripts oficial, sem executar projetos, importar mídia ou renderizar.
- Somente quando o menu Python não invoca o script e a janela principal já foi observada, `lua_console.py` procura por `Workspace`, `Console` e pelo prompt explícito `Lua>`, via capturas e OCR.
- Caso qualquer confirmação visual falhe, o fallback **não digita nada**. Com todas reconhecidas, envia somente um comando fixo `dofile` para o probe de leitura.
- O probe consulta o objeto `resolve` e, quando o ambiente suporta `bmd.writestring`, registra `apiConnected`, versão e nome do produto. Não registra segredos, arquivos pessoais ou dados de licença.
- O JSON do supervisor diferencia `luaApiReachable` de `nativeRenderProven`. Mesmo que a API Lua seja acessível, o workflow pesado **continua falhando** enquanto um render nativo e MP4 validado não existirem.

## Como verificar sem consumir uma execução pesada automaticamente

A alteração está numa branch separada e preserva o workflow manual original. O workflow leve **DaVinci Resolve — diagnostico, nao renderiza** roda o teste `test_safety.py` sem instalar Resolve. A [execução 38261394792](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38261394792) aprovou os 22 testes.

Para testar o Console real futuramente, só execute manualmente o workflow DVIP da branch com fonte oficial válida e disponibilidade de minutos do GitHub Actions. Leia `glx/result.json` e os arquivos `glx/lua-console-*.png` / `glx/lua-console-*.log` no artefato sintético. Em modo de mídia privada, capturas e logs não são publicados.

Este teste serve para decidir se faz sentido desenvolver um editor Lua interno **usando apenas as capacidades efetivamente disponíveis**. Não demonstra nem tenta contornar funcionalidades pagas.
